/* LOCAL-only rendered contact-policy acceptance; requires isolated synthetic fixture JSON.
   Changes only own synthetic drafts; approval is a separate guarded QA helper. Never run on production. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'/home/ramin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const base=process.env.CONTACT_POLICY_BASE||'http://127.0.0.1:8794';assert.match(base,/^http:\/\/127\.0\.0\.1:\d+$/);
const fixture=JSON.parse(fs.readFileSync(process.env.CONTACT_POLICY_FIXTURE||'.tmp/place-contact-policy-browser-20261022/auth.json'));
const out=process.env.CONTACT_POLICY_OUTPUT||'.tmp/place-contact-policy-browser-20261022/evidence';fs.mkdirSync(out,{recursive:true});
const result={origin:base,fixtures:'synthetic-only',matrix:[],flows:[],failures:[],blockedExternal:[]};let browser;
async function contextFor(role,width=1440){const c=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});if(role)await c.addCookies([{name:'kidsmap_admin_nav_preview_session',value:fixture.cookies[role],url:base}]);await c.route('**/*',route=>{const u=new URL(route.request().url());if(u.origin===base||['data:','blob:'].includes(u.protocol))return route.continue();result.blockedExternal.push(u.origin);return route.abort('blockedbyclient')});return c;}
async function goStep(p,n){const select=p.locator('[data-pc-section-select]');if(await select.isVisible())await select.selectOption(`pc-section-${n}`);else await p.locator(`[data-pc-nav-link="${n}"]`).click();await p.waitForTimeout(80);}
async function taxonomy(p,category,subcategory){await goStep(p,1);const cat=p.locator('[data-permanent-place-form] [name="category"]');if(await cat.isVisible())await cat.selectOption(String(category));else await p.locator(`[data-pw-category="${category}"]`).click();const sub=p.locator('[data-permanent-place-form] [name="subcategory"]');if(await sub.isVisible())await sub.selectOption(String(subcategory));else{await p.locator('.pw-subcategory-trigger').click();await p.locator(`.pw-subcategory-item[data-value="${subcategory}"]`).click();}await p.waitForTimeout(80);}
async function showField(p,name){const f=p.locator(`[data-permanent-place-form] [name="${name}"]`);if(!await f.isVisible()){const detail=f.locator('xpath=ancestor::details[1]');if(await detail.count())await detail.locator(':scope > summary').click();}return f;}
async function state(p){return p.evaluate(()=>({width:innerWidth,docWidth:document.documentElement.scrollWidth,nature:document.querySelectorAll('[data-permanent-place-form] [name="nature"]').length,phoneRequired:document.querySelector('[data-pw-required="phone1"]')?.hidden===false,hints:[...document.querySelectorAll('[data-contact-policy-hint],[data-pc-contact-hint],[data-pw-contact-hint]')].map(e=>e.textContent.trim()),sectionContactTag:document.querySelector('[data-pc-section-tag="2"]')?.dataset.tag}));}
async function run(name,fn){if(process.env.CONTACT_POLICY_FLOW_FILTER&&!name.includes(process.env.CONTACT_POLICY_FLOW_FILTER))return;try{await fn();result.flows.push({name,status:'PASS'})}catch(e){result.flows.push({name,status:'FAIL',message:e.message});result.failures.push({name,message:e.message})}}
async function nativeSubmit(p){await p.locator('[data-permanent-place-form]').evaluate(form=>{let input=document.createElement('input');input.type='hidden';input.name='form_action';input.value='save_and_publish';form.append(input);HTMLFormElement.prototype.submit.call(form)});await p.waitForLoadState('domcontentloaded');}
(async()=>{
 browser=await chromium.launch({executablePath:'/opt/google/chrome/chrome',args:['--no-sandbox']});
 if(!process.env.CONTACT_POLICY_SKIP_MATRIX)for(const lang of ['az','ru','en'])for(const width of [320,360,390,768,1024,1280,1440]){
  const c=await contextFor('owner',width),p=await c.newPage();const errors=[],http=[];p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error'&&!m.text().includes('ERR_BLOCKED_BY_CLIENT'))errors.push(m.text())});p.on('response',r=>{if(new URL(r.url()).origin===base&&r.status()>=400)http.push({path:new URL(r.url()).pathname,status:r.status()})});
  const name=`${lang}-${width}`;try{
   const r=await p.goto(`${base}/${lang}/account/places/${fixture.matrixPlaces[name]}/edit/?candidate_current=1`);assert.equal(r.status(),200);await p.waitForTimeout(150);
   const initial=await state(p);assert.equal(initial.nature,0,'nature choice absent');assert.equal(initial.phoneRequired,false,'park contact marker optional');assert.ok(initial.hints.some(Boolean),'localized contact hint present');assert.equal(initial.docWidth,initial.width,'initial overflow');
   await goStep(p,2);await p.locator('[name="phone1"]').fill('+994501112233');await (await showField(p,'website')).fill('https://example.invalid/contact-policy');
   await taxonomy(p,fixture.taxonomy.commercialCategory,fixture.taxonomy.commercialSubcategory);const commercial=await state(p);assert.equal(commercial.phoneRequired,true,'commercial contact required');assert.notDeepEqual(commercial.hints,initial.hints,'hint changes with taxonomy');
   assert.equal(await p.locator('[name="phone1"]').inputValue(),'+994501112233');assert.equal(await p.locator('[name="website"]').inputValue(),'https://example.invalid/contact-policy');
   await taxonomy(p,fixture.taxonomy.parkCategory,fixture.taxonomy.playgroundSubcategory);assert.equal((await state(p)).phoneRequired,false,'playground contact optional');
   await goStep(p,2);assert.equal((await state(p)).docWidth,width,'contacts panel overflow');
   if(width===390||width===1440)await p.screenshot({path:path.join(out,`${name}.png`),fullPage:false});
   assert.deepEqual(errors,[]);assert.deepEqual(http,[]);result.matrix.push({name,status:'PASS',initial,commercial,errors,http});
  }catch(e){result.matrix.push({name,status:'FAIL',message:e.message,state:await state(p).catch(()=>null),errors,http});result.failures.push({name,message:e.message});await p.screenshot({path:path.join(out,`${name}-failure.png`),fullPage:false}).catch(()=>{});}await c.close();
 }
 const c=await contextFor('owner'),p=await c.newPage();
 await run('create form no nature and dynamic contact choice',async()=>{for(const lang of ['az','ru','en']){let r=await p.goto(`${base}/${lang}/account/places/create/?type=permanent&fresh=1`);assert.equal(r.status(),200);assert.equal((await state(p)).nature,0);await taxonomy(p,fixture.taxonomy.parkCategory,fixture.taxonomy.parkSubcategory);assert.equal((await state(p)).phoneRequired,false);await taxonomy(p,fixture.taxonomy.commercialCategory,fixture.taxonomy.commercialSubcategory);assert.equal((await state(p)).phoneRequired,true);}});
 await run('pending taxonomy draft keeps centre contact required after reopen',async()=>{
  await p.goto(`${base}/ru/account/places/${fixture.ids.legacyPublic}/edit/?candidate_current=1`);await taxonomy(p,fixture.taxonomy.commercialCategory,fixture.taxonomy.commercialSubcategory);
  assert.equal((await state(p)).phoneRequired,true);await goStep(p,4);
  await Promise.all([p.waitForNavigation(),p.locator('button[name="form_action"][value="save_draft"]').click()]);
  await p.goto(`${base}/ru/account/places/${fixture.ids.legacyPublic}/edit/?candidate_current=1`);
  assert.equal(await p.locator('[data-permanent-place-form] [name="category"]').inputValue(),fixture.taxonomy.commercialCategory);assert.equal((await state(p)).phoneRequired,true);
  await Promise.all([p.waitForNavigation(),nativeSubmit(p)]);assert.ok(await p.locator('[data-pw-field="phone1"] .pw-error').count()>0);result.pendingTaxonomyRejected=true;
 });
 await run('pending unapproved public nature never exempts centre contact',async()=>{
  assert.ok(fixture.ids.pendingNature);await p.goto(`${base}/ru/account/places/${fixture.ids.pendingNature}/edit/?candidate_current=1`);
  const st=await state(p);assert.equal(st.nature,0);assert.equal(st.phoneRequired,true);
  const ready=JSON.parse(await p.locator('#pc-readiness').innerText());assert.equal(ready.items.find(x=>x.code==='phone').complete,false);
  await Promise.all([p.waitForNavigation(),nativeSubmit(p)]);assert.ok(await p.locator('[data-pw-field="phone1"] .pw-error').count()>0);result.pendingNatureRejected=true;
 });
 await run('approved public park changed to centre requires contact',async()=>{
  assert.ok(fixture.ids.legacyPublic);await p.goto(`${base}/ru/account/places/${fixture.ids.legacyPublic}/edit/?candidate_current=1`);
  assert.equal((await state(p)).phoneRequired,false);assert.equal((await state(p)).nature,0);
  await taxonomy(p,fixture.taxonomy.commercialCategory,fixture.taxonomy.commercialSubcategory);assert.equal((await state(p)).phoneRequired,true);
  await Promise.all([p.waitForNavigation(),nativeSubmit(p)]);
  assert.ok(await p.locator('[data-pw-field="phone1"] .pw-error').count()>0);assert.equal((await state(p)).phoneRequired,true);
  result.legacyPublicCentreRejected=true;
 });
 await run('commercial missing contact rejected by server',async()=>{await p.goto(`${base}/ru/account/places/${fixture.ids.commercial}/edit/?candidate_current=1`);await Promise.all([p.waitForNavigation(),nativeSubmit(p)]);assert.ok(new URL(p.url()).pathname.includes(`/places/${fixture.ids.commercial}/edit/`));assert.ok(await p.locator('[data-pw-field="phone1"] .pw-error').count()>0,'server contact error rendered');result.commercialContactError=await p.locator('[data-pw-field="phone1"] .pw-error').allTextContents();});
 await run('commercial website alternative submits without phone',async()=>{await p.goto(`${base}/ru/account/places/${fixture.ids.commercial}/edit/?candidate_current=1`);await goStep(p,2);await (await showField(p,'website')).fill('https://example.invalid/qa-commercial');await goStep(p,4);await Promise.all([p.waitForNavigation(),p.locator('[data-pc-submit]').click()]);assert.equal(new URL(p.url()).pathname,'/ru/account/places/');});
 await run('contactless park submits for moderation',async()=>{await p.goto(`${base}/ru/account/places/${fixture.ids.park}/edit/?candidate_current=1`);const ready=JSON.parse(await p.locator('#pc-readiness').innerText());assert.equal(ready.is_ready,true);assert.equal(ready.completed_count,ready.required_count);await goStep(p,4);await Promise.all([p.waitForNavigation(),p.locator('[data-pc-submit]').click()]);assert.equal(new URL(p.url()).pathname,'/ru/account/places/');});
 await c.close();
 const ac=await contextFor('admin'),ap=await ac.newPage();
 await run('admin stored readiness contactless park parity',async()=>{let r=await ap.goto(`${base}/ru/admin/catalog/place/${fixture.ids.park}/change/`);assert.equal(r.status(),200);const text=await ap.locator('#content').innerText();assert.ok(text.includes('100%'),'admin ready100percent');assert.equal(await ap.locator('[data-pf-publish]').evaluateAll(es=>es.length>0&&es.every(e=>!e.disabled)),true);result.adminReady100=true;await ap.screenshot({path:path.join(out,'admin-park-ready.png'),fullPage:false});});
 if(process.env.CONTACT_POLICY_PUBLIC){await run('approved contactless park appears in public detail and catalog',async()=>{
  const published=JSON.parse(fs.readFileSync('.tmp/place-contact-policy-browser-20261022/publication.json'));assert.equal(published.publicQueryable,true);assert.equal(published.contactFieldsEmpty,true);assert.equal(published.natureUnchanged,true);
  const pc=await contextFor(null),pp=await pc.newPage();let errors=[];pp.on('pageerror',e=>errors.push(e.message));
  let r=await pp.goto(new URL(published.url,base).href);assert.equal(r.status(),200);assert.ok((await pp.locator('main').innerText()).includes('QA'));await pp.screenshot({path:path.join(out,'public-park-detail.png'),fullPage:false});
  r=await pp.goto(`${base}/ru/catalog/?q=${encodeURIComponent('QA əlaqəsiz park')}`);assert.equal(r.status(),200);
  const target=await pp.locator(`a[href*="/place/${published.park}-"],a[href="${published.url}"]`).count();assert.ok(target>0,'approved contactless park has actual catalog card link');assert.deepEqual(errors,[]);
  result.publicCatalogPresence=true;result.publicDetail=true;await pp.screenshot({path:path.join(out,'public-park-catalog.png'),fullPage:false});await pc.close();
 });}
 await ac.close();result.blockedExternal=[...new Set(result.blockedExternal)];result.summary={matrix:result.matrix.length,matrixPassed:result.matrix.filter(x=>x.status==='PASS').length,flows:result.flows.length,flowPassed:result.flows.filter(x=>x.status==='PASS').length,failures:result.failures.length};fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result.summary));if(result.failures.length){console.log(JSON.stringify(result.failures,null,2));process.exitCode=1;}
})().catch(e=>{console.error(e);process.exitCode=1}).finally(async()=>{if(browser)await browser.close()});
