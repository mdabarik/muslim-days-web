#!/usr/bin/env python3
"""Extract one source page (Git LFS on `main`) and write an overview image.

usage: .venv/bin/python pipeline/prepare.py 752
writes work/pages/page_0752.png (300 dpi, 2480x3509) and work/pages/overview_0752.jpg
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "work" / "pages"


def source_png(page: int) -> Path:
    out = PAGES / f"page_{page:04d}.png"
    if out.exists() and out.stat().st_size > 100_000:
        return out
    PAGES.mkdir(parents=True, exist_ok=True)
    pointer = subprocess.run(
        ["git", "show", f"main:output/extracted_pages/page_{page:04d}.png"],
        cwd=ROOT, check=True, capture_output=True).stdout
    data = subprocess.run(["git", "lfs", "smudge"], cwd=ROOT, input=pointer,
                          check=True, capture_output=True).stdout
    tmp = out.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.rename(out)
    return out


def main():
    page = int(sys.argv[1])
    png = source_png(page)
    overview = PAGES / f"overview_{page:04d}.jpg"
    if not overview.exists():
        # Red rules every 100 source px, labelled with the source y, so crops
        # can be placed straight from the overview.
        im = Image.open(png).convert("RGB")
        scale = 820 / im.width
        small = im.resize((820, round(im.height * scale)), Image.LANCZOS)
        draw = ImageDraw.Draw(small)
        for y in range(0, im.height, 100):
            sy = round(y * scale)
            draw.line([(0, sy), (14 if y % 500 else 30, sy)], fill=(220, 0, 0), width=1)
            draw.line([(806 if y % 500 else 790, sy), (820, sy)], fill=(220, 0, 0), width=1)
            if y % 200 == 0:
                draw.text((16, sy - 5), str(y), fill=(220, 0, 0))
        small.save(overview, quality=85)
    w, h = Image.open(png).size
    print(f"source {png.relative_to(ROOT)} {w}x{h}")
    print(f"overview {overview.relative_to(ROOT)}: red ticks every 100 source px, labels give source y")


if __name__ == "__main__":
    main()
