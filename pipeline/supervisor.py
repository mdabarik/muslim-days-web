#!/usr/bin/env python3
"""Keep transcribing pages, newest first, with a few headless Claude workers.

Runs forever under launchd (pipeline/install.sh). It survives restarts because
all progress lives in pipeline/state/progress.json; a page counts as done only
after its transcript validates and builds. When Claude reports a usage limit,
no new work starts until the limit resets, then it carries on by itself.

usage: .venv/bin/python pipeline/supervisor.py            # run the queue
       .venv/bin/python pipeline/supervisor.py --once 752 # one page, foreground
Every 10 minutes it also runs pipeline/autopush.sh (commit + push of data).
env:   QURAN_WORKERS (default 3), QURAN_MODEL (default opus)
"""
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "pipeline" / "state"
LOGS = ROOT / "pipeline" / "logs"
PROGRESS = STATE / "progress.json"
PY = str(ROOT / ".venv" / "bin" / "python")
CLAUDE = os.environ.get("CLAUDE_BIN", str(Path.home() / ".local" / "bin" / "claude"))
WORKERS = int(os.environ.get("QURAN_WORKERS", "3"))
MODEL = os.environ.get("QURAN_MODEL", "opus")
FIRST, LAST = 1, 752
TIMEOUT = 50 * 60
PUSH_EVERY = 10 * 60
MAX_ATTEMPTS = 3
AUTH_RE = re.compile(r"not logged in|please run /login|invalid api key|oauth token|authentication", re.I)
LIMIT_RE = re.compile(r"usage limit|rate limit|limit reached|hit your limit|resets? (at )?\d|429|overloaded|quota", re.I)
ALLOWED = ["Read", "Write", "Edit",
           "Bash(.venv/bin/python pipeline/prepare.py *)",
           "Bash(.venv/bin/python pipeline/crop.py *)",
           "Bash(.venv/bin/python pipeline/check.py *)"]


def log(msg):
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def load():
    try:
        return json.loads(PROGRESS.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"pages": {}, "pause_until": None}


def save(state):
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = PROGRESS.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True))
    tmp.replace(PROGRESS)


def prompt(page):
    text = (ROOT / "pipeline" / "worker_prompt.md").read_text()
    return text.replace("{PAGE3}", f"{page:03d}").replace("{PAGE}", str(page))


def start(page):
    LOGS.mkdir(parents=True, exist_ok=True)
    out = open(LOGS / f"{page:03d}.log", "a")
    out.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} start page {page}\n")
    out.flush()
    cmd = [CLAUDE, "-p", prompt(page), "--model", MODEL, "--permission-mode", "acceptEdits",
           "--allowedTools", *ALLOWED, "--output-format", "text"]
    # Use the CLI's own login, never auth inherited from a parent Claude session.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("ANTHROPIC_", "CLAUDE_CODE_", "CLAUDE_AGENT_", "CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT"))}
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                            env=env, start_new_session=True)
    return proc, out


def tail(page, n=4000):
    try:
        return (LOGS / f"{page:03d}.log").read_text()[-n:]
    except FileNotFoundError:
        return ""


