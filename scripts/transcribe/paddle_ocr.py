#!/usr/bin/env python3
"""Save PaddleOCR Arabic visual-detection/recognition evidence per page."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from paddleocr import PaddleOCR

STATUS = "unreviewed_paddle_ocr_hypothesis_do_not_publish"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--input-dir", type=Path, default=Path("output/extracted_pages"))
    ap.add_argument("--output-dir", type=Path, default=Path("output/ocr/paddle"))
    args = ap.parse_args()
    if not (1 <= args.start <= args.end <= 752):
        raise SystemExit("Page range must be within 1..752")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ocr = PaddleOCR(lang="ar", device="cpu",
                    text_detection_model_name="PP-OCRv5_mobile_det",
                    text_recognition_model_name="arabic_PP-OCRv5_mobile_rec",
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False, use_textline_orientation=False)
    for page in range(args.start, args.end + 1):
        image = args.input_dir / f"page_{page:04}.png"
        output = args.output_dir / f"page_{page:04}.paddle.json"
        source_hash = sha256(image)
        if output.exists():
            old = json.loads(output.read_text())
            if old.get("source", {}).get("sha256") == source_hash:
                print(json.dumps({"page": page, "status": "already_present"}), flush=True)
                continue
        result = next(iter(ocr.predict(str(image))))
        data = dict(result)
        keep = {key: data.get(key) for key in ("dt_polys", "rec_texts", "rec_scores", "rec_boxes") if key in data}
        def plain(value):
            if hasattr(value, "tolist"):
                return value.tolist()
            if isinstance(value, list):
                return [plain(x) for x in value]
            return value
        keep = {key: plain(value) for key, value in keep.items()}
        report = {
            "status": STATUS,
            "provider": "paddleocr",
            "model": "PP-OCRv5_mobile_det + arabic_PP-OCRv5_mobile_rec",
            "limitations": "PaddleOCR release has no Bengali bn recognition model here; Bengali evidence remains in local Tesseract output. Quranic annotation shapes and harakat require source review.",
            "page": page,
            "source": {"path": str(image), "sha256": source_hash},
            "result": keep,
        }
        tmp = output.with_suffix(".tmp")
        tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        tmp.replace(output)
        print(json.dumps({"page": page, "status": STATUS, "detections": len(keep.get("rec_texts", []))}), flush=True)

if __name__ == "__main__":
    main()
