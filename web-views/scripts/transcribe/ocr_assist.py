"""Record local OCR suggestions from crops of the mandatory scanned PDF.

This tool never writes reader data. OCR is evidence for a human source review, not
an authority for Arabic harakat, Bengali spelling, or annotation placement.
"""
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageEnhance

PDF_SHA256 = '73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recognize(image, lang, model_dir, temp_dir):
    image_path = temp_dir / f'{lang}.png'
    image.save(image_path)
    env = {**os.environ, 'TESSDATA_PREFIX': str(model_dir)}
    result = subprocess.run(
        ['tesseract', str(image_path), 'stdout', '-l', lang, '--psm', '7'],
        capture_output=True, text=True, env=env, check=False,
    )
    if result.returncode:
        raise RuntimeError(f'Tesseract {lang}: {result.stderr.strip()}')
    return result.stdout.strip()


def crop_band(image, top, bottom):
    height = image.height
    band = image.convert('L').crop((0, round(height * top), image.width, round(height * bottom)))
    band = band.resize((band.width * 2, band.height * 2))
    return ImageEnhance.Contrast(band).enhance(1.8)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--page', type=int, required=True, help='Physical PDF page number, one-based')
    parser.add_argument('--crop-dir', type=Path, required=True, help='Directory containing row00.png, row01.png, ... cropped from that PDF page')
    parser.add_argument('--model-dir', type=Path, required=True, help='Local Tesseract tessdata_best ara.traineddata and ben.traineddata')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--first', type=int, default=0)
    parser.add_argument('--last', type=int, default=10)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    models = {lang: sha(args.model_dir / f'{lang}.traineddata') for lang in ('ara', 'ben')}
    rows = []
    with tempfile.TemporaryDirectory(prefix='.ocr-assist-', dir=args.output.parent) as temporary:
        temp_dir = Path(temporary)
        for index in range(args.first, args.last + 1):
            source = args.crop_dir / f'row{index:02}.png'
            if not source.is_file():
                source = args.crop_dir / f'row{index}.png'
            if not source.is_file():
                raise FileNotFoundError(source)
            image = Image.open(source)
            # Existing pilot row crops place the previous Bengali line at the top,
            # the source's upper signs next, then the Arabic body. Fractions are
            # only OCR pre-processing, never source glyph coordinates.
            arabic = crop_band(image, .27, .91)
            bengali = crop_band(image, 0, .20)
            rows.append({
                'rowIndex': index,
                'sourceCrop': str(source),
                'sourceCropSha256': sha(source),
                'arabicOcr': recognize(arabic, 'ara', args.model_dir, temp_dir),
                'bengaliOcrOfPreviousRow': recognize(bengali, 'ben', args.model_dir, temp_dir),
            })
    report = {
        'status': 'unreviewed_ocr_hypotheses_do_not_publish',
        'sourcePdfSha256': PDF_SHA256,
        'physicalPage': args.page,
        'method': 'Local Tesseract OCR on row crops rendered from the mandatory PDF',
        'modelSha256': models,
        'limitations': 'OCR drops or changes harakat, Bengali letters, and annotation marks. Every glyph must be checked against the original PDF; no OCR string is accepted automatically.',
        'rows': rows,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'page': args.page, 'rows': len(rows), 'status': report['status']}))


if __name__ == '__main__':
    main()
