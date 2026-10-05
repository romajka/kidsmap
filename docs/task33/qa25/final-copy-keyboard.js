async(page)=>{
const origin='http://127.0.0.1:8795',base='/docs/task33/design/specialist/',files=__QA25_FILES__,rows=[],checks=[],events={errors:[],failed:[],staticFailures:[],external:[]};
page.on('pageerror',e=>events.errors.push(String(e)));
page.on('console',m=>{if(m.type()==='error')events.errors.push(m.text())});
page.on('requestfailed',r=>events.failed.push({url:r.url(),error:r.failure()?.errorText}));
page.on('response',r=>{if(r.status()>=400)events.staticFailures.push({url:r.url(),status:r.status()})});
await page.context().route('**/*',route=>{const url=new URL(route.request().url());if(url.origin===origin)return route.continue();events.external.push(url.origin);return route.abort();});
for(const width of [390,1440])for(const lang of ['az','ru','en'])for(const file of files){
 await page.setViewportSize({width,height:900});await page.goto(origin+base+file+'?lang='+lang,{waitUntil:'networkidle'});
 const facts=await page.evaluate(()=>({lang:document.documentElement.lang,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,h1:!!document.querySelector('h1'),text:document.querySelector('main').innerText}));
 const issues=[];
 if(facts.lang!==lang||!facts.h1||facts.scrollWidth>width+1)issues.push('structure_language_or_overflow');
 if(file==='reconciliation.html'&&/\bemployment\b|legacy[_ ]owner|verified_person_user|owner_id|place_id/i.test(facts.text))issues.push('reconciliation_implementation_copy');
 if(file==='review.html'&&lang!=='en'&&/\bstaff\b|\breviewer\b/i.test(facts.text))issues.push('mixed_role_copy');
 rows.push({file,lang,width,issues});
 await page.keyboard.press('Tab');
 checks.push({file,lang,width,check:'tab_reaches_skip_link',pass:await page.locator('.skip').evaluate(e=>document.activeElement===e)});
 await page.keyboard.press('Enter');
 checks.push({file,lang,width,check:'keyboard_skip_enters_main',pass:await page.locator('main').evaluate(e=>document.activeElement===e)});
 if(lang==='ru'){await page.screenshot({path:'__QA25_EVIDENCE__/'+file.replace('.html','')+'-'+lang+'-'+width+'.png',fullPage:true});}
 if(file==='reconciliation.html'){
  await page.locator('[data-action="reconcile"]').focus();await page.keyboard.press('Enter');
  checks.push({file,lang,width,check:'keyboard_demo_reconciliation_shows_result',pass:!!await page.locator('#reconciliation-result').textContent()});
 }
}
for(const width of [390,1440])for(const lang of ['az','ru','en'])for(const file of ['person','organization','claim','documents','review']){
 await page.setViewportSize({width,height:900});await page.goto(origin+base+file+'.html?lang='+lang+'&state=denied',{waitUntil:'networkidle'});
 const facts=await page.evaluate(()=>({lang:document.documentElement.lang,state:document.body.dataset.state,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,text:document.querySelector('main').innerText,controls:document.querySelector('main').querySelectorAll('textarea,input[type=file],[data-action="approve-document"],[data-action="org-consent"],[data-action="person-consent"]').length}));
 const issues=[];
 if(facts.lang!==lang||facts.state!=='denied'||facts.scrollWidth>width+1||facts.controls)issues.push('denied_role_controls_or_overflow');
 if(lang!=='en'&&/\bstaff\b|\breviewer\b/i.test(facts.text))issues.push('mixed_role_denial_copy');
 rows.push({file:file+'.html',lang,width,state:'denied',issues});
}
for(const lang of ['az','ru','en'])for(const state of ['pending','rejected','revoked']){
 await page.goto(origin+base+'profile.html?lang='+lang+'&state='+state,{waitUntil:'networkidle'});
 checks.push({file:'profile.html',lang,state,check:'nonpublic_certificate_absent',pass:await page.locator('[data-action="certificate"]').count()===0});
}
return{rows,total:rows.length,passed:rows.filter(r=>!r.issues.length).length,checks,checksPassed:checks.filter(c=>c.pass).length,events};
}
