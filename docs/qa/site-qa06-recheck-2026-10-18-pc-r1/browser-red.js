async original=>{
const base='http://127.0.0.1:33510',O='/mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1',Q='/mnt/c/kidsmap/.tmp/site06-pc-plan-r1',hub='/admin/catalog/sitegalleryimage/',rows=[],pageerrors=[],local_errors=[],blocked=[],console_errors=[],browser=original.context().browser();
try{
for(const role of ['content','super']){
const c=await browser.newContext({viewport:{width:1440,height:950},serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));
const a=await c.newPage(),p=await c.newPage();for(const x of[a,p]){x.setDefaultTimeout(12000);x.on('pageerror',e=>pageerrors.push(String(e)));x.on('console',m=>{if(m.type()==='error')console_errors.push(m.text());});x.on('response',r=>{if(new URL(r.url()).hostname==='127.0.0.1'&&r.status()>=400)local_errors.push({path:new URL(r.url()).pathname,status:r.status()});});}
await a.goto(base+'/qa/site06/login/'+role+'/');const state=async()=>(await a.request.get(base+'/qa/site06/state/')).json();
async function upload(file,selector){const response=a.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/ajax-upload/'));await a.locator(selector).setInputFiles(Q+'/'+file);const r=await response;await a.waitForTimeout(200);return{status:r.status(),json:await r.json()};}
async function publicLogo(lang,s){await p.goto(base+(lang==='az'?'/':'/'+lang+'/'));const img=p.locator('img').filter({visible:true});return p.locator('img[src="/media/'+s.logo+'"]').evaluateAll(es=>({found:es.length,decoded:es.length>0&&es.every(e=>e.complete&&e.naturalWidth>0),widths:es.map(e=>e.naturalWidth)}));}
for(const lang of ['az','ru','en']){
const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await a.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
for(const width of [390,1440]){
for(const x of[a,p])await x.setViewportSize({width,height:950});await a.goto(base+hub);
const selector='.km-media-row[data-field=logo] input[type=file]',initial=await upload('valid.png',selector),before=await state(),initialPublic=await publicLogo(lang,before);
const bad=await upload('broken.png',selector),afterBad=await state(),badPublic=await publicLogo(lang,afterBad);await p.screenshot({path:O+'/png/red-'+role+'-'+lang+'-'+width+'-broken-public-logo.png',animations:'disabled'});await a.screenshot({path:O+'/png/red-'+role+'-'+lang+'-'+width+'-accepted-bad-logo.png',animations:'disabled'});
const retry=await upload('valid.png',selector),restored=await state(),retryPublic=await publicLogo(lang,restored);
rows.push({id:'invalid-main-media',role,lang,width,initial,bad,retry,initialPublic,badPublic,retryPublic,before,afterBad,restored,checks:{initialValid200:initial.status===200,initialLogoDecoded:initialPublic.decoded,invalidRejected400:bad.status===400,noBadWrite:JSON.stringify(before)===JSON.stringify(afterBad),publicLogoRemainsDecoded:badPublic.decoded,retry200:retry.status===200,retryLogoDecoded:retryPublic.decoded,otherSettingsPreserved:restored.footer_phone===before.footer_phone&&restored.footer_email===before.footer_email&&restored.brand_name===before.brand_name}});
const beforeGallery=await state(),badGallery=await upload('broken.png','.km-gallery-grid[data-placement=HOME_HERO] input[type=file]'),afterGallery=await state();rows.push({id:'invalid-gallery-media',role,lang,width,badGallery,before:beforeGallery,after:afterGallery,checks:{invalidRejected400:badGallery.status===400,noBadWrite:JSON.stringify(beforeGallery)===JSON.stringify(afterGallery)}});
if(role==='super'&&width===1440){
const goodSVG=await upload('safe.svg',selector),svgState=await state(),svgPublic=await publicLogo(lang,svgState);const partner=await upload('safe.svg','.km-gallery-grid[data-placement=HOME_PARTNERS] input[type=file]');rows.push({id:'existing-svg-controls',role,lang,width,goodSVG,partner,checks:{svgLogo200:goodSVG.status===200,svgLogoDecoded:svgPublic.decoded,svgPartner200:partner.status===200}});await upload('valid.png',selector);
const path='/admin/catalog/sitebrandingsettings/1/change/';await a.goto(base+path);const before=await state();await a.locator('[name=logo][type=file]').setInputFiles(Q+'/broken.png');const response=a.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===path);await Promise.all([a.waitForNavigation({waitUntil:'domcontentloaded'}),a.locator('button[name=_continue]').click()]);const posted=await response,after=await state(),fieldErrors=await a.locator('.field-logo .errorlist,#id_logo_error').count();rows.push({id:'invalid-branding-form',role,lang,width,status:posted.status(),before,after,checks:{invalidForm200:posted.status()===200,fieldErrorPresent:fieldErrors>0,noBadWrite:JSON.stringify(before)===JSON.stringify(after)}});await a.screenshot({path:O+'/png/red-super-'+lang+'-1440-accepted-bad-form.png',animations:'disabled'});await a.goto(base+hub);await upload('valid.png',selector);
}
await p.screenshot({path:O+'/png/red-'+role+'-'+lang+'-'+width+'-restored-public-logo.png',animations:'disabled'});
}
}
await c.close();
}
return{rows,pageerrors,local_errors,blocked,console_errors,scope:'Current unchanged app; real native uploads/forms; simulated fictional fixture auth; invalid SVG payloads never loaded in browser. Expected RED no-write/400 contract is proposed policy, existing positive controls retained.'};
}catch(e){return{rows,pageerrors,local_errors,blocked,console_errors,error:String(e)};}
}
