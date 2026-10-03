"""Merge new source transcriptions (source/pages/page-NNN.json) into dist/data.

The seven earlier pages keep their original candidate objects untouched, except page 6, whose
original rows 0-2 are copied verbatim and continued by a new transcription. Nothing here
fills text from another edition; ayah references and words come only from the authoring files.
"""
import hashlib, json, os, sys, unicodedata
from pathlib import Path

ROOT = Path(os.environ.get('QURAN_ROOT') or Path(__file__).resolve().parents[2])
SOURCE = ROOT / 'source/pages'
DIST = ROOT / 'dist/data'
PDF_HASH = '73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640'
TRANSCRIPTION = 'claude-2026-10'
LEGEND = {  # (printed, enclosure) -> (legend, legend page, conditional); taken from the earlier pages and the PDF4-5 legend
    ('১', 'none'): ('এক আলিফ', 5, False), ('৩', 'none'): ('তিন আলিফ', 5, False), ('৪', 'none'): ('চার আলিফ', 5, False),
    ('ম', 'none'): ('মোটা', 4, False), ('শ', 'none'): ('শিষ', 4, False), ('গ', 'none'): ('গুন্নাহ', 4, False),
    ('ক', 'none'): ('ক্বলক্বলাহ', 4, False), ('৭', 'none'): ('ইখফা', 4, False),
    ('৬', 'none'): ('দম ফেলিলে তিন / না ফেলিলে এক', 5, True),
    ('১', 'circle'): ('দম ফেলিলে এক আলিফ', 5, True), ('২', 'circle'): ('দম ফেলিলে দুই আলিফ', 5, True),
}
SHAPES = {
    'ringed-wedge': ('', 'oval', 'আরবী সাকিন', 4, 'Closed oval enclosing inverted-V wedge'),
    'conditional-three-or-one': ('৬', 'none', 'দম ফেলিলে তিন / না ফেলিলে এক', 5, 'Conditional sign printed like Bengali ৬ with a right lobe'),
    'solid-down-arrow': ('', 'none', None, None, 'Solid downward arrow above a stop / verse boundary'),
}
VISUAL = 'Visual reading from a 300 dpi render of the original PDF page; no pixel boxes measured; independent review recorded separately.'


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    tmp.replace(path)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def clusters(text, prefix):
    result = []
    for index, c in enumerate(text):
        if unicodedata.category(c).startswith('M') and result:
            result[-1]['text'] += c
            result[-1]['endCodepoint'] = index + 1
        else:
            result.append({'id': f'{prefix}:g{len(result)}', 'text': c, 'startCodepoint': index, 'endCodepoint': index + 1, 'sourceBox': None, 'verified': False})
    return result


def conf(level):
    return {'level': level or 'medium', 'basis': VISUAL}


