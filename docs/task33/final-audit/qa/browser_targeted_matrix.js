async(page)=>{
const origin='http://127.0.0.1:8788',rows=[],checks=[],events={errors:[],failed:[],staticFailures:[],stubs:[],expectedRejections:[]};
const observations=[];
let expectedImpactRejection=false;
page.on('pageerror',e=>events.errors.push(String(e)));
page.on('console',m=>{if(m.type()==='error'){if(expectedImpactRejection&&/400/.test(m.text()))events.expectedRejections.push(m.text());else events.errors.push(m.text())}});
page.on('requestfailed',r=>events.failed.push({url:r.url(),error:r.failure()?.errorText}));
page.on('response',r=>{if(r.status()>=400&&r.url().includes('/static/'))events.staticFailures.push({url:r.url(),status:r.status()})});
await page.context().unroute('**/*');await page.context().route('**/*',async route=>{
 const u=new URL(route.request().url());if(u.origin===origin)return route.continue();
 if(u.pathname==='/qa-font.ttf')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.ttf'})});
 events.stubs.push(u.origin);if(u.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});
 return route.fulfill({status:200,contentType:u.pathname.endsWith('.css')?'text/css':'application/javascript',body:''});
});
const fixtures=await(await page.request.get(origin+'/qa28/fixtures')).json();
const session=async role=>page.request.get(origin+'/qa28/session/'+role+'?lang=ru');
const state=async()=> (await page.request.get(origin+'/qa28/targeted-state')).json();
for(const width of [390,1280])for(const lang of ['az','ru','en'])for(const screen of ['program','activity','organization']){
 await page.setViewportSize({width,height:900});await page.request.get(origin+'/qa28/session/'+(screen==='program'?'network_owner':'parent')+'?lang='+lang);
 const response=await page.goto(origin+fixtures.paths[lang][screen],{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
 const facts=await page.evaluate(()=>({lang:document.documentElement.lang,title:document.title,heading:document.querySelector('h1')?.innerText,body:document.body.innerText,viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,roundedFont:document.fonts.check('24px "Material Symbols Rounded"'),visible_main_landmarks:[...document.querySelectorAll('main')].filter(e=>e.getBoundingClientRect().width&&e.getBoundingClientRect().height).length,
 canonical:document.querySelector('link[rel="canonical"]')?.href,alternates:[...document.querySelectorAll('link[hreflang]')].map(e=>e.hreflang),schema:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>JSON.parse(e.textContent)),csrf:[...document.querySelectorAll('form[method="post"]')].every(e=>!!e.querySelector('[name="csrfmiddlewaretoken"]'))}));
 const issues=[];if(response.status()!==200)issues.push('HTTP_'+response.status());if(facts.lang!==lang)issues.push('language');if(facts.scrollWidth>width+1)issues.push('overflow');if(!facts.heading||!facts.title)issues.push('heading_title');if(!facts.csrf)issues.push('csrf');
 if(screen!=='program'){
  if(!facts.canonical||new URL(facts.canonical).hostname!=='kidsmap.az')issues.push('canonical');
  if(!['az','ru','en'].every(l=>facts.alternates.includes(l)))issues.push('hreflang');
  if(!facts.schema.length)issues.push('schema_absent');
  if(facts.body.includes('QA AUDIT PRIVATE'))issues.push('private_leak');
 }
 if(screen==='activity'&&(!facts.body.includes('25')||!facts.body.includes('Saturday 10:00')||!facts.body.includes('QA AUDIT LOCAL '+lang.toUpperCase())))issues.push('local_data_missing');
 if(screen==='program'&&!facts.body.includes('QA23 SELECTED BRANCH'))issues.push('impact_branch_missing');
 if(screen==='program'&&!facts.roundedFont)issues.push('program_icon_font_missing');
 const control=page.locator('main input:not([type="hidden"]):visible,main button:visible,main a[href]:visible').first();
 if(await control.count()){await control.focus();checks.push({check:'focus',screen,width,lang,pass:await control.evaluate(e=>document.activeElement===e)});await page.keyboard.press('Tab');checks.push({check:'tab',screen,width,lang,pass:await page.evaluate(()=>document.activeElement!==document.body&&scrollX===0)})}
 rows.push({screen,actor:screen==='program'?'network_owner':'parent',lang,width,status:response.status(),url:page.url(),facts,issues});
 if(lang==='ru')await page.screenshot({path:'__QA28_EVIDENCE__/'+screen+'-ru-'+width+'.png',fullPage:true});
}
await session('parent');for(const width of [320,390]){
 await page.setViewportSize({width,height:900});await page.goto(origin+fixtures.paths.ru.catalog,{waitUntil:'networkidle'});
 observations.push({observation:'RU_count_copy_geometry',width,...await page.locator('.results-count-text').evaluate(e=>{const r=e.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(e);const text=range.getBoundingClientRect(),ancestors=[];for(let p=e.parentElement;p&&ancestors.length<5;p=p.parentElement){const b=p.getBoundingClientRect(),s=getComputedStyle(p);ancestors.push({className:p.className,left:b.left,right:b.right,width:b.width,overflowX:s.overflowX,textOverflow:s.textOverflow})}return {ancestors,clippedByAncestor:ancestors.some(p=>['hidden','clip'].includes(p.overflowX)&&(text.right>p.right+1||text.left<p.left-1)),text:e.textContent.trim(),elementWidth:r.width,textRangeWidth:text.width,clientWidth:e.clientWidth,scrollWidth:e.scrollWidth,overflow:getComputedStyle(e).overflow,textOverflow:getComputedStyle(e).textOverflow,clipped:Math.max(text.width,e.scrollWidth)>r.width+1}})});
 await page.screenshot({path:'__QA28_EVIDENCE__/catalog-count-ru-'+width+'.png',fullPage:false});
}
await page.setViewportSize({width:1280,height:900});await session('network_owner');await page.goto(origin+fixtures.paths.ru.program,{waitUntil:'networkidle'});
const form=page.locator('main form[action$="/save/"]'),before=await state();
const old=await form.evaluate(e=>Object.fromEntries([...new FormData(e)].filter(([,v])=>typeof v==='string')));
await form.locator('[name="name_az"]').fill('QA AUDIT PENDING PROGRAM');
expectedImpactRejection=true;
await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(fixtures.paths.ru.program_save)),form.locator('[name="submit"]').click()]);await page.waitForLoadState('networkidle');
checks.push({check:'impact_confirmation_required_native_POST',pass:await page.locator('main [name="impact_confirmed"]').count()>0&&(await page.locator('.account-main-content').innerText()).includes('Проверьте затронутые филиалы')&&(await state()).revision_status===null});
expectedImpactRejection=false;
await page.locator('main [name="impact_confirmed"]').check();
await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(fixtures.paths.ru.program_save)),page.locator('main [name="submit"]').click()]);await page.waitForLoadState('networkidle');
const after=await state();checks.push({check:'program_native_owner_edit_candidate_only',pass:after.revision_status==='pending'&&after.revision_payload.name_az==='QA AUDIT PENDING PROGRAM'&&after.program_name===before.program_name&&after.description===before.description&&after.supplement===before.supplement});
await page.screenshot({path:'__QA28_EVIDENCE__/program-pending-after-edit.png',fullPage:false});
const stale=await page.request.post(origin+fixtures.paths.ru.program_save,{form:{...old,submit:'1',impact_confirmed:'1'}});checks.push({check:'program_stale_edit_denied',status:stale.status(),pass:stale.status()===409});
await session('parent');for(const screen of ['activity','organization']){const response=await page.request.get(origin+fixtures.paths.ru[screen]);checks.push({check:'pending_program_not_public',screen,pass:response.status()===200&&!(await response.text()).includes('QA AUDIT PENDING PROGRAM')})}
for(const screen of ['private_activity','private_organization']){const response=await page.request.get(origin+fixtures.paths.ru[screen]);checks.push({check:'private_entity_closed',screen,status:response.status(),pass:response.status()===404&&!(await response.text()).includes('QA AUDIT PRIVATE')})}
await session('all_network');const denied=await page.request.get(origin+fixtures.paths.ru.program);checks.push({check:'place_edit_does_not_grant_program_manage',status:denied.status(),pass:denied.status()===404});
const orgResponse=await page.request.get(origin+fixtures.paths.ru.all_network),orgHTML=await orgResponse.text();const token=orgHTML.match(/name="csrfmiddlewaretoken" value="([^"]+)"/);
checks.push({check:'manager_current_csrf_available',pass:!!token});
if(token){const r=await page.request.post(origin+fixtures.paths.ru.program_save,{form:{...old,csrfmiddlewaretoken:token[1],impact_confirmed:'1',submit:'1'}});checks.push({check:'program_manage_POST_scope_denied_valid_CSRF',status:r.status(),pass:r.status()===404})}
return {rows,checks,events,observations,fixtures:'approved Program/Org/Activity fixtures are direct synthetic setup; native owner edit and scope are actual browser HTTP; no full publication flow claimed'};
}
