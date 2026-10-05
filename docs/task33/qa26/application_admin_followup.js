async(page)=>{
const origin='http://127.0.0.1:8786',includeAdmin=true,events={errors:[],failed:[],staticFailures:[],stubs:[],expectedErrors:[]};let phase='start',expectedStatus=0;
page.on('pageerror',e=>events.errors.push({error:String(e),url:page.url(),phase}));
page.on('console',m=>{if(m.type()==='error'){if(expectedStatus&&m.text().includes(String(expectedStatus)))events.expectedErrors.push(m.text());else events.errors.push({error:m.text(),phase})}});
page.on('requestfailed',r=>events.failed.push({url:r.url(),error:r.failure()?.errorText,phase}));
page.on('response',r=>{if(r.status()>=400&&r.url().includes('/static/'))events.staticFailures.push({url:r.url(),status:r.status(),phase})});
await page.context().route('**/*',async route=>{
 const url=new URL(route.request().url());if(url.origin===origin)return route.continue();events.stubs.push(url.origin);
 if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});
 if(url.pathname==='/qa-font.ttf')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.ttf'})});
 return route.fulfill({status:200,contentType:url.pathname.endsWith('.css')?'text/css':'application/javascript',body:''});
});
const fixtures=await(await page.request.get(origin+'/qa26/fixtures')).json(),rows=[],checks=[];
const runtimeCssResponse=await page.request.get(origin+'/static/admin/css/pages/kidsmap_admin_form_shell.css?v=8',{headers:{'Cache-Control':'no-cache'}});const runtimeCss=await runtimeCssResponse.text();
const session=async(role,lang='ru')=>page.request.get(origin+'/qa26/session/'+role+'?lang='+lang);
const state=async()=>(await(await page.request.get(origin+'/qa26/state')).json());
const surfaces={};
if(includeAdmin){surfaces.admin='reviewer';surfaces.admin_add='reviewer'}
const labels={az:{past:'Başa çatıb',cancelled:'Ləğv edilib',rescheduled:'Vaxtı dəyişdirilib'},ru:{past:'Завершено',cancelled:'Отменено',rescheduled:'Перенесено'},en:{past:'Ended',cancelled:'Cancelled',rescheduled:'Rescheduled'}};
for(const width of [320,360,390,768,1024,1280,1440])for(const lang of ['az','ru','en'])for(const [screen,actor] of Object.entries(surfaces)){
 phase=screen+'-'+lang+'-'+width;await page.setViewportSize({width,height:900});await session(actor,lang);
 const response=await page.goto(origin+fixtures.paths[lang][screen],{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
 const facts=await page.evaluate(()=>({lang:document.documentElement.lang,heading:document.querySelector('h1')?.innerText,body:document.body.innerText,viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,iconFontLoaded:[...document.querySelectorAll('[class*="material-symbols"],.fa,.fas')].filter(e=>e.getBoundingClientRect().width).every(e=>{const style=getComputedStyle(e),family=style.fontFamily.split(',')[0].trim();return document.fonts.check(style.fontWeight+' 24px '+family)}),csrf:[...document.querySelectorAll('form[method="post"]')].every(e=>!!e.querySelector('[name="csrfmiddlewaretoken"]')),controls:[...document.querySelectorAll('main input:not([type="hidden"]),main select,main textarea,main button')].filter(e=>e.getBoundingClientRect().width&&getComputedStyle(e).visibility!=='hidden').map(e=>({name:e.name,tag:e.tagName,label:!!(e.labels?.length||e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')||e.tagName==='BUTTON')})),schema:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>{try{return JSON.parse(e.textContent)}catch{return null}}),timers:document.querySelectorAll('[data-temporary-event-timer]').length}));
 const issues=[];if(response.status()!==200)issues.push('HTTP_'+response.status());if(facts.lang!==lang)issues.push('language');if(facts.scrollWidth>width+1)issues.push('overflow');if(!facts.csrf)issues.push('missing_csrf');if(!facts.iconFontLoaded)issues.push('icon_font_not_loaded');if(facts.controls.some(e=>!e.label))issues.push('unlabelled_controls');
 if(['past','cancelled','rescheduled'].includes(screen)){
  if(!facts.body.includes(labels[lang][screen]))issues.push('occurrence_label');if(['cancelled','rescheduled'].includes(screen)&&facts.timers)issues.push('misleading_countdown');
 }
 if(['physical','past','cancelled','rescheduled','online'].includes(screen)){
  const schema=facts.schema.find(s=>s?.['@type']==='Event');if(!schema)issues.push('event_schema_missing');
  else{
   if(screen==='online'){
    if(JSON.stringify(schema.location)!==JSON.stringify({'@type':'VirtualLocation'}))issues.push('invented_online_geography');if(facts.body.includes('QA26 HISTORIC ADDRESS')||facts.body.includes('QA26 TODAY ADDRESS'))issues.push('online_physical_address');if(schema.organizer?.['@type']!=='Person'||!facts.body.includes(schema.organizer?.name))issues.push('person_organizer_parity');
   }else{
    if(!facts.body.includes('QA26 HISTORIC ADDRESS')||facts.body.includes('QA26 TODAY ADDRESS'))issues.push('snapshot_drift');if(schema.location?.address?.streetAddress!=='QA26 HISTORIC ADDRESS')issues.push('snapshot_schema_parity');
    if(schema.location?.geo?.latitude!==40.4||schema.location?.geo?.longitude!==49.8)issues.push('snapshot_coords');if(schema.organizer?.name!=='QA26 ORGANIZER '+lang.toUpperCase()||!facts.body.includes(schema.organizer?.name))issues.push('organization_parity');
   }
   if(screen==='physical'){
    if(schema.aggregateRating?.reviewCount!==1||Number(schema.aggregateRating?.ratingValue)!==5||(schema.review||[]).length!==1)issues.push('typed_review_rating');if(!facts.body.includes('QA26 APPROVED REVIEW')||facts.body.includes('QA26 PENDING EDIT')||facts.body.includes('QA26 FOREIGN PENDING'))issues.push('typed_review_visibility');
    if(new Date(schema.startDate).getTime()!==new Date(fixtures.start).getTime()||new Date(schema.endDate).getTime()!==new Date(fixtures.end).getTime())issues.push('date_schema');if(!facts.body.includes('Asia/Baku'))issues.push('baku_timezone_missing');
   }
   if(screen==='cancelled'&&schema.eventStatus!=='https://schema.org/EventCancelled')issues.push('cancel_schema');if(screen==='rescheduled'&&(!facts.body.includes('Asia/Baku')||schema.previousStartDate!==fixtures.previous_start))issues.push('reschedule_history');
  }
 }
 if(['create','edit','admin','admin_add'].includes(screen)){
  for(const field of ['organizer_organization','organizer_specialist','event_format'])if(!await page.locator('[name="'+field+'"]').count())issues.push('missing_'+field);
  if(screen==='edit'&&!await page.locator('[name="expected_updated_at"]').inputValue())issues.push('missing_version');
  if(lang!=='ru'&&['Выберите одного организатора','Организация','Специалист','Формат'].some(t=>facts.body.includes(t)))issues.push('untranslated_new_copy');
 }
 const focusable=page.locator('main input:not([type="hidden"]):visible,main select:visible,main textarea:visible,main button:visible,main a[href]:visible,#content input:not([type="hidden"]):visible,#content select:visible').first();
 if(await focusable.count()){await focusable.focus();checks.push({check:'focus',screen,width,lang,pass:await focusable.evaluate(e=>document.activeElement===e)});await page.keyboard.press('Tab');checks.push({check:'tab',screen,width,lang,pass:await page.evaluate(()=>document.activeElement!==document.body&&scrollX===0)})}
 rows.push({screen,actor,width,lang,status:response.status(),issues,facts});if(lang==='ru'&&[320,360,390,1440].includes(width))await page.screenshot({path:'__QA26_EVIDENCE__/'+screen+'-'+width+'.png',fullPage:true});
}
if(includeAdmin){
 phase='admin_publish';await session('reviewer');await page.goto(origin+fixtures.paths.ru.admin);const form=page.locator('#event_form');
 const beforeAdminSave=(await state()).draft;const adminEnteredName='QA26 BROWSER ADMIN SAVE';await form.locator('[name="name"]').fill(adminEnteredName);
 // Date data and organizer were already supplied by actual owner edit service.
 await form.locator('[name="photo"]').setInputFiles({name:'qa26.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=','base64')});
 await form.locator('[name="_continue"]:visible').first().click();await page.waitForLoadState('networkidle');
 const adminSaved=(await state()).draft;const adminSaveErrors=await page.locator('.errorlist,.errornote').allTextContents();checks.push({check:'admin_actual_save_online',errors:adminSaveErrors,pass:adminSaved.version!==beforeAdminSave.version&&adminSaved.admin_name===adminEnteredName&&adminSaved.has_photo&&adminSaveErrors.length===0&&adminSaved.format==='online'&&!adminSaved.has_place&&!adminSaved.has_coords&&adminSaved.address===''});
 await page.goto(origin+fixtures.paths.ru.admin,{waitUntil:'networkidle'});const publish=page.locator('[name="_publish_event"]:visible').first();
 const publishCount=await publish.count();const publishDisabled=publishCount?await publish.isDisabled():null;checks.push({check:'admin_online_publish_enabled',count:publishCount,disabled:publishDisabled,pass:publishCount>0&&!publishDisabled});
 if(await publish.count()&&!await publish.isDisabled()){await publish.click();await page.waitForLoadState('networkidle')}
 const published=(await state()).draft;checks.push({check:'admin_actual_publication',pass:published.status==='published'&&JSON.stringify(published.snapshot)==='{}'});
 await page.screenshot({path:'__QA26_EVIDENCE__/admin-after-publication.png',fullPage:true});
 r=await page.request.get(origin+fixtures.paths.ru.draft);checks.push({check:'admin_publication_visible_actual_detail',pass:r.status()===200});
}
return {runtime:fixtures.runtime,runtimeCss,total:rows.length,passed:rows.filter(r=>!r.issues.length).length,checksPassed:checks.filter(c=>c.pass).length,checks,rows,events,externalTransport:'External CDN and integrations stubbed; cached Material Symbols font only. Actual local CSS/JS/Django routes.'};
}