def convert(a, n, review):
    """Authoring JSON -> candidate in the earlier pages' schema (boxes null)."""
    rows = []
    for ri, row in enumerate(a['rows']):
        ri = row.get('row_index', ri)
        words_in_row = []
        segments = []
        for si, seg in enumerate(row.get('arabic', [])):
            ws = []
            for w in seg['words']:
                words_in_row.append(w)
                ws.append({'id': f'r{ri}w{len(words_in_row)}', 'text': w, 'bbox': None})
            stop = seg.get('stop')
            segments.append({
                'ayah_ref': seg['ayah'], 'text': ' '.join(seg['words']), 'words': ws, 'bbox': None, 'confidence': conf(seg.get('confidence')),
                'stop_sign': {'printed': stop, 'kind': 'ruku' if stop == 'ع' else 'waqf', 'bbox': None} if stop else None,
                'verse_marker': {'numeral_bn': seg['end_marker'], 'form': 'rosette', 'bbox': None} if seg.get('end_marker') else None,
            })
        glyphs = []
        for mi, m in enumerate(row.get('marks', []), 1):
            shape = m.get('shape')
            if shape:
                printed, enclosure, legend, legend_page, desc = SHAPES[shape]
                conditional = shape == 'conditional-three-or-one'
            else:
                printed, enclosure = m['printed'], m.get('enclosure', 'none')
                legend, legend_page, conditional = LEGEND.get((printed, enclosure), (None, None, False))
                desc = f'Printed Bengali {printed}' + ('' if enclosure == 'none' else f' inside a {enclosure}')
            t = m['target']
            if isinstance(t, int):
                attachment = {'target': f'r{ri}w{t}', 'basis': 'visual_estimate', 'offset_in_word': round(float(m['offset']), 3),
                              'offset_basis': 'Visual estimate of the sign centre from the word\'s right edge on a 300 dpi crop; semantic span inferred.'}
            else:
                kind, idx = t.split(':')
                attachment = {'target': f'{kind}:{idx}', 'basis': 'visual_estimate', 'offset_in_word': None, 'offset_basis': 'Sign printed above a stop/verse boundary, not a word.'}
            glyphs.append({'id': f'r{ri}-a{mi}', 'printed': printed, 'shape_description': desc, 'enclosure': enclosure, 'legend_bengali': legend,
                           'legend_source_page': legend_page, 'conditional': conditional, 'bbox': None, 'attachment': attachment,
                           'confidence': conf(m.get('confidence')), **({'shape_id': shape} if shape else {})})
        bengali = [{'ayah_ref': b['ayah'], 'numeral_bn': b.get('numeral', ''), 'text': b['text'], 'bbox': None, 'confidence': conf(b.get('confidence'))} for b in row.get('bengali', [])]
        rows.append({'row_index': ri, 'bbox': None, 'annotation_band': {'bbox': None, 'glyphs': glyphs}, 'arabic_segments': segments, 'bengali_segments': bengali})
    headers = []
    for h in a.get('surah_headers', []):
        headers.append({'surah': h['surah'], 'before_row': h['before_row'], 'arabic': h.get('arabic'), 'bengali': h.get('bengali'),
                        'surah_number_bn': h.get('surah_number_bn'), 'revelation_bn': h.get('revelation_bn'), 'ruku_bn': h.get('ruku_bn'),
                        'ayah_count_bn': h.get('ayah_count_bn'), 'basmala': h.get('basmala'), 'bbox': None})
    top = next((h for h in headers if h['before_row'] == 0), None)
    return {
        'schema_version': '1.1.0-claude',
        'source': {'pdf_sha256': PDF_HASH, 'pdf_page_number': n, 'coordinate_system': 'pdftoppm 300 dpi; boxes not measured (null)'},
        'printed_page': a.get('printed_page'),
        'surah_header': {k: top[k] for k in ('arabic', 'bengali', 'surah_number_bn', 'revelation_bn', 'ruku_bn', 'ayah_count_bn', 'bbox')} if top else None,
        'basmala': top['basmala'] if top and top.get('basmala') else None,
        'surah_headers': headers,
        'rows': rows,
        'page_furniture': [{**f, 'bbox': None, 'confidence': conf(f.get('confidence'))} for f in a.get('furniture', [])],
        'non_content_marks': a.get('non_content_marks', []),
        'provenance': {'method': 'Source-first visual transcription from the local original PDF at 300 dpi; reference skeleton used only as a mismatch detector.',
                       'extracted_by': a.get('extracted_by', 'Claude transcription agent'), 'reviewed_by': (review or {}).get('reviewer'),
                       'transcription': TRANSCRIPTION},
        'unresolved': [{'id': f'P{n}-U{i + 1}', 'question': u.get('question') or u.get('note'), 'where': u.get('where'), 'blocking': True} for i, u in enumerate(a.get('uncertain', []))],
    }


