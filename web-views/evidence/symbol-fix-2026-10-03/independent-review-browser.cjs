const {chromium}=require('playwright');
const fs=require('fs'), path=require('path'),crypto=require('crypto');
const base=path.resolve(__dirname,'../../dist');
const hash=rel=>crypto.createHash('sha256').update(fs.readFileSync(path.join(base,rel))).digest('hex');
const assets=['index.html','app.js','symbols.js','anchors.js','style.css','fonts/QarianSymbols.woff2','data/symbol-catalog.json','data/manifest.json',...Array.from({length:7},(_,i)=>`data/pages/${String(i+1).padStart(3,'0')}.json`)];
(async()=>{
 const hashes=Object.fromEntries(assets.map(x=>[x,hash(x)]));
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1360,height:1000}});let errors=[];page.on('pageerror',e=>errors.push(e.message));
 const rows=[];
 for(const n of [1,2,3,4,5,6,7]){
  await page.goto(`http://127.0.0.1:4173/#surah=${n===1?1:2}&page=${n}`);await page.waitForSelector('.text-row');await page.evaluate(()=>document.fonts.ready);
  const p=JSON.parse(fs.readFileSync(path.join(base,`data/pages/${String(n).padStart(3,'0')}.json`)));
  const custom=p.annotations.filter(a=>a.display?.symbolId);
  const actual=await page.evaluate(()=>({questionMarks:[...document.querySelectorAll('.mark,.detail-symbol')].filter(e=>e.textContent==='?').length,fontLoaded:document.fonts.check('18px "Qarian Symbols"'),details:[...document.querySelectorAll('[data-annotation-detail]')].map(e=>({id:e.dataset.annotationDetail,text:e.querySelector('.detail-symbol').textContent})),marks:[...document.querySelectorAll('.mark')].map(e=>({id:e.dataset.annotation,text:e.textContent,symbol:e.dataset.symbolId,border:getComputedStyle(e).borderWidth,font:getComputedStyle(e).fontFamily,visibility:getComputedStyle(e).visibility,rect:e.getBoundingClientRect().toJSON()})),images:document.querySelectorAll('#content img,#content canvas,#content svg,#content iframe').length,overflow:document.documentElement.scrollWidth>innerWidth}));
  const mismatches=custom.filter(a=>!actual.details.some(d=>d.id===a.sourceId&&d.text===a.display.character));
  const selection=await page.locator('.detail-symbol.source-symbol').first().evaluate(e=>{const r=document.createRange();r.selectNodeContents(e);const s=getSelection();s.removeAllRanges();s.addRange(r);return s.toString()===e.textContent});
  rows.push({page:n,totalAnnotations:p.annotations.length,expectedCustom:custom.length,detailCount:actual.details.length,mismatches:mismatches.map(a=>a.id),selection,...actual});
 }
 for(const width of [1360,390,320]){
  await page.setViewportSize({width,height:900});
  await page.goto('http://127.0.0.1:4173/#surah=2&page=3');await page.waitForSelector('[data-annotation="r4-a15"]');
  for(const size of [26,34,56]){await page.locator('#font-size').fill(String(size));await page.locator('#font-size').dispatchEvent('input');await page.waitForTimeout(70);rows.push({width,size,overflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),arrow:await page.locator('[data-annotation="r4-a15"]').evaluate(e=>({text:e.textContent,parentTarget:e.parentElement.dataset.sourceTarget,border:getComputedStyle(e).borderWidth}))});}
 }
 for(const [n,row] of [[1,0],[3,0],[3,4],[6,1],[7,10]]){
  await page.goto(`http://127.0.0.1:4173/#surah=${n===1?1:2}&page=${n}`);await page.waitForSelector(`.text-row[data-row="${row}"]`);
  await page.locator('#font-size').fill('34');await page.locator('#font-size').dispatchEvent('input');
  for(const width of [1360,390]){await page.setViewportSize({width,height:900});await page.waitForTimeout(100);await page.locator(`.text-row[data-row="${row}"]`).screenshot({path:path.join(__dirname,`independent-review-p${n}-r${row}-${width}.png`)});}
 }
 const hashesAfter=Object.fromEntries(assets.map(x=>[x,hash(x)]));
 await browser.close();fs.writeFileSync(path.join(__dirname,'independent-review-browser.json'),JSON.stringify({hashes,hashesAfter,stable:JSON.stringify(hashes)===JSON.stringify(hashesAfter),rows,errors},null,2));
 console.log(JSON.stringify({stable:JSON.stringify(hashes)===JSON.stringify(hashesAfter),pages:7,errors}));
})().catch(e=>{console.error(e);process.exit(1)});
