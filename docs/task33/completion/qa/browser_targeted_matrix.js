async(page)=>{
const origin='http://127.0.0.1:8788',rows=[],checks=[],events={errors:[],failed:[],staticFailures:[],stubs:[],expectedRejections:[]};
const observations=[];
let expectedRejection=null;
page.on('pageerror',e=>events.errors.push(String(e)));
page.on('console',m=>{if(m.type()==='error'){
 const location=m.location().url;
 if(expectedRejection&&location===expectedRejection.url&&m.text().includes('status of '+expectedRejection.status))events.expectedRejections.push({text:m.text(),location});
 else events.errors.push({text:m.text(),location});
}});
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
for(const width of [320,360,390,768,1024,1280,1440])for(const lang of ['az','ru','en'])for(const screen of ['program','activity','organization']){
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
 if(screen==='program'&&facts.visible_main_landmarks!==1)issues.push('program_main_landmark_count');
 const control=page.locator('main input:not([type="hidden"]):visible,main button:visible,main a[href]:visible').first();
 if(await control.count()){await control.focus();checks.push({check:'focus',screen,width,lang,pass:await control.evaluate(e=>document.activeElement===e)});await page.keyboard.press('Tab');checks.push({check:'tab',screen,width,lang,pass:await page.evaluate(()=>document.activeElement!==document.body&&scrollX===0)})}
 rows.push({screen,actor:screen==='program'?'network_owner':'parent',lang,width,status:response.status(),url:page.url(),facts,issues});
 if(lang==='ru')await page.screenshot({path:'__QA28_EVIDENCE__/'+screen+'-ru-'+width+'.png',fullPage:true});
}
await session('parent');for(const width of [320,390]){
 await page.setViewportSize({width,height:900});await page.goto(origin+fixtures.paths.ru.catalog,{waitUntil:'networkidle'});
 observations.push({observation:'RU_count_copy_geometry',width,...await page.locator('.results-count-text').evaluate(e=>{const r=e.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(e);const text=range.getBoundingClientRect(),ancestors=[];for(let p=e.parentElement;p&&ancestors.length<5;p=p.parentElement){const b=p.getBoundingClientRect(),s=getComputedStyle(p);ancestors.push({className:p.className,left:b.left,right:b.right,width:b.width,overflowX:s.overflowX,textOverflow:s.textOverflow})}return {ancestors,clippedByAncestor:ancestors.some(p=>['hidden','clip'].includes(p.overflowX)&&(text.right>p.right+1||text.left<p.left-1)),text:e.textContent.trim(),elementWidth:r.width,textRangeWidth:text.width,clientWidth:e.clientWidth,scrollWidth:e.scrollWidth,overflow:getComputedStyle(e).overflow,textOverflow:getComputedStyle(e).textOverflow,clipped:Math.max(text.width,e.scrollWidth)>r.width+1}})});
 const countObservation=observations.at(-1);
 checks.push({check:'count_text_not_clipped',width,pass:!countObservation.clipped&&!countObservation.clippedByAncestor});
 for(const selector of ['[data-catalog-map-open]','.results-toolbar [data-filters-open]']){
  const button=page.locator(selector).first();
  const box=await button.boundingBox();
  checks.push({check:'count_neighbor_button_visible',width,selector,pass:!!box&&box.x>=0&&box.x+box.width<=width+1});
  await button.focus();checks.push({check:'count_neighbor_button_focus',width,selector,pass:await button.evaluate(e=>e===document.activeElement)});
 }
 await page.screenshot({path:'__QA28_EVIDENCE__/catalog-count-ru-'+width+'.png',fullPage:false});
}
await page.setViewportSize({width:1280,height:900});await session('network_owner');await page.goto(origin+fixtures.paths.ru.program,{waitUntil:'networkidle'});
const form=page.locator('main form[action$="/save/"]'),before=await state();
const old=await form.evaluate(e=>Object.fromEntries([...new FormData(e)].filter(([,v])=>typeof v==='string')));
await form.locator('[name="name_az"]').fill('QA AUDIT PENDING PROGRAM');
expectedRejection={url:origin+fixtures.paths.ru.program_save,status:400};
await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(fixtures.paths.ru.program_save)),form.locator('[name="submit"]').click()]);await page.waitForLoadState('networkidle');
checks.push({check:'impact_confirmation_required_native_POST',pass:await page.locator('main [name="impact_confirmed"]').count()>0&&(await page.locator('.account-main-content').innerText()).includes('Проверьте затронутые филиалы')&&(await state()).revision_status===null});
expectedRejection=null;
await page.locator('main [name="impact_confirmed"]').check();
await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(fixtures.paths.ru.program_save)),page.locator('main [name="submit"]').click()]);await page.waitForLoadState('networkidle');
const after=await state();checks.push({check:'program_native_owner_edit_candidate_only',pass:after.revision_status==='pending'&&after.revision_payload.name_az==='QA AUDIT PENDING PROGRAM'&&after.program_name===before.program_name&&after.description===before.description&&after.supplement===before.supplement});
await page.screenshot({path:'__QA28_EVIDENCE__/program-pending-after-edit.png',fullPage:false});
await page.locator('main [name="expected_version"]').evaluate((e,value)=>e.value=value,old.expected_version);
await page.locator('main [name="revision_version"]').evaluate((e,value)=>e.value=value,old.revision_version);
await page.locator('main [name="impact_confirmed"]').check();
expectedRejection={url:origin+fixtures.paths.ru.program_save,status:409};
const [stale]=await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url()===origin+fixtures.paths.ru.program_save),page.locator('main [name="submit"]').click()]);
await page.waitForLoadState('networkidle');
checks.push({check:'program_stale_native_edit_denied',status:stale.status(),pass:stale.status()===409&&(await state()).revision_version===after.revision_version});
expectedRejection=null;
await session('parent');for(const screen of ['activity','organization']){const response=await page.request.get(origin+fixtures.paths.ru[screen]);checks.push({check:'pending_program_not_public',screen,pass:response.status()===200&&!(await response.text()).includes('QA AUDIT PENDING PROGRAM')})}
for(const screen of ['private_activity','private_organization']){const response=await page.request.get(origin+fixtures.paths.ru[screen]);checks.push({check:'private_entity_closed',screen,status:response.status(),pass:response.status()===404&&!(await response.text()).includes('QA AUDIT PRIVATE')})}
await session('all_network');const denied=await page.request.get(origin+fixtures.paths.ru.program);checks.push({check:'place_edit_does_not_grant_program_manage',status:denied.status(),pass:denied.status()===404});
const orgResponse=await page.request.get(origin+fixtures.paths.ru.all_network),orgHTML=await orgResponse.text();const token=orgHTML.match(/name="csrfmiddlewaretoken" value="([^"]+)"/);
checks.push({check:'manager_current_csrf_available',pass:!!token});
if(token){const r=await page.request.post(origin+fixtures.paths.ru.program_save,{form:{...old,csrfmiddlewaretoken:token[1],impact_confirmed:'1',submit:'1'}});checks.push({check:'program_manage_POST_scope_denied_valid_CSRF',status:r.status(),pass:r.status()===404})}
// Create a classified standalone Activity through the actual owner controls,
// approve through the actual reviewer form, then inspect all public consumers.
const taxonomyState=async()=> (await page.request.get(origin+'/qa28/taxonomy-state')).json();
await session('standalone_owner');await page.goto(origin+fixtures.paths.ru.standalone_owner,{waitUntil:'networkidle'});
const copy=await page.locator('#pw-copy').evaluate(e=>JSON.parse(e.textContent));
await page.locator('[data-pc-add-activity]').click();
const card=page.locator('[data-pc-activity-list] > .pc-activity-card').last();
await card.getByRole('textbox',{name:copy.activity_name,exact:true}).fill('QA COMPLETION ART CLASS');
await card.getByRole('textbox',{name:copy.activity_description,exact:true}).fill('QA approved standalone art lessons');
await card.locator('[data-activity-category]').selectOption('ART');
const taxonomyBefore=await taxonomyState();
await card.locator('[data-activity-subcategory]').selectOption(String(taxonomyBefore.subcategory_id));
await card.getByRole('textbox',{name:copy.group_name,exact:true}).fill('QA ART GROUP');
await card.getByRole('spinbutton',{name:copy.group_age_from,exact:true}).first().fill('4');
await card.getByRole('spinbutton',{name:copy.group_age_to,exact:true}).first().fill('8');
await card.getByRole('textbox',{name:copy.group_schedule,exact:true}).fill('Saturday 10:00');
await card.getByRole('spinbutton',{name:copy.plan_price,exact:true}).fill('31');
await page.screenshot({path:'__QA28_EVIDENCE__/taxonomy-owner-before-submit.png',fullPage:true});
const [createdResponse]=await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url()===origin+fixtures.paths.ru.owner_photo_save),page.locator('[data-pc-submit]').click()]);
await page.waitForLoadState('networkidle');
const taxonomyPending=await taxonomyState();
checks.push({check:'taxonomy_owner_form_create_pending_not_public',status:createdResponse.status(),pass:createdResponse.status()===200&&taxonomyPending.revision_status==='pending'&&taxonomyPending.activity_count===0});
const filterQuery='?category=ART&subcategory='+taxonomyBefore.subcategory_id+'&age=6';
let mapResponse=await page.request.get(origin+fixtures.paths.ru.map_api+filterQuery);
let mapPayload=await mapResponse.json();
checks.push({check:'taxonomy_pending_map_absent',pass:mapResponse.status()===200&&!mapPayload.points.some(p=>(p.members||[]).some(m=>m.id===taxonomyBefore.place_id))});
await session('moderator');await page.goto(origin+fixtures.paths.ru.taxonomy_review,{waitUntil:'networkidle'});
await page.screenshot({path:'__QA28_EVIDENCE__/taxonomy-review-before-approval.png',fullPage:true});
const [approvalResponse]=await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url()===origin+fixtures.paths.ru.taxonomy_review),page.locator('button[name="action"][value="approve"]').click()]);
await page.waitForLoadState('networkidle');
const taxonomyApproved=await taxonomyState();
checks.push({check:'taxonomy_native_approval_materializes_classification',status:approvalResponse.status(),pass:approvalResponse.status()===302&&taxonomyApproved.revision_status==='approved'&&taxonomyApproved.activity_count===1&&taxonomyApproved.activity_category==='ART'&&taxonomyApproved.activity_subcategory===taxonomyBefore.subcategory_id});
await session('parent');await page.goto(origin+fixtures.paths.ru.catalog+filterQuery,{waitUntil:'networkidle'});
checks.push({check:'taxonomy_approved_catalog_result',pass:await page.locator('main').innerText().then(t=>t.includes('QA23 STANDALONE'))});
await page.locator('[data-catalog-map-open]').click();
await page.screenshot({path:'__QA28_EVIDENCE__/taxonomy-approved-catalog-map.png',fullPage:false});
mapResponse=await page.request.get(origin+fixtures.paths.ru.map_api+filterQuery);mapPayload=await mapResponse.json();
checks.push({check:'taxonomy_approved_map_result',pass:mapResponse.status()===200&&mapPayload.points.some(p=>(p.members||[]).some(m=>m.id===taxonomyBefore.place_id))});
const wrong=await page.request.get(origin+fixtures.paths.ru.map_api+filterQuery.replace('age=6','age=12'));
checks.push({check:'taxonomy_same_group_age_mismatch_excluded',pass:wrong.status()===200&&!(await wrong.json()).points.some(p=>(p.members||[]).some(m=>m.id===taxonomyBefore.place_id))});
await page.goto(origin+taxonomyApproved.urls.ru,{waitUntil:'networkidle'});
checks.push({check:'taxonomy_approved_activity_card',pass:(await page.locator('main').innerText()).includes('QA COMPLETION ART CLASS')});
return {rows,checks,events,observations,fixtures:'Initial Program/Org fixtures synthetic; standalone Activity created, submitted and approved through native owner/reviewer forms; public catalog, age/category/subcategory filter, map and Activity card checked after approval.'};
}