def doc_from_candidate(n, cand, cand_bytes, legacy=None, review=None, review_path=None, catalog=None):
    candidate_sha = sha(cand_bytes)
    doc = {'schemaVersion': '2.0.0-draft', 'source': cand['source'], 'candidateSha256': candidate_sha, 'status': 'draft', 'fullyVerified': False,
           'legacyReview': legacy, 'transcription': TRANSCRIPTION, 'transcriptionReview': None, 'originalCandidate': cand, 'graphemes': {}, 'annotations': []}
    if review is not None:
        doc['transcriptionReview'] = {'file': str(review_path.relative_to(ROOT)), 'sha256': sha(review_path.read_bytes()), 'verdict': review.get('verdict'),
                                      'reviewer': review.get('reviewer'), 'scope': review.get('scope')}
    symbols = {s['id']: s for s in catalog['symbols']}
    custom = 0
    for row in cand['rows']:
        for seg in row['arabic_segments']:
            for w in seg['words']:
                doc['graphemes'][w['id']] = clusters(w['text'], f'p{n}:{w["id"]}')
        for g in row['annotation_band']['glyphs']:
            a = {'id': f'p{n}:{g["id"]}', 'rowIndex': row['row_index'], 'sourceId': g['id'], 'text': g.get('printed') or None, 'sourceBox': g.get('bbox'),
                 'targetGraphemeId': None, 'verified': False, 'unresolved': ['letter_anchor_not_verified'], 'draftWordAttachment': g.get('attachment')}
            shape = g.get('shape_id') or ('conditional-three-or-one' if g.get('printed') == '৬' else None)
            if shape:
                s = symbols[shape]
                a['display'] = {'status': 'source_shape_identified', 'symbolId': s['id'], 'character': s['text'], 'fontFamily': catalog['font']['family'],
                                'fontSha256': catalog['font']['sha256'], 'labelBn': g.get('legend_bengali') or s.get('labelBn'), 'standardUnicodeIdentity': None,
                                'encoding': 'project_private_use', 'shapeFamilyConfirmed': True, 'exactOccurrenceOutlineVerified': False,
                                'reviewFile': doc['transcriptionReview']['file'] if review else None, 'reviewSha256': doc['transcriptionReview']['sha256'] if review else None}
                a['unresolved'].append('exact_occurrence_outline_not_verified')
                custom += 1
            t = (g.get('attachment') or {}).get('target') or ''
            if t.startswith(('stop:', 'marker:')):
                kind, idx = t.split(':')
                idx = int(idx)
                segs = row['arabic_segments']
                kind_full = 'stop_sign' if kind == 'stop' else 'verse_marker'
                a['displayAttachment'] = {'targetKind': kind_full, 'rowIndex': row['row_index'], 'segmentIndex': idx,
                                          'targetId': f'p{n}:r{row["row_index"]}:s{idx}:{"stop" if kind == "stop" else "marker"}', 'offset': 0.5,
                                          'verification': 'Boundary attachment read from source; not a letter-identity assertion.'}
                assert idx < len(segs) and segs[idx].get(kind_full), f'page {n} {g["id"]}: boundary target missing'
            doc['annotations'].append(a)
    doc['symbolCatalogue'] = {'url': 'data/symbol-catalog.json', 'sha256': sha((DIST / 'symbol-catalog.json').read_bytes()), 'fontSha256': catalog['font']['sha256'], 'contract': 'source-shapes-pua-1'}
    doc['symbolProgress'] = {'customGlyphOccurrences': custom, 'replacedQuestionMarkOccurrences': 0, 'unresolvedIdentities': 0, 'exactLetterAnchorsVerified': 0}
    return doc


