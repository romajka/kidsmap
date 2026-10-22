/* LOCAL real-browser checks. Requires isolated synthetic fixture; never contacts live endpoints. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'/home/ramin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const base=process.env.PHONE_QA_BASE||'http://127.0.0.1:8796';
assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);
const fixture=JSON.parse(fs.readFileSync(process.env.PHONE_QA_FIXTURE||'.tmp/phone-whatsapp-20261022/public-fixture.json'));
assert.equal(fixture.synthetic,true);assert.equal(fixture.database,'phone_whatsapp_20261022');
const out=process.env.PHONE_QA_OUTPUT||'.tmp/phone-whatsapp-20261022/browser-public';fs.mkdirSync(out,{recursive:true});
const matrixFilter=process.env.PHONE_QA_FILTER||'';
const matrixPattern=process.env.PHONE_QA_FILTER_REGEX?new RegExp(process.env.PHONE_QA_FILTER_REGEX):null;
const report={origin:base,synthetic:true,matrix:[],failures:[],externalBlocked:[],mapProvider:'NOT RUN (external requests blocked)'};
let browser;
(async()=>{
 browser=await chromium.launch({executablePath:'/opt/google/chrome/chrome',args:['--no-sandbox']});
 for(const lang of ['az','ru','en'])for(const width of [375,390,768,1024,1280,1440])for(const mode of ['separate','none','whatsapp_only']){
  const name=`${lang}-${width}-${mode}`;if(matrixPattern?!matrixPattern.test(name):(matrixFilter&&!name.includes(matrixFilter)))continue;const c=await browser.newContext({viewport:{width,height:1000},permissions:['clipboard-read','clipboard-write'],reducedMotion:'reduce'}),p=await c.newPage();
  const errors=[],requests=[],httpErrors=[];
  await c.route('**/*',route=>{const u=new URL(route.request().url());if(u.origin===base||['data:','blob:'].includes(u.protocol))return route.continue();report.externalBlocked.push(u.origin);return route.abort('blockedbyclient')});
  p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(new URL(r.url()).origin===base&&r.status()>=400)httpErrors.push({path:new URL(r.url()).pathname,status:r.status()})});p.on('request',r=>{if(r.method()==='POST')requests.push({url:r.url(),csrf:!!r.headers()['x-csrftoken']})});
  try{
   const item=fixture.places[mode],pageUrl=new URL(item.path,base);pageUrl.pathname=pageUrl.pathname.replace(/^\/(az|ru|en)\//,`/${lang}/`);
   if(!/^\/(az|ru|en)\//.test(pageUrl.pathname))pageUrl.pathname=`/${lang}${pageUrl.pathname}`;
   const r=await p.goto(pageUrl.href);assert.equal(r.status(),200);await p.waitForTimeout(100);
   const initial=await p.content();for(const digits of ['994504274393','13104564918','905321234567','995555123456'])assert.ok(!initial.includes(digits),'initial HTML contact privacy');
   assert.equal(await p.locator('.detail-wrap a[href^="tel:"],.detail-wrap a[href^="https://wa.me/"]:not([href*="?"])').count(),0,'no exposed href before reveal');
   const call=p.locator('[data-phone-reveal]:not([data-phone-whatsapp])').first(),wa=p.locator('[data-phone-whatsapp="1"]').first();
   if(mode==='whatsapp_only'){assert.equal(await p.locator('[data-phone-reveal]:not([data-phone-whatsapp])').count(),0);await wa.click();}
   else await call.click();
   await p.waitForFunction(()=>document.querySelector('.detail-wrap a[href^="tel:"],.detail-wrap a[href^="https://wa.me/"]:not([href*="?"])'));
   const callHrefs=await p.locator('.detail-wrap a[href^="tel:"]').evaluateAll(es=>[...new Set(es.map(e=>e.getAttribute('href')))]);
   const waHrefs=await p.locator('.detail-wrap a[href^="https://wa.me/"]:not([href*="?"])').evaluateAll(es=>[...new Set(es.map(e=>e.getAttribute('href')))]);
   if(mode==='separate'){
    assert.ok(callHrefs.includes('tel:+994504274393'));assert.ok(callHrefs.includes('tel:+995555123456'));assert.deepEqual(waHrefs,['https://wa.me/13104564918']);
    const copy=p.locator('.km-phone-copy-btn[data-copy="+994504274393"]').first();await copy.click();assert.equal(await p.evaluate(()=>navigator.clipboard.readText()),'+994504274393');
   }else if(mode==='none'){assert.deepEqual(callHrefs,['tel:+905321234567']);assert.deepEqual(waHrefs,[]);assert.equal(await p.locator('[data-phone-whatsapp]').count(),0)}
   else {assert.deepEqual(callHrefs,[]);assert.deepEqual(waHrefs,['https://wa.me/13104564918'])}
   assert.equal(requests.length,1,'all CTA instances share one protected request');assert.ok(requests[0].csrf);assert.ok(requests[0].url.includes(`/api/places/${item.id}/phones/`));
   if(width===375){const mobile=p.locator('.detail-mobile-bar');assert.ok(await mobile.isVisible());if(mode!=='separate'){const sizing=await mobile.evaluate(e=>({bar:e.clientWidth,cta:e.firstElementChild.getBoundingClientRect().width,padding:parseFloat(getComputedStyle(e).paddingLeft)+parseFloat(getComputedStyle(e).paddingRight)}));assert.ok(sizing.cta>=sizing.bar-sizing.padding-2,'single contact fills mobilebar')}assert.ok(await mobile.locator(mode==='none'?'a[href^="tel:"]':'a[href^="https://wa.me/"]:not([href*="?"])').count()>0)}
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'no horizontal overflow');assert.deepEqual(errors,[]);assert.deepEqual(httpErrors,[]);
   if(lang==='ru'&&(width===375||width===1440))await p.screenshot({path:path.join(out,name+'.png'),fullPage:false});
   report.matrix.push({name,status:'PASS',callHrefs,waHrefs,protectedRequests:requests.length});
  }catch(e){console.error(name,e.message);report.failures.push({name,message:e.message,errors,httpErrors});report.matrix.push({name,status:'FAIL'});await p.screenshot({path:path.join(out,name+'-failure.png'),fullPage:false}).catch(()=>{})}
  await c.close();
 }
 // Exercise actual catalog CTA and the map consumer factory without pretending
 // a blocked external map provider was rendered.
 for(const width of [375,1440]){
  const c=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'}),p=await c.newPage();
  await c.route('**/*',route=>new URL(route.request().url()).origin===base?route.continue():route.abort('blockedbyclient'));
  const name=`catalog-map-whatsapp-only-${width}`;
  try{
   const item=fixture.places.whatsapp_only,r=await p.goto(`${base}/ru/catalog/`);assert.equal(r.status(),200);
   const card=p.locator(`article[data-place-id="${item.id}"]`).first();
   assert.ok(await card.count());const btn=card.locator('[data-phone-reveal]').first();await btn.click();
   const link=card.locator('a[href="https://wa.me/13104564918"]');await link.waitFor();assert.ok(await link.count());
   const payload=await p.locator('#catalog-map-data').textContent(),data=JSON.parse(payload);
   const flatten=data.flatMap(point=>point.members||[point]);const member=flatten.find(x=>x.id===item.id);assert.ok(member);assert.equal(member.has_phone,false);assert.equal(member.has_whatsapp,true);assert.ok(!payload.includes('13104564918'));
   await p.evaluate(id=>{const node=document.createElement('div');node.id='qa-map-contact';node.innerHTML=window.kidsMapPhoneButton(id,'catalog-map-card-action is-secondary',true);document.querySelector('main').append(node)},item.id);
   await p.locator('#qa-map-contact button').click();assert.equal(await p.locator('#qa-map-contact a').getAttribute('href'),'https://wa.me/13104564918');
   report.matrix.push({name,status:'PASS',map:'real payload and CTA factory; provider NOT RUN'});
  }catch(e){report.matrix.push({name,status:'FAIL'});report.failures.push({name,message:e.message});await p.screenshot({path:path.join(out,name+'-failure.png'),fullPage:false}).catch(()=>{})}
  await c.close();
 }
 report.externalBlocked=[...new Set(report.externalBlocked)];report.summary={total:report.matrix.length,passed:report.matrix.filter(x=>x.status==='PASS').length,failed:report.failures.length};fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report.summary));if(report.failures.length){console.log(JSON.stringify(report.failures));process.exitCode=1}
})().catch(e=>{console.error(e);process.exitCode=1}).finally(async()=>{if(browser)await browser.close()});
