"""Scan transcript format, validation and conversion to the web page JSON.

A transcript (transcripts/NNN.json) is what a worker reads off one scanned page:

{
  "page": 752,                       # physical PDF page
  "printed_page": "৭৫৩",
  "surah_headers": [ {"surah": 113, "before_row": 0, "arabic": "سورة الفلق",
                      "bengali": "সূরা ফালাক্ব", "surah_number_bn": "সূরা-১১৩",
                      "revelation_bn": "মাক্কী", "ruku_bn": "রুকু-১",
                      "ayah_count_bn": "আয়াত-৫", "basmala": "بِسْمِ ..."} ],
  "rows": [ {
      "segments": [ {"ayah_ref": "113:1", "words": ["قُلْ", "اَعُوْذُ", ...],
                     "verse_number_bn": "১"} ],          # null if the ayah continues
      "annotations": [ {"glyph": "১", "enclosure": "circle", "label_bn": "এক আলিফ",
                        "layer": "band", "word": 2, "letter": 3} ],
      "bengali": [ {"ayah_ref": "113:1", "numeral_bn": "১", "text": "বল, ..."} ]
  } ],
  "non_quran": "short note about other printed content (du'a, index...)",
  "unresolved": ["anything that could not be read with confidence"]
}

`word` is 1-based across the whole row in reading order (right to left).
`letter` is the 1-based letter cluster inside that word (see `clusters`).
"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF_SHA = "73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640"
ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿‌‍]")
BENGALI_DIGITS = set("০১২৩৪৫৬৭৮৯")
SYMBOLS = {s["id"]: s for s in json.loads((ROOT / "data" / "symbol-catalog.json").read_text())["symbols"]}


def clusters(text):
    """Base character plus the combining marks that follow it."""
    out = []
    for i, c in enumerate(text):
        if unicodedata.category(c).startswith("M") and out:
            out[-1]["text"] += c
            out[-1]["end"] = i + 1
        else:
            out.append({"text": c, "start": i, "end": i + 1})
    return out


def row_words(row):
    return [w for seg in row.get("segments", []) for w in seg.get("words", [])]


def validate(t, page):
    errors, warnings = [], []
    if t.get("page") != page:
        errors.append(f"page is {t.get('page')!r}, expected {page}")
    rows = t.get("rows")
    if not isinstance(rows, list):
        return ["rows must be a list"], warnings
    for h in t.get("surah_headers") or []:
        if not isinstance(h.get("surah"), int) or not 1 <= h["surah"] <= 114:
            errors.append(f"surah header has bad surah {h.get('surah')!r}")
        if not isinstance(h.get("before_row"), int) or not 0 <= h["before_row"] <= len(rows):
            errors.append(f"surah header {h.get('surah')} has bad before_row {h.get('before_row')!r}")
    for r, row in enumerate(rows):
        segs = row.get("segments") or []
        if not segs:
            errors.append(f"row {r}: no segments")
        for s, seg in enumerate(segs):
            ref = seg.get("ayah_ref", "")
            m = re.fullmatch(r"(\d{1,3}):(\d{1,3})", ref or "")
            if not m or not 1 <= int(m.group(1)) <= 114:
                errors.append(f"row {r} seg {s}: bad ayah_ref {ref!r}")
            words = seg.get("words") or []
            if not words:
                errors.append(f"row {r} seg {s}: no words")
            for w in words:
                if not isinstance(w, str) or not w.strip() or " " in w:
                    errors.append(f"row {r} seg {s}: bad word {w!r}")
                elif not ARABIC.search(w):
                    errors.append(f"row {r} seg {s}: word {w!r} has no Arabic letters")
                elif re.search(r"[A-Za-z0-9,:;«»|_]", w):
                    errors.append(f"row {r} seg {s}: word {w!r} has non-Arabic characters")
            num = seg.get("verse_number_bn")
            if num is not None and (not num or not set(num) <= BENGALI_DIGITS):
                errors.append(f"row {r} seg {s}: verse_number_bn must be Bengali digits or null")
            if num and m and str(int(m.group(2))) != num.translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")):
                errors.append(f"row {r} seg {s}: verse number {num} does not match {ref}")
        words = row_words(row)
        for a, ann in enumerate(row.get("annotations") or []):
            where = f"row {r} annotation {a + 1} ({ann.get('glyph')!r})"
            if ann.get("layer") not in ("band", "arabic"):
                errors.append(f"{where}: layer must be 'band' or 'arabic'")
            if ann.get("enclosure") not in ("none", "circle"):
                errors.append(f"{where}: enclosure must be 'none' or 'circle'")
            if ann.get("symbol") and ann["symbol"] not in SYMBOLS:
                errors.append(f"{where}: unknown symbol {ann['symbol']!r}")
            if not ann.get("glyph") and not ann.get("symbol"):
                errors.append(f"{where}: needs glyph or symbol")
            if not ann.get("label_bn"):
                warnings.append(f"{where}: no label_bn")
            wi, li = ann.get("word"), ann.get("letter")
            if not isinstance(wi, int) or not 1 <= wi <= len(words):
                errors.append(f"{where}: word {wi!r} outside 1..{len(words)}")
                continue
            n = len(clusters(words[wi - 1]))
            if not isinstance(li, int) or not 1 <= li <= n:
                errors.append(f"{where}: letter {li!r} outside 1..{n} of {words[wi - 1]}")
        for b in row.get("bengali") or []:
            if not b.get("text"):
                errors.append(f"row {r}: empty Bengali segment")
    if not rows and not t.get("non_quran"):
        errors.append("no rows and no non_quran note")
    return errors, warnings


def describe(t):
    """Human-readable table so a worker can re-check every anchor."""
    lines = []
    for r, row in enumerate(t.get("rows", [])):
        words = row_words(row)
        lines.append(f"row {r}: {len(words)} words, {len(row.get('annotations') or [])} annotations")
        for i, w in enumerate(words, 1):
            cl = " ".join(f"{k}:{c['text']}" for k, c in enumerate(clusters(w), 1))
            marks = [a for a in row.get("annotations") or [] if a.get("word") == i]
            ms = ", ".join(f"{a.get('glyph') or a.get('symbol')}{'(o)' if a.get('enclosure') == 'circle' else ''}"
                           f"@{a.get('letter')}/{a.get('layer')}" for a in marks)
            lines.append(f"  w{i:<2} {w}   [{cl}]" + (f"   <= {ms}" if ms else ""))
    return "\n".join(lines)


def build(t):
    page = t["page"]
    pre = f"p{page}"
    rows, annotations, graphemes = [], [], {}
    for r, row in enumerate(t["rows"]):
        word_ids, segs = [], []
        n = 0
        for seg in row["segments"]:
            words = []
            for w in seg["words"]:
                n += 1
                wid = f"r{r}w{n}"
                word_ids.append((wid, w))
                words.append({"id": wid, "text": w, "bbox": None})
                graphemes[wid] = [{"id": f"{pre}:{wid}:g{k}", "text": c["text"], "startCodepoint": c["start"],
                                   "endCodepoint": c["end"], "sourceBox": None, "verified": False}
                                  for k, c in enumerate(clusters(w))]
            num = seg.get("verse_number_bn")
            segs.append({"ayah_ref": seg["ayah_ref"], "text": " ".join(seg["words"]), "words": words, "bbox": None,
                         "stop_sign": None,
                         "verse_marker": {"numeral_bn": num, "form": "rosette", "bbox": None} if num else None,
                         "confidence": {"level": "medium", "basis": "Read from the 300 dpi scan of the original PDF page."}})
        glyphs = []
        for k, ann in enumerate(row.get("annotations") or [], 1):
            wid, wtext = word_ids[ann["word"] - 1]
            count = len(clusters(wtext))
            sid = f"r{r}-a{k}"
            glyphs.append({"id": sid, "printed": ann.get("glyph") or "", "enclosure": ann["enclosure"],
                           "legend_bengali": ann.get("label_bn") or "", "layer": ann["layer"],
                           "attachment": {"target": wid, "basis": "scan_letter", "letter": ann["letter"],
                                          "offset_in_word": round((ann["letter"] - 0.5) / count, 4)}})
            rec = {"id": f"{pre}:{sid}", "rowIndex": r, "sourceId": sid, "text": ann.get("glyph") or "",
                   "layer": ann["layer"], "targetGraphemeId": f"{pre}:{wid}:g{ann['letter'] - 1}",
                   "anchor": "letter_from_scan", "verified": False, "unresolved": []}
            if ann.get("symbol"):
                sym = SYMBOLS[ann["symbol"]]
                rec["display"] = {"status": "source_shape_candidate", "symbolId": sym["id"], "character": sym["text"],
                                  "fontFamily": sym["fontFamily"], "labelBn": ann.get("label_bn") or sym["labelBn"]}
            annotations.append(rec)
        rows.append({"row_index": r, "bbox": None,
                     "annotation_band": {"bbox": None, "glyphs": glyphs},
                     "arabic_segments": segs,
                     "bengali_segments": [{"ayah_ref": b.get("ayah_ref"), "numeral_bn": b.get("numeral_bn") or "",
                                           "text": b["text"], "bbox": None} for b in row.get("bengali") or []]})
    headers = [dict(h, bbox=None) for h in t.get("surah_headers") or []]
    candidate = {
        "schema_version": "2.0.0-scan",
        "source": {"pdf_sha256": PDF_SHA, "pdf_page_number": page},
        "printed_page": t.get("printed_page"),
        "expected_rows": len(rows),
        "surah_header": None, "basmala": None,
        "surah_headers": headers,
        "rows": rows,
        "page_furniture": [t["non_quran"]] if t.get("non_quran") else [],
        "non_content_marks": [],
        "provenance": {"method": "Fresh visual transcription of the 300 dpi scan: Arabic words, Bengali translation and every upper sign anchored to its letter.",
                       "transcription": "scan-2026-10", "reviewed_by": None},
        "unresolved": [{"id": f"P{page}-U{i}", "question": q, "blocking": False}
                       for i, q in enumerate(t.get("unresolved") or [], 1)],
    }
    return {
        "schemaVersion": "2.0.0-draft",
        "source": {"pdf_sha256": PDF_SHA, "pdf_page_number": page,
                   "coordinate_system": "pdf-300dpi origin top-left pixels [x,y,width,height]"},
        "status": "scan_transcribed",
        "fullyVerified": False,
        "transcription": "scan-2026-10",
        "originalCandidate": candidate,
        "annotations": annotations,
        "symbolCatalogue": {"url": "data/symbol-catalog.json", "contract": "source-shapes-pua-1"},
        "graphemes": graphemes,
    }