def reset_time(text):
    """Best effort: '... resets 3pm' / 'resets at 15:00' / '|1761811200'. Fallback 20 min."""
    now = datetime.now()
    m = re.search(r"\|(\d{10})\b", text)
    if m:
        return datetime.fromtimestamp(int(m.group(1))) + timedelta(minutes=2)
    m = re.search(r"resets?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text, re.I)
    if m:
        h, mi = int(m.group(1)), int(m.group(2) or 0)
        if m.group(3):
            h = h % 12 + (12 if m.group(3).lower() == "pm" else 0)
        t = now.replace(hour=h % 24, minute=mi, second=0, microsecond=0)
        if t <= now:
            t += timedelta(days=1)
        return t + timedelta(minutes=2)
    return now + timedelta(minutes=20)


def finish(page, proc, state):
    """Check a finished worker. Returns True if the run hit a usage limit."""
    entry = state["pages"].setdefault(str(page), {"attempts": 0})
    out = tail(page)
    check = subprocess.run([PY, "pipeline/check.py", str(page)], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode == 0 and check.returncode == 0:
        build = subprocess.run([PY, "pipeline/build.py", str(page)], cwd=ROOT, capture_output=True, text=True)
        if build.returncode == 0:
            m = re.search(r"PAGE \d+ DONE[^\n]*", out)
            entry.update(status="done", built_mtime=(ROOT / "transcripts" / f"{page:03d}.json").stat().st_mtime, note=m.group(0) if m else "done", updated=f"{datetime.now():%Y-%m-%d %H:%M}")
            log(f"page {page} done")
            return False
        out += build.stdout + build.stderr
    last_lines = "\n".join(out.strip().splitlines()[-6:])
    if proc.returncode != 0 and AUTH_RE.search(last_lines):
        state["pause_until"] = (datetime.now() + timedelta(minutes=10)).isoformat(timespec="minutes")
        entry["status"] = "pending"
        log(f"page {page}: Claude CLI is not logged in; run `claude` then /login. Retrying in 10 min")
        return True
    if proc.returncode != 0 and LIMIT_RE.search(last_lines):
        until = reset_time(last_lines)
        state["pause_until"] = until.isoformat(timespec="minutes")
        entry["status"] = "pending"
        log(f"page {page}: usage limit, pausing until {until:%H:%M}")
        return True
    entry["attempts"] = entry.get("attempts", 0) + 1
    entry["status"] = "failed" if entry["attempts"] >= MAX_ATTEMPTS else "pending"
    entry["note"] = (check.stdout.strip().splitlines() or ["no transcript"])[-1][:200]
    entry["updated"] = f"{datetime.now():%Y-%m-%d %H:%M}"
    log(f"page {page}: attempt {entry['attempts']} failed ({entry['note']})")
    return False


def absorb_transcripts(state, busy):
    """Build transcripts written elsewhere (e.g. by in-session agents) once they validate.
    A transcript edited after its last build is rebuilt; one still invalid is left alone."""
    changed = False
    for path in sorted((ROOT / "transcripts").glob("*.json")):
        page = int(path.stem)
        entry = state["pages"].get(str(page), {})
        mtime = path.stat().st_mtime
        if page in busy or entry.get("built_mtime") == mtime or time.time() - mtime < 120:
            continue
        check = subprocess.run([PY, "pipeline/check.py", str(page)], cwd=ROOT, capture_output=True, text=True)
        if check.returncode != 0:
            continue
        build = subprocess.run([PY, "pipeline/build.py", str(page)], cwd=ROOT, capture_output=True, text=True)
        if build.returncode == 0:
            state["pages"][str(page)] = dict(entry, status="done", built_mtime=mtime,
                                             note=entry.get("note") or "transcript built",
                                             updated=f"{datetime.now():%Y-%m-%d %H:%M}")
            log(f"page {page} built from transcript")
            changed = True
    return changed


def next_pages(state, busy):
    for page in range(LAST, FIRST - 1, -1):
        e = state["pages"].get(str(page), {})
        if page not in busy and e.get("status") not in ("done", "failed"):
            yield page


def run_queue():
    STATE.mkdir(parents=True, exist_ok=True)
    lock = open(STATE / "lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("another supervisor is running; exiting")
        return
    state = load()
    for e in state["pages"].values():
        if e.get("status") == "running":
            e["status"] = "pending"
    save(state)
    running = {}
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    log(f"supervisor up: {WORKERS} workers, model {MODEL}")
    last_push = 0.0
    while not stopping:
        # Commit and push progress every 10 minutes, even while paused.
        if time.time() - last_push >= PUSH_EVERY:
            last_push = time.time()
            subprocess.Popen(["/bin/zsh", "pipeline/autopush.sh"], cwd=ROOT, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for page, (proc, out, started) in list(running.items()):
            if proc.poll() is None and time.time() - started > TIMEOUT:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait()
                log(f"page {page}: timed out")
            if proc.poll() is not None:
                out.close()
                del running[page]
                finish(page, proc, state)
                save(state)
        if absorb_transcripts(state, running):
            save(state)
        pause = state.get("pause_until")
        paused = pause and datetime.now() < datetime.fromisoformat(pause)
        if not paused and pause:
            state["pause_until"] = None
            save(state)
            log("usage limit window over; resuming")
        if not paused:
            for page in next_pages(state, running):
                if len(running) >= WORKERS:
                    break
                proc, out = start(page)
                running[page] = (proc, out, time.time())
                state["pages"].setdefault(str(page), {"attempts": 0})["status"] = "running"
                save(state)
                log(f"page {page} started (pid {proc.pid})")
        if not running and not paused and next(next_pages(state, running), None) is None:
            log("queue finished")
            while not stopping:
                time.sleep(3600)
        time.sleep(15)
    for page, (proc, out, _) in running.items():
        os.killpg(proc.pid, signal.SIGTERM)
        state["pages"][str(page)]["status"] = "pending"
    save(state)
    log("supervisor stopped")


def run_once(page):
    state = load()
    proc, out = start(page)
    proc.wait()
    out.close()
    finish(page, proc, state)
    save(state)
    print(json.dumps(state["pages"].get(str(page)), ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--once":
        run_once(int(sys.argv[2]))
    else:
        run_queue()
