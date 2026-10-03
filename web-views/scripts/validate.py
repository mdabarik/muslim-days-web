"""Structural checks pass separately from the intentionally blocked release gate."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
def load(p):return json.loads(p.read_text())
def validate(root=DIST):
 m=load(root/'data/manifest.json');assert len(m['surahs'])==114;assert [s['id'] for s in m['surahs']]==list(range(1,115));assert len(m['pages'])==760
 counts={'words':0,'annotations':0,'rows':0};blockers=[];docs=[]
 catalog=load(root/'data/symbol-catalog.json');symbol_map={s['id']:s for s in catalog['symbols']}
 font_sha=hashlib.sha256((root/catalog['font']['url']).read_bytes()).hexdigest();assert font_sha==catalog['font']['sha256'],'Font integrity failure'
 catalog_sha=hashlib.sha256((root/'data/symbol-catalog.json').read_bytes()).hexdigest()
 review_path=ROOT/'evidence/symbol-fix-2026-10-03/source-legend-audit.json';review=load(review_path);review_sha=hashlib.sha256(review_path.read_bytes()).hexdigest()
 records={(r.get('page') or r.get('pdfPage'),r.get('sourceId') or r.get('id')):r for r in review['occurrences']+review.get('conditionalOccurrences',[])}
 unresolved_ids={(r['pdfPage'],r['id']) for r in review['unresolved'] if r.get('suppressAssertedCharacterDisplay')}
 custom_count=empty_fixed=0
 for p in m['pages']:
  if not p.get('file'):
   blockers.append(f'PDF {p["page"]}: missing transcription / source-page classification');continue
  d=load(root/p['file']);assert not p['fullyVerified'];assert not d['fullyVerified'];assert d['status']=='draft';docs.append(d);source=d['originalCandidate'];assert d['source']['pdf_sha256']==m['source']['sha256'];assert p['candidateSha256']==d['candidateSha256']
  original=ROOT.parent/'muslim_days/tool/quran_fidelity/full_quran/content'/f'page-{p["page"]:03}'/f'page-{p["page"]:03}.json'
  if original.exists():assert hashlib.sha256(original.read_bytes()).hexdigest()==d['candidateSha256'],'Changed source candidate'
  gs={};words={};glyphs=[]
  for row in source['rows']:
   counts['rows']+=1
   for s in row['arabic_segments']:
    for w in s['words']:
     words[w['id']]=w;clusters=d['graphemes'][w['id']]
     assert ''.join(g['text'] for g in clusters)==w['text'],'Unicode sequence changed'
     for g in clusters:
      assert g['id'] not in gs;gs[g['id']]=g
      assert w['text'][g['startCodepoint']:g['endCodepoint']]==g['text']
     counts['words']+=1
   glyphs.extend((row.get('annotation_band') or {}).get('glyphs',[]))
  assert len(glyphs)==len(d['annotations']);counts['annotations']+=len(glyphs)
  for a,old in zip(d['annotations'],glyphs):
   assert a['sourceId']==old['id'];assert a['sourceBox']==old['bbox'];assert a['draftWordAttachment']==old['attachment'];assert a['text']==(old.get('printed') or None)
   display=a.get('display');key=(p['page'],a['sourceId'])
   if key in unresolved_ids:assert display and display['status']=='unresolved_identity','Damaged source character promoted'
   if display:
    assert display['reviewSha256']==review_sha,'Stale symbol source review'
    if display['status']=='source_shape_identified':
     r=records[key];assert r['sourceJsonSha256']==d['candidateSha256'];assert r['sourceAnnotationSha256']==hashlib.sha256(json.dumps(old,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
     assert display['symbolId']==r['shapeId'],'Symbol family substituted';g=symbol_map[display['symbolId']]
     assert display['character']==g['text'] and display['fontSha256']==font_sha,'Wrong glyph/font binding'
     assert display['standardUnicodeIdentity'] is None and not display['exactOccurrenceOutlineVerified']
     assert a.get('displayAttachment')==r.get('displayAttachment'),'Boundary target differs from independent source review'
     custom_count+=1;empty_fixed+=old.get('printed')==''
   elif key in records:raise AssertionError('Reviewed source glyph mapping dropped')
   if a['verified']:
    assert a['targetGraphemeId'] in gs and gs[a['targetGraphemeId']]['verified'];assert gs[a['targetGraphemeId']]['sourceBox'];assert a.get('review'), 'No independent anchor review'
   else:blockers.append(f'PDF {p["page"]} {a["sourceId"]}: unverified letter anchor')
  review=d.get('fullAcceptance') or {}
  if not (review.get('verdict')=='accept' and review.get('scope')=='entire_source_page_and_web_render' and review.get('candidateSha256')==d['candidateSha256'] and review.get('independentReviewer') and review.get('fontSha256') and review.get('renderSha256')):
   blockers.append(f'PDF {p["page"]}: missing full source+web independent acceptance')
  if any(u.get('blocking') and u.get('status')!='resolved' for u in source.get('unresolved',[])):blockers.append(f'PDF {p["page"]}: unresolved source')
  if d.get('symbolCatalogue'):assert d['symbolCatalogue']['sha256']==catalog_sha and d['symbolCatalogue']['fontSha256']==font_sha,'Stale page symbol contract'
 assert custom_count==m['summary']['symbolRepairs']['customGlyphOccurrences'] and empty_fixed==m['summary']['symbolRepairs']['replacedQuestionMarkOccurrences']
 for k,v in counts.items():assert v==m['summary'][k],(k,v,m['summary'][k])
 for s in m['surahs']:
  if not s['sourcePageMappingComplete']:blockers.append(f'Surah {s["id"]}: whole-surah continuity not verified')
  if s['verifiedAyahs']:assert s['status']=='verified','Draft ayat promoted'
 assert not m['releaseReady'] or not blockers, 'Unsafe ready claim'
 assert not any(x.suffix.lower() in {'.pdf','.png','.jpg','.jpeg','.webp'} for x in (root/'data').rglob('*')),'Scan data in reader'
 return {'structuralStatus':'pass','releaseStatus':'blocked' if blockers else 'pass','counts':counts,'blockerCount':len(blockers),'blockers':blockers,'scope':'Data integrity and truthful acceptance gate; not source accuracy verification'}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--release',action='store_true');args=parser.parse_args();report=validate();(ROOT/'evidence/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='blockers'}));sys.exit(2 if args.release and report['releaseStatus']=='blocked' else 0)
