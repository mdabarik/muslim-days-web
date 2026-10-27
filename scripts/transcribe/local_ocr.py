#!/usr/bin/env python3
"""Create resumable local Tesseract OCR evidence for the 752 extracted pages.

This deliberately records OCR hypotheses and annotation-band evidence only. It
does not alter the source PNGs or publish Quran text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageEnhance


STATUS = "unreviewed_local_ocr_hypothesis_do_not_publish"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def prepare(image: Image.Image, top: float, bottom: float, scale: int = 2) -> Image.Image:
    band = image.convert("L").crop((0, round(image.height * top), image.width, round(image.height * bottom)))
    band = band.resize((band.width * scale, band.height * scale))
    return ImageEnhance.Contrast(band).enhance(1.6)


def recognize(image: Image.Image, lang: str, temp_dir: Path, name: str) -> str:
    source = temp_dir / f"{name}.png"
    image.save(source, format="PNG", optimize=True)
    result = subprocess.run(
        ["tesseract", str(source), "stdout", "-l", lang, "--psm", "7"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Tesseract {lang} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def process(page: int, image_path: Path, output_path: Path, force: bool) -> None:
    source_hash = sha256(image_path)
    if output_path.exists() and not force:
        old = json.loads(output_path.read_text())
        if old.get("source", {}).get("sha256") == source_hash:
            print(json.dumps({"page": page, "status": "already_present"}))
            return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(image_path).convert("RGB")
    rows = []
    with tempfile.TemporaryDirectory(prefix=f"local-ocr-{page:04}-", dir=output_path.parent) as temp:
        temp_dir = Path(temp)
        for index in range(11):
            y0 = 125 + 268 * index
            y1 = min(image.height, y0 + 330)
            raw = image.crop((60, y0, image.width - 160, y1))
            rows.append({
                "rowIndex": index,
                "cropRect300dpi": [60, y0, image.width - 160, y1],
                "annotationBandRectInCrop": [0, round(raw.height * .20), raw.width, round(raw.height * .30)],
                "annotationTextBen": recognize(prepare(raw, .20, .30), "ben", temp_dir, f"r{index:02}-marks-ben"),
                "annotationTextAra": recognize(prepare(raw, .20, .30), "ara", temp_dir, f"r{index:02}-marks-ara"),
                "arabicOcr": recognize(prepare(raw, .27, .91), "ara", temp_dir, f"r{index:02}-arabic"),
                "bengaliTopOcr": recognize(prepare(raw, 0, .20), "ben", temp_dir, f"r{index:02}-ben-top"),
                "bengaliBottomOcr": recognize(prepare(raw, .91, 1.0), "ben", temp_dir, f"r{index:02}-ben-bottom"),
            })

    report = {
        "status": STATUS,
        "method": "Local Tesseract 5.5.3 on 300-DPI extracted PNG row bands",
        "source": {"path": str(image_path), "sha256": source_hash, "dimensions": list(image.size)},
        "languages": ["ara", "ben"],
        "rowGeometry": {"firstTop": 125, "step": 268, "height": 330, "status": "approximate; verify against source"},
        "limitations": "OCR may omit or alter Arabic harakat, Bengali letters, and annotation shapes. Annotation crops and coordinates are evidence; every glyph requires source-image review.",
        "physicalPage": page,
        "rows": rows,
    }
    tmp = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(output_path)
    print(json.dumps({"page": page, "status": STATUS, "rows": len(rows), "output": str(output_path)}), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir", type=Path, default=Path("output/extracted_pages"))
    ap.add_argument("--output-dir", type=Path, default=Path("output/ocr/local"))
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--end", type=int)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    end = args.end if args.end is not None else args.start
    if not (1 <= args.start <= end <= 752):
        raise SystemExit("Page range must be within 1..752")
    for page in range(args.start, end + 1):
        image = args.input_dir / f"page_{page:04}.png"
        if not image.exists():
            raise FileNotFoundError(image)
        process(page, image, args.output_dir / f"page_{page:04}.local.json", args.force)


if __name__ == "__main__":
    main()
