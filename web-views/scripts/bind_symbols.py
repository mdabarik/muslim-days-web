"""Attach reviewed source-shape display mappings without altering source candidates."""
import hashlib,json
from pathlib import Path
REVIEW_PATH='evidence/symbol-fix-2026-10-03/source-legend-audit.json'
def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(data):return json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def save(p,d):
 temp=p.with_suffix('.tmp');temp.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')));temp.replace(p)
def apply(root):
 root=Path(root);review_file=root/REVIEW_PATH;catalog_file=root/'dist/data/symbol-catalog.json'
 if not review_file.exists() or not catalog_file.exists():return
 review=json.loads(review_file.read_text());catalog=json.loads(catalog_file.read_text());symbols={s['id']:s for s in catalog['symbols']}
 font=root/'dist'/catalog['font']['url'];assert sha(font.read_bytes())==catalog['font']['sha256'],'Symbol font/catalog mismatch'
 records=review['occurrences']+review.get('conditionalOccurrences',[])
 records={(int(r.get('page') or r.get('pdfPage')),r.get('sourceId') or r.get('id')):r for r in records}
 assert len(records)>=55
 unknown={(int(r['pdfPage']),r['id']):r for r in review['unresolved'] if r.get('suppressAssertedCharacterDisplay')}
 review_hash=sha(review_file.read_bytes());catalog_hash=sha(catalog_file.read_bytes())
 total_custom=total_replaced=total_unknown=0;page_status={};surah_status={}
 for p in sorted((root/'dist/data/pages').glob('*.json')):
  doc=json.loads(p.read_text());no=doc['source']['pdf_page_number'];legacy={m['id']:m for row in doc['originalCandidate']['rows'] for m in (row.get('annotation_band') or {}).get('glyphs',[])}
  custom=replaced=unresolved=0
  for a in doc['annotations']:
   a.pop('display',None);a.pop('displayAttachment',None)
   m=legacy[a['sourceId']];key=(no,a['sourceId'])
   if key in unknown:
    a['display']={'status':'unresolved_identity','labelBn':'মূলের ক্ষতিগ্রস্ত চিহ্ন; পরিচয় অমীমাংসিত','reviewSha256':review_hash,'reviewFile':REVIEW_PATH};unresolved+=1
    if 'source_symbol_identity_unresolved' not in a['unresolved']:a['unresolved'].append('source_symbol_identity_unresolved')
   elif key in records:
    r=records[key];assert r['sourceJsonSha256']==doc['candidateSha256'],'Stale shape review';assert r['sourceAnnotationSha256']==sha(canonical(m)),'Changed annotation under review'
    assert r.get('shapeIdentified',r.get('shapeIdentityConfirmed')),'Shape not confirmed'
    symbol=symbols[r['shapeId']]
    a['display']={'status':'source_shape_identified','symbolId':symbol['id'],'character':symbol['text'],'fontFamily':catalog['font']['family'],'fontSha256':catalog['font']['sha256'],'labelBn':r.get('meaningFromSourceLegend') or symbol['labelBn'],'standardUnicodeIdentity':None,'encoding':'project_private_use','shapeFamilyConfirmed':True,'exactOccurrenceOutlineVerified':False,'reviewFile':REVIEW_PATH,'reviewSha256':review_hash}
    if r.get('displayAttachment'):a['displayAttachment']=r['displayAttachment']
    a['unresolved']=[u for u in a['unresolved'] if u!='unicode_shape_unresolved']
    if 'exact_occurrence_outline_not_verified' not in a['unresolved']:a['unresolved'].append('exact_occurrence_outline_not_verified')
    custom+=1;replaced+=not bool(m.get('printed'))
  doc['symbolCatalogue']={'url':'data/symbol-catalog.json','sha256':catalog_hash,'fontSha256':catalog['font']['sha256'],'contract':'source-shapes-pua-1'}
  doc['symbolProgress']={'customGlyphOccurrences':custom,'replacedQuestionMarkOccurrences':replaced,'unresolvedIdentities':unresolved,'exactLetterAnchorsVerified':0}
  save(p,doc);page_status[no]=doc['symbolProgress'];total_custom+=custom;total_replaced+=replaced;total_unknown+=unresolved
 manifest_path=root/'dist/data/manifest.json';manifest=json.loads(manifest_path.read_text())
 manifest['symbolCatalogue']={'url':'data/symbol-catalog.json','sha256':catalog_hash,'fontSha256':catalog['font']['sha256']}
 for p in manifest['pages']:
  p['symbolStatus']=page_status.get(p['page'],{'status':'not_transcribed_no_symbol_inventory'})
 for s in manifest['surahs']:
  s['symbolProgress']={'replacedQuestionMarkOccurrences':sum(page_status[p]['replacedQuestionMarkOccurrences'] for p in s['pages']),'customGlyphOccurrences':sum(page_status[p]['customGlyphOccurrences'] for p in s['pages']),'unresolvedIdentities':sum(page_status[p]['unresolvedIdentities'] for p in s['pages']),'allSurahOccurrencesVerified':False}
 manifest['summary']['symbolRepairs']={'customGlyphOccurrences':total_custom,'replacedQuestionMarkOccurrences':total_replaced,'unresolvedIdentities':total_unknown,'wholeQuranSymbolInventoryComplete':False}
 save(manifest_path,manifest);save(root/'evidence/progress.json',manifest)
 save(root/'evidence/symbol-fix-2026-10-03/integration.json',{'sourceReviewSha256':review_hash,'catalogSha256':catalog_hash,'fontSha256':catalog['font']['sha256'],'counts':manifest['summary']['symbolRepairs'],'pages':page_status,'fullQuranVerified':False,'sourceCandidatesModified':False})
 print(json.dumps(manifest['summary']['symbolRepairs']))
if __name__=='__main__':apply(Path(__file__).resolve().parents[1])
