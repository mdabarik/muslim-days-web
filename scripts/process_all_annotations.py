#!/usr/bin/env python3
"""
Batch annotation extractor for Quran pages (Page 16 to 752).
Renders scanned PDF pages, detects Tajweed annotation symbols across all rows,
and updates page JSONs and manifests.
"""
import os
import sys
import json
import subprocess
import time
import numpy as np
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
PDF_PATH = "/Users/barik/Desktop/Life & Love/muslims-days/source-pdf/Quran - Qariyana Quranul Karim.pdf"
RENDERS_DIR = os.path.join(PROJECT_ROOT, "quran-verification", "renders")
LOG_FILE = os.path.join(PROJECT_ROOT, "quran-verification", "extractor.log")

from scripts.extract_page_annotations import extract_annotations_for_row

def log(msg):
    t = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{t}] {msg}\n"
    print(line, end="")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except Exception:
        pass

def render_page(p_num):
    os.makedirs(RENDERS_DIR, exist_ok=True)
    out_prefix = os.path.join(RENDERS_DIR, f"page_{p_num:03d}")
    target_png = f"{out_prefix}-{p_num:03d}.png"
    if os.path.exists(target_png):
        return target_png
    # Check alternate naming
    matches = [f for f in os.listdir(RENDERS_DIR) if f.startswith(f"page_{p_num:03d}") and f.endswith(".png")]
    if matches:
        return os.path.join(RENDERS_DIR, matches[0])
    
    cmd = ["/opt/homebrew/bin/pdftoppm", "-png", "-r", "300", "-f", str(p_num), "-l", str(p_num), PDF_PATH, out_prefix]
    subprocess.run(cmd, check=True)
    matches = [f for f in os.listdir(RENDERS_DIR) if f.startswith(f"page_{p_num:03d}") and f.endswith(".png")]
    if matches:
        return os.path.join(RENDERS_DIR, matches[0])
    return None

def process_page(p_num):
    p_str = f"{p_num:03d}"
    page_file = os.path.join(PROJECT_ROOT, "data", "pages", f"{p_str}.json")
    webview_page_file = os.path.join(PROJECT_ROOT, "webview", "data", "pages", f"{p_str}.json")

    if not os.path.exists(page_file):
        return 0

    with open(page_file) as f:
        d = json.load(f)

    # Check if page already has annotations
    ann_count = len(d.get("annotations", []))
    if ann_count > 20 and p_num != 16:
        log(f"Page {p_str} already has {ann_count} annotations, skipping.")
        return ann_count

    png_path = render_page(p_num)
    if not png_path or not os.path.exists(png_path):
        log(f"Page {p_str}: render failed.")
        return 0

    im = Image.open(png_path).convert("L")
    arr = np.array(im)
    w, h = im.size

    y0 = 145
    row_h = 285

    all_page_annotations = []
    rows = d.get("originalCandidate", {}).get("rows", [])
    for r_idx in range(len(rows)):
        top = y0 + r_idx * row_h
        bot = top + row_h
        row_crop = arr[top:bot, 100:w-100]

        row_obj = rows[r_idx]
        row_words = []
        for s in row_obj.get("arabic_segments", []):
            row_words.extend(s.get("words", []))

        glyphs, anns = extract_annotations_for_row(row_crop, r_idx, p_num, row_words)
        row_obj["annotation_band"] = {
            "bbox": [100, top, w - 200, 65],
            "glyphs": glyphs
        }
        all_page_annotations.extend(anns)

    d["annotations"] = all_page_annotations
    d["status"] = "draft_with_cv_annotations"

    for out_p in [page_file, webview_page_file]:
        if os.path.exists(os.path.dirname(out_p)):
            with open(out_p, "w") as f:
                json.dump(d, f, ensure_ascii=False)

    log(f"Page {p_str}: successfully extracted {len(all_page_annotations)} annotations across {len(rows)} rows!")
    return len(all_page_annotations)

def update_manifest():
    for mpath in [
        os.path.join(PROJECT_ROOT, "data", "manifest.json"),
        os.path.join(PROJECT_ROOT, "webview", "data", "manifest.json")
    ]:
        if not os.path.exists(mpath):
            continue
        with open(mpath) as f:
            m = json.load(f)

        total_ann = 0
        for p in m.get("pages", []):
            pfile = os.path.join(PROJECT_ROOT, p["file"])
            if os.path.exists(pfile):
                try:
                    with open(pfile) as pf:
                        pd = json.load(pf)
                    cnt = len(pd.get("annotations", []))
                    p["annotations"] = cnt
                    total_ann += cnt
                except Exception:
                    pass

        m["summary"]["annotations"] = total_ann
        with open(mpath, "w") as f:
            json.dump(m, f, ensure_ascii=False)

if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 17
    end = int(sys.argv[2]) if len(sys.argv) > 2 else start + 3

    log(f"Starting batch extraction for pages {start} to {end}...")
    for p in range(start, end + 1):
        process_page(p)
        update_manifest()
