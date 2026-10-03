// Ayah view mechanics: regrouping of existing source segments by ayah_ref. Not a source-accuracy approval.
// BASE defaults to the original working copy's preview; set BASE=http://127.0.0.1:4180 for the handoff copy.
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const BASE=process.env.BASE||'http://127.0.0.1:4173';
(async()=>{const root=path.resolve(__dirname,'..'),out=path.join(root,'evidence/ayah-view-2026-10-03'),checks=[],errors=[],requests=[];fs.mkdirSync(out,{recursive:true});
 const b=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true}),p=await b.newPage({viewport:{width:1360,height:950}});
 p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>requests.push(r.url()));
 const check=(name,ok,detail)=>{checks.push({name,passed:!!ok,detail});assert(ok,name+(detail===undefined?'':' '+JSON.stringify(detail)))};
 const settle=()=>p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
 const pages=[1,2,3,4,5,6,7].map(n=>JSON.parse(fs.readFileSync(path.join(root,`dist/data/pages/${String(n).padStart(3,'0')}.json`))));
 // Expected grouping, computed independently from the raw candidate data.
 function expected(surah){const ayahs=new Map();for(const doc of pages)for(const row of doc.originalCandidate.rows){for(const seg of row.arabic_segments){if(!seg.ayah_ref.startsWith(surah+':'))continue;const a=ayahs.get(seg.ayah_ref)||{words:[],bn:[],marks:0};a.words.push(...seg.words.map(w=>w.text));ayahs.set(seg.ayah_ref,a)}for(const seg of row.bengali_segments||[]){if(!seg.ayah_ref?.startsWith(surah+':'))continue;const a=ayahs.get(seg.ayah_ref)||{words:[],bn:[],marks:0};a.bn.push(seg.text.trim());ayahs.set(seg.ayah_ref,a)}}return [...ayahs].sort((x,y)=>Number(x[0].split(':')[1])-Number(y[0].split(':')[1]))}
 const read=()=>p.locator('.ayah-section').evaluateAll(es=>es.map(e=>({ref:e.dataset.ayahSection,words:[...e.querySelectorAll('.word')].map(w=>w.textContent),bn:e.querySelector('.translation')?.childNodes[1]?.textContent||'',incomplete:e.classList.contains('ayah-incomplete')})));
 for(const surah of [1,2]){
  await p.goto(`${BASE}/#surah=${surah}`);await p.waitForSelector('.ayah-section');await p.evaluate(()=>document.fonts.ready);await settle();
  const want=expected(surah),got=await read();
  check(`Surah ${surah}: default view is ayah`,await p.locator('#reader').getAttribute('data-view')==='ayah'&&await p.locator('.page-nav').isHidden());
  check(`Surah ${surah}: one section per source ayah_ref`,JSON.stringify(got.map(g=>g.ref))===JSON.stringify(want.map(w=>w[0])),got.length);
  check(`Surah ${surah}: Arabic codepoints and order unchanged`,want.every(([ref,w],i)=>JSON.stringify(got[i].words)===JSON.stringify(w.words)));
  check(`Surah ${surah}: Bengali segments joined without edits`,want.every(([ref,w],i)=>got[i].bn===w.bn.join(' ')));
 }
 check('All 700 annotation records rendered across both surahs',await (async()=>{let n=0;for(const s of [1,2]){await p.goto(`${BASE}/#surah=${s}&view=ayah`);await p.waitForSelector('.ayah-section');n+=await p.locator('.ayah-section .mark').count()}return n===700})());
 await p.goto(`${BASE}/#surah=2&view=ayah`);await p.waitForSelector('.ayah-section');
 check('Missing ayahs shown as gaps, not filled',JSON.stringify(await p.locator('.ayah-gap').evaluateAll(es=>es.map(e=>e.dataset.missingAyahs)))==='["28-30","37-286"]');
 check('Partial ayahs flagged',JSON.stringify(await p.locator('.ayah-incomplete').evaluateAll(es=>es.map(e=>e.dataset.ayahSection)))==='["2:27","2:31"]');
 check('Cross-page ayah keeps both pages',await p.locator('[data-ayah-section="2:26"]').getAttribute('data-pages')==='5 6');
 check('Three boundary arrows stay on their stop/verse targets',await p.locator('.ayah-section .boundary-target .mark').count()===3);
 check('Partial page identified',(await p.locator('.page-issues').innerText()).includes('পৃষ্ঠা ৬-এর মাত্র ৩টি সারি'));
 await p.selectOption('#ayah-select','2:8');await settle();
 check('Ayah select highlights its section',await p.locator('.highlight[data-ayah-section="2:8"]').count()===1);
 await p.locator('.view-switch [data-view="rows"]').click();await p.waitForSelector('.text-row:not(.ayah-section)');
 const switched=await p.evaluate(()=>({hash:location.hash,highlighted:[...document.querySelectorAll('.highlight [data-ayah]')].map(e=>e.dataset.ayah)}));
 check('Switch to source rows keeps the reader at that ayah',switched.hash.includes('view=rows')&&switched.hash.includes('page=3')&&switched.highlighted.includes('2:8'),switched);
 await p.locator('.view-switch [data-view="ayah"]').click();await p.waitForSelector('.ayah-section');
 check('Switch back to ayah view',await p.locator('.highlight[data-ayah-section="2:8"]').count()===1);
 await p.goto(`${BASE}/#surah=1&view=ayah`);await p.waitForSelector('.ayah-section');await p.evaluate(()=>document.fonts.ready);
 for(const width of [1360,390,320])for(const size of [26,34,56]){await p.setViewportSize({width,height:950});await p.locator('#font-size').fill(String(size));await p.locator('#font-size').dispatchEvent('input');await settle();
  check(`Fatiha first two ayahs: ten source signs visible ${width}/${size}`,await p.locator('.fatiha-opening-band .mark').evaluateAll(es=>es.length===10&&es.every(e=>getComputedStyle(e).visibility==='visible'&&getComputedStyle(e).color==='rgb(21, 21, 21)')));
  check(`No horizontal overflow ${width}/${size}`,await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth))}
 await p.setViewportSize({width:390,height:844});await p.locator('#font-size').fill('34');await p.locator('#font-size').dispatchEvent('input');await settle();
 await p.locator('[data-ayah-section="1:4"]').screenshot({path:path.join(out,'fatiha-ayah4-mobile.png')});
 await p.goto(`${BASE}/#surah=2&view=ayah&ayah=2:26`);await p.waitForSelector('.ayah-section');await settle();await p.locator('[data-ayah-section="2:26"]').screenshot({path:path.join(out,'cross-page-2-26-mobile.png')});
 await p.locator('[data-missing-ayahs="28-30"]').screenshot({path:path.join(out,'gap-28-30-mobile.png')});
 await p.goto(`${BASE}/#surah=114&view=ayah`);await p.waitForFunction(()=>document.querySelector('#surah-title').textContent==='আন-নাস');
 check('Missing surah never substituted',await p.locator('.word').count()===0&&(await p.locator('#content').innerText()).includes('প্রস্তুত হয়নি'));
 check('No displayed raster/SVG/canvas',await p.locator('#content img,#content svg,#content canvas').count()===0);
 check('No runtime errors',!errors.length,errors);check('No remote requests',requests.every(u=>u.startsWith(BASE+'/')),requests.filter(u=>!u.startsWith(BASE+'/')));
 await b.close();
 fs.writeFileSync(path.join(out,'browser-check.json'),JSON.stringify({status:'pass',base:BASE,scope:'Ayah-view regrouping mechanics only; source text, glyph shapes and letter anchors are not newly verified',checks,errors,hashes:Object.fromEntries(['index.html','app.js','style.css'].map(f=>[f,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'dist',f))).digest('hex')]))},null,2));
 console.log(JSON.stringify({passed:checks.length,errors}));
})().catch(e=>{console.error(e);process.exitCode=1});
