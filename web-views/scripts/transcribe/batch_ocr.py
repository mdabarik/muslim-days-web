"""Build an incremental OCR work queue from the original scanned PDF.

Each output is an unreviewed visual-reading aid. Nothing in this script writes
source/pages or dist/data. PDF row boundaries vary, so all crops and OCR text
must be inspected against the original before any transcription is accepted.
"""
import argparse
import hashlib
import io
import json
import tempfile
from pathlib import Path

import pypdfium2 as pdfium

from ocr_assist import PDF_SHA256, crop_band, recognize, sha


def image_sha(image):
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return hashlib.sha256(buf.getvalue()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--start', type=int, required=True, help='First physical PDF page, one-based')
    parser.add_argument('--end', type=int, required=True, help='Last physical PDF page, inclusive')
    parser.add_argument('--row-start', type=int, default=125, help='Approximate first row top at 300 dpi')
    parser.add_argument('--row-step', type=int, default=268)
    parser.add_argument('--row-height', type=int, default=330)
    args = parser.parse_args()
    if sha(args.pdf) != PDF_SHA256:
        raise SystemExit('Original PDF SHA-256 differs from the project source')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    document = pdfium.PdfDocument(str(args.pdf))
    if not (1 <= args.start <= args.end <= len(document)):
        raise SystemExit('Page range outside original PDF')
    model_hashes = {lang: sha(args.model_dir / f'{lang}.traineddata') for lang in ('ara', 'ben')}
    completed = []
    with tempfile.TemporaryDirectory(prefix='.batch-ocr-', dir=args.output_dir) as temporary:
        temp_dir = Path(temporary)
        for n in range(args.start, args.end + 1):
            output = args.output_dir / f'pdf-page-{n:03}.ocr.json'
            if output.exists():
                existing = json.loads(output.read_text())
                if existing.get('sourcePdfSha256') == PDF_SHA256 and existing.get('modelSha256') == model_hashes:
                    completed.append({'page': n, 'status': 'already_present'})
                    print(json.dumps(completed[-1]), flush=True)
                    continue
            image = document[n - 1].render(scale=300 / 72).to_pil().convert('RGB')
            rows = []
            for index in range(11):
                y0 = args.row_start + args.row_step * index
                y1 = min(image.height, y0 + args.row_height)
                raw = image.crop((60, y0, image.width - 160, y1))
                arabic = crop_band(raw, .27, .91)
                bengali = crop_band(raw, 0, .20)
                rows.append({
                    'approximateRowIndex': index,
                    'cropRect300dpi': [60, y0, image.width - 220, y1 - y0],
                    'arabicOcr': recognize(arabic, 'ara', args.model_dir, temp_dir),
                    'bengaliOcrOfPreviousRow': recognize(bengali, 'ben', args.model_dir, temp_dir),
                })
            report = {
                'status': 'unreviewed_ocr_hypotheses_do_not_publish',
                'sourcePdfSha256': PDF_SHA256,
                'physicalPage': n,
                'render': {'dpi': 300, 'dimensions': list(image.size), 'sha256': image_sha(image)},
                'modelSha256': model_hashes,
                'rowGeometry': {'firstTop': args.row_start, 'step': args.row_step, 'height': args.row_height, 'status': 'approximate_not_verified'},
                'limitations': 'OCR is not a Quran transcription. It may omit or alter Arabic letters, harakat, Bengali letters, special signs and row boundaries; compare every output to the source PDF.',
                'rows': rows,
            }
            temporary_output = output.with_suffix('.tmp')
            temporary_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            temporary_output.replace(output)
            completed.append({'page': n, 'status': report['status']})
            print(json.dumps(completed[-1]), flush=True)
    summary = {'sourcePdfSha256': PDF_SHA256, 'range': [args.start, args.end], 'pagesRecorded': len(completed), 'status': 'OCR preparation only; zero pages verified or integrated by this process'}
    (args.output_dir / 'latest-run.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
