#!/usr/bin/env python3
"""Package an empty native-text verse frame from reviewed Fatihah verse-1.

PYTHONPATH=/tmp/quran-web-tools python3 quran-web/scripts/build_verse_frame.py
Only the isolated inner numeral contour is removed. The original source
ornament is retained; actual verse digits must be separate selectable text.
"""
import hashlib
import json
from pathlib import Path
import re

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont

WEB = Path(__file__).resolve().parents[1]
ROOT = WEB.parent
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    source = ROOT / 'muslim_days/tool/quran_fidelity/runs/fatihah-001/round-05/mark-vectors.json'
    assert SHA(source) == 'e616c888f359df46c318dbd4b165a7189ad2f9bf561553b909e8314fdf68428d'
    vectors = json.loads(source.read_text())
    trace = vectors['traces']['verse-1']
    paths = re.findall(r'M[^M]+', trace['path'])
    assert len(paths) == 9
    boxes = []
    for path in paths:
        bounds = BoundsPen(None)
        parse_path(path, bounds)
        boxes.append(list(bounds.bounds))
    assert boxes[5] == [598, 174, 613, 199], 'Isolated numeral contour changed'
    assert boxes[0] == [577, 152, 635, 224], 'Outer ornament changed'
    keep = [i for i in range(len(paths)) if i != 5]
    outline = ' '.join(paths[i] for i in keep)
    left, top, right, bottom = boxes[0]
    scale = 1000 / (bottom - top)
    pen = TTGlyphPen(None)
    parse_path(outline, TransformPen(pen, (scale, 0, 0, -scale, -left * scale, bottom * scale)))
    glyph = pen.glyph()
    glyph_name = 'uniE200'
    advance = round((right - left) * scale)
    glyphs = {'.notdef': TTGlyphPen(None).glyph(), 'space': TTGlyphPen(None).glyph(), glyph_name: glyph}
    font = FontBuilder(1000, isTTF=True)
    font.setupGlyphOrder(list(glyphs))
    font.setupCharacterMap({32: 'space', 0xE200: glyph_name})
    font.setupGlyf(glyphs)
    font.setupHorizontalMetrics({'.notdef': (advance, 0), 'space': (250, 0), glyph_name: (advance, 0)})
    font.setupHorizontalHeader(ascent=1000, descent=0, lineGap=0)
    font.setupNameTable({'familyName': 'Quran Verse Frame', 'styleName': 'Regular',
                        'uniqueFontIdentifier': 'QuranVerseFrame-20261003-v1',
                        'fullName': 'Quran Verse Frame Regular', 'psName': 'QuranVerseFrame-Regular',
                        'version': 'Version 1.000',
                        'description': 'Empty source-derived Fatihah verse ornament. Separate live Unicode Bengali digits required.'})
    font.setupOS2(sTypoAscender=1000, sTypoDescender=0, sTypoLineGap=0, usWinAscent=1000, usWinDescent=0)
    font.setupPost()
    font.setupMaxp()
    font.font['head'].created = font.font['head'].modified = 2082844800
    font.font.recalcTimestamp = False
    font.font.flavor = 'woff2'
    output = WEB / 'dist/fonts/VerseFrame.woff2'
    font.font.save(output)
    check = TTFont(output)
    assert check.getBestCmap()[0xE200] == glyph_name
    assert check['glyf'][glyph_name].numberOfContours == 8
    assert not any(t in check for t in ('SVG ', 'CBDT', 'CBLC', 'sbix', 'EBDT', 'EBLC'))
    metadata = {
        'schemaVersion': '1.0.0', 'id': 'fatihah-verse-frame', 'text': '\ue200', 'codepoint': 'U+E200',
        'font': {'family': 'Quran Verse Frame', 'url': 'fonts/VerseFrame.woff2', 'sha256': SHA(output),
                 'bytes': output.stat().st_size, 'unitsPerEm': 1000, 'ascenderEm': 1, 'descenderEm': 0,
                 'lineGapEm': 0, 'advanceEm': advance / 1000, 'inkHeightEm': 1,
                 'containsRasterOrSvg': False},
        'source': {'pdfSha256': '73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640',
                   'physicalPage': 1, 'traceId': 'verse-1', 'vectorSha256': SHA(source),
                   'vectorFile': str(source.relative_to(ROOT)), 'sourceImageSha256': vectors['source_image_sha256'],
                   'sourceBoundsXYXY': boxes[0], 'removedNumeralContourIndex': 5,
                   'removedNumeralBoundsXYXY': boxes[5], 'retainedContourIndices': keep,
                   'method': 'Remove only isolated numeral-1 contour from reviewed nine-contour verse-1 trace; keep eight ornament contours unchanged before uniform font scaling and integer rounding.'},
        'layout': {'fontSizeEqualsFrameHeight': True, 'lineHeightEm': 1, 'widthEm': advance / 1000,
                   'heightEm': 1, 'baselineFromTopEm': 1,
                   'digitCenterXEm': (606 - left) / (bottom - top), 'digitCenterYEm': .5,
                   'safeDigitBoxEm': {'left': (588 - left) / (bottom - top), 'top': (175 - top) / (bottom - top),
                                      'width': 36 / (bottom - top), 'height': 26 / (bottom - top)},
                   'css': 'Render PUA frame in Quran Verse Frame, font-size equal to desired frame height, line-height:1, width:.806em, no padding or letter spacing. Overlay the actual verse-number string as separate selectable Bengali text centered in the aperture; reduce its size for 2/3 digits. Keep the existing exact first-verse source marker untouched.'},
        'encoding': 'Private-use glyph encodes only the ornament, never the numeral. Actual Bengali Unicode digits remain separate real text.',
        'limits': ['Reusing this specific first-Fatihah ornament is a visual design choice, not proof that every source-PDF verse marker has identical geometry.',
                   'The original first verse source marker remains separate and unchanged.',
                   'No Arabic body, harakat, annotation glyph, Unicode numeral data or general font is modified.',
                   'Source-pixel outlines and integer font coordinates approximate scan edges; original publisher font is not recovered.'],
    }
    (WEB / 'dist/data/verse-frame.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'font': str(output), 'bytes': output.stat().st_size, 'sha256': SHA(output), 'advanceEm': advance / 1000, 'retainedContours': 8}))


if __name__ == '__main__':
    main()
