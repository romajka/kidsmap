async(page)=>{
const origin='http://127.0.0.1:8784',events={errors:[],failed:[],staticFailures:[],stubs:[]};
page.on('pageerror',e=>events.errors.push(String(e)));
page.on('console',m=>{if(m.type()==='error')events.errors.push(m.text())});
page.on('requestfailed',r=>events.failed.push({url:r.url(),error:r.failure()?.errorText}));
page.on('response',r=>{if(r.status()>=400&&r.url().includes('/static/'))events.staticFailures.push({url:r.url(),status:r.status()})});
await page.context().unroute('**/*');
await page.context().route('**/*',async route=>{
 const url=new URL(route.request().url());
 if(url.origin===origin)return route.continue();
 events.stubs.push(url.origin);
 if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});
 return route.fulfill({status:200,contentType:url.pathname.endsWith('.css')?'text/css':'application/javascript',body:''});
});
const fixtures=await(await page.request.get(origin+'/qa24/fixtures')).json();
const rows=[],checks=[];
for(const width of [320,360,390,768,1024,1280,1440])for(const lang of ['az','ru','en'])for(const role of ['public','person','manager','foreign','volunteer','staff','reviewer']){
 await page.setViewportSize({width,height:900});
 await page.request.get(origin+'/qa24/session/'+role+'?lang='+lang);
 const response=await page.goto(origin+fixtures.paths[lang][role],{waitUntil:'networkidle'});
 await page.evaluate(()=>document.fonts.ready);
 if(role==='person'){
  if(await page.locator('form [data-owner-step]').count()!==5)throw new Error('Personal editor must contain five real form steps');
  const tab=page.locator('[data-owner-step-target]').last();
  if(await tab.isVisible())await tab.click();
  else for(let step=0;step<4;step++){
   const next=page.locator('[data-owner-step]:not([hidden]) [data-owner-next]');
   if(await next.count())await next.click();
   else await page.locator('[data-owner-next]:visible').first().click();
  }
 }
 const facts=await page.evaluate(()=>{
  const rect=e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,width:r.width}};
  const group=document.querySelector('#documents-group-wrapper');
  return {lang:document.documentElement.lang,body:document.body.innerText,heading:document.querySelector('h1')?.innerText,
   privateMediaLinks:[...document.querySelectorAll('a[href]')].filter(e=>/\/media\/(protected_docs|specialist-documents|private-media)/i.test(e.href)).length,
   downloads:[...document.querySelectorAll('a[href*="/documents/"][href$="/download/"]')].map(e=>({href:e.getAttribute('href'),rect:rect(e)})),
   forbiddenFileInputs:document.querySelectorAll('input[type="file"][name^="documents-"]').length,
   editableConsent:document.querySelectorAll('input[name^="documents-"][name$="-is_published"],select[name^="documents-"][name$="-opted_in_by"]').length,
   inlinePresent:!!document.querySelector('[id^="documents-"][id$="-group"]'),scrollWidth:document.documentElement.scrollWidth,viewport:innerWidth,
   groupBounds:group?rect(group):null,csrf:[...document.querySelectorAll('form[method="post"]')].every(e=>!!e.querySelector('[name="csrfmiddlewaretoken"]'))}
 });
 const issues=[];
 if(response.status()!==200)issues.push('HTTP_'+response.status());
 if(facts.lang!==lang)issues.push('shell_language');
 if(facts.privateMediaLinks||facts.forbiddenFileInputs||facts.editableConsent)issues.push('private_url_or_editable_file_consent');
 if(!facts.csrf)issues.push('missing_csrf');
 if(role==='reviewer'){
  if(!facts.body.includes('QA24 PRIVATE IDENTITY')||!facts.body.includes('QA24 PENDING CERTIFICATE')||facts.downloads.length!==3)issues.push('reviewer_inline_missing');
  if(facts.groupBounds&&(facts.groupBounds.left < -1||facts.groupBounds.right>width+1))issues.push('document_inline_clipped');
  const link=page.locator('a[href*="/documents/"][href$="/download/"]').first();
  if(await link.count()){
   const wrapper=page.locator('#documents-group-wrapper');
   await wrapper.focus();
   const before=await wrapper.evaluate(e=>({x:scrollX,left:e.scrollLeft,max:e.scrollWidth-e.clientWidth}));
   await page.keyboard.press('ArrowRight');await page.waitForTimeout(150);
   const moved=await wrapper.evaluate(e=>({x:scrollX,left:e.scrollLeft}));
   checks.push({role,width,lang,check:'document_region_keyboard_scroll',pass:before.x===0&&moved.x===0&&(before.max<=1||moved.left>before.left)});
   await wrapper.evaluate(e=>e.scrollLeft=0);
   await page.keyboard.press('Tab');
   await page.waitForFunction(()=>{const e=document.activeElement,w=document.querySelector('#documents-group-wrapper');if(!e||!w)return false;const r=e.getBoundingClientRect(),b=w.getBoundingClientRect();return scrollX===0&&r.left>=Math.max(0,b.left)-1&&r.right<=Math.min(innerWidth,b.right)+1},null,{timeout:1500}).catch(()=>{});
   checks.push({role,width,lang,check:'reviewer_download_keyboard_focus',pass:await link.evaluate(e=>document.activeElement===e&&scrollX===0)});
   const controls=wrapper.locator('select,textarea,a[href*="/documents/"]');
   let usable=true;const controlFacts=[];
   for(let i=0;i<await controls.count();i++){
    if(i){await page.keyboard.press('Tab');await page.waitForFunction(()=>{const e=document.activeElement,w=document.querySelector('#documents-group-wrapper');if(!e||!w)return false;const r=e.getBoundingClientRect(),b=w.getBoundingClientRect();return scrollX===0&&r.left>=Math.max(0,b.left)-1&&r.right<=Math.min(innerWidth,b.right)+1},null,{timeout:1500}).catch(()=>{});}
    const detail=await controls.nth(i).evaluate(e=>{const r=e.getBoundingClientRect(),w=document.querySelector('#documents-group-wrapper'),b=w.getBoundingClientRect();return{tag:e.tagName,name:e.name,focused:document.activeElement===e,activeTag:document.activeElement?.tagName,activeName:document.activeElement?.name,x:scrollX,left:r.left,right:r.right,viewport:innerWidth,regionLeft:b.left,regionRight:b.right,regionClient:w.clientWidth,regionScrollLeft:w.scrollLeft}});
    controlFacts.push(detail);usable=usable&&detail.focused&&detail.x===0&&detail.left>=Math.max(0,detail.regionLeft)-1&&detail.right<=Math.min(width,detail.regionRight)+1;
   }
   await wrapper.evaluate(e=>e.scrollLeft=e.scrollWidth);
   checks.push({role,width,lang,check:'reviewer_all_controls_and_rightmost_columns_reachable',controls:controlFacts,pass:usable&&await wrapper.evaluate(e=>scrollX===0&&e.scrollLeft>=e.scrollWidth-e.clientWidth-1)});
  }
 }else if(role==='staff'){
  if(facts.body.includes('QA24 PRIVATE IDENTITY')||facts.body.includes('QA24 PENDING CERTIFICATE')||facts.downloads.length)issues.push('ordinary_staff_inline_leak');
 }else if(role==='person'){
  const copy={az:'Sənədlər məxfi qalır.',ru:'Документы остаются приватными.',en:'Documents remain private.'};
  if(!facts.body.includes(copy[lang]))issues.push('private_document_help_not_localized');
  if(!await page.locator('input[type="file"][name="documents"]').count())issues.push('verified_person_upload_missing');
  const upload=page.locator('input[type="file"][name="documents"]');
  if(await upload.count()){
   await upload.focus();
   checks.push({role,width,lang,check:'person_document_upload_keyboard_focus',pass:await upload.evaluate(e=>document.activeElement===e)});
  }
  if(facts.scrollWidth>facts.viewport+1)issues.push('person_editor_overflow');
 }else{
  if(facts.body.includes('QA24 RETIRED PRIVATE LOCATION'))issues.push('retired_location_leaked_as_current');
  if(facts.body.includes('QA24 PRIVATE IDENTITY')||facts.body.includes('QA24 PENDING CERTIFICATE'))issues.push('private_document_name_leak');
  if(!facts.body.includes('QA24 PUBLIC CERTIFICATE')||facts.downloads.length!==1)issues.push('approved_owner_optin_certificate_missing');
  if(facts.scrollWidth>facts.viewport+1)issues.push('public_overflow');
  const link=page.locator('a[href*="/documents/"][href$="/download/"]').first();
  if(await link.count()){await link.scrollIntoViewIfNeeded();await link.focus();checks.push({role,width,lang,check:'certificate_keyboard_focus',pass:await link.evaluate(e=>document.activeElement===e)})}
 }
 rows.push({role,width,lang,status:response.status(),issues,facts});
 if(width===390)for(const kind of ['identity','pending','approved']){
  const download=await page.request.get(origin+fixtures.paths[lang]['document_'+kind]);
  const expected=role==='volunteer'?403:(['person','reviewer'].includes(role)||kind==='approved'?200:404);
  let pass=download.status()===expected;
  if(expected===200)pass=pass&&(await download.body()).toString()==='%PDF-synthetic-only'&&download.headers()['content-disposition']?.includes('attachment')&&download.headers()['cache-control']==='private, no-store';
  checks.push({role,width,lang,kind,check:'document_http_boundary',status:download.status(),expected,pass});
 }
 if([390,1440].includes(width))await page.screenshot({path:'__QA24_EVIDENCE__/'+role+'-'+lang+'-'+width+'.png',fullPage:true});
}
const invariant=await(await page.request.get(origin+'/qa24/invariants')).json();
checks.push({check:'browser_did_not_change_documents',pass:invariant.unchanged});
return {rows,total:rows.length,passed:rows.filter(r=>!r.issues.length).length,checks,checksPassed:checks.filter(r=>r.pass).length,events};
}
