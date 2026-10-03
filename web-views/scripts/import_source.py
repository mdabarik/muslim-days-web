"""Import source-evidenced drafts; never synthesize missing Quran content."""
import hashlib, json, re, unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'muslim_days/tool/quran_fidelity/full_quran/content'
OUT=ROOT/'dist/data'
PDF_HASH='73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640'
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))); tmp.replace(path)
def clusters(text,prefix):
 result=[]
 for index,c in enumerate(text):
  if unicodedata.category(c).startswith('M') and result:
   result[-1]['text']+=c; result[-1]['endCodepoint']=index+1
  else: result.append({'id':f'{prefix}:g{len(result)}','text':c,'startCodepoint':index,'endCodepoint':index+1,'sourceBox':None,'verified':False})
 return result
progress=json.loads((SOURCE/'PROGRESS.json').read_text())
table=(ROOT.parent/'muslim_days/lib/data/surah_data.dart').read_text().split('const _tableEn')[0]
names=re.findall(r"'([^'\n]+\|[^'\n]+\|[MD]\|\d+)'",table)
assert len(names)==114
surahs=[]
for i,n in enumerate(names,1):
 bn,ar,place,count=n.split('|')
 surahs.append({'id':i,'nameBn':bn,'nameAr':ar,'directoryOnly':True,'sourceVerifiedName':False,'pages':[],'draftAyahs':[],'verifiedAyahs':[],'status':'not_transcribed','sourcePageMappingComplete':False})
page_index=[];total_words=total_marks=total_rows=0
for no in range(1,761):
 path=SOURCE/f'page-{no:03}'/f'page-{no:03}.json'
 entry={'page':no,'status':'not_transcribed','fullyVerified':False,'surahs':[],'ayahs':[],'rows':0,'words':0,'annotations':0,'verifiedLetterAnchors':0}
 if path.exists():
  raw=path.read_bytes(); d=json.loads(raw)
  assert d['source']['pdf_sha256']==PDF_HASH
  sha=hashlib.sha256(raw).hexdigest()
  assert progress['pages'][str(no)]['candidate_sha256']==sha, f'Stale candidate {no}'
  review_path=SOURCE/f'page-{no:03}'/'verify-codex/verify.json'
  review=json.loads(review_path.read_text()) if review_path.exists() else None
  doc={'schemaVersion':'2.0.0-draft','source':d['source'],'candidateSha256':sha,'status':'draft','fullyVerified':False,'legacyReview':review,'originalCandidate':d,'graphemes':{},'annotations':[]}
  refs=set();words=0;marks=0
  for row in d['rows']:
   for seg in row['arabic_segments']:
    if seg.get('ayah_ref'): refs.add(seg['ayah_ref'])
    for word in seg.get('words',[]):
     key=f'p{no}:{word["id"]}';doc['graphemes'][word['id']]=clusters(word['text'],key);words+=1
   for mark in (row.get('annotation_band') or {}).get('glyphs',[]):
    doc['annotations'].append({'id':f'p{no}:{mark["id"]}','rowIndex':row['row_index'],'sourceId':mark['id'],'text':mark.get('printed') or None,'sourceBox':mark.get('bbox'),'targetGraphemeId':None,'verified':False,'unresolved':['letter_anchor_not_verified']+(['unicode_shape_unresolved'] if not mark.get('printed') else []),'draftWordAttachment':mark.get('attachment')})
    marks+=1
  refs=sorted(refs,key=lambda x:tuple(map(int,x.split(':'))))
  sids=sorted({int(x.split(':')[0]) for x in refs})
  entry.update(status='partial_draft' if no==6 else 'draft',surahs=sids,ayahs=refs,rows=len(d['rows']),words=words,annotations=marks,candidateSha256=sha,legacyBodyReview=progress['pages'][str(no)].get('body_verified'),file=f'data/pages/{no:03}.json')
  for sid in sids:
   s=surahs[sid-1];s['pages'].append(no);s['draftAyahs']+= [r for r in refs if int(r.split(':')[0])==sid];s['status']='draft_incomplete'
  total_words+=words;total_marks+=marks;total_rows+=len(d['rows'])
  write(OUT/f'pages/{no:03}.json',doc)
 page_index.append(entry)
for s in surahs:s['draftAyahs']=sorted(set(s['draftAyahs']),key=lambda x:int(x.split(':')[1]))
manifest={'schemaVersion':'2.0.0-draft','title':'কুরআন · মূল সংস্করণ','source':{'filename':'CamScanner 09-20-2026 01.00.pdf','sha256':PDF_HASH,'pageCount':760},'releaseReady':False,'summary':{'surahs':114,'surahsWithDrafts':sum(bool(s['pages']) for s in surahs),'verifiedSurahs':0,'pagesWithDrafts':7,'fullyVerifiedPages':0,'rows':total_rows,'words':total_words,'annotations':total_marks,'verifiedLetterAnchors':0},'navigationProvenance':'Surah directory labels only: existing muslim_days/lib/data/surah_data.dart; not a transcription of PDF titles. Ayah references are copied only from source candidates, using this edition numbering. No other Quran text is substituted.','blockingIssues':['753 physical pages have no structured transcription; page 6 is partial.','700 annotation-to-letter identities are not verified. Word-relative offsets are not character anchors.','Source-compatible font outlines and harakat geometry are not verified.','No complete page has independent full-content plus web-render acceptance.','Damaged source glyphs and decorated titles remain unresolved.','PDF has duplicate scans and non-Quran appendix pages; whole-book continuity is not verified.'],'surahs':surahs,'pages':page_index}
write(OUT/'manifest.json',manifest)
write(ROOT/'evidence/progress.json',manifest)
print(json.dumps(manifest['summary']))

from bind_symbols import apply
apply(ROOT)
