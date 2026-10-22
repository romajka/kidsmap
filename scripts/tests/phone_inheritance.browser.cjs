/* LOCAL synthetic confirmed organization with WhatsApp only. No writes. */
const fs=require('node:fs'),assert=require('node:assert/strict');
const {chromium}=require('/home/ramin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const qa='.tmp/phone-whatsapp-20261022',base='http://127.0.0.1:8796';
const fixture=JSON.parse(fs.readFileSync(`${qa}/inheritance-fixture.json`)),auth=JSON.parse(fs.readFileSync(`${qa}/forms-auth.json`));
assert.equal(fixture.synthetic,true);assert.equal(fixture.database,'phone_whatsapp_20261022');assert.ok(fixture.placeId>4);
const result={synthetic:true,placeId:fixture.placeId,checks:[],errors:[],writesBlocked:0};let browser;
(async()=>{
 browser=await chromium.launch({executablePath:'/opt/google/chrome/chrome',args:['--no-sandbox']});
 const c=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});await c.addCookies([{name:auth.cookieName,value:auth.session,url:base}]);
 await c.route('**/*',route=>{const r=route.request();if(!['GET','HEAD'].includes(r.method())){result.writesBlocked++;return route.abort('blockedbyclient')}return new URL(r.url()).origin===base?route.continue():route.abort('blockedbyclient')});
 const p=await c.newPage();p.on('pageerror',e=>result.errors.push(e.message));
 await p.goto(`${base}/ru/account/places/${fixture.placeId}/edit/?candidate_current=1`);await p.locator('[data-pc-nav-link="2"]').click();
 const contact=JSON.parse(await p.locator('#pc-readiness').textContent()).items.find(x=>x.code==='phone');
 assert.deepEqual(contact.config.inherited_by_mode,{legacy:true,same:false,separate:false,none:false});
 const mode=p.locator('[name=whatsapp_mode]'),badge=p.locator('[data-pw-required=phone1]'),hint=p.locator('[data-pc-contact-hint]');
 assert.equal(await mode.inputValue(),'legacy');assert.equal(await badge.isVisible(),false);const inheritedHint=await hint.innerText();
 for(const selected of ['none','same','separate']){await mode.selectOption(selected);assert.equal(await badge.isVisible(),true);assert.notEqual(await hint.innerText(),inheritedHint);assert.notEqual(await p.locator('[data-pc-step-badge="2"]').getAttribute('data-status'),'complete');}
 await mode.selectOption('legacy');assert.equal(await badge.isVisible(),false);assert.equal(await hint.innerText(),inheritedHint);
 result.checks.push('Owner disabling/changing inherited WhatsApp immediately restores contact requirement and clears completed section');
 await p.goto(`${base}/ru/admin/catalog/place/${fixture.placeId}/change/`);await p.locator('#id_whatsapp_mode').waitFor();
 const config=JSON.parse(await p.locator('#km-place-progress-config').textContent()).find(x=>x.code==='phone');assert.deepEqual(config.config.inherited_by_mode,{legacy:true,same:false,separate:false,none:false});
 const done=p.locator('[data-progress-done]').first(),initial=Number(await done.innerText());assert.ok(initial>0);
 for(const selected of ['none','same','separate']){await p.locator('#id_whatsapp_mode').selectOption(selected);assert.equal(Number(await done.innerText()),initial-1);}
 await p.locator('#id_whatsapp_number').fill('+1 310 456 4918');assert.equal(Number(await done.innerText()),initial);
 await p.locator('#id_whatsapp_mode').selectOption('none');assert.equal(Number(await done.innerText()),initial-1);
 await p.locator('#id_whatsapp_mode').selectOption('legacy');assert.equal(Number(await done.innerText()),initial);
 result.checks.push('Admin readiness follows selected mode and ignores hidden stale separate number');
 assert.deepEqual(result.errors,[]);await c.close();
})().catch(e=>{result.failure=e.stack;process.exitCode=1}).finally(async()=>{if(browser)await browser.close();fs.writeFileSync(`${qa}/browser-inheritance.json`,JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));});
