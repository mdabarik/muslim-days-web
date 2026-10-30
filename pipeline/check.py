#!/usr/bin/env python3
"""Validate a transcript and print its word/letter table.

usage: .venv/bin/python pipeline/check.py 752
Exit code 0 means the transcript is structurally valid (not that it is correct).
"""
import json
import sys

from transcript import ROOT, describe, validate


def main():
    page = int(sys.argv[1])
    path = ROOT / "transcripts" / f"{page:03d}.json"
    try:
        t = json.loads(path.read_text())
    except FileNotFoundError:
        raise SystemExit(f"missing {path.relative_to(ROOT)}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"invalid JSON in {path.relative_to(ROOT)}: {e}")
    errors, warnings = validate(t, page)
    print(describe(t))
    for w in warnings:
        print("WARN", w)
    for e in errors:
        print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} errors")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
