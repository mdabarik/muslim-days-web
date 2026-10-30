#!/bin/zsh
# Install (or remove) the launchd agent that keep the transcription running.
#   pipeline/install.sh            install and start
#   pipeline/install.sh uninstall  stop and remove
#   pipeline/install.sh status     show what is running
set -eu
root="${0:A:h:h}"
agents=~/Library/LaunchAgents
sup=com.muslimdays.quran-supervisor
push=com.muslimdays.quran-autopush
uid=$(id -u)
agent_path="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

case "${1:-install}" in
uninstall)
  for a in $sup $push; do launchctl bootout gui/$uid/$a 2>/dev/null || true; rm -f $agents/$a.plist; done
  print "removed"; exit 0 ;;
status)
  for a in $sup $push; do launchctl print gui/$uid/$a 2>/dev/null | grep -E '^\s*(state|pid|last exit code) ' | sed "s/^/$a /" || print "$a not loaded"; done
  exit 0 ;;
esac

mkdir -p $agents "$root/pipeline/logs"
chmod +x "$root/pipeline/autopush.sh"

# Supervisor: always running, restarted by launchd if it exits; caffeinate -i
# keeps the Mac from idle-sleeping while it works (the screen can still sleep).
cat > $agents/$sup.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$sup</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/caffeinate</string><string>-i</string>
    <string>$root/.venv/bin/python</string><string>$root/pipeline/supervisor.py</string>
  </array>
  <key>WorkingDirectory</key><string>$root</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>$agent_path</string>
    <key>HOME</key><string>$HOME</string>
    <key>QURAN_WORKERS</key><string>${QURAN_WORKERS:-3}</string>
    <key>QURAN_MODEL</key><string>${QURAN_MODEL:-opus}</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>60</integer>
  <key>Nice</key><integer>10</integer>
  <key>StandardOutPath</key><string>$root/pipeline/logs/supervisor.log</string>
  <key>StandardErrorPath</key><string>$root/pipeline/logs/supervisor.log</string>
</dict></plist>
EOF

launchctl bootout gui/$uid/$push 2>/dev/null || true; rm -f $agents/$push.plist
for a in $sup; do
  launchctl bootout gui/$uid/$a 2>/dev/null && sleep 3 || true
  launchctl bootstrap gui/$uid $agents/$a.plist
done
print "installed: $sup (always on; commits and pushes every 10 min)"
print "logs: $root/pipeline/logs/"
