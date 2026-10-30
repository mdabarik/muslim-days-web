#!/usr/bin/env python3
"""Turn transcripts/NNN.json into the web page JSON and refresh the manifest.

usage: .venv/bin/python pipeline/build.py 752 [751 ...]
       .venv/bin/python pipeline/build.py --manifest   (only recompute the manifest)
Writes data/pages/NNN.json and the identical webview/data/pages/NNN.json.
"""
import json
import re
import sys

from transcript import ROOT, build, validate

OUTPUTS = [ROOT / "data", ROOT / "webview" / "data"]


def write_json(path, value):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False))
    tmp.replace(path)


def build_page(page):
    t = json.loads((ROOT / "transcripts" / f"{page:03d}.json").read_text())
    errors, _ = validate(t, page)
    if errors:
        raise SystemExit(f"page {page}: transcript invalid, run pipeline/check.py {page}")
    doc = build(t)
    for out in OUTPUTS:
        write_json(out / "pages" / f"{page:03d}.json", doc)


def page_entry(page, doc):
    rows = doc["originalCandidate"]["rows"]
    segs = [s for r in rows for s in r["arabic_segments"]]
    refs = list(dict.fromkeys(s["ayah_ref"] for s in segs if re.fullmatch(r"\d+:\d+", s.get("ayah_ref") or "")))
    surahs = sorted({int(r.split(":")[0]) for r in refs} |
                    {h["surah"] for h in doc["originalCandidate"].get("surah_headers") or []})
    return {"page": page, "status": doc.get("status"), "fullyVerified": bool(doc.get("fullyVerified")),
            "file": f"data/pages/{page:03d}.json", "surahs": surahs, "ayahs": refs, "rows": len(rows),
            "words": sum(len(s["words"]) for s in segs), "annotations": len(doc.get("annotations") or [])}


def refresh_manifest():
    path = ROOT / "data" / "manifest.json"
    manifest = json.loads(path.read_text())
    old = {p["page"]: p for p in manifest["pages"]}
    pages = []
    for page in sorted(old):
        doc = json.loads((ROOT / "data" / "pages" / f"{page:03d}.json").read_text())
        if doc.get("transcription") == "scan-2026-10":
            pages.append(dict(old[page], **page_entry(page, doc)))
        else:
            pages.append(dict(old[page], status=doc.get("status"), fullyVerified=bool(doc.get("fullyVerified"))))
    manifest["pages"] = pages
    # A surah's page list comes from the fresh scan transcripts where they exist.
    fresh = {p["page"] for p in pages if p.get("status") == "scan_transcribed"}
    for s in manifest["surahs"]:
        kept = [p for p in s.get("pages", []) if p not in fresh]
        s["pages"] = sorted(set(kept) | {p["page"] for p in pages if p["page"] in fresh and s["id"] in p["surahs"]})
        s["verified"] = False
        s["status"] = "draft"
    summary = manifest["summary"]
    summary["fullyVerifiedPages"] = sum(p["fullyVerified"] for p in pages)
    summary["verifiedSurahs"] = 0
    summary["verifiedLetterAnchors"] = 0
    summary["scanTranscribedPages"] = len(fresh)
    manifest["blockingIssues"] = [
        f"{len(pages) - len(fresh)} pages still carry the old OCR draft and are queued for fresh scan transcription.",
        "Scan transcriptions are single-pass readings; no page has an independent final review yet.",
    ]
    for out in OUTPUTS:
        write_json(out / "manifest.json", manifest)


def main():
    args = sys.argv[1:]
    for a in args:
        if a != "--manifest":
            build_page(int(a))
    refresh_manifest()


if __name__ == "__main__":
    main()
