// Exact-context font: never use these four ligatures for unreviewed Arabic words.
let layout,loading;
export async function loadOpening(doc){
 if(doc.source.pdf_page_number!==1)return;
 if(!loading)loading=(async()=>{const response=await fetch('data/opening-typography.json');if(!response.ok)throw new Error('Opening typography unavailable');const data=await response.json();const faces=await document.fonts.load('34px "Fatihah Opening"');if(!faces.length)throw new Error('Opening font unavailable');layout=data;})();
 try{await loading}catch(err){console.warn(err.message)}
}
function matchingWord(word,doc){
 if(!layout||doc.source.pdf_page_number!==layout.scope.physicalPage||doc.source.pdf_sha256!==layout.source.pdfSha256||doc.candidateSha256!=='40ea961e502a04ac307f6de32926108a2080de1faf5df500ebc8d39bed004ca7')return null;
 return layout.words.find(w=>w.pageWordId===word.id&&w.text===word.text);
}
export function applyOpeningWord(wrap,body,word,doc){
 const spec=matchingWord(word,doc);if(!spec)return false;
 wrap.classList.add('source-opening-word');wrap.dataset.openingWord=spec.id;
 wrap.style.width=spec.widthEm+'em';wrap.style.height=spec.heightEm+'em';
 body.style.left=spec.textLeftEm+'em';body.style.top=spec.textTopEm+'em';
 for(const node of wrap.querySelectorAll('.mark')){
  const id=node.dataset.annotation.replace(/^r0-/,''),mark=layout.marks.find(m=>m.id===id&&m.wordId===spec.id);if(!mark)continue;
  node.classList.add('opening-mark');node.textContent=mark.text;
  node.style.left=mark.leftEm+'em';node.style.top=mark.topEm+'em';node.style.right='auto';node.style.width=mark.widthEm+'em';node.dataset.sourceLeftEm=mark.leftEm;
  node.title+=' — প্রথম আয়াতের উৎস-মাপ অনুযায়ী শব্দের সঙ্গে অবস্থান সংরক্ষিত; অক্ষর-পরিচয় যাচাইকৃত নয়';
 }
 return true;
}
export function openingEnding(doc,seg){
 if(seg.ayah_ref!=='1:1'||!matchingWord(seg.words?.[0]||{},doc)||seg.stop_sign?.printed!=='لا'||seg.verse_marker?.numeral_bn!=='১')return null;
 const spec=layout.layout.endingWrapper,wrap=document.createElement('span');wrap.className='opening-ending';wrap.style.width=spec.widthEm+'em';wrap.style.height=spec.heightEm+'em';wrap.setAttribute('aria-label','ওয়াক্‌ফ لا · আয়াত ১');
 for(const m of layout.marks.filter(m=>m.wordId==='ending')){const n=document.createElement('span');n.className='opening-ending-glyph';n.textContent=m.text;n.style.left=m.leftEm+'em';n.style.top=m.topEm+'em';n.style.width=m.widthEm+'em';n.dataset.sourceTrace=m.id;n.title=m.id==='stop-1'?'ওয়াক্‌ফ لا':'আয়াত ১';wrap.append(n)}
 return wrap;
}
