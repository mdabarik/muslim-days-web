const {chromium}=require('playwright');const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
(async()=>{
 const root=path.resolve(__dirname,'..'),out=path.join(root,'evidence/symbol-fix-2026-10-03');
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1200,height:900}});const errors=[],checks=[];page.on('pageerror',e=>errors.push(e.message));
 function check(name,ok,detail){checks.push({name,passed:!!ok,detail});assert(ok,name)}
 let totalCustom=0,emptyFixed=0;
 for(let n=1;n<=7;n++){
  const data=JSON.parse(fs.readFileSync(path.join(root,`dist/data/pages/${String(n).padStart(3,'0')}.json`)));
  await page.goto(`http://127.0.0.1:4173/#surah=${n===1?1:2}&page=${n}`);await page.waitForSelector('.word');await page.evaluate(()=>document.fonts.ready);
  check(`page${n}: no question-mark placeholders`,await page.locator('.mark,.detail-symbol').evaluateAll(nodes=>nodes.every(n=>!n.textContent.includes('?'))));
  check(`page${n}: complete annotation detail inventory`,await page.locator('.row-evidence li').count()===data.annotations.length);
  const customs=data.annotations.filter(a=>a.display?.symbolId);totalCustom+=customs.length;emptyFixed+=customs.filter(a=>a.text===null).length;
  check(`page${n}: all reviewed source glyphs displayed`,await page.locator('.row-evidence .source-symbol').count()===customs.length);
  check(`page${n}: custom font ready`,await page.evaluate(()=>document.fonts.check('16px "Qarian Symbols"','\ue000\ue002\ue003')));
  const expected=data.originalCandidate.rows.flatMap(r=>r.arabic_segments.flatMap(s=>s.words.map(w=>w.text)));
  check(`page${n}: Arabic Unicode unchanged`,JSON.stringify(await page.locator('.word').allTextContents())===JSON.stringify(expected));
  check(`page${n}: glyph is text, not image`,await page.locator('#content img,#content canvas,#content svg,#content object,#content iframe').count()===0);
  for(const a of customs){const e=page.locator(`[data-annotation-detail="${a.sourceId}"] .source-symbol`);check(`page${n}/${a.sourceId}: exact PUA contract`,await e.textContent()===a.display.character)}
  for(const width of [1200,390,320])for(const size of [26,34,56]){
   await page.setViewportSize({width,height:900});await page.locator('#font-size').fill(String(size));await page.locator('#font-size').dispatchEvent('input');await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   check(`page${n} ${width}/${size}: no overflow`,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   check(`page${n} ${width}/${size}: intrinsic ring not doubled`,await page.locator('.mark[data-symbol-id="ringed-wedge"]').evaluateAll(ns=>ns.every(n=>getComputedStyle(n).borderTopWidth==='0px')));
  }
 }
 check('55 original empty marks now rendered',emptyFixed===55,emptyFixed);check('97 custom symbol occurrences',totalCustom===97,totalCustom);
 for(const [n,id,target] of [[3,'r4-a15','r4-marker8'],[6,'r1-a16','r1-stop-mim'],[7,'r10-a2','p7:r10:s0:stop']]){
  await page.goto(`http://127.0.0.1:4173/#surah=2&page=${n}`);await page.waitForSelector('.word');
  check(`page${n}: arrow on source boundary`,await page.locator(`[data-source-target="${target}"] [data-annotation="${id}"][data-symbol-id="solid-down-arrow"]`).count()===1);
 }
 await page.goto('http://127.0.0.1:4173/#surah=2&page=3');await page.waitForSelector('.word');
 check('Damaged mark not falsely displayed as শ',(await page.locator('[data-annotation-detail="r0-a8"] .detail-symbol').textContent())==='অস্পষ্ট');
 await page.locator('.symbol-guide').evaluate(e=>e.open=true);
 check('PUA glyph native selection',await page.locator('.guide-symbol').first().evaluate(e=>{const r=document.createRange();r.selectNodeContents(e);const s=getSelection();s.removeAllRanges();s.addRange(r);const selected=s.toString();s.removeAllRanges();return selected===e.textContent&&selected.codePointAt(0)===0xe000}));
 await page.setViewportSize({width:1200,height:1000});await page.locator('#font-size').fill('34');await page.locator('#font-size').dispatchEvent('input');await page.screenshot({path:path.join(out,'desktop-symbols.png'),fullPage:false});
 await page.setViewportSize({width:390,height:900});await page.locator('#font-size').blur();await page.screenshot({path:path.join(out,'mobile-symbols.png'),fullPage:false});
 await page.locator('.text-row').first().scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'mobile-row-symbols.png'),fullPage:false});
 check('No runtime errors',errors.length===0,errors);
 const hashes=Object.fromEntries(['app.js','symbols.js','style.css','data/symbol-catalog.json','fonts/QarianSymbols.woff2'].map(p=>[p,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'dist',p))).digest('hex')]));
 fs.writeFileSync(path.join(out,'browser-check.json'),JSON.stringify({status:'pass',scope:'Symbol display/selection/navigation mechanics only, not exact source letter anchors or full Quran fidelity',checks,errors,hashes,totals:{totalCustom,emptyFixed}},null,2));await browser.close();console.log(JSON.stringify({status:'pass',checks:checks.length,totalCustom,emptyFixed}));
})().catch(e=>{console.error(e);process.exitCode=1});
