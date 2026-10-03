import {loadVerseFrame,verseNumber} from './verse-markers.js';
import {loadOpening,applyOpeningWord,openingEnding} from './opening.js';
import {placeVerifiedAnchor} from './anchors.js';
import {configureSymbols,symbolNode,symbolDescriptor} from './symbols.js';
const $=id=>document.getElementById(id), bn=n=>String(n).replace(/\d/g,d=>'০১২৩৪৫৬৭৮৯'[d]);
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
const cache=new Map();let symbolCatalog,manifest,surah=1,pageNo=1,requestId=0,activeDoc,activeDocs,view='ayah';
const anchorUpdates=[];
async function json(url){const r=await fetch(url);if(!r.ok)throw new Error(`ডেটা লোড হয়নি (${r.status})`);return r.json()}
function storedView(){try{return localStorage.getItem('quran-view')}catch{return null}}
function route(){const p=new URLSearchParams(location.hash.slice(1));return {surah:Number(p.get('surah'))||1,page:Number(p.get('page'))||null,ayah:p.get('ayah'),view:(p.get('view')||storedView())==='rows'?'rows':'ayah'}}
function navigate(sid,p=null,a=null){const q=new URLSearchParams({surah:sid});if(p)q.set('page',p);if(a)q.set('ayah',a);q.set('view',view);const h='#'+q;if(location.hash===h)loadRoute();else location.hash=h}
function directory(){const q=$('search').value.trim().toLowerCase().replace(/[০-৯]/g,d=>'০১২৩৪৫৬৭৮৯'.indexOf(d));$('surah-list').replaceChildren();let count=0;for(const s of manifest.surahs){if(q&&!`${s.id} ${s.nameBn} ${s.nameAr}`.toLowerCase().includes(q))continue;count++;const a=el('a','surah-link'+(s.pages.length?' has-draft':''));a.href='#surah='+s.id;if(s.id===surah)a.setAttribute('aria-current','page');a.append(el('span','num',bn(s.id)));const label=el('span');label.append(el('strong','',s.nameBn),el('small','',s.pages.length?'আংশিক খসড়া আছে':'পাঠ রূপান্তর বাকি'));a.append(label,el('span','state-dot'));a.onclick=()=>{$('sidebar').classList.remove('open');$('list-toggle').setAttribute('aria-expanded','false')};$('surah-list').append(a)}if(!count)$('surah-list').append(el('p','empty','এই নামে কোনো সূরা পাওয়া যায়নি।'))}
function option(value,label){const o=el('option','',label);o.value=value;return o}
function controls(s,doc){$('page-select').replaceChildren();for(const p of s.pages)$('page-select').append(option(p,bn(p)+(p===6?' · আংশিক':'')));$('page-select').value=String(pageNo);$('page-select').disabled=!s.pages.length;
 $('ayah-select').replaceChildren(option('','নির্বাচন করুন'));for(const a of s.draftAyahs)$('ayah-select').append(option(a,bn(a.split(':')[1])));$('ayah-select').disabled=!doc;
 const pos=s.pages.indexOf(pageNo);$('previous').disabled=pos<=0;$('next').disabled=pos<0||pos>=s.pages.length-1;$('page-count').textContent=s.pages.length?`${bn(pos+1)} / ${bn(s.pages.length)} সংরক্ষিত পৃষ্ঠা`:'';
 $('page-label').textContent=doc?`মূল PDF · পৃষ্ঠা ${bn(pageNo)}${doc.originalCandidate.printed_page?' · মুদ্রিত '+doc.originalCandidate.printed_page:''}`:'এই সূরার পাঠ এখনো রূপান্তর হয়নি';$('reader').dataset.page=pageNo;
 if(doc&&view==='ayah')$('page-label').textContent=`আয়াত অনুযায়ী · মূল PDF পৃষ্ঠা ${bn(s.pages[0])}${s.pages.length>1?'–'+bn(s.pages.at(-1)):''}-এর সংরক্ষিত খসড়া`;
 $('reader').dataset.view=view;for(const b of document.querySelectorAll('.view-switch button'))b.setAttribute('aria-pressed',String(b.dataset.view===view));
}
function annotationFor(doc,mark){return doc.annotations.find(a=>a.sourceId===mark.id)}
function attachmentFor(doc,mark){const a=annotationFor(doc,mark);return a?.displayAttachment || {targetKind:'word',targetId:mark.attachment?.target,offset:mark.attachment?.offset_in_word}}
function makeMark(mark,doc){
 const a=annotationFor(doc,mark),node=symbolNode(a,mark,'mark');
 node.dataset.annotation=mark.id;node.dataset.enclosure=mark.enclosure||'none';
 node.title+=' — মূলের সঙ্গে সঠিক অবস্থানের পূর্ণ যাচাই বাকি';
 const fraction=attachmentFor(doc,mark).offset;
 if(Number.isFinite(fraction))node.style.right=`${fraction*100}%`;else{node.style.right='50%';node.classList.add('source-uncertain')}
 return node;
}
function renderWord(word,marks,doc){
 const wrap=el('span','word-wrap'+(!$('show-marks').checked?' no-marks':''));wrap.dataset.wordId=word.id;
 const body=el('span','word',word.text);body.lang='ar';body.dir='rtl';wrap.append(body);
 if($('show-marks').checked)for(const m of marks){const a=annotationFor(doc,m),node=makeMark(m,doc);
  if(a?.verified&&a.targetGraphemeId)anchorUpdates.push(()=>placeVerifiedAnchor(wrap,body,node,a,doc.graphemes[word.id]));wrap.append(node)}
 applyOpeningWord(wrap,body,word,doc);
 return wrap;
}
function boundaryId(doc,row,segmentIndex,kind,item){return item.id||`p${doc.source.pdf_page_number}:r${row.row_index}:s${segmentIndex}:${kind==='stop_sign'?'stop':'marker'}`}
function boundary(doc,row,segmentIndex,kind,item,marks){
 const id=boundaryId(doc,row,segmentIndex,kind,item);
 const wrap=el('span','boundary-target');wrap.dataset.sourceTarget=id;
 wrap.append(kind==='stop_sign'?el('span','stop',item.printed):verseNumber(item.numeral_bn));
 if($('show-marks').checked)for(const m of marks){const a=attachmentFor(doc,m);if(a.targetKind===kind&&a.targetId===id)wrap.append(makeMark(m,doc))}
 return wrap;
}
function symbolGuide(){
 const guide=el('details','symbol-guide');guide.append(el('summary','','চিহ্ন পরিচিতি · মূল PDF-এর নির্দেশনা'));
 const guideList=el('ul');
 for(const [symbolId,label] of [['ringed-wedge','আরবী সাকিন — PDF পৃষ্ঠা ৪-এর নির্দেশনা'],['conditional-three-or-one','দম ফেলিলে তিন / না ফেলিলে এক — PDF পৃষ্ঠা ৫-এর নির্দেশনা'],['solid-down-arrow','নিচমুখী তীর — উৎসে ওয়াক্‌ফের সীমানার ওপর দেখা যায়; আলাদা অর্থ অনুমান করা হয়নি']]){
  const g=symbolCatalog.symbols.find(g=>g.id===symbolId),li=el('li');li.append(symbolNode({display:{symbolId,character:g.text}},{},'guide-symbol'),document.createTextNode(label));guideList.append(li)}
 guide.append(guideList,el('p','','এই চিহ্নগুলো সিলেক্টযোগ্য বিশেষ ফন্টে আঁকা। অন্য অ্যাপে কপি করলে একই ফন্ট প্রয়োজন। প্রতিটি ব্যবহারের অক্ষর-সংযোগ ও হুবহু আকৃতির পূর্ণ যাচাই বাকি।'));return guide;
}
function renderBasmala(d,container){if(d.basmala){const b=el('section','basmala'),ar=el('div','ar',d.basmala.arabic);ar.lang='ar';ar.dir='rtl';b.append(ar,el('p','bn',d.basmala.bengali));container.append(b)}}
// One source segment: its words, then any stop sign / verse marker. `scope` limits the ayah-start lookup.
function appendSegment(flow,doc,row,index,seg,marks,scope){
 const originalEnding=openingEnding(doc,seg);
 for(let i=0;i<(seg.words||[]).length;i++){const w=seg.words[i],word=renderWord(w,marks.filter(m=>{const a=attachmentFor(doc,m);return a.targetKind==='word'&&a.targetId===w.id}),doc);word.dataset.ayah=seg.ayah_ref;if(i===0&&!scope.querySelector(`[data-ayah-start="${seg.ayah_ref}"]`))word.dataset.ayahStart=seg.ayah_ref;if(originalEnding&&i===seg.words.length-1){const tail=el('span','opening-tail');tail.append(word,originalEnding);flow.append(tail,document.createTextNode(' '))}else flow.append(word,document.createTextNode(' '))}
 if(!originalEnding&&(seg.stop_sign||seg.verse_marker)){const end=el('span','verse-end');if(seg.stop_sign?.printed)end.append(boundary(doc,row,index,'stop_sign',seg.stop_sign,marks));if(seg.verse_marker?.numeral_bn)end.append(boundary(doc,row,index,'verse_marker',seg.verse_marker,marks));flow.append(end)}
}
// items: [{doc,m}] — a mark's annotation record lives in its own page document.
function markEvidence(items,block,unplaced){
 const details=el('details','row-evidence');details.append(el('summary','',`${bn(items.length)}টি চিহ্নের তথ্য · অক্ষর-সংযোগের পূর্ণ যাচাই বাকি`));const list=el('ul');
 for(const {doc,m} of items){const a=annotationFor(doc,m),li=el('li'),descriptor=symbolDescriptor(a,m);li.dataset.annotationDetail=m.id;
  const displayed=symbolNode(a,m,'detail-symbol');if(!descriptor.custom)displayed.dataset.enclosure=m.enclosure||'none';
  li.append(displayed,document.createTextNode(' · '+descriptor.label));
  if(a?.display?.status==='unresolved_identity'){li.append(document.createTextNode(' · ক্ষতিগ্রস্ত মূল থেকে নিশ্চিত পাঠ পাওয়া যায়নি; অনুমান করে কোনো অক্ষর বসানো হয়নি।'));details.open=true}
  else if(a?.displayAttachment)li.append(document.createTextNode(' · উৎসে ওয়াক্‌ফের সীমানার সঙ্গে সম্পর্ক দেখা গেছে; এটি অক্ষরের ওপরের চিহ্ন নয়।'));
  list.append(li)
 }
 details.append(list);
 if(unplaced){details.open=true;block.append(el('p','unplaced-note',`${bn(unplaced)}টি চিহ্নের অবস্থান অমীমাংসিত; নিচের তালিকায় পাঠ ও তথ্য রাখা হয়েছে।`))}
 block.append(details)
}
function render(doc){
 activeDoc=doc;activeDocs=null;anchorUpdates.length=0;const container=$('content');container.replaceChildren();const d=doc.originalCandidate;
 container.append(symbolGuide());
 renderSourceHeader(d,container);
 renderBasmala(d,container);
 for(const row of d.rows){
  const block=el('section','text-row');block.dataset.row=row.row_index;block.append(el('div','row-title',`মূলের সারি ${bn(row.row_index+1)}`));
  const flow=el('div','arabic-flow');if(doc.source.pdf_page_number===1&&row.row_index===0)flow.classList.add('fatiha-opening-row');flow.lang='ar';flow.dir='rtl';const marks=(row.annotation_band||{}).glyphs||[];
  for(const [index,seg] of row.arabic_segments.entries())appendSegment(flow,doc,row,index,seg,marks,container);
  block.append(flow);
  for(const seg of row.bengali_segments||[]){const p=el('p','translation');p.append(el('span','ref',seg.numeral_bn||bn(seg.ayah_ref?.split(':')[1]||'')),document.createTextNode(seg.text));block.append(p)}
  if(marks.length){
   const renderedIds=new Set([...flow.querySelectorAll('[data-word-id],[data-source-target]')].map(e=>e.dataset.wordId||e.dataset.sourceTarget));
   markEvidence(marks.map(m=>({doc,m})),block,marks.filter(m=>!renderedIds.has(attachmentFor(doc,m).targetId)).length)
  }
  container.append(block)
 }
 const issues=(d.unresolved||[]).filter(u=>u.status!=='resolved'),box=el('section','page-issues');box.append(el('h3','',pageNo===6?'পৃষ্ঠা ৬-এর মাত্র ৩টি সারি সংরক্ষিত; বাকি অংশ অনুপস্থিত।':'এই পৃষ্ঠার পূর্ণ যাচাই শেষ হয়নি।'));const list=el('ul');list.append(el('li','','কারিয়ানা চিহ্নের অক্ষরভিত্তিক অবস্থানের পূর্ণ যাচাই বাকি।'),el('li','','চেনা বিশেষ চিহ্ন এখন মূল থেকে তৈরি ফন্টে আছে; প্রতিটি ব্যবহারের হুবহু আকৃতি ও মূল পাঠের ফন্ট এখনো পুরোপুরি যাচাইকৃত নয়।'));for(const u of issues)list.append(el('li','',u.question||u.description||u.id));box.append(list);container.append(box);
 renderFurniture(d,container,doc);scheduleAnchors();
}
// Ayah view: regroup the surah's source segments by their recorded ayah_ref.
// Boundaries come only from the source's ayah_ref and printed verse markers; nothing is filled in.
const bnNumber=t=>Number(String(t||'').replace(/[০-৯]/g,d=>'০১২৩৪৫৬৭৮৯'.indexOf(d)))||0;
function collectAyahs(docs){
 const ayahs=new Map(),mine=ref=>ref?.split(':')[0]===String(surah);
 const entry=ref=>{if(!ayahs.has(ref))ayahs.set(ref,{ref,n:Number(ref.split(':')[1]),parts:[],bengali:[],marks:[],unplaced:[]});return ayahs.get(ref)};
 for(const doc of docs)for(const row of doc.originalCandidate.rows){
  const marks=(row.annotation_band||{}).glyphs||[],owner=new Map();
  for(const [index,seg] of row.arabic_segments.entries()){if(!mine(seg.ayah_ref))continue;
   entry(seg.ayah_ref).parts.push({doc,row,index,seg,marks});
   for(const w of seg.words||[])owner.set(w.id,seg.ayah_ref);
   for(const kind of ['stop_sign','verse_marker'])if(seg[kind])owner.set(boundaryId(doc,row,index,kind,seg[kind]),seg.ayah_ref)}
  for(const seg of row.bengali_segments||[])if(mine(seg.ayah_ref))entry(seg.ayah_ref).bengali.push(seg);
  for(const m of marks){const ref=owner.get(attachmentFor(doc,m).targetId);if(ref)entry(ref).marks.push({doc,m});else{const first=row.arabic_segments.find(s=>mine(s.ayah_ref));if(first)entry(first.ayah_ref).unplaced.push({doc,m})}}
 }
 return [...ayahs.values()].sort((a,b)=>a.n-b.n);
}
function sourceLocation(parts){
 const pages=new Map();for(const {doc,row} of parts){const p=doc.source.pdf_page_number;if(!pages.has(p))pages.set(p,new Set());pages.get(p).add(row.row_index+1)}
 return [...pages].map(([p,rows])=>{const r=[...rows];return `পৃষ্ঠা ${bn(p)} · সারি ${bn(r[0])}${r.length>1?'–'+bn(r.at(-1)):''}`}).join(' → ');
}
const ended=a=>!!a?.parts.at(-1)?.seg.verse_marker?.numeral_bn;
function ayahGap(from,to){const p=el('section','ayah-gap');p.dataset.missingAyahs=`${from}-${to}`;p.append(el('strong','',from===to?`আয়াত ${bn(from)}`:`আয়াত ${bn(from)}–${bn(to)}`),document.createTextNode(' · মূল PDF থেকে এখনো রূপান্তর হয়নি। অনুমান বা অন্য সংস্করণের পাঠ বসানো হয়নি।'));return p}
function ayahSection(a,prev){
 const block=el('section','text-row ayah-section');block.dataset.ayahSection=a.ref;block.dataset.pages=[...new Set(a.parts.map(p=>p.doc.source.pdf_page_number))].join(' ');
 const title=el('div','row-title');title.append(el('strong','',`আয়াত ${bn(a.n)}`),el('span','',a.parts.length?sourceLocation(a.parts):'আরবি অংশ সংরক্ষিত নেই'));block.append(title);
 if(a.parts.length){
  const flow=el('div','arabic-flow');flow.lang='ar';flow.dir='rtl';
  // Fatiha's first printed row keeps its black instructional band; the row view's baseline raise is not needed here.
  if(a.parts.some(p=>p.doc.source.pdf_page_number===1&&p.row.row_index===0))flow.classList.add('fatiha-opening-band');
  for(const p of a.parts)appendSegment(flow,p.doc,p.row,p.index,p.seg,p.marks,block);
  block.append(flow);
 }
 if(a.bengali.length){const p=el('p','translation');p.append(el('span','ref',a.bengali.find(s=>s.numeral_bn)?.numeral_bn||bn(a.n)),document.createTextNode(a.bengali.map(s=>s.text.trim()).join(' ')));block.append(p)}
 const gaps=[];
 if(a.n>1&&!(prev?.n===a.n-1&&ended(prev)))gaps.push('শুরুর অংশ আগের অনুপস্থিত পৃষ্ঠায় থাকতে পারে');
 if(!ended(a))gaps.push('আয়াত-চিহ্ন পর্যন্ত বাকি অংশ এখনো রূপান্তর হয়নি');
 if(gaps.length){block.classList.add('ayah-incomplete');block.append(el('p','ayah-status',`অসম্পূর্ণ আয়াত: ${gaps.join('; ')}।`))}
 const items=[...a.marks,...a.unplaced];if(items.length)markEvidence(items,block,a.unplaced.length);
 return block;
}
function renderAyahs(docs){
 activeDoc=null;activeDocs=docs;anchorUpdates.length=0;const container=$('content');container.replaceChildren(symbolGuide());
 const first=docs.find(doc=>doc.originalCandidate.rows.some(r=>r.arabic_segments.some(s=>s.ayah_ref===`${surah}:1`)))?.originalCandidate;
 if(first){renderSourceHeader(first,container);renderBasmala(first,container)}
 const ayahs=collectAyahs(docs);let next=1;
 for(const [i,a] of ayahs.entries()){if(a.n>next)container.append(ayahGap(next,a.n-1));container.append(ayahSection(a,ayahs[i-1]));next=a.n+1}
 const total=bnNumber(first?.surah_header?.ayah_count_bn);if(total>=next)container.append(ayahGap(next,total));
 const box=el('section','page-issues');box.append(el('h3','','এই সূরার পূর্ণ যাচাই শেষ হয়নি।'));const list=el('ul');list.append(el('li','','আয়াতের ভাগ মূলের আয়াত-উল্লেখ ও আয়াত-চিহ্ন থেকে নেওয়া; আয়াতভিত্তিক বিন্যাস মূলের সারি-বিন্যাস নয়।'),el('li','','কারিয়ানা চিহ্নের অক্ষরভিত্তিক অবস্থানের পূর্ণ যাচাই বাকি।'),el('li','','চেনা বিশেষ চিহ্ন এখন মূল থেকে তৈরি ফন্টে আছে; প্রতিটি ব্যবহারের হুবহু আকৃতি ও মূল পাঠের ফন্ট এখনো পুরোপুরি যাচাইকৃত নয়।'));
 for(const doc of docs){const p=doc.source.pdf_page_number;if(manifest.pages[p-1]?.status==='partial_draft')list.append(el('li','',`পৃষ্ঠা ${bn(p)}-এর মাত্র ${bn(doc.originalCandidate.rows.length)}টি সারি সংরক্ষিত; বাকি অংশ অনুপস্থিত।`));for(const u of (doc.originalCandidate.unresolved||[]).filter(u=>u.status!=='resolved'))list.append(el('li','',`পৃষ্ঠা ${bn(p)}: ${u.question||u.description||u.id}`))}
 box.append(list);container.append(box);
 const furniture=el('details','furniture-pages');furniture.append(el('summary','','মূলের শিরোনাম ও প্রান্তলেখা · পৃষ্ঠাভিত্তিক খসড়া'));
 for(const doc of docs){const before=furniture.childElementCount;renderFurniture(doc.originalCandidate,furniture,doc);if(furniture.childElementCount>before)furniture.lastElementChild.prepend(el('p','furniture-page',`মূল PDF পৃষ্ঠা ${bn(doc.source.pdf_page_number)}`))}
 if(furniture.childElementCount>1)container.append(furniture);
 scheduleAnchors();
}
let anchorFrame;function scheduleAnchors(){cancelAnimationFrame(anchorFrame);anchorFrame=requestAnimationFrame(()=>{for(const fn of anchorUpdates)try{fn()}catch(err){console.warn('Anchor withheld:',err.message)};withholdCollisions()})}
// Source glyph advance boxes include empty side bearings. For the opening
// row's two catalogue symbols, compare actual horizontal ink without moving them.
const markMeasure=document.createElement('canvas').getContext('2d');
function markCollisionBox(mark){
 const rect=mark.getBoundingClientRect();
 if(!markMeasure||!mark.matches(':is(.fatiha-opening-row,.fatiha-opening-band) .mark.source-symbol:not(.opening-mark)'))return rect;
 const style=getComputedStyle(mark);markMeasure.font=`${style.fontSize} ${style.fontFamily}`;markMeasure.textAlign='left';markMeasure.direction='ltr';
 const ink=markMeasure.measureText(mark.textContent);
 if(!Number.isFinite(ink.actualBoundingBoxLeft)||!Number.isFinite(ink.actualBoundingBoxRight)||ink.width<=0)return rect;
 const origin=rect.left+(rect.width-ink.width)/2;
 return {left:Math.max(rect.left,origin-ink.actualBoundingBoxLeft),right:Math.min(rect.right,origin+ink.actualBoundingBoxRight),top:rect.top,bottom:rect.bottom};
}
function withholdCollisions(){
 for(const row of document.querySelectorAll('.text-row')){
  const marks=[...row.querySelectorAll('.mark')];marks.forEach(m=>{m.style.visibility='visible';delete m.dataset.withheld});const blocked=new Set();
  for(let i=0;i<marks.length;i++){const a=markCollisionBox(marks[i]);for(let j=i+1;j<marks.length;j++){const b=markCollisionBox(marks[j]);if(a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top){blocked.add(marks[i]);blocked.add(marks[j])}}}
  blocked.forEach(m=>{m.style.visibility='hidden';m.dataset.withheld='collision'});
  let note=row.querySelector('.collision-note');if(blocked.size){if(!note){note=el('p','collision-note');row.querySelector('.row-evidence').before(note)}note.textContent=`${bn(blocked.size)}টি চিহ্ন কাছাকাছি পড়ে অস্পষ্ট হচ্ছিল। অনুমান করে স্থান বদলানো হয়নি; নিচের তালিকায় পাঠ ও তথ্য দেখুন।`;note.hidden=false;row.querySelector('.row-evidence').open=true}else if(note)note.hidden=true;
 }
}
function renderSourceHeader(d,container){
 const header=d.surah_header;if(!header)return;
 const section=el('section','source-opening');section.setAttribute('aria-label','মূলের সূরা শিরোনাম · খসড়া');
 const ar=el('p','header-ar',header.arabic);ar.lang='ar';ar.dir='rtl';
 section.append(ar,el('h2','',header.bengali));
 const meta=el('div','source-opening-meta');
 meta.append(el('span','',`সূরা নং-${header.surah_number_bn} ${header.revelation_bn}`),el('span','',`রুকু-${header.ruku_bn} আয়াত-${header.ayah_count_bn}`));
 section.append(meta);container.append(section);
}
function renderFurniture(d,container,doc){
 const items=d.page_furniture||[];if(!items.length)return;
 const section=el('section','source-furniture');section.append(el('h3','','মূলের শিরোনাম ও প্রান্তলেখা · খসড়া'),el('p','furniture-note','সংরক্ষিত পাঠ নিচে আছে। অলংকৃত অক্ষর, চিহ্ন ও মূলের বিন্যাসের চূড়ান্ত যাচাই বাকি।'));

 for(const item of items){if(item.symbol){const symbol=el('p','furniture-symbol',item.symbol);symbol.lang='ar';symbol.dir='rtl';section.append(symbol)}if(item.observed_components_top_to_bottom){const components=el('p','furniture-components','নথিভুক্ত ওপর থেকে নিচের অংশ: ');const shapes={'vertical stroke':'[উল্লম্ব রেখা: আকৃতির বর্ণনা]','horizontal rule':'[অনুভূমিক রেখা: আকৃতির বর্ণনা]'};components.append(document.createTextNode(item.observed_components_top_to_bottom.map(t=>shapes[t]||t).join(' · ')));section.append(components)}if(item.text){const p=el('p','furniture-text',item.text);if(item.language==='ar'){p.lang='ar';p.dir='rtl'}section.append(p)}else if(item.kind!=='footer_legend'){section.append(el('p','furniture-unresolved','প্রান্তলেখার পাঠ অমীমাংসিত। সম্ভাব্য পাঠকে নিশ্চিত পাঠ হিসেবে দেখানো হয়নি।'))}
  if(item.entries){const list=el('ul');for(const e of item.entries){const li=el('li');const g=!e.printed&&['inverted_v','wedge'].includes(e.shape_kind)&&e.enclosure==='oval'?symbolCatalog.symbols.find(g=>g.id==='ringed-wedge'):null;li.append(symbolNode(g?{display:{symbolId:g.id,character:g.text}}:null,e,'detail-symbol'),document.createTextNode(' — '+e.text));list.append(li)}section.append(list)}
 }
 container.append(section);
}
async function loadPage(p,keep){let doc=cache.get(p);if(!doc){doc=await json(manifest.pages[p-1].file);cache.set(p,doc)}while(cache.size>Math.max(3,keep))cache.delete(cache.keys().next().value);await loadOpening(doc);return doc}
async function loadRoute(){const req=++requestId,r=route();surah=Number.isInteger(r.surah)&&r.surah>=1&&r.surah<=114?r.surah:1;const s=manifest.surahs[surah-1];pageNo=s.pages.includes(r.page)?r.page:(s.pages[0]||0);view=r.view;directory();$('current-name').textContent=s.nameBn;$('surah-number').textContent='সূরা '+bn(surah);$('surah-title').textContent=s.nameBn;$('surah-arabic').textContent=s.nameAr;$('surah-caption').textContent=s.pages.length?`${bn(s.pages.length)}টি উৎস-পৃষ্ঠায় সংরক্ষিত খসড়া · সম্পূর্ণ সূরা যাচাই হয়নি`:'মূল PDF থেকে এই সূরার পাঠ রূপান্তর বাকি';activeDoc=null;activeDocs=null;controls(s,null);
 if(!s.pages.length){$('content').replaceChildren();const b=el('div','empty');b.append(el('strong','','এই সূরার পাঠ এখনো প্রস্তুত হয়নি।'),document.createTextNode('মূল PDF থেকে আরবি, বাংলা ও সব চিহ্ন উদ্ধার ও যাচাই বাকি। এখানে অনুমান বা অন্য সংস্করণের পাঠ বসানো হয়নি।'));$('content').append(b);return}
 $('content').replaceChildren(el('p','empty','সংরক্ষিত পাঠ লোড হচ্ছে…'));try{if(view==='ayah'){const docs=await Promise.all(s.pages.map(p=>loadPage(p,s.pages.length)));if(req!==requestId)return;renderAyahs(docs);controls(s,docs[0])}else{const doc=await loadPage(pageNo,3);if(req!==requestId)return;render(doc);controls(s,doc)}if(r.ayah)jumpAyah(r.ayah)}catch(err){if(req===requestId){$('content').replaceChildren(el('p','empty error',err.message),Object.assign(el('button','','আবার চেষ্টা করুন'),{onclick:loadRoute}));}}}
