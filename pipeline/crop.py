#!/usr/bin/env python3
"""Crop a region of a source page at full resolution for reading.

usage: .venv/bin/python pipeline/crop.py PAGE X Y W H NAME [--zoom 1.5]
Coordinates are full-resolution source pixels (2480x3509). Output is capped at
1500 px wide so it is shown without downscaling; crop narrower regions to read
small marks. Writes work/crops/PAGE/NAME.png.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page", type=int)
    ap.add_argument("x", type=int)
    ap.add_argument("y", type=int)
    ap.add_argument("w", type=int)
    ap.add_argument("h", type=int)
    ap.add_argument("name")
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--ruler", action="store_true", help="add a strip with source x coordinates on top")
    a = ap.parse_args()
    src = ROOT / "work" / "pages" / f"page_{a.page:04d}.png"
    if not src.exists():
        raise SystemExit(f"missing {src}; run pipeline/prepare.py {a.page} first")
    im = Image.open(src).convert("RGB")
    box = (max(0, a.x), max(0, a.y), min(im.width, a.x + a.w), min(im.height, a.y + a.h))
    crop = im.crop(box)
    scale = a.zoom
    if crop.width * scale > 1500:
        scale = 1500 / crop.width
    if scale != 1.0:
        crop = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.LANCZOS)
    if a.ruler:
        strip = 22
        ruled = Image.new("RGB", (crop.width, crop.height + strip), "white")
        ruled.paste(crop, (0, strip))
        draw = ImageDraw.Draw(ruled)
        for x in range((box[0] // 10 + 1) * 10, box[2], 10):
            sx = round((x - box[0]) * scale)
            major = x % 50 == 0
            draw.line([(sx, strip - (10 if major else 4)), (sx, strip)], fill=(220, 0, 0))
            if x % 100 == 0:
                draw.text((sx + 2, 1), str(x), fill=(220, 0, 0))
        crop = ruled
    out = ROOT / "work" / "crops" / f"{a.page:03d}" / f"{a.name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    crop.save(out)
    print(f"{out.relative_to(ROOT)} {crop.width}x{crop.height} (source box {box}, scale {scale:.2f})")


if __name__ == "__main__":
    main()
