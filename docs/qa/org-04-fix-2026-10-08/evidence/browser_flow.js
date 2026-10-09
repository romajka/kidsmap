async original=>{
const base='http://localhost:8788',browser=original.context().browser(),rows=[],errors=[],network=[],prefixes={ru:'/ru',az:'',en:'/en'};
const c=await browser.newContext({viewport:{width:1440,height:950},reducedMotion:'reduce'}),p=await c.newPage();
function hooks(p){p.on('pageerror',e=>errors.push(String(e)));p.on('response',r=>{if(r.status()>=400)network.push({status:r.status(),url:r.url()})});}
hooks(p);await c.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());
function check(id,ok,detail){rows.push({id,status:ok?'PASS':'FAIL',...detail});}
async function confirm(page){const nav=page.waitForNavigation({waitUntil:'load'});await page.locator('[name=consent]').check();await page.locator('[data-confirm-form] button[type=submit]').click();await nav;}
try{
await p.goto(base+'/qa/');await p.getByRole('button',{name:'Войти: demo_owner',exact:true}).click();
// Actual valid CSRF, exact historical transports, association verified by next preview.
await p.goto(base+'/ru/account/organizations/43/branches/74/detach-preview/');
const csrf=await p.locator('[data-confirm-form] [name=csrfmiddlewaretoken]').inputValue();
const legacy=await p.request.post(base+'/ru/account/organizations/43/branches/74/detach/',{form:{expected_ownership_version:'1'},headers:{'X-CSRFToken':csrf},maxRedirects:0});
check('legacy-html-review-only',legacy.status()===302&&legacy.headers().location==='/ru/account/organizations/43/branches/74/detach-preview/');
const api=await p.request.post(base+'/ru/api/ownership/detach/place/74/',{data:{organization_id:43,expected_ownership_version:1},headers:{'X-CSRFToken':csrf}});
let apiData={};try{apiData=await api.json()}catch{}
check('legacy-json-confirmation-required',api.status()===409&&apiData.error==='confirmation_required',{statusCode:api.status()});
await p.reload();check('legacy-transports-link-still-present',await p.locator('tr[data-result=detached]').count()===1);
// Exit without consenting; then return.
await p.locator('main a').first().click();await p.goto(base+'/ru/account/organizations/43/branches/74/detach-preview/');
check('exit-review-no-detach',await p.locator('tr[data-result=detached]').count()===1);
const bound=await p.locator('[data-confirm-form]').evaluate(form=>({preview_id:form.elements.preview_id.value,idempotency_key:form.elements.idempotency_key.value}));
const missing=await p.request.post(p.url(),{form:{...bound,action:'confirm'},headers:{'X-CSRFToken':csrf},maxRedirects:0});check('server-rejects-missing-consent',missing.status()===409);
const absent=await p.request.post(p.url(),{form:{action:'confirm',consent:'1',idempotency_key:bound.idempotency_key},headers:{'X-CSRFToken':csrf},maxRedirects:0});check('server-rejects-missing-receipt',absent.status()===409);
await confirm(p);const resultUrl=p.url();check('confirmed-result',await p.locator('tr[data-result=detached]').count()===1&&resultUrl.includes('/organization-operations/'));
const repeat=await p.request.post(resultUrl,{form:{...bound,action:'confirm',consent:'1'},headers:{'X-CSRFToken':csrf},maxRedirects:0});check('repeat-same-receipt-key',repeat.status()===302);
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
await p.setViewportSize({width,height:950});await p.goto(base+prefixes[lang]+resultUrl.replace(base,'').replace('/ru',''));
const g=await p.evaluate(()=>({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth}));check('result-'+lang+'-'+width,await p.locator('tr[data-result=detached]').count()===1&&g.scroll<=g.width,{geometry:g});
if(width===390||width===1440)await p.locator('main').screenshot({path:'output/playwright/org04-fix-20261008/result-'+lang+'-'+width+'.png'});
}
// Keyboard-only confirmation of different synthetic places, one per context size/language.
let id=75;
for(const lang of ['ru','az','en'])for(const width of [390,1440]){
await p.setViewportSize({width,height:950});await p.goto(base+prefixes[lang]+'/account/places/');
const href=prefixes[lang]+'/account/organizations/43/branches/'+id+'/detach-preview/';
await p.locator('a[href="'+href+'"]').focus();let nav=p.waitForNavigation({waitUntil:'load'});await p.keyboard.press('Enter');await nav;
check('keyboard-owner-link-'+lang+'-'+width,p.url().endsWith(href));
await p.locator('[name=consent]').focus();await p.keyboard.press('Space');const checked=await p.locator('[name=consent]').isChecked();await p.keyboard.press('Tab');const active=await p.locator('[data-confirm-form] button').evaluate(el=>el===document.activeElement);
nav=p.waitForNavigation({waitUntil:'load'});await p.keyboard.press('Enter');await nav;
check('keyboard-confirm-'+lang+'-'+width,checked&&active&&await p.locator('tr[data-result=detached]').count()===1);id++;
}
// Two genuine tabs: first changes the link, second cannot apply its older snapshot.
await p.setViewportSize({width:390,height:950});const second=await c.newPage();hooks(second);
await p.goto(base+'/ru/account/organizations/43/branches/81/detach-preview/');await second.goto(p.url());
await confirm(p);await confirm(second);
check('two-tabs-conflict',await p.locator('tr[data-result=detached]').count()===1&&await second.locator('tr[data-result=changed]').count()===1);
await second.locator('main').screenshot({path:'output/playwright/org04-fix-20261008/conflict-ru-390.png'});
const retry=second.locator('main a[href$="/branches/81/detach-preview/"]');check('conflict-new-review-stays-detach',await retry.count()===1);
await second.close();
// Lawful private link review/confirm/result remains redacted.
await p.goto(base+'/ru/account/organizations/44/branches/82/detach-preview/');await confirm(p);
const privateText=await p.locator('main').innerText();check('private-confirmed-no-disclosure',await p.locator('tr[data-result=detached]').count()===1&&!privateText.includes('ORG04 PRIVATE SECRET')&&!privateText.includes('ORG04 PRIVATE ADDRESS'));
await p.locator('main').screenshot({path:'output/playwright/org04-fix-20261008/private-result-ru-390.png'});
const privateResult=p.url();
// Unauthorized role: no preview/receipt and no metadata; result also actor-bound.
const foreign=await browser.newContext(),f=await foreign.newPage();await foreign.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());
await f.goto(base+'/qa/');await f.getByRole('button',{name:'Войти: demo_parent',exact:true}).click();
for(const url of [resultUrl,base+'/ru/account/organizations/43/branches/74/detach-preview/']){
const res=await f.goto(url);check('foreign-denied-'+(url===resultUrl?'receipt':'preview'),res.status()===404&&!await f.locator('body').innerText().then(t=>t.includes('ORG04 Тестовое место 0')));}
await foreign.close();
return {rows,errors,network,resultUrl,privateResult};
}catch(e){check('flow-harness',false,{error:String(e).slice(0,240)});return{rows,errors,network};}finally{await c.close();}
}
