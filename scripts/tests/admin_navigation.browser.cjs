/* Rendered LOCAL admin navigation acceptance. Run against isolated synthetic fixtures only.
   ADMIN_NAV_FIXTURE must point to ignored JSON {cookies:{admin,limited,volunteer},ids:{...}}.
   Session values never enter outputs. The script creates only synthetic unpublished drafts; it never deletes records or publishes. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/home/ramin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const base = process.env.ADMIN_NAV_BASE || 'http://127.0.0.1:8794';
assert.match(base, /^http:\/\/127\.0\.0\.1:\d+$/,'LOCAL isolated origin required');
const fixturePath = process.env.ADMIN_NAV_FIXTURE || '.tmp/admin-navigation-browser-20261022/auth.json';
const fixture = JSON.parse(fs.readFileSync(fixturePath));
const out = process.env.ADMIN_NAV_OUTPUT || '.tmp/admin-navigation-browser-20261022/evidence';
fs.mkdirSync(out,{recursive:true});
const report = {origin:base, fixture:'synthetic-only', source:'main checkout WORKTREE', matrix:[], flows:[], failures:[], externalRequestsBlocked:[]};
const widths=[320,360,390,768,1024,1280,1440];
let browser;
async function contextFor(role,width=1440) {
 const c=await browser.newContext({viewport:{width,height:1000}, reducedMotion:'reduce'});
 await c.addCookies([{name:'kidsmap_admin_nav_preview_session',value:fixture.cookies[role],url:base}]);
 await c.route('**/*',route=>{let u=new URL(route.request().url());if(u.origin===base||['data:','blob:'].includes(u.protocol))return route.continue();report.externalRequestsBlocked.push(u.origin);return route.abort('blockedbyclient');});
 return c;
}
async function inspect(p){return p.evaluate(()=>({
 overflow:document.documentElement.scrollWidth>innerWidth+1,
 viewport:innerWidth,bodyWidth:document.body.scrollWidth,
 groups:[...document.querySelectorAll('[data-km-sidebar-group]')].map(g=>({key:g.dataset.kmSidebarKey,active:g.classList.contains('is-active'),open:g.dataset.open==='true',label:g.querySelector('[data-km-sidebar-toggle]')?.innerText.trim(),hidden:g.querySelector('[data-km-sidebar-panel]')?.hidden})),
 current:[...document.querySelectorAll('.km-admin-sidebar [aria-current="page"]')].map(a=>({label:a.innerText.trim(),href:a.getAttribute('href')})),
 openerExpanded:document.querySelector('.km-admin-header__toggle[data-widget="pushmenu"]')?.getAttribute('aria-expanded'),
 sidebarOpen:document.body.classList.contains('sidebar-open'),
 brokenIcons:[...document.querySelectorAll('.km-admin-sidebar svg use')].filter(u=>!document.getElementById(u.getAttribute('href')?.slice(1))).length
}));}
async function showField(p,name){const field=p.locator(`[name="${name}"]`);if(!await field.isVisible()){const id=await field.evaluate(e=>e.closest('.tab-pane')?.id);if(id)await p.locator(`[role="tab"][href="#${id}"]`).click();}return field;}
async function record(name,fn){if(process.env.ADMIN_NAV_FLOW_FILTER&&!name.includes(process.env.ADMIN_NAV_FLOW_FILTER))return;try{await fn();report.flows.push({name,status:'PASS'});}catch(e){report.flows.push({name,status:'FAIL',message:e.message});report.failures.push({name,message:e.message});}}
(async()=>{
 let ready=false;for(let attempt=0;attempt<40;attempt++){try{const r=await fetch(base+'/ru/admin/login/');if(r.status===200){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,250));}assert.ok(ready,'isolated server warmup');
 browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/opt/google/chrome/chrome',args:['--no-sandbox']});
 for (const lang of (process.env.ADMIN_NAV_SKIP_MATRIX ? [] : ['az','ru','en'])) for(const width of widths){
  const c=await contextFor('admin',width);const p=await c.newPage();let errors=[],staticFailures=[];
  p.on('pageerror',e=>errors.push(e.message));
  p.on('console',m=>{if(m.type()==='error'&&!m.text().includes('ERR_BLOCKED_BY_CLIENT'))errors.push(m.text());});
  p.on('response',r=>{if(r.status()>=400&&new URL(r.url()).origin===base)staticFailures.push({path:new URL(r.url()).pathname,status:r.status()});});
  const name=`${lang}-${width}`;
  try{
   await p.addInitScript(()=>{for(const key of ['catalog','moderation','dictionaries','users','content','analytics','seo','system','accounts','volunteers','moderation_sla','settings'])localStorage.setItem('km-admin-sidebar:'+key,'1');});
   const response=await p.goto(`${base}/${lang}/admin/catalog/activity/${fixture.ids.activity}/change/`);assert.equal(response.status(),200);
   await p.waitForTimeout(200);let closed=await inspect(p);
   assert.equal(closed.overflow,false,'initial horizontal overflow');assert.equal(closed.brokenIcons,0,'unresolved sidebar symbols');
   assert.ok(closed.groups.some(g=>g.active&&g.open),'active child must open its parent');
   if(width<768){assert.equal(closed.groups.filter(g=>g.open).length,1,'stale desktop state must open exactly current mobile parent');await p.locator('.km-admin-header__toggle[data-widget="pushmenu"]').click();await p.waitForTimeout(350);assert.equal((await inspect(p)).openerExpanded,'true');}
   const toggles=p.locator('[data-km-sidebar-toggle]');const n=await toggles.count();assert.ok(n>=4,'full admin sections');
   await toggles.nth(n-1).click();await p.waitForTimeout(80);
   let opened=await inspect(p);assert.equal(opened.overflow,false,'open menu horizontal overflow');
   if(width<768)assert.ok(opened.groups.filter(g=>g.open).length<=1,'mobile accordion opens at most1section');
   if(width===390||width===1440)await p.screenshot({path:path.join(out,`${name}.png`),fullPage:false});
   if(width<768){await p.keyboard.press('Escape');await p.waitForTimeout(350);assert.equal((await inspect(p)).openerExpanded,'false','Escape closes drawer');assert.ok(await p.locator('.km-admin-header__toggle[data-widget="pushmenu"]').evaluate(e=>e===document.activeElement),'Escape returns opener focus');}
   if(width>=768)assert.ok(closed.groups.filter(g=>g.open).length>1,'desktop preserves multiple stored groups');
   assert.deepEqual(errors,[],'application console/page errors');assert.deepEqual(staticFailures,[],'same-origin errors/static404');
   report.matrix.push({name,status:'PASS',closed,opened,errors,staticFailures});
  }catch(e){report.matrix.push({name,status:'FAIL',message:e.message,observed:await inspect(p).catch(()=>null),errors,staticFailures});report.failures.push({name,message:e.message});await p.screenshot({path:path.join(out,`${name}-failure.png`),fullPage:false}).catch(()=>{});}
  await c.close();
 }
 const c=await contextFor('admin');const p=await c.newPage();
 await record('classical organization/program/activity/group routes retained',async()=>{
  for(const model of ['organization','program','activity','offeringgroup']){let r=await p.goto(`${base}/ru/admin/catalog/${model}/`);assert.equal(r.status(),200,model);}
 });
 await record('five main Catalog destinations resolve',async()=>{
  await p.goto(`${base}/ru/admin/catalog/place/`);
  const links=await p.locator('[data-km-sidebar-key="catalog"] a').evaluateAll(es=>es.map(e=>({label:e.innerText.trim(),href:e.getAttribute('href')})));
  assert.equal(links.length,5);report.catalogDestinations=[];
  for(const link of links){const r=await p.goto(new URL(link.href,base).href);assert.equal(r.status(),200,link.href);report.catalogDestinations.push({...link,status:r.status()});}
 });
 await record('all directory and technical hub links resolve',async()=>{
  let checked=0;
  for(const hub of ['directories','technical']){
   const response=await p.goto(`${base}/ru/admin/navigation/${hub}/`);assert.equal(response.status(),200);
   const links=await p.locator('.km-admin-navigation-hub__link').evaluateAll(es=>es.map(e=>e.getAttribute('href')));assert.ok(links.length>=4);
   for(const href of links){const r=await p.goto(new URL(href,base).href);assert.equal(r.status(),200,href);checked++;}
  }
  report.hubDestinationsChecked=checked;
 });
 await record('place to activity list and preselected activity add',async()=>{
  await p.goto(`${base}/ru/admin/catalog/place/${fixture.ids.place}/change/`);
  const links=await p.locator('.km-admin-related-links a').evaluateAll(es=>es.map(e=>e.getAttribute('href')));
  assert.ok(links.some(u=>u.includes('place__id__exact='+fixture.ids.place)));
  const add=links.find(u=>u.includes('/activity/add/'));assert.ok(add);await p.goto(new URL(add,base).href);
  assert.equal(await p.locator('[name="place"]').inputValue(),String(fixture.ids.place));
 });
 await record('activity to group add and group return path',async()=>{
  await p.goto(`${base}/ru/admin/catalog/activity/${fixture.ids.activity}/change/`);
  const links=await p.locator('.km-business-links-grid a').evaluateAll(es=>es.map(e=>e.getAttribute('href')));
  const add=links.find(u=>u.includes('/offeringgroup/add/'));assert.ok(add);await p.goto(new URL(add,base).href);
  assert.equal(await p.locator('[name="activity"]').inputValue(),String(fixture.ids.activity));
  await p.goto(`${base}/ru/admin/catalog/offeringgroup/${fixture.ids.group}/change/`);
  const returns=await p.locator('.km-business-links-grid a').evaluateAll(es=>es.map(e=>e.getAttribute('href')));
  assert.ok(returns.some(u=>u.includes(`/activity/${fixture.ids.activity}/change/`)));
  assert.ok(returns.some(u=>u.endsWith(`/place/${fixture.ids.place}/change/#pricing`)));
 });
 await record('foreign parent hints rejected and own program selected',async()=>{
  let r=await p.goto(`${base}/ru/admin/catalog/activity/add/?place=${fixture.ids.other_place}`);assert.equal(r.status(),403);
  r=await p.goto(`${base}/ru/admin/catalog/program/add/?organization=${fixture.ids.organization}`);assert.equal(r.status(),200);
  assert.equal(await p.locator('[name="organization"]').inputValue(),String(fixture.ids.organization));
 });
 await record('synthetic activity draft create and edit roundtrip',async()=>{
  await p.goto(`${base}/ru/admin/catalog/activity/add/?place=${fixture.ids.place}`);
  const name='QA browser activity '+Date.now();await (await showField(p,'name_az')).fill(name);
  await Promise.all([p.waitForURL(/\/activity\/\d+\/change\//),p.locator('button[name="_save_draft"]').click()]);
  assert.equal(await p.locator('[name="name_az"]').inputValue(),name);
  const id=Number(p.url().match(/activity\/(\d+)\/change/)[1]);
  await (await showField(p,'name_az')).fill(name+' edited');
  await Promise.all([p.waitForNavigation(),p.locator('button[name="_save_draft"]').click()]);
  assert.equal(await p.locator('[name="name_az"]').inputValue(),name+' edited');
  report.createdActivityId=id;
 });
 await record('synthetic group draft create and edit roundtrip',async()=>{
  await p.goto(`${base}/ru/admin/catalog/offeringgroup/add/?activity=${fixture.ids.activity}`);
  const name='QA browser group '+Date.now();await (await showField(p,'name_az')).fill(name);
  await p.locator('[name="age_from"]').fill('5');await p.locator('[name="age_to"]').fill('7');
  await p.locator('#id_language').fill('RU');await (await showField(p,'schedule_text')).fill('Tue/Thu 16:00');
  await Promise.all([p.waitForURL(/\/offeringgroup\/\d+\/change\//),p.locator('button[name="_save_draft"]').click()]);
  assert.equal(await p.locator('[name="name_az"]').inputValue(),name);
  report.createdGroupId=Number(p.url().match(/offeringgroup\/(\d+)\/change/)[1]);
  await (await showField(p,'schedule_text')).fill('Tue/Thu 17:00');
  await Promise.all([p.waitForNavigation(),p.locator('button[name="_save_draft"]').click()]);
  assert.equal(await p.locator('[name="schedule_text"]').inputValue(),'Tue/Thu 17:00');
 });
 await record('place validation error and draft save preserves navigation',async()=>{
  await p.setViewportSize({width:1440,height:1000});await p.goto(`${base}/ru/admin/catalog/place/add/?type=permanent`);
  assert.ok((await p.locator('#content').innerText()).includes('Сначала сохраните место.'));
  await p.locator('[name="name_az"]').fill('QA browser draft place '+Date.now());
  await p.locator('[name="category"]').selectOption('EDU',{force:true});
  await p.locator('[name="age_from"]').fill('8');await p.locator('[name="age_to"]').fill('5');
  await Promise.all([p.waitForNavigation(),p.locator('button[name="_save_draft"]').click()]);
  assert.ok(await p.locator('.errorlist,.km-pf-field__error').count()>0,'invalid age range displays error');
  await p.locator('[name="age_from"]').fill('5');await p.locator('[name="age_to"]').fill('8');
  await Promise.all([p.waitForNavigation(),p.locator('button[name="_save_draft"]').click()]);
  assert.match(p.url(),/\/place\/\d+\/change\//);assert.equal(await p.locator('[name="status"]').inputValue(),'draft');
  assert.ok(await p.locator('.km-admin-related-links a[href*="/activity/add/"]').count()>0);
  report.createdPlaceId=Number(p.url().match(/place\/(\d+)\/change/)[1]);
 });
 await record('group pricing link opens actual place pricing editor',async()=>{
  await p.goto(`${base}/ru/admin/catalog/offeringgroup/${fixture.ids.group}/change/`);
  const href=await p.locator('.km-business-links-grid a[href$="#pricing"]').getAttribute('href');await p.goto(new URL(href,base).href);
  assert.equal(new URL(p.url()).hash,'#pricing');assert.equal(await p.locator('#pricing').count(),1);
  assert.equal(await p.locator('[name="pricing_plans"]').count(),1);assert.equal(await p.locator('[name="nested_pricing"]').count(),1);
 });
 await record('localized volunteer moderation parent stays active',async()=>{
  let r=await p.goto(`${base}/ru/admin/volunteer/moderation/`);assert.equal(r.status(),200);
  let groups=(await inspect(p)).groups;assert.equal(groups.find(g=>g.key==='moderation')?.active,true);assert.equal(groups.find(g=>g.key==='moderation')?.open,true);
 });
 await record('overview starts mobile collapsed',async()=>{await p.setViewportSize({width:390,height:850});await p.goto(`${base}/ru/admin/`);assert.equal((await inspect(p)).groups.filter(g=>g.open).length,0);});
 await record('keyboard group activation',async()=>{await p.locator('.km-admin-header__toggle[data-widget="pushmenu"]').click();let t=p.locator('[data-km-sidebar-toggle]').first();await t.focus();await p.keyboard.press('Enter');assert.equal(await t.getAttribute('aria-expanded'),'true');await p.keyboard.press('Space');assert.equal(await t.getAttribute('aria-expanded'),'false');});
 await record('mobile drawer close button and resize restoration',async()=>{
  await p.setViewportSize({width:390,height:850});await p.goto(`${base}/ru/admin/catalog/activity/${fixture.ids.activity}/change/`);
  const opener=p.locator('.km-admin-header__toggle[data-widget="pushmenu"]');await opener.click();
  await p.locator('[data-km-sidebar-close]').click();await p.waitForTimeout(350);assert.equal(await opener.getAttribute('aria-expanded'),'false');
  assert.ok(await opener.evaluate(e=>e===document.activeElement));
  await p.setViewportSize({width:1440,height:1000});await p.evaluate(()=>localStorage.setItem('km-admin-sidebar:settings','1'));await p.reload();
  assert.ok((await inspect(p)).groups.filter(g=>g.open).length>=2);
  await p.setViewportSize({width:390,height:850});assert.equal((await inspect(p)).groups.filter(g=>g.open).length,1);
 });
 await record('mobile Tab navigation and backdrop dismissal',async()=>{
  await p.setViewportSize({width:390,height:1000});await p.goto(`${base}/ru/admin/catalog/activity/${fixture.ids.activity}/change/`);
  const opener=p.locator('.km-admin-header__toggle[data-widget="pushmenu"]');await opener.click();
  await p.locator('[data-km-sidebar-toggle]').first().focus();await p.keyboard.press('Tab');
  assert.ok(await p.evaluate(()=>document.querySelector('.main-sidebar').contains(document.activeElement)));
  assert.equal(await p.evaluate(()=>document.activeElement.tagName),'A');
  await p.locator('#sidebar-overlay').click({position:{x:350,y:900}});await p.waitForTimeout(350);
  assert.equal(await opener.getAttribute('aria-expanded'),'false');assert.ok(await opener.evaluate(e=>e===document.activeElement));
 });
 await record('hubs responsive and no unresolved icons',async()=>{
  for(const lang of ['az','ru','en'])for(const width of [320,390,1440])for(const hub of ['directories','technical']){
   await p.setViewportSize({width,height:1000});await p.goto(`${base}/${lang}/admin/navigation/${hub}/`);
   let state=await inspect(p);assert.equal(state.overflow,false,`${lang}${width}${hub}`);
   assert.equal(await p.locator('.km-admin-navigation-hub svg use').evaluateAll(es=>es.filter(e=>!document.getElementById(e.getAttribute('href').slice(1))).length),0);
   if(lang==='ru'&&width!==320)await p.screenshot({path:path.join(out,`hub-${hub}-${width}.png`),fullPage:false});
  }
 });
 await c.close();
 for(const role of ['limited','volunteer']){
  const rc=await contextFor(role,390),rp=await rc.newPage();
  await record(`${role} isolated sidebar`,async()=>{let r=await rp.goto(`${base}/ru/admin/`);assert.equal(r.status(),200);const snapshot=await inspect(rp);report[role]={path:new URL(rp.url()).pathname,snapshot};assert.equal(snapshot.overflow,false);if(role==='volunteer')assert.ok(new URL(rp.url()).pathname.includes('volunteer'));});
  await record(`${role} direct business route denied`,async()=>{let r=await rp.goto(`${base}/ru/admin/catalog/activity/${fixture.ids.activity}/change/`);assert.equal(r.status(),403);});
  await rc.close();
 }
 report.externalRequestsBlocked=[...new Set(report.externalRequestsBlocked)];report.summary={matrix:report.matrix.length,matrixPassed:report.matrix.filter(x=>x.status==='PASS').length,flows:report.flows.length,flowPassed:report.flows.filter(x=>x.status==='PASS').length,failures:report.failures.length};
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report.summary));
 if(report.failures.length){console.log(JSON.stringify(report.failures,null,2));process.exitCode=1;}
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});