def main():
    catalog = json.loads((DIST / 'symbol-catalog.json').read_text(encoding='utf-8'))
    manifest = json.loads((DIST / 'manifest.json').read_text(encoding='utf-8'))
    built = []
    for path in sorted(SOURCE.glob('page-[0-9][0-9][0-9].json')):
        n = int(path.stem.split('-')[1])
        a = json.loads(path.read_text(encoding='utf-8'))
        review_path = path.with_name(f'page-{n:03}.review.json')
        review = json.loads(review_path.read_text(encoding='utf-8')) if review_path.exists() else None
        entry = manifest['pages'][n - 1]
        if a.get('kind') in ('duplicate', 'non_quran', 'blank'):
            entry.update(status=a['kind'], note=a.get('note'), duplicateOf=a.get('duplicate_of'))
            built.append(n)
            continue
        cand = convert(a, n, review)
        legacy = None
        if a.get('continues_original_rows'):
            # The frozen export holds the untouched earlier page; its rows are copied verbatim.
            old = json.loads((ROOT.parent / f'output-json/data/pages/{n:03}.json').read_text(encoding='utf-8'))
            base, keep = old['originalCandidate'], a['continues_original_rows']
            cand['rows'] = base['rows'][:keep] + [r for r in cand['rows'] if r['row_index'] >= keep]
            for k in ('surah_header', 'basmala', 'printed_page'):
                cand[k] = cand[k] or base.get(k)
            cand['base_candidate'] = base
            cand['provenance']['continues'] = {'originalCandidateSha256': old['candidateSha256'], 'rowsCopiedVerbatim': list(range(keep))}
            legacy = old.get('legacyReview')
        cand_bytes = json.dumps(cand, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        doc = doc_from_candidate(n, cand, cand_bytes, legacy, review, review_path if review else None, catalog)
        if a.get('continues_original_rows'):
            # keep the earlier annotation records (and their reviewed display) for the copied rows
            old_ann = {x['sourceId']: x for x in old['annotations']}
            doc['annotations'] = [old_ann.get(x['sourceId'], x) if x['rowIndex'] < a['continues_original_rows'] else x for x in doc['annotations']]
            doc['symbolProgress'] = {**old['symbolProgress'], 'customGlyphOccurrences': sum((x.get('display') or {}).get('status') == 'source_shape_identified' for x in doc['annotations'])}
        write(DIST / f'pages/{n:03}.json', doc)
        refs = sorted({s['ayah_ref'] for r in cand['rows'] for s in r['arabic_segments']}, key=lambda x: tuple(map(int, x.split(':'))))
        entry.update(status='draft' if not a.get('incomplete') else 'partial_draft', fullyVerified=False, surahs=sorted({int(r.split(':')[0]) for r in refs}), ayahs=refs,
                     rows=len(cand['rows']), words=sum(len(s['words']) for r in cand['rows'] for s in r['arabic_segments']),
                     annotations=len(doc['annotations']), verifiedLetterAnchors=0, candidateSha256=doc['candidateSha256'],
                     transcription=TRANSCRIPTION, reviewVerdict=(review or {}).get('verdict'), file=f'data/pages/{n:03}.json',
                     symbolStatus=doc['symbolProgress'])
        entry.pop('legacyBodyReview', None) if not legacy else None
        built.append(n)
    # rebuild surah/page indexes and totals from every page that has a file
    for s in manifest['surahs']:
        s['pages'], s['draftAyahs'] = [], []
    totals = {'rows': 0, 'words': 0, 'annotations': 0}
    custom = 0
    for e in manifest['pages']:
        if not e.get('file'):
            continue
        for k in totals:
            totals[k] += e[k]
        custom += (e.get('symbolStatus') or {}).get('customGlyphOccurrences', 0)
        for sid in e['surahs']:
            s = manifest['surahs'][sid - 1]
            s['pages'].append(e['page'])
            s['draftAyahs'] += [r for r in e['ayahs'] if int(r.split(':')[0]) == sid]
            s['status'] = 'draft_incomplete'
    for s in manifest['surahs']:
        s['draftAyahs'] = sorted(set(s['draftAyahs']), key=lambda x: int(x.split(':')[1]))
        s['symbolProgress'] = {**s.get('symbolProgress', {}), 'customGlyphOccurrences': sum(manifest['pages'][p - 1].get('symbolStatus', {}).get('customGlyphOccurrences', 0) for p in s['pages'])}
    with_files = [e for e in manifest['pages'] if e.get('file')]
    manifest['summary'].update(surahsWithDrafts=sum(bool(s['pages']) for s in manifest['surahs']), pagesWithDrafts=len(with_files), **totals)
    manifest['summary']['symbolRepairs']['customGlyphOccurrences'] = custom
    missing = 760 - len(with_files) - sum(e.get('status') in ('duplicate', 'non_quran', 'blank') for e in manifest['pages'])
    manifest['blockingIssues'][0] = f'{missing} physical pages have no structured transcription.' if missing else 'Every Quran page has a draft transcription; none is independently fully verified.'
    write(DIST / 'manifest.json', manifest)
    write(ROOT / 'evidence/progress.json', manifest)
    print(json.dumps({'builtPages': len(built), 'summary': manifest['summary']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
