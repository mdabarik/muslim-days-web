#!/usr/bin/env python3
"""Rank visual label candidates from reviewed PDF crops; never verifies/promotes."""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def norm(path):
 a=np.array(Image.open(path).convert('L'));m=a<105
 ys,xs=np.where(m)
 if not len(xs):return None
 m=m[ys.min():ys.max()+1,xs.min():xs.max()+1]
 im=Image.fromarray((m*255).astype('uint8')).resize((24,32),Image.Resampling.NEAREST)
 return np.array(im)>0
def sim(a,b):
 best=0.0
 for dy in range(-2,3):
  for dx in range(-2,3):
   c=np.roll(np.roll(b,dy,0),dx,1);inter=(a&c).sum();union=(a|c).sum();best=max(best,float(inter/union) if union else 0)
 return best
def main():
 ap=argparse.ArgumentParser();ap.add_argument('page',type=int);a=ap.parse_args();base=ROOT/'evidence/resume-2026-10-21'/f'page{a.page:03d}-annotation-review'
 det=json.load(open(base/'candidate-detection.json'));tm=json.load(open(ROOT/'evidence/resume-2026-10-21/annotation-templates/manifest.json'))
 refs=[]
 for r in tm['records']:
  if r['dpi']!=300:continue
  label=r['displayCharacter'] or r['printed']
  if not label:continue
  z=norm(ROOT/r['file'])
  if z is not None:refs.append((label,r['page'],r['sourceId'],z))
 out=[]
 for c in det['candidates']:
  z=norm(ROOT/c['file']);scores=[]
  if z is not None:
   best={}
   for label,p,sid,t in refs:best[label]=max(best.get(label,0),sim(z,t))
   scores=sorted(({'label':k,'score':round(v,4)} for k,v in best.items()),key=lambda x:x['score'],reverse=True)[:3]
  out.append({**c,'suggestions':scores,'status':'unreviewed_visual_suggestion'})
 report={'physicalPage':a.page,'status':'suggestions_only_no_verification','referenceManifest':'evidence/resume-2026-10-21/annotation-templates/manifest.json','candidateCount':len(out),'candidates':out,'rule':'Scores only prioritize direct PDF review. They cannot establish identity, completeness, or grapheme anchor.'}
 (base/'label-suggestions.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'page':a.page,'candidates':len(out),'highScore':sum(bool(x['suggestions']) and x['suggestions'][0]['score']>=.72 for x in out)}))
if __name__=='__main__':main()
