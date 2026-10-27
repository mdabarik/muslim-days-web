#!/usr/bin/env python3
"""Autonomous background orchestrator for multi-engine OCR of the 752-page Quran.

Features:
- Low-thread / low-resource footprint (1 page at a time) to prevent throttling or overheating.
- PaddleOCR (Arabic baseline, words & bounding boxes)
- Local Tesseract OCR (Bengali + Arabic row and annotation bands)
- Dynamic page acquisition: Checks LFS checkout, or extracts directly from source-pdf if not yet extracted.
- Resilient checkpointing: Skips already completed pages.
- Progress monitoring JSON and logs.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
EXTRACTED_DIR = BASE_DIR / "output" / "extracted_pages"
OCR_DIR = BASE_DIR / "output" / "ocr"
PADDLE_DIR = OCR_DIR / "paddle"
LOCAL_DIR = OCR_DIR / "local"
PROGRESS_FILE = OCR_DIR / "pipeline_progress.json"
SOURCE_PDF = BASE_DIR / "source-pdf" / "Quran - Qariyana Quranul Karim.pdf"
VENV_PYTHON = BASE_DIR / ".venv-ocr" / "bin" / "python3"


def log(msg: str) -> None:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    with open(OCR_DIR / "pipeline.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def update_progress(current_page: int, total_pages: int = 752) -> None:
    paddle_count = len(list(PADDLE_DIR.glob("page_*.paddle.json")))
    local_count = len(list(LOCAL_DIR.glob("page_*.local.json")))
    available_images = len(list(EXTRACTED_DIR.glob("page_*.png")))

    progress = {
        "timestamp": datetime.datetime.now().isoformat(),
        "current_page": current_page,
        "total_pages": total_pages,
        "images_available": available_images,
        "paddle_completed": paddle_count,
        "local_completed": local_count,
        "percent_paddle": round((paddle_count / total_pages) * 100, 2),
        "percent_local": round((local_count / total_pages) * 100, 2),
        "status": "running" if current_page <= total_pages else "completed"
    }

    tmp_file = PROGRESS_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(progress, indent=2), encoding="utf-8")
    tmp_file.replace(PROGRESS_FILE)


def ensure_page_image(page: int) -> Path:
    img_path = EXTRACTED_DIR / f"page_{page:04}.png"
    if img_path.exists() and img_path.stat().st_size > 1024:
        return img_path

    # Try Git LFS checkout for this specific page
    try:
        rel_path = f"output/extracted_pages/page_{page:04}.png"
        subprocess.run(["git", "lfs", "checkout", rel_path], cwd=BASE_DIR, capture_output=True, timeout=15)
        if img_path.exists() and img_path.stat().st_size > 1024:
            return img_path
    except Exception:
        pass

    # Fallback: Extract directly from source PDF using pypdfium2 or pymupdf if available
    try:
        import pypdfium2 as pdfium
        if SOURCE_PDF.exists():
            log(f"Extracting page {page} directly from source PDF...")
            pdf = pdfium.PdfDocument(str(SOURCE_PDF))
            # 1-based page to 0-based index
            pdf_page = pdf[page - 1]
            # 300 DPI (standard scale: 300 / 72 = 4.1666667)
            bitmap = pdf_page.render(scale=300 / 72)
            pil_image = bitmap.to_pil()
            EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
            pil_image.save(img_path, format="PNG")
            return img_path
    except Exception as e:
        log(f"Fallback extraction failed for page {page}: {e}")

    return img_path


def run_paddle_ocr(page: int) -> bool:
    output_path = PADDLE_DIR / f"page_{page:04}.paddle.json"
    if output_path.exists() and output_path.stat().st_size > 100:
        return True

    cmd = [
        str(VENV_PYTHON if VENV_PYTHON.exists() else sys.executable),
        str(BASE_DIR / "scripts" / "transcribe" / "paddle_ocr.py"),
        "--start", str(page),
        "--end", str(page)
    ]
    try:
        res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=120)
        if res.returncode == 0:
            log(f"PaddleOCR completed page {page}")
            return True
        else:
            log(f"PaddleOCR page {page} failed: {res.stderr.strip()}")
            return False
    except Exception as e:
        log(f"PaddleOCR exception page {page}: {e}")
        return False


def run_local_ocr(page: int) -> bool:
    output_path = LOCAL_DIR / f"page_{page:04}.local.json"
    if output_path.exists() and output_path.stat().st_size > 100:
        return True

    cmd = [
        str(VENV_PYTHON if VENV_PYTHON.exists() else sys.executable),
        str(BASE_DIR / "scripts" / "transcribe" / "local_ocr.py"),
        "--start", str(page),
        "--end", str(page)
    ]
    try:
        res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=120)
        if res.returncode == 0:
            log(f"Local Tesseract OCR completed page {page}")
            return True
        else:
            log(f"Local OCR page {page} failed: {res.stderr.strip()}")
            return False
    except Exception as e:
        log(f"Local OCR exception page {page}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=752)
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between pages to keep CPU cool")
    args = parser.parse_args()

    PADDLE_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    log(f"=== Starting autonomous OCR pipeline (pages {args.start} to {args.end}) ===")

    for page in range(args.start, args.end + 1):
        img = ensure_page_image(page)
        if not img.exists() or img.stat().st_size <= 1024:
            log(f"Warning: page image {page} not yet available. Retrying next iteration...")
            time.sleep(2.0)
            img = ensure_page_image(page)

        if img.exists() and img.stat().st_size > 1024:
            # 1. PaddleOCR (Arabic words & boxes)
            run_paddle_ocr(page)

            # 2. Local Tesseract (Arabic & Bengali row bands and instructional marks)
            run_local_ocr(page)
        else:
            log(f"Skipping OCR for page {page} (image not ready)")

        update_progress(page, args.end)

        if args.delay > 0:
            time.sleep(args.delay)

    log("=== Autonomous OCR pipeline finished all requested pages ===")
    update_progress(args.end + 1, args.end)


if __name__ == "__main__":
    main()
