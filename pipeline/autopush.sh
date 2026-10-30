#!/bin/zsh
# Commit and push transcription progress. launchd runs this every 10 minutes.
# Only data paths are staged; code changes are never swept into these commits.
set -u
cd "${0:A:h}/.."
branch=features/full-quran-transcription
log=pipeline/logs/autopush.log
mkdir -p pipeline/logs
stamp() { print -r -- "$(date '+%Y-%m-%d %H:%M:%S') $*" >> $log }

[[ "$(git branch --show-current)" == "$branch" ]] || { stamp "not on $branch, skipped"; exit 0 }
[[ -e .git/index.lock || -e .git/MERGE_HEAD || -d .git/rebase-merge || -d .git/rebase-apply ]] && { stamp "git busy, skipped"; exit 0 }

git add -- transcripts data webview/data pipeline/state/progress.json 2>>$log
if git diff --cached --quiet; then
  stamp "nothing new"
else
  done=$(.venv/bin/python -c 'import json;p=json.load(open("pipeline/state/progress.json"))["pages"];print(sum(v.get("status")=="done" for v in p.values()))' 2>/dev/null || echo "?")
  git commit -q -m "data(quran): scan transcription progress, $done pages done" >>$log 2>&1 && stamp "committed ($done pages done)"
fi

if [[ -n "$(git log --oneline @{u}..HEAD 2>/dev/null)" ]]; then
  if git push -q origin "$branch" >>$log 2>&1; then stamp "pushed"; else stamp "push failed, will retry next run"; fi
fi
