#!/usr/bin/env python3
"""Prepare lossless source evidence for page-by-page annotation review.

This script never OCRs, identifies, or promotes a mark. It renders the requested
physical PDF page, saves eleven generous row crops, and records hashes so a later
human/source review can bind every observed mark without changing the evidence.
"""
import argparse, hashlib, json, subprocess
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PDF = Path('/Users/barik/Downloads/oct 1 bin/CamScanner 09-20-2026 01.00.pdf')
PDF_SHA = '73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640'

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('page',type=int);ap.add_argument('--dpi',type=int,default=300)
    a=ap.parse_args(); assert 1 <= a.page <= 760
    out=ROOT/'evidence'/'resume-2026-10-21'/f'page{a.page:03d}-annotation-review';out.mkdir(parents=True,exist_ok=True)
    stem=out/f'p{a.page:03d}'
    subprocess.run(['pdftoppm','-f',str(a.page),'-singlefile','-png','-r',str(a.dpi),str(PDF),str(stem)],check=True,stdout=subprocess.DEVNULL)
    page=stem.with_suffix('.png');im=Image.open(page);w,h=im.size
    # Preserve overlap deliberately: exact row boundaries are confirmed during review.
    top=int(h*.075);bottom=int(h*.945);step=(bottom-top)/11
    crops=[]
    for i in range(11):
        y0=max(0,int(top+i*step-step*.28));y1=min(h,int(top+(i+1)*step+step*.12))
        p=out/f'row{i:02d}.png';im.crop((int(w*.03),y0,int(w*.97),y1)).save(p)
        crops.append({'rowIndex':i,'file':str(p.relative_to(ROOT)),'box':[int(w*.03),y0,int(w*.97),y1],'sha256':sha256(p)})
    report={'physicalPage':a.page,'status':'evidence_prepared_review_pending','sourcePdf':str(PDF),'sourcePdfSha256':PDF_SHA,'renderDpi':a.dpi,'pageImage':{'file':str(page.relative_to(ROOT)),'size':[w,h],'sha256':sha256(page)},'rowCrops':crops,'promotionRule':'No mark is verified until identity, source box, target grapheme, and direct source review are saved.'}
    (out/'review-status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'page':a.page,'rows':len(crops),'report':str(out/'review-status.json')}))

if __name__=='__main__': main()
