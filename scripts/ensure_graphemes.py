#!/usr/bin/env python3
"""
Ensures all 752 pages have proper Arabic grapheme clusters populated.
"""
import os
import json
import unicodedata

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def clusters(text, prefix):
    result = []
    for index, c in enumerate(text or ""):
        if unicodedata.category(c).startswith('M') and result:
            result[-1]['text'] += c
            result[-1]['endCodepoint'] = index + 1
        else:
            result.append({
                'id': f'{prefix}:g{len(result)}',
                'text': c,
                'startCodepoint': index,
                'endCodepoint': index + 1,
                'sourceBox': None,
                'verified': False
            })
    return result

def ensure_page_graphemes(p_num):
    p_str = f"{p_num:03d}"
    paths = [
        os.path.join(PROJECT_ROOT, "data", "pages", f"{p_str}.json"),
        os.path.join(PROJECT_ROOT, "webview", "data", "pages", f"{p_str}.json")
    ]
    if not os.path.exists(paths[0]):
        return 0

    with open(paths[0]) as f:
        d = json.load(f)

    graphemes = d.get("graphemes") or {}
    if len(graphemes) > 0:
        return 0  # Already has graphemes

    rows = d.get("originalCandidate", {}).get("rows", [])
    new_graphemes = {}
    for r in rows:
        for s in r.get("arabic_segments", []):
            for w in s.get("words", []):
                new_graphemes[w["id"]] = clusters(w.get("text", ""), f"p{p_num}:{w['id']}")

    d["graphemes"] = new_graphemes
    for p in paths:
        if os.path.exists(os.path.dirname(p)):
            with open(p, "w") as f:
                json.dump(d, f, ensure_ascii=False)

    return len(new_graphemes)

if __name__ == "__main__":
    total_populated = 0
    pages_updated = 0
    for p in range(1, 753):
        cnt = ensure_page_graphemes(p)
        if cnt > 0:
            pages_updated += 1
            total_populated += cnt
    print(f"Ensured graphemes: {pages_updated} pages updated with {total_populated} word grapheme clusters.")
