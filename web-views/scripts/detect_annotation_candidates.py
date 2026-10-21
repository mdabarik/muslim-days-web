#!/usr/bin/env python3
"""Detect small ink components in annotation bands; output review candidates only."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('page',type=int);a=ap.parse_args()
 base=ROOT/'evidence/resume-2026-10-21'/f'page{a.page:03d}-annotation-review';im=Image.open(base/f'p{a.page:03d}.png').convert('L');A=np.array(im);H,W=A.shape
 # Calibrated from 300-DPI Quran pages. Wide crops and explicit review prevent promotion errors.
 # Annotation labels occupy the narrow strip below the prior translation and
 # above the next Arabic harakat. Keeping this band narrow avoids promoting
 # Arabic vowel marks as annotation candidates.
 first=int(H*.047); spacing=int(H*.0778); band_h=int(H*.010); candidates=[];thumbs=[]
 for row in range(11):
  y0=max(0,first+row*spacing);y1=min(H,y0+band_h);x0=int(W*.055);x1=int(W*.945)
  mask=A[y0:y1,x0:x1] < 75
  # Remove scan rules but retain compact glyph strokes.
  lab,n=ndimage.label(mask,structure=np.ones((3,3),dtype=int));objs=ndimage.find_objects(lab)
  rowc=[]
  for label,sl in enumerate(objs,1):
   if sl is None:continue
   yy,xx=sl;h=yy.stop-yy.start;w=xx.stop-xx.start;area=int((lab[sl]==label).sum())
   if not (5<=w<=85 and 8<=h<=75 and 18<=area<=1800):continue
   bx=[x0+xx.start,y0+yy.start,w,h];crop=Image.fromarray(A[bx[1]:bx[1]+h,bx[0]:bx[0]+w]).convert('RGB')
   key=f'r{row:02d}-c{len(rowc):02d}';p=base/f'candidate-{key}.png';crop.save(p)
   rec={'rowIndex':row,'candidateId':key,'sourceBox':bx,'area':area,'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'candidate_unreviewed'};rowc.append(rec);candidates.append(rec)
  # RTL source order
  rowc.sort(key=lambda z:z['sourceBox'][0],reverse=True)
 report={'physicalPage':a.page,'status':'candidate_detection_only','sourceImage':str((base/f'p{a.page:03d}.png').relative_to(ROOT)),'bandModel':{'firstY':first,'spacing':spacing,'height':band_h},'candidateCount':len(candidates),'candidates':candidates,'rule':'Components may be noise, harakat, or translation text. Direct visual review is mandatory before identity or anchor promotion.'}
 (base/'candidate-detection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 # Review sheet with source boxes, never a publication asset.
 rgb=Image.open(base/f'p{a.page:03d}.png').convert('RGB');dr=ImageDraw.Draw(rgb)
 for r in candidates:
  x,y,w,h=r['sourceBox'];dr.rectangle((x-2,y-2,x+w+2,y+h+2),outline='red',width=2);dr.text((x,y-12),r['candidateId'],fill='red')
 rgb.save(base/'candidate-overlay.jpg',quality=88)
 print(json.dumps({'page':a.page,'candidates':len(candidates),'report':str(base/'candidate-detection.json')}))
if __name__=='__main__':main()
