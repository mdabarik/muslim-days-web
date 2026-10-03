#!/usr/bin/env python3
"""Package four audited full-vowelled word contexts and seven native signs.

Run from anywhere with Pillow-independent fonttools + brotli available:
  PYTHONPATH=/tmp/quran-web-tools python3 quran-web/scripts/build_opening_typography.py
No new Quran text is inferred and this font must not be used outside its scope.
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
SOURCE = ROOT / 'muslim_days/tool/quran_fidelity/runs/fatihah-001/source-font-vowelled-feasibility'
ROUND = ROOT / 'muslim_days/tool/quran_fidelity/runs/fatihah-001/round-05'
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    font_path = SOURCE / 'FatihahSourcePilot.ttf'
    contour_path = SOURCE / 'word-contours.json'
    vector_path = ROUND / 'mark-vectors.json'
    assert SHA(font_path) == 'e13097a9846281686adcd7cbe3e83894915039c2c53abefe2a2539d2410dad69'
    assert SHA(contour_path) == 'de1605cef8c965f1334b4f1cbf41e6c404d64cb19f8f2a7ba0c33ee806d2b561'
    assert SHA(vector_path) == 'e616c888f359df46c318dbd4b165a7189ad2f9bf561553b909e8314fdf68428d'
    source = json.loads(contour_path.read_text())
    vectors = json.loads(vector_path.read_text())
    font = TTFont(font_path, recalcTimestamp=False)
    words = []
    for word in source['words']:
        glyph = font['glyf'][word['id']]
        advance, lsb = font['hmtx'][word['id']]
        words.append({
            'id': word['id'], 'pageWordId': 'r0' + word['id'],
            'text': word['text'], 'supportedSequences': word.get('shaping_sequences', [word['text']]),
            'sourceOriginX': word['origin_x'], 'sourceBaselineY': word['baseline_y'],
            'sourceAdvancePx': word['advance_px'], 'sourceInkBoxXYWH': word['ink_bbox'],
            'widthEm': advance / 1000, 'heightEm': 2,
            'baselineFromWrapperTopEm': (word['baseline_y'] - 37) / 100,
            'textTopEm': (word['baseline_y'] - 37) / 100 - 1.11,
            'textLeftEm': 0,
            'glyphMetrics': {'advanceUnits': advance, 'leftSideBearingUnits': lsb,
                             'inkBoundsFontUnits': [glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax],
                             'leftSideBearingMinusXMinEm': (lsb - glyph.xMin) / 1000},
            'sourceXToWrapperEm': '(sourceX - sourceOriginX) / 100',
            'sourceXToAdvanceFraction': '(sourceX - sourceOriginX) / sourceAdvancePx',
            'harakatEmbedded': True, 'embeddedHarakatCount': len(word['included_detached_mark_ids']),
            'letterAnchorsVerified': False,
        })
    word_map = {w['id']: w for w in words}
    marks = []
    entries = [('a1', 'w2'), ('a2', 'w3'), ('a3', 'w4'), ('a4', 'w4'), ('a5', 'w4'),
               ('stop-1', 'ending'), ('verse-1', 'ending')]
    for i, (mark_id, word_id) in enumerate(entries):
        trace = vectors['traces'][mark_id]
        rec = RecordingPen()
        parse_path(trace['path'], rec)
        bounds = BoundsPen(None)
        rec.replay(bounds)
        left, top, right, bottom = bounds.bounds
        pen = TTGlyphPen(None)
        rec.replay(TransformPen(pen, (10, 0, 0, -10, -left * 10, bottom * 10)))
        codepoint = 0xE100 + i
        glyph_name = f'uni{codepoint:04X}'
        order = list(font.getGlyphOrder())
        font['glyf'][glyph_name] = pen.glyph()
        font['hmtx'][glyph_name] = (round((right - left) * 10), 0)
        font.setGlyphOrder(order + [glyph_name])
        for table in font['cmap'].tables:
            if table.isUnicode():
                table.cmap[codepoint] = glyph_name
        origin_x = word_map[word_id]['sourceOriginX'] if word_id != 'ending' else 575
        marks.append({
            'id': mark_id, 'wordId': word_id, 'text': chr(codepoint), 'codepoint': f'U+{codepoint:04X}',
            'sourceTraceId': mark_id, 'sourceInkBoundsXYXY': [left, top, right, bottom],
            'leftEm': (left - origin_x) / 100, 'topEm': (bottom - 37) / 100 - 1.11,
            'widthEm': (right - left) / 100, 'inkHeightEm': (bottom - top) / 100,
            'baselineFromWrapperTopEm': (bottom - 37) / 100,
            'sourceCenterX': (left + right) / 2,
            'sourceCenterAdvanceFraction': ((left + right) / 2 - origin_x) / (word_map[word_id]['sourceAdvancePx'] if word_id != 'ending' else 65),
            'identity': 'source occurrence outline encoded in Private Use Area; preserve mark id and catalogue',
            'positionBasis': 'Observed original source coordinates within atomic source-word wrapper; not inferred Unicode grapheme/letter anchor',
            'letterAnchorVerified': False,
        })
    # Preserve original word outlines, word shaping, advances and vertical metrics.
    for n in font['name'].names:
        if n.nameID in (1, 4, 6):
            n.string = ('FatihahOpeningSource' if n.nameID == 6 else 'Fatihah Opening Source').encode(n.getEncoding())
    font['head'].created = font['head'].modified = 2082844800
    font.flavor = 'woff2'
    output = WEB / 'dist/fonts/FatihahOpening.woff2'
    font.save(output)
    check = TTFont(output)
    original = TTFont(font_path)
    assert check['GSUB'].compile(check) == original['GSUB'].compile(original)
    for w in words:
        key = w['id']
        assert check['glyf'][key].compile(check['glyf']) == original['glyf'][key].compile(original['glyf'])
        assert check['hmtx'][key] == original['hmtx'][key]
    assert not any(t in check for t in ('SVG ', 'CBDT', 'CBLC', 'sbix', 'EBDT', 'EBLC'))
    data = {
        'schemaVersion': '1.0.0', 'scope': {'physicalPage': 1, 'rowIndex': 0, 'printedAyah': '1:1', 'wordIds': ['r0w1', 'r0w2', 'r0w3', 'r0w4']},
        'status': 'source-contour-rendering-for-four-audited-contexts; new HTML integration needs browser review',
        'font': {'family': 'Fatihah Opening Source', 'url': 'fonts/FatihahOpening.woff2',
                 'sha256': SHA(output), 'bytes': output.stat().st_size, 'unitsPerEm': 1000,
                 'ascentEm': 1.43, 'descentEm': .21, 'sourceFontSha256': SHA(font_path),
                 'wordGlyphsAndGsubPreserved': True, 'containsRasterOrSvg': False},
        'source': {'pdfSha256': '73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640',
                   'imageSha256': vectors['source_image_sha256'], 'imageSize': [1510, 1420],
                   'imageOffsetInFullPage': [275, 1100], 'fullPageImageSize': [2120, 3000],
                   'wordContoursSha256': SHA(contour_path), 'markVectorsSha256': SHA(vector_path),
                   'priorReview': str((ROUND / 'review.json').relative_to(ROOT)),
                   'priorReviewSha256': SHA(ROUND / 'review.json')},
        'layout': {'sourcePixelsPerEm': 100, 'sourceUnitsPerPixel': 10,
                   'wrapperSourceTop': 37, 'wrapperSourceBottom': 237, 'wrapperHeightEm': 2,
                   'textLineHeightEm': 1, 'textBaselineFromLineBoxTopEm': 1.11,
                   'css': 'word wrapper: position:relative;display:inline-block;height:2em. Every native child: position:absolute;font-family:"Fatihah Opening Source";font-size:1em;line-height:1;font-feature-settings:"rlig" 1;font-synthesis:none;white-space:pre;direction:rtl;unicode-bidi:isolate. Set child left/top in em using data; zero margins/padding/letter-spacing. Keep overflow visible and baseline word wrappers at a shared top. Do not duplicate embedded harakat.',
                   'baselineFormula': 'textTopEm = (sourceBaselineY - 37) / 100 - 1.11; markTopEm = (sourceInkBottomY - 37) / 100 - 1.11',
                   'endingWrapper': {'id': 'ending', 'sourceOriginX': 575, 'widthEm': .65, 'heightEm': 2}},
        'words': words, 'marks': marks,
        'limitations': ['Only the four exact vowelled contexts are supported. Never apply the font globally or to another occurrence solely because its base text matches.',
                        'Source pixel contours are threshold approximations, not original publisher font outlines.',
                        'Whole-word ligatures preserve source body letters and harakat but do not prove individual letter caret/anchor geometry.',
                        'Prior review concerns a frozen SVG text sample; this new HTML layout requires its own visible rendering and copy checks.',
                        'PUA upper/ending shapes are selectable but need this catalogue to retain interpretation when copied.'],
    }
    dest = WEB / 'dist/data/opening-typography.json'
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'font': str(output), 'bytes': output.stat().st_size, 'sha256': SHA(output), 'data': str(dest)}))


if __name__ == '__main__':
    main()
