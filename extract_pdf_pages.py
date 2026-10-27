#!/usr/bin/env python3
"""Render pages in order, conservatively deduplicate, and flag image defects.

No OCR, PDF writes, text reconstruction, or automatic sharpening. Quality
scores are screening heuristics, not a certification of text readability.
Only identical full-resolution RGB pixels are automatically deduplicated.
Non-identical similar scans are retained for human comparison.
"""
import argparse
import csv
import hashlib
import math
from pathlib import Path
import shutil
import sys

import cv2
import numpy as np
from PIL import Image
import pymupdf


FIELDS = [
    'page_number', 'filename', 'duplicate_status', 'related_pages',
    'quality_status', 'action_taken', 'width_px', 'height_px', 'render_dpi',
    'source_scan_dpi', 'median_laplacian', 'low_sharpness_tile_fraction',
    'contrast', 'sha256_pixels', 'notes',
]


def hash_image(gray):
    small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
    values = cv2.dct(small.astype(np.float32))[:8, :8].ravel()[1:]
    return int.from_bytes(np.packbits(values > np.median(values)).tobytes(), 'big')


def similarity(a, b):
    """Full-page correlation plus ink overlap; these never authorize deletion."""
    af, bf = a.astype(np.float32), b.astype(np.float32)
    af -= af.mean()
    bf -= bf.mean()
    denom = float(np.linalg.norm(af) * np.linalg.norm(bf))
    corr = float(np.sum(af * bf) / denom) if denom else 0.0
    _, ai = cv2.threshold(a, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    _, bi = cv2.threshold(b, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    union = np.count_nonzero(ai | bi)
    overlap = np.count_nonzero(ai & bi) / union if union else 0.0
    return corr, overlap


def quality(gray, source_dpi, dpi):
    # Work at a consistent physical scale. Inspect patches across the whole
    # page so blank margins do not dominate the focus score.
    if dpi != 300:
        gray = cv2.resize(gray, None, fx=300 / dpi, fy=300 / dpi)
    scores, contrasts = [], []
    for y in range(0, gray.shape[0], 256):
        for x in range(0, gray.shape[1], 256):
            tile = gray[y:y + 256, x:x + 256]
            lo, hi = np.percentile(tile, (5, 95))
            contrast = float(hi - lo)
            if contrast > 12:
                scores.append(float(cv2.Laplacian(tile, cv2.CV_32F).var()))
                contrasts.append(contrast)
    med = float(np.median(scores)) if scores else 0.0
    low_fraction = float(np.mean(np.array(scores) < 45)) if scores else 1.0
    contrast = float(np.median(contrasts)) if contrasts else 0.0
    flags = []
    if source_dpi is not None and source_dpi < 200:
        flags.append('low_source_resolution')
    if not scores:
        flags.append('blank_or_very_faint')
    else:
        # Conservative screening cutoff calibrated against 100% crops from
        # this scan. Texture/noise can inflate this score; it is not proof
        # that small Bengali text or Arabic diacritics are readable.
        if med < 300 or low_fraction > 0.35:
            flags.append('suspected_blur')
        if contrast < 55:
            flags.append('low_contrast')
    return flags, med, low_fraction, contrast


def scan_dpi(page):
    # Inspect image placement, without extracting text or using OCR. Account
    # for rotation using the two transform-vector lengths, not bbox alone.
    values = []
    for info in page.get_image_info():
        rect = pymupdf.Rect(info['bbox']) & page.rect
        if rect.is_empty or rect.get_area() < page.rect.get_area() * 0.1:
            continue
        a, b, c, d, _, _ = info['transform']
        width, height = math.hypot(a, b), math.hypot(c, d)
        if width and height:
            values.append(min(info['width'] * 72 / width,
                              info['height'] * 72 / height))
    return min(values) if values else None


def save_report(path, rows):
    temp = path.with_suffix('.csv.tmp')
    with temp.open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)


def flag_review(folder, filename):
    target = folder / filename
    if not target.exists():
        # A relative link avoids storing a second full copy of every flag.
        target.symlink_to(Path('..') / 'extracted_pages' / filename)


def geometric_match(first, second):
    """Find distributed matching scan detail; similarity only, never deletion."""
    points_a, desc_a, size_a, thumb_a = first
    points_b, desc_b, size_b, thumb_b = second
    if desc_a is None or desc_b is None or min(len(desc_a), len(desc_b)) < 40:
        return False
    matches = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(desc_a, desc_b, k=2)
    good = [m for pair in matches if len(pair) == 2
            for m, n in [pair] if m.distance < 60 and m.distance < 0.65 * n.distance]
    if len(good) < 40:
        return False
    a = np.float32([points_a[m.queryIdx] for m in good])
    b = np.float32([points_b[m.trainIdx] for m in good])
    transform, mask = cv2.findHomography(a, b, cv2.RANSAC, 3.0)
    if transform is None or mask is None:
        return False
    inliers = mask.ravel().astype(bool)
    if inliers.sum() < 40 or inliers.mean() < 0.15:
        return False
    for points, (width, height) in ((a[inliers], size_a), (b[inliers], size_b)):
        # Match text throughout the body, not just a header, border, or QR code.
        normalized = points / (width, height)
        if np.ptp(normalized[:, 0]) < 0.55 or np.ptp(normalized[:, 1]) < 0.65:
            return False
        quadrants = (normalized[:, 0] > 0.5).astype(int) + 2 * (normalized[:, 1] > 0.5)
        if min(np.bincount(quadrants, minlength=4)) < 3:
            return False
    # Repeated glyph shapes can create spurious feature matches. Require the
    # aligned page body itself to agree, in addition to geometric evidence.
    height, width = thumb_b.shape
    scale_a = np.diag([thumb_a.shape[1] / size_a[0], thumb_a.shape[0] / size_a[1], 1])
    scale_b = np.diag([width / size_b[0], height / size_b[1], 1])
    aligned = cv2.warpPerspective(thumb_a, scale_b @ transform @ np.linalg.inv(scale_a),
                                  (width, height), borderValue=255)
    body = np.s_[int(height*.1):int(height*.9), int(width*.1):int(width*.9)]
    corr, overlap = similarity(aligned[body], thumb_b[body])
    return corr >= 0.90 and overlap >= 0.75


def check_scan_similarity(source, output):
    """Catch separately scanned copies with shifted or tilted page content.

    The full-resolution PNG checks run during extraction. This extra screening
    uses compact source renders to find candidates without rereading gigabytes
    of PNGs. Every non-identical candidate is retained for visual review.
    """
    report_path = output / 'quality_report.csv'
    with report_path.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    features, hashes, numbers = [], [], []
    orb = cv2.ORB_create(nfeatures=1400, fastThreshold=12)
    cv2.setNumThreads(2)
    with pymupdf.open(source) as doc:
        for row in rows:
            if not (output / 'extracted_pages' / row['filename']).exists():
                continue
            number = int(row['page_number'])
            pix = doc[number - 1].get_pixmap(dpi=96, colorspace=pymupdf.csGRAY, alpha=False)
            gray = np.frombuffer(pix.samples_mv, np.uint8).reshape(pix.height, pix.width)
            h, w = gray.shape
            mask = np.zeros_like(gray)
            mask[int(h * .08):int(h * .92), int(w * .08):int(w * .92)] = 255
            keys, descriptors = orb.detectAndCompute(gray, mask)
            points = np.float32([key.pt for key in keys])
            features.append((points, descriptors, (w, h), cv2.resize(gray, (256, 362), interpolation=cv2.INTER_AREA)))
            hashes.append((hash_image(gray), hash_image(gray[int(h*.1):int(h*.9), int(w*.1):int(w*.9)])))
            numbers.append(number)
            del gray, pix
            pymupdf.TOOLS.store_shrink(100)
            if len(numbers) % 100 == 0:
                print(f'Scan similarity features: {len(numbers)}/{len(rows)}', flush=True)
    pairs = set()
    for i, image_hashes in enumerate(hashes):
        distances = sorted((min((image_hashes[0] ^ other[0]).bit_count(),
                                (image_hashes[1] ^ other[1]).bit_count()), j)
                           for j, other in enumerate(hashes) if i != j)
        for distance, j in distances[:8]:
            if distance <= 20:
                pairs.add(tuple(sorted((i, j))))
    found = []
    for count, (i, j) in enumerate(sorted(pairs), 1):
        if geometric_match(features[i], features[j]):
            first, second = numbers[i], numbers[j]
            found.append((first, second))
            for current, other in ((first, second), (second, first)):
                row = rows[current - 1]
                if row['duplicate_status'] != 'exact_duplicate_retained':
                    row['duplicate_status'] = 'uncertain_similarity_retained'
                related = set(str(row['related_pages']).split(';')) - {''}
                related.add(str(other))
                row['related_pages'] = ';'.join(sorted(related, key=int))
                row['action_taken'] = 'Kept original render; linked in needs_review for visual comparison'
                row['notes'] += ' Distributed visual features match another scan; full-page identity requires review.'
                flag_review(output / 'needs_review', row['filename'])
        if count % 1000 == 0:
            print(f'Scan similarity pairs: {count}/{len(pairs)}', flush=True)
    save_report(report_path, rows)
    print(f'Geometric scan screening: {len(pairs)} candidate pairs; flagged pairs: {found}', flush=True)
    return found


def run(source, output, dpi):
    source = source.resolve(strict=True)
    original_stat = source.stat()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f'Refusing to overwrite nonempty output folder: {output}')
    cv2.setNumThreads(2)
    with pymupdf.open(source) as doc:
        if doc.needs_pass:
            raise ValueError('The PDF requires a password.')
        if not doc.is_pdf:
            raise ValueError('The source is not a PDF.')
        pages_dir, review_dir = output / 'extracted_pages', output / 'needs_review'
        pages_dir.mkdir(parents=True, exist_ok=True)
        review_dir.mkdir(parents=True, exist_ok=True)
        report_path = output / 'quality_report.csv'
        rows = []
        exact, candidates = {}, []
        print(f'Source: {source}\nPages: {len(doc)}; render DPI: {dpi}', flush=True)
        for index in range(len(doc)):
            number = index + 1
            filename = f'page_{number:04d}.png'
            row = dict.fromkeys(FIELDS, '')
            row.update(page_number=number, filename=filename, render_dpi=dpi,
                       duplicate_status='not_checked', quality_status='not_checked')
            rows.append(row)
            path = pages_dir / filename
            try:
                page = doc[index]
                w = math.ceil(page.rect.width * dpi / 72)
                h = math.ceil(page.rect.height * dpi / 72)
                if w * h > 100_000_000:
                    raise ValueError('Page exceeds 100 megapixels; manual rendering required')
                if shutil.disk_usage(output).free < max(2 * 1024**3, w * h * 6):
                    raise OSError('Insufficient disk space; at least 2 GiB reserve required')
                pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
                rgb = np.frombuffer(pix.samples_mv, np.uint8).reshape(pix.height, pix.width, 3)
                gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
                digest = hashlib.sha256()
                digest.update(f'{pix.width}x{pix.height}:RGB:'.encode())
                digest.update(pix.samples_mv)
                pixel_hash = digest.hexdigest()
                native_dpi = scan_dpi(page)
                flags, sharpness, low_fraction, contrast = quality(gray, native_dpi, dpi)
                row.update(width_px=pix.width, height_px=pix.height,
                           source_scan_dpi=round(native_dpi, 1) if native_dpi else '',
                           median_laplacian=round(sharpness, 2),
                           low_sharpness_tile_fraction=round(low_fraction, 3),
                           contrast=round(contrast, 1), sha256_pixels=pixel_hash,
                           quality_status=';'.join(flags) or 'no_automatic_quality_flag',
                           notes='Readability not certified; no sharpening applied without visual evidence of benefit.')
                # Save every rendered page before making duplicate decisions.
                temp = path.with_suffix('.png.tmp')
                image = Image.fromarray(rgb)
                image.save(temp, format='PNG', dpi=(dpi, dpi), compress_level=6)
                image.close()
                temp.replace(path)
                if pixel_hash in exact:
                    kept = exact[pixel_hash]
                    row.update(duplicate_status='exact_duplicate_removed', related_pages=kept,
                               action_taken=f'Removed identical pixel copy; retained page_{kept:04d}.png (equal quality and resolution)')
                    rows[kept - 1]['duplicate_status'] = 'exact_duplicate_retained'
                    path.unlink()
                else:
                    exact[pixel_hash] = number
                    phash = hash_image(gray)
                    thumb = cv2.resize(gray, (192, 256), interpolation=cv2.INTER_AREA)
                    aspect = pix.width / pix.height
                    matches = []
                    for prior, prior_hash, prior_aspect, prior_thumb in candidates:
                        if abs(aspect / prior_aspect - 1) > 0.03:
                            continue
                        if (phash ^ prior_hash).bit_count() > 12:
                            continue
                        corr, overlap = similarity(thumb, prior_thumb)
                        if corr >= 0.92 and overlap >= 0.80:
                            matches.append(prior)
                            other = rows[prior - 1]
                            if other['duplicate_status'] != 'exact_duplicate_retained':
                                other['duplicate_status'] = 'uncertain_similarity_retained'
                            related = set(str(other['related_pages']).split(';')) - {''}
                            related.add(str(number))
                            other['related_pages'] = ';'.join(sorted(related, key=int))
                            other['action_taken'] = 'Kept original render; linked in needs_review for visual comparison'
                            flag_review(review_dir, other['filename'])
                    row.update(duplicate_status='uncertain_similarity_retained' if matches else 'no_duplicate_detected',
                               related_pages=';'.join(map(str, matches)),
                               action_taken='Kept original 300 DPI render' if dpi == 300 else 'Kept original render')
                    if flags or matches:
                        flag_review(review_dir, filename)
                        row['action_taken'] += '; linked in needs_review'
                    candidates.append((number, phash, aspect, thumb))
                del rgb, gray, pix
                pymupdf.TOOLS.store_shrink(100)
            except Exception as error:
                row.update(quality_status='processing_error', action_taken='Manual retry required', notes=str(error))
                save_report(report_path, rows)
                if isinstance(error, OSError):
                    raise
            save_report(report_path, rows)
            print(f'{number}/{len(doc)}: {row["duplicate_status"]}; {row["quality_status"]}', flush=True)
        final_stat = source.stat()
        if (original_stat.st_size, original_stat.st_mtime_ns) != (final_stat.st_size, final_stat.st_mtime_ns):
            raise RuntimeError('Source changed externally during processing; inspect results')
        removed = sum(r['duplicate_status'] == 'exact_duplicate_removed' for r in rows)
        errors = sum(r['quality_status'] == 'processing_error' for r in rows)
        print(f'Finished: {len(rows)} pages; {removed} exact duplicates removed; '
              f'{len(list(review_dir.iterdir()))} review links; {errors} errors.\nReport: {report_path}', flush=True)
        if not errors:
            check_scan_similarity(source, output)
        return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'output')
    parser.add_argument('--dpi', type=int, default=300, choices=range(150, 601), metavar='150..600')
    args = parser.parse_args()
    return run(args.pdf, args.output.resolve(), args.dpi)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
