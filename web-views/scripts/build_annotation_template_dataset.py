#!/usr/bin/env python3
"""Crop reviewed annotation occurrences for visual matching; never promotes matches."""
import hashlib,json,re
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence/resume-2026-10-21/annotation-templates';CROPS=OUT/'crops';CROPS.mkdir(parents=True,exist_ok=True)
records=[]
for n in (1,2,3,4,5,7,15):
 d=json.load(open(ROOT/f'dist/data/pages/{n:03d}.json'));coord=d['source'].get('coordinate_system','');dpi=600 if '600dpi' in coord else 300
 page=OUT/'source-pages'/f'p{n:03d}-{dpi}.png';im=Image.open(page).convert('RGB');w,h=im.size
 for a in d['annotations']:
  b=a.get('sourceBox')
  if not b:continue
  x,y,bw,bh=map(int,b);pad=max(3,dpi//100);box=(max(0,x-pad),max(0,y-pad),min(w,x+bw+pad),min(h,y+bh+pad))
  if box[2]<=box[0] or box[3]<=box[1]:continue
  key=f'p{n:03d}-{a["sourceId"]}';cp=CROPS/f'{key}.png';im.crop(box).save(cp)
  raw=cp.read_bytes();display=(a.get('display') or {}).get('character')
  records.append({'page':n,'sourceId':a['sourceId'],'printed':a.get('text'),'displayCharacter':display,'displayStatus':(a.get('display') or {}).get('status'),'sourceBox':b,'cropBox':list(box),'dpi':dpi,'file':str(cp.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'verifiedIdentity':bool((a.get('display') or {}).get('status')=='source_shape_identified')})
summary={}
for r in records:
 k=r['displayCharacter'] or r['printed'] or 'UNRESOLVED';summary[k]=summary.get(k,0)+1
report={'status':'template_evidence_only_no_automatic_verification','sourcePdfSha256':'73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640','records':records,'countsByObservedLabel':summary,'recordCount':len(records),'rule':'A visual match is only a candidate; direct source review must confirm identity and grapheme anchor.'}
(OUT/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'records':len(records),'labels':summary},ensure_ascii=False))