function jumpAyah(ref){const target=[...document.querySelectorAll(view==='ayah'?'[data-ayah-section]':'[data-ayah]')].find(e=>(e.dataset.ayahSection||e.dataset.ayah)===ref);document.querySelectorAll('.highlight').forEach(n=>n.classList.remove('highlight'));if(target){target.closest('.text-row').classList.add('highlight');target.scrollIntoView({block:'center',behavior:'instant'});$('ayah-select').value=ref}}
function progress(){const root=$('progress-content');root.replaceChildren();const s=manifest.summary,stats=el('div','stats');for(const [value,label]of [[s.verifiedSurahs+'/114','সম্পূর্ণ যাচাইকৃত সূরা'],[s.fullyVerifiedPages+'/760','সম্পূর্ণ যাচাইকৃত পৃষ্ঠা'],[s.verifiedLetterAnchors+'/'+s.annotations,'যাচাইকৃত অক্ষর-সংযোগ']]){const stat=el('div','stat');stat.append(el('strong','',bn(value)),document.createTextNode(label));stats.append(stat)}root.append(stats,el('p','',`৭টি পৃষ্ঠায় ৫৭টি সারি ও ৪৯৭টি শব্দের খসড়া আছে। পৃষ্ঠা ৬ অসম্পূর্ণ; আরও ৭৫৩টি পৃষ্ঠার প্রতিলিপি নেই। ৭৬০টি পৃষ্ঠার টেক্সট স্তর পরীক্ষা করা হয়েছে—আরবি বা বাংলা পাঠ পাওয়া যায়নি।`));const ul=el('ul');for(const t of ['পৃষ্ঠা ১–২-এর মূল পাঠের পুরোনো স্বাধীন পর্যালোচনা আছে; সেটি এই ওয়েবের ফন্ট বা অক্ষর-সংযোগের অনুমোদন নয়।','পৃষ্ঠা ৩-এর একটি ক্ষতিগ্রস্ত চিহ্ন এবং অলংকৃত শিরোনামসহ অমীমাংসিত অংশ রয়েছে।','পৃষ্ঠা ৪–৭-এর খসড়া ও বইয়ের সম্পূর্ণ ধারাবাহিকতা যাচাই বাকি।','৭৬০টি PDF পৃষ্ঠা মানেই ৭৬০টি স্বতন্ত্র কুরআনের পৃষ্ঠা নয়: পুনরাবৃত্ত স্ক্যান ও পরিশিষ্ট আছে।'])ul.append(el('li','',t));root.append(ul);const scroll=el('div','progress-table'),table=el('table');const head=el('tr');for(const t of ['সূরা','খসড়া আয়াতের উল্লেখ','পূর্ণ যাচাই'])head.append(el('th','',t));table.append(head);for(const sur of manifest.surahs){const tr=el('tr');tr.append(el('td','',`${bn(sur.id)}. ${sur.nameBn}`),el('td','',sur.draftAyahs.length?`${bn(sur.draftAyahs.length)} · আংশিক`:'নেই'),el('td','','বাকি'));table.append(tr)}scroll.append(table);root.append(scroll,el('p','','সূরার তালিকা নেভিগেশন মেটাডেটা; তালিকার নাম PDF-এর শিরোনাম থেকে হুবহু যাচাই করা হয়নি।'));const hash=el('p','','মূল PDF SHA-256: ');hash.append(el('code','',manifest.source.sha256));root.append(hash);$('progress-dialog').showModal()}
$('search').addEventListener('input',()=>manifest&&directory());$('list-toggle').onclick=()=>{const on=$('sidebar').classList.toggle('open');$('list-toggle').setAttribute('aria-expanded',on)};$('progress-open').onclick=()=>manifest&&progress();$('details-open').onclick=()=>manifest&&progress();$('progress-close').onclick=()=>$('progress-dialog').close();$('progress-dialog').onclick=e=>{if(e.target===$('progress-dialog')&&e.offsetX<0)$('progress-dialog').close()};
$('page-select').onchange=e=>{const p=Number(e.target.value);if(view==='ayah'){pageNo=p;document.querySelector(`[data-pages~="${p}"]`)?.scrollIntoView({block:'start',behavior:'instant'})}else navigate(surah,p)};$('ayah-select').onchange=e=>{if(e.target.value){const a=e.target.value;if(view==='ayah'){history.replaceState(null,'','#'+new URLSearchParams({surah,ayah:a,view}));jumpAyah(a);return}const target=manifest.pages[pageNo-1]?.ayahs.includes(a)?pageNo:manifest.pages.find(p=>p.ayahs.includes(a))?.page;navigate(surah,target,a)}};$('previous').onclick=()=>{const p=manifest.surahs[surah-1].pages;navigate(surah,p[p.indexOf(pageNo)-1])};$('next').onclick=()=>{const p=manifest.surahs[surah-1].pages;navigate(surah,p[p.indexOf(pageNo)+1])};
// The selected (highlighted) ayah — the toolbar is above the text, so it may be scrolled away — else the first ayah near the top of the viewport.
function visibleAyah(){const h=document.querySelector('.highlight');if(h){const ayah=h.dataset.ayahSection||(h.querySelector(`[data-ayah="${route().ayah}"]`)?route().ayah:h.querySelector('[data-ayah]')?.dataset.ayah);return {ayah,page:Number(h.dataset.pages?.split(' ')[0])||pageNo}}const top=[...document.querySelectorAll(view==='ayah'?'.ayah-section':'.text-row [data-ayah]')].find(e=>e.getBoundingClientRect().bottom>innerHeight*.2);return top&&{ayah:top.dataset.ayahSection||top.dataset.ayah,page:Number(top.dataset.pages?.split(' ')[0])||pageNo}}
for(const b of document.querySelectorAll('.view-switch button'))b.onclick=()=>{if(b.dataset.view===view||!manifest)return;const at=visibleAyah();view=b.dataset.view;try{localStorage.setItem('quran-view',view)}catch{}navigate(surah,view==='rows'?(at?.page||pageNo):null,at?.ayah||null)};
function font(value){value=Math.max(26,Math.min(56,Number(value)||34));document.documentElement.style.setProperty('--arabic-size',value+'px');$('font-size').value=value;$('font-value').value=bn(value);scheduleAnchors();try{localStorage.setItem('quran-font-size',value)}catch{}}
$('font-size').oninput=e=>font(e.target.value);$('show-marks').onchange=()=>{if(activeDocs)renderAyahs(activeDocs);else if(activeDoc)render(activeDoc);$('anchor-note').hidden=!$('show-marks').checked};window.addEventListener('hashchange',()=>manifest&&loadRoute());new ResizeObserver(scheduleAnchors).observe($('content'));document.fonts.addEventListener('loadingdone',scheduleAnchors);try{font(localStorage.getItem('quran-font-size')||34)}catch{font(34)}
try{[manifest,symbolCatalog]=await Promise.all([json('data/manifest.json'),json('data/symbol-catalog.json')]);let fontReady=false;try{const faces=await document.fonts.load('18px "Qarian Symbols"');fontReady=faces.length>0&&document.fonts.check('18px "Qarian Symbols"')}catch{}configureSymbols(symbolCatalog,fontReady);await loadVerseFrame();await loadRoute()}catch(err){$('content').replaceChildren(el('p','empty error','ডেটা লোড করা যায়নি। পৃষ্ঠাটি আবার লোড করুন।'));console.error(err)}
