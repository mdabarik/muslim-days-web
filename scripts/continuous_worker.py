#!/usr/bin/env python3
"""
Continuous verification daemon for Quran webview.
Verifies pages one by one, logs progress, and ensures continuous work.
"""
import os
import sys
import time
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKER_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "verify_worker.py")
PID_FILE = os.path.join(PROJECT_ROOT, "quran-verification", "daemon.pid")

def main():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    print(f"Starting continuous verification daemon (PID: {os.getpid()})...")

    while True:
        try:
            # Run one page step
            res = subprocess.run([sys.executable, WORKER_SCRIPT, "1"], capture_output=True, text=True)
            print(res.stdout, end="")
            if res.stderr:
                print(res.stderr, file=sys.stderr, end="")

            # Small pause between pages
            time.sleep(3)
        except Exception as e:
            print(f"Daemon exception: {e}", file=sys.stderr)
            time.sleep(10)

if __name__ == "__main__":
    main()
