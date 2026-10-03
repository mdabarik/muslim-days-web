#!/usr/bin/env python3
"""Build a tiny selectable font for observed, non-Unicode Qarian mark shapes.

Requires Pillow, fonttools and brotli. Example:
  PYTHONPATH=/tmp/quran-web-tools python3 quran-web/scripts/build_symbol_font.py

Only the documented templates are included. PUA assignments describe
local graphic shapes, never Unicode identities or verified reading rules.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from PIL import Image
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont

WEB = Path(__file__).resolve().parents[1]
ROOT = WEB.parent
WORK = WEB / 'evidence/symbol-fix-2026-10-03/font-work'
ROUND = ROOT / 'muslim_days/tool/quran_fidelity/runs/fatihah-001/round-05'
PDF_HASH = '73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def pixel_outline(points):
    """Trace exact threshold pixel edges; omit only collinear vertices."""
    edges = defaultdict(list)
    for x, y in sorted(points, key=lambda p: (p[1], p[0])):
        if (x, y - 1) not in points:
            edges[x, y].append((x + 1, y))
        if (x + 1, y) not in points:
            edges[x + 1, y].append((x + 1, y + 1))
        if (x, y + 1) not in points:
            edges[x + 1, y + 1].append((x, y + 1))
        if (x - 1, y) not in points:
            edges[x, y + 1].append((x, y))
    paths = []
    while edges:
        start = next(iter(edges))
        point = start
        vertices = [point]
        while True:
            nxt = edges[point].pop()
            if not edges[point]:
                del edges[point]
            vertices.append(nxt)
            point = nxt
            if point == start:
                break
        simple = []
        for p in vertices:
            while len(simple) > 1 and (simple[-1][0] - simple[-2][0]) * (p[1] - simple[-1][1]) == (simple[-1][1] - simple[-2][1]) * (p[0] - simple[-1][0]):
                simple.pop()
            simple.append(p)
        paths.append('M ' + ' L '.join(f'{x} {y}' for x, y in simple) + ' Z')
    return ' '.join(paths)


def trace_arrow():
    source = WORK / 'source-pdf3-arrow-native.png'
    assert sha(source) == '5354d4a920700dbceb760adc3646f685d0b66f7db994bec1f00bacbc0e4d1f26', 'Source crop changed'
    im = Image.open(source).convert('L')
    assert im.size == (190, 250), 'Expected unresized PDF3 crop at 300 dpi'
    box = (55, 68, 95, 118)
    x0, y0, x1, y1 = box
    pixels = im.load()
    remaining = {(x, y) for y in range(y0, y1) for x in range(x0, x1) if pixels[x, y] < 128}
    components = []
    while remaining:
        start = min(remaining, key=lambda p: (p[1], p[0]))
        remaining.remove(start)
        stack, component = [start], {start}
        while stack:
            x, y = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    p = x + dx, y + dy
                    if p in remaining:
                        remaining.remove(p)
                        stack.append(p)
                        component.add(p)
        components.append(component)
    selected = max(components, key=len)
    assert len(selected) > 100, 'Arrow component not found'
    assert all(x0 < x < x1 - 1 and y0 < y < y1 - 1 for x, y in selected), 'Arrow touches selection edge'
    return {
        'path': pixel_outline(selected),
        'source': {'pdfSha256': PDF_HASH, 'physicalPage': 3, 'renderDpi': 300,
                   'renderSize': [2480, 3509], 'cropBoxXYXY': [430, 1160, 620, 1410],
                   'cropFile': str(source.relative_to(WEB)), 'cropSha256': sha(source),
                   'selectionBoxXYXYInCrop': list(box),
                   'method': 'Grayscale <128, largest 8-connected component inside inspected selection, closed pixel-edge outlines; no smoothing or invented curves.',
                   'foregroundPixels': len(selected), 'touchesSelectionEdge': False},
    }


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    vectors_file = ROUND / 'mark-vectors.json'
    assert sha(vectors_file) == 'e616c888f359df46c318dbd4b165a7189ad2f9bf561553b909e8314fdf68428d'
    assert sha(ROUND / 'source-reference.png') == 'ea7d60b22a7ad45a06dddacdc04303fd844a64c0f0cc5e1d25bf469a0f58fed4'
    vectors = json.loads(vectors_file.read_text())
    definitions = [
        ('ringed-wedge', 0xE000, 'a5', 'একটি ডিম্বাকার বেষ্টনীর মধ্যে খোলা ∧-আকৃতির চিহ্ন', True),
        ('bare-wedge', 0xE001, 'w1-m2', 'বেষ্টনীবিহীন খোলা ∧-আকৃতির চিহ্ন', False),
        ('solid-down-arrow', 0xE002, None, 'নিচের দিকে মোটা তীরচিহ্ন', False),
        ('conditional-three-or-one', 0xE003, 'a4', 'উৎসে দেখা বিশেষ শর্তসাপেক্ষ মাত্রাচিহ্ন', False),
    ]
    outlines = {}
    catalog = []
    glyphs = {'.notdef': TTGlyphPen(None).glyph(), 'space': TTGlyphPen(None).glyph()}
    metrics = {'.notdef': (300, 0), 'space': (300, 0)}
    cmap = {32: 'space'}
    for symbol_id, codepoint, trace_id, label, intrinsic_ring in definitions:
        if trace_id:
            trace = vectors['traces'][trace_id]
            outline = {
                'path': trace['path'],
                'source': {'pdfSha256': PDF_HASH, 'physicalPage': 1,
                           'vectorFile': str(vectors_file.relative_to(ROOT)), 'vectorSha256': sha(vectors_file),
                           'traceId': trace_id, 'sourceImageSha256': vectors['source_image_sha256'],
                           'sourceImageSize': [1510, 1420], 'fullPageImageSize': [2120, 3000],
                           'cropOffsetInFullPage': [275, 1100], 'traceBoxXYWH': trace['bbox'],
                           'method': vectors['method'], 'threshold': vectors['threshold']},
            }
        else:
            outline = trace_arrow()
        outlines[symbol_id] = outline
        recording = RecordingPen()
        parse_path(outline['path'], recording)
        bounds = BoundsPen(None)
        recording.replay(bounds)
        left, top, right, bottom = bounds.bounds
        scale = 780 / (bottom - top)
        pen = TTGlyphPen(None)
        recording.replay(TransformPen(pen, (scale, 0, 0, -scale, 60 - left * scale, 90 + bottom * scale)))
        glyph_name = f'uni{codepoint:04X}'
        glyphs[glyph_name] = pen.glyph()
        advance = round((right - left) * scale + 120)
        metrics[glyph_name] = (advance, 60)
        cmap[codepoint] = glyph_name
        catalog.append({
            'id': symbol_id, 'text': chr(codepoint), 'codepoint': f'U+{codepoint:04X}',
            'labelBn': label, 'fontFamily': 'Qarian Symbols', 'intrinsicRing': intrinsic_ring,
            'advanceWidthEm': advance / 1000, 'inkHeightEm': .78,
            'identity': 'private-use observed graphical template; not a Unicode identity',
            'meaningVerified': False, 'occurrenceShapeVerified': False, 'letterAnchorVerified': False,
            'source': outline['source'],
            'limits': 'Template copied from one inspected occurrence. Threshold and integer font coordinates approximate scan edges. Reuse does not verify every occurrence, reading meaning, original metal/typeface design or letter position.',
        })
        if symbol_id == 'conditional-three-or-one':
            catalog[-1]['legendInterpretation'] = {
                'textBn': 'দম ফেলিলে তিন; না ফেলিলে এক',
                'physicalPage': 5,
                'sourceEvidence': 'evidence/symbol-fix-2026-10-03/source-legend-audit.json',
                'status': 'source reader confirms legend rule for this graphic family; does not identify this as Unicode Bengali digit 6 or approve individual occurrences',
            }
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(list(glyphs))
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=1000, descent=-100)
    builder.setupNameTable({'familyName': 'Qarian Symbols', 'styleName': 'Regular',
                            'uniqueFontIdentifier': 'QarianSymbols-20261003-v1',
                            'fullName': 'Qarian Symbols Regular', 'psName': 'QarianSymbols-Regular',
                            'version': 'Version 1.000',
                            'description': 'Private-use scan-derived graphic templates. No verified Unicode semantics or Quran-wide fidelity claim.'})
    builder.setupOS2(sTypoAscender=1000, sTypoDescender=-100, usWinAscent=1000, usWinDescent=100)
    builder.setupPost()
    builder.setupMaxp()
    builder.font['head'].created = builder.font['head'].modified = 2082844800
    builder.font.recalcTimestamp = False
    builder.font.flavor = 'woff2'
    output = WEB / 'dist/fonts/QarianSymbols.woff2'
    output.parent.mkdir(parents=True, exist_ok=True)
    builder.font.save(output)
    check = TTFont(output)
    assert all(check.getBestCmap()[c] == f'uni{c:04X}' for c in (0xE000, 0xE001, 0xE002, 0xE003))
    assert not any(t in check for t in ('SVG ', 'CBDT', 'CBLC', 'sbix', 'EBDT', 'EBLC'))
    catalog_doc = {
        'schemaVersion': '1.0.0', 'status': 'source-derived-templates-not-whole-Quran-verified',
        'font': {'family': 'Qarian Symbols', 'url': 'fonts/QarianSymbols.woff2',
                 'sha256': sha(output), 'bytes': output.stat().st_size, 'format': 'WOFF2 TrueType outlines',
                 'unitsPerEm': 1000, 'containsRasterOrSvg': False},
        'encoding': 'BMP Private Use Area; preserve symbol ID and this catalogue with copied PUA text. PUA characters have no meaning outside this font/data contract.',
        'symbols': catalog,
        'unresolved': ['Damaged PDF3 row0-a8 has no confidently separable/recovered glyph; no font glyph is assigned.',
                       'Exact occurrence-specific outlines, semantic interpretations and letter anchors remain separate verification tasks.'],
    }
    dump(WEB / 'dist/data/symbol-catalog.json', catalog_doc)
    dump(WORK / 'glyph-outlines.json', outlines)
    dump(WORK / 'font-build-report.json', {'fontSha256': sha(output), 'fontBytes': output.stat().st_size,
         'catalogSha256': sha(WEB / 'dist/data/symbol-catalog.json'), 'tables': sorted(check.keys()),
         'puaCmap': {f'U+{c:04X}': check.getBestCmap()[c] for c in (0xE000, 0xE001, 0xE002, 0xE003)},
         'rasterOrSvgTables': [], 'semanticOrOccurrenceApproval': False})
    print(json.dumps({'font': str(output), 'bytes': output.stat().st_size, 'sha256': sha(output)}))


if __name__ == '__main__':
    main()
