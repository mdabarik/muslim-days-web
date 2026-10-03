#!/usr/bin/env python3
"""Build a renamed OFL Arabic body font changing only the two sukun outlines.

PYTHONPATH=/tmp/quran-web-tools python3 quran-web/scripts/build_sukun_font.py
Apply only to running Arabic word text. Original-PDF basmala calligraphy uses
round sukuns, so basmala, titles and annotation fonts must remain unchanged.
"""
import hashlib
import json
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont

WEB = Path(__file__).resolve().parents[1]
ROOT = WEB.parent
FONTS = WEB / 'dist/fonts'
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
TARGETS = ('uni0652', 'glyph01442')


def main():
    source_path = FONTS / 'Amiri-Regular.woff2'
    assert SHA(source_path) == '083b22369749e48712b4d6da6c4a13279d62efd17cba60a9fae9f9ecec82c29f'
    vectors_path = ROOT / 'muslim_days/tool/quran_fidelity/runs/fatihah-001/round-05/mark-vectors.json'
    assert SHA(vectors_path) == 'e616c888f359df46c318dbd4b165a7189ad2f9bf561553b909e8314fdf68428d'
    vectors = json.loads(vectors_path.read_text())
    trace = vectors['traces']['w1-m2']
    record = RecordingPen()
    parse_path(trace['path'], record)
    source_bounds = BoundsPen(None)
    record.replay(source_bounds)
    sx0, sy0, sx1, sy1 = source_bounds.bounds
    original = TTFont(source_path, recalcTimestamp=False)
    font = TTFont(source_path, recalcTimestamp=False)
    assert font.getBestCmap()[0x0652] == TARGETS[0]
    assert font['GSUB'].table.LookupList.Lookup[51].SubTable[0].mapping['uni0652'] == TARGETS[1]
    # This font's ss03 changes ampersand/at; it is not a sukun alternate.
    assert font['GSUB'].table.LookupList.Lookup[195].SubTable[0].mapping == {'ampersand': 'glyph06121', 'at': 'glyph01482'}
    changed = []
    for name in TARGETS:
        old = font['glyf'][name]
        old_bounds = [old.xMin, old.yMin, old.xMax, old.yMax]
        scale = min((old.xMax - old.xMin) / (sx1 - sx0), (old.yMax - old.yMin) / (sy1 - sy0))
        center_x, center_y = (old.xMin + old.xMax) / 2, (old.yMin + old.yMax) / 2
        pen = TTGlyphPen(None)
        record.replay(TransformPen(pen, (scale, 0, 0, -scale,
                                       center_x - (sx0 + sx1) / 2 * scale,
                                       center_y + (sy0 + sy1) / 2 * scale)))
        glyph = pen.glyph()
        font['glyf'][name] = glyph
        glyph.recalcBounds(font['glyf'])
        changed.append({'glyph': name, 'originalBounds': old_bounds,
                        'newBounds': [glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax],
                        'uniformSourceScale': scale, 'advanceAndLsb': list(font['hmtx'][name])})
    names = {1: 'Quran Wedge Arabic', 3: 'QuranWedgeArabic-20261003-v1',
             4: 'Quran Wedge Arabic Regular', 5: 'Version 1.000; source wedge adaptation of Amiri 1.002',
             6: 'QuranWedgeArabic-Regular', 16: 'Quran Wedge Arabic', 17: 'Regular',
             18: 'Quran Wedge Arabic Regular', 21: 'Quran Wedge Arabic', 22: 'Regular'}
    for name in font['name'].names:
        if name.nameID in names:
            name.string = names[name.nameID].encode(name.getEncoding())
    font['head'].created = font['head'].modified = 2082844800
    font.recalcTimestamp = False
    # Existing composite bounds contain the smaller fitted outline. Preserve
    # their stored bytes along with every non-target glyph's original data.
    font.recalcBBoxes = False
    font.flavor = 'woff2'
    output = FONTS / 'QuranWedgeArabic.woff2'
    font.save(output)
    derived = TTFont(output)
    outline_changes = [name for name in original.getGlyphOrder()
                       if original['glyf'][name].compile(original['glyf'], recalcBBoxes=False) != derived['glyf'][name].compile(derived['glyf'], recalcBBoxes=False)]
    assert set(outline_changes) == set(TARGETS), outline_changes
    preserved = ('cmap', 'GSUB', 'GPOS', 'GDEF', 'hmtx', 'hhea', 'OS/2')
    for table in preserved:
        assert original[table].compile(original) == derived[table].compile(derived), table
    composites = [name for name in original.getGlyphOrder() if original['glyf'][name].isComposite()
                  and any(c.glyphName in TARGETS for c in original['glyf'][name].components)]
    assert set(composites) == {'uniFE7E', 'uniFE7F'}, composites
    assert original.getBestCmap() == derived.getBestCmap()
    assert not any(t in derived for t in ('SVG ', 'CBDT', 'CBLC', 'sbix', 'EBDT', 'EBLC'))
    license_file = FONTS / 'OFL.txt'
    license_notice = FONTS / 'QuranWedgeArabic-NOTICE.txt'
    license_notice.write_text(
        'Quran Wedge Arabic Regular — modified version of Amiri Regular 1.002\n'
        'Copyright 2010-2022 The Amiri Project Authors (https://github.com/aliftype/amiri).\n'
        'Licensed under the SIL Open Font License, Version 1.1; see OFL.txt.\n\n'
        'Modification: only uni0652 and its contextual alternate glyph01442 outlines\n'
        'were changed to a source-derived open wedge. Unicode, shaping, positioning,\n'
        'metrics and all other glyph outlines are unchanged. Family/PostScript names\n'
        'were changed to Quran Wedge Arabic / QuranWedgeArabic-Regular.\n'
        'The source wedge is a trace of PDF1 mark w1-m2, not a recovered publisher font.\n'
        'Apply only to running Arabic body words, not basmala or annotation typography.\n', encoding='utf-8')
    metadata = {
        'schemaVersion': '1.0.0',
        'family': 'Quran Wedge Arabic', 'url': 'fonts/QuranWedgeArabic.woff2',
        'sha256': SHA(output), 'bytes': output.stat().st_size,
        'sourceFont': {'file': 'fonts/Amiri-Regular.woff2', 'sha256': SHA(source_path), 'version': '1.002'},
        'license': {'name': 'SIL Open Font License 1.1', 'file': 'fonts/OFL.txt', 'sha256': SHA(license_file),
                    'notice': 'fonts/QuranWedgeArabic-NOTICE.txt', 'renamedDerivative': True},
        'sourceShape': {'pdfSha256': '73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640',
                        'physicalPage': 1, 'traceId': 'w1-m2', 'vectorSha256': SHA(vectors_path),
                        'sourceImageSha256': vectors['source_image_sha256'],
                        'boundsInSourceCrop': list(source_bounds.bounds), 'originalVectorFile': str(vectors_path.relative_to(ROOT)),
                        'method': 'Uniformly fit inspected source wedge contour inside previous sukun ink bounds, preserving its aspect ratio and old center; original mark anchors and metrics remain intact.'},
        'replacementGlyphs': changed, 'changedOutlineCount': len(outline_changes),
        'otherGlyphOutlinesUnchanged': len(original.getGlyphOrder()) - len(outline_changes),
        'preservedTables': list(preserved), 'unicodePreserved': 'U+0652; no text substitution or PUA conversion',
        'contextualCoverage': 'uni0652 and its only GSUB substitution output glyph01442, lookup 51; ss03 is unrelated ampersand/at styling.',
        'inheritedPresentationForms': {'glyphs': composites, 'codepoints': ['U+FE7E', 'U+FE7F'],
                                       'note': 'Composite glyph bytes are unchanged but their referenced sukun outline inherits the wedge. These are sukun presentation forms, not other diacritics.'},
        'applyTo': 'Running Arabic .word text only. Exclude basmala calligraphy, headings, Qarian Symbols, Bengali annotation fonts, and independently source-shaped Fatihah opening font.',
        'limits': 'Changes sukun graphic family only. It does not recover the entire source typeface or verify source-specific letter/haraka positions. Rounded integer font coordinates approximate source-pixel contours.',
    }
    (WEB / 'dist/data/sukun-font.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'font': str(output), 'bytes': output.stat().st_size, 'sha256': SHA(output), 'changedGlyphs': outline_changes, 'preservedTables': preserved}))


if __name__ == '__main__':
    main()
