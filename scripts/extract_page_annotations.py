#!/usr/bin/env python3
"""
Automated annotation extractor using Computer Vision & Template Matching.
Extracts upper Tajweed / Qari annotation symbols from scanned Quran pages.
"""
import os
import sys
import json
import glob
import numpy as np
from PIL import Image
from scipy import ndimage

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON_DIR = os.path.join(PROJECT_ROOT, "quran-verification", "canonical_templates")

# Load canonical symbol templates
CANON_TEMPLATES = {}
SYMBOL_MAP = {
    "gonnah_go": ("গ", "none", "গুণ্নাহ"),
    "one_alif_1": ("১", "none", "এক আলিফ"),
    "two_alif_2": ("২", "none", "দুই আলিফ"),
    "mota_mo": ("ম", "none", "মোটা"),
    "shish_sho": ("শ", "none", "শীষ"),
    "qolqolah_ko": ("ক", "none", "কলকলাহ"),
    "arabic_sakin": (None, "oval", "আরবী সাকিন"),
    "cond_6": ("৬", "none", "দম ফেলিলে তিন / না ফেলিলে এক")
}

def load_canonical_templates():
    if CANON_TEMPLATES:
        return
    for path in glob.glob(os.path.join(CANON_DIR, "*.png")):
        name = os.path.splitext(os.path.basename(path))[0]
        im = Image.open(path).convert("L").resize((32, 32))
        CANON_TEMPLATES[name] = np.array(im) < 128

def classify_patch(patch_arr):
    load_canonical_templates()
    im = Image.fromarray(patch_arr).resize((32, 32))
    arr = np.array(im)
    best_name, best_score = None, 0.0
    for name, carr in CANON_TEMPLATES.items():
        intersection = np.sum(arr & carr)
        union = np.sum(arr | carr)
        score = intersection / max(1, union)
        if score > best_score:
            best_score = score
            best_name = name
    if best_score >= 0.45:
        return best_name, best_score
    return None, best_score

def extract_annotations_for_row(row_crop_arr, row_index, page_num, words):
    """
    Given a row image (approx 285px high) and its words,
    extracts all upper annotation symbols and matches them to words.
    """
    h, w = row_crop_arr.shape
    # Annotation band is top 0 to 65px
    band = row_crop_arr[0:min(65, h), :]
    ink_mask = band < 140

    labeled, num_features = ndimage.label(ink_mask)
    objs = ndimage.find_objects(labeled)

    candidates = []
    for sl in objs:
        y_sl, x_sl = sl
        bh = y_sl.stop - y_sl.start
        bw = x_sl.stop - x_sl.start
        area = np.sum(ink_mask[sl])
        # Filter for typical symbol sizes
        if 18 <= bh <= 50 and 12 <= bw <= 50 and area > 80:
            patch = ink_mask[sl]
            sym_name, score = classify_patch(patch)
            if sym_name:
                candidates.append({
                    "x": x_sl.start,
                    "y": y_sl.start,
                    "w": bw,
                    "h": bh,
                    "sym_name": sym_name,
                    "score": score
                })

    # Sort in RTL order (largest x first)
    candidates.sort(key=lambda c: c["x"], reverse=True)

    glyphs = []
    annotations = []

    # Map symbols to words based on x-coordinate
    # In row, words span from right (w-100) to left (100)
    for idx, c in enumerate(candidates):
        sym_info = SYMBOL_MAP.get(c["sym_name"], ("১", "none", "এক আলিফ"))
        printed, enclosure, legend = sym_info
        sym_id = f"r{row_index}-a{idx + 1}"
        ann_id = f"p{page_num}:{sym_id}"

        # Match to word
        matched_word = words[0]["id"] if words else f"r{row_index}w1"
        offset = 0.5
        if words:
            # Estimate word slot along line
            # Rightmost word is index 0, leftmost is index len(words)-1
            word_idx = int((1.0 - (c["x"] / max(1, w))) * len(words))
            word_idx = max(0, min(len(words) - 1, word_idx))
            matched_word = words[word_idx]["id"]
            # Relative offset in word
            offset = 0.5

        glyph_rec = {
            "id": sym_id,
            "printed": printed or "",
            "shape_description": legend,
            "enclosure": enclosure,
            "legend_bengali": legend,
            "conditional": c["sym_name"] == "cond_6",
            "bbox": [c["x"], c["y"], c["w"], c["h"]],
            "attachment": {
                "target": matched_word,
                "basis": "cv_detection",
                "offset_in_word": offset
            }
        }
        if c["sym_name"] == "arabic_sakin":
            glyph_rec["shape_id"] = "ringed-wedge"
        elif c["sym_name"] == "cond_6":
            glyph_rec["shape_id"] = "conditional-three-or-one"

        glyphs.append(glyph_rec)

        ann_rec = {
            "id": ann_id,
            "rowIndex": row_index,
            "sourceId": sym_id,
            "text": printed,
            "sourceBox": [c["x"], c["y"], c["w"], c["h"]],
            "targetGraphemeId": None,
            "verified": False,
            "unresolved": [],
            "draftWordAttachment": {
                "target": matched_word,
                "basis": "cv_detection",
                "offset_in_word": offset
            }
        }
        if c["sym_name"] == "arabic_sakin":
            ann_rec["display"] = {
                "status": "source_shape_candidate",
                "symbolId": "ringed-wedge",
                "character": "",
                "fontFamily": "Qarian Symbols",
                "labelBn": "আরবী সাকিন"
            }
        elif c["sym_name"] == "cond_6":
            ann_rec["display"] = {
                "status": "source_shape_candidate",
                "symbolId": "conditional-three-or-one",
                "character": "",
                "fontFamily": "Qarian Symbols",
                "labelBn": "দম ফেলিলে তিন / না ফেলিলে এক"
            }

        annotations.append(ann_rec)

    return glyphs, annotations

print("Annotation extractor module loaded.")
