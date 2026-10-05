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
const surfaces={create:'owner',edit:'owner',physical:'public',past:'public',cancelled:'public',rescheduled:'public',online:'public',landing:'public'};
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
 rows.push({screen,actor,width,lang,status:response.status(),issues,facts});if(lang==='ru'&&[390,1440].includes(width))await page.screenshot({path:'__QA26_EVIDENCE__/'+screen+'-'+width+'.png',fullPage:true});
}
phase='private_boundary';for(const kind of ['draft','pending','rejected','deleted']){await session('public');const r=await page.request.get(origin+fixtures.paths.ru[kind]);checks.push({check:'unpublished_closed',kind,status:r.status(),pass:r.status()===404})}
await session('venue');let r=await page.request.get(origin+fixtures.paths.ru.edit);checks.push({check:'venue_owner_no_event_rights',status:r.status(),pass:r.status()===403});
// Browser submits real rendered form controls and real CSRF; no forced validator bypass.
phase='online_create';await session('owner');await page.goto(origin+fixtures.paths.ru.create);await page.locator('[name="organizer_organization"]').selectOption(String(fixtures.ids.org));await page.locator('[name="event_format"]').selectOption('online');
checks.push({check:'online_address_not_required_visible',pass:await page.locator('[name="address"]').evaluate(e=>!e.getBoundingClientRect().width||(!e.required&&!e.closest('label').innerText.includes('*')))});
await page.locator('[name="name_az"]').fill('QA26 BROWSER ONLINE');await page.locator('[name="category"]').selectOption(fixtures.ids.category);await page.locator('[name="event_date"]').fill(fixtures.date);await page.locator('[name="start_time_input"]').fill('23:30');await page.locator('[name="end_date"]').fill(fixtures.end_date);await page.locator('[name="end_time_input"]').fill('01:30');
await page.locator('[name="form_action"][value="save_draft"]').click();await page.waitForLoadState('networkidle');
const saved=(await state()).created.find(e=>e.name==='QA26 BROWSER ONLINE');checks.push({check:'real_online_draft_save',pass:!!saved&&saved.status==='draft'&&saved.resolved==='resolved'&&!saved.has_place&&!saved.has_coords&&saved.address===''});
checks.push({check:'browser_Baku_save_uses_Baku_dates',pass:!!saved&&new Date(saved.start).getTime()===new Date(fixtures.start).getTime()&&new Date(saved.end).getTime()===new Date(fixtures.end).getTime()});
phase='edit_versions';await page.goto(origin+fixtures.paths.ru.edit);const old=await page.locator('form[data-event-form]').evaluate(e=>Object.fromEntries([...new FormData(e)].filter(([,value])=>typeof value==='string')));await page.locator('[name="name_az"]').fill('QA26 BROWSER EDIT');await page.locator('[name="form_action"][value="save_draft"]').click();await page.waitForLoadState('networkidle');checks.push({check:'actual_edit_save',pass:(await state()).draft.name==='QA26 BROWSER EDIT'});
old.form_action='save_draft';old.name_az='QA26 BROWSER STALE';r=await page.request.post(origin+fixtures.paths.ru.edit,{form:old});const staleBody=await r.text();checks.push({check:'stale_edit_denied',status:r.status(),pass:(await state()).draft.name==='QA26 BROWSER EDIT'&&/reload|перезаг|обнов|yenilə/i.test(staleBody)});
phase='csrf';r=await page.request.post(origin+fixtures.paths.ru.create,{form:{name_az:'QA26 BROWSER NO CSRF',form_action:'save_draft'}});checks.push({check:'csrf_enforced',status:r.status(),pass:r.status()===403&&!((await state()).created.some(e=>e.name==='QA26 BROWSER NO CSRF'))});
phase='organizer_error';await page.goto(origin+fixtures.paths.ru.create);await page.locator('[name="name_az"]').fill('QA26 BROWSER MISSING ORGANIZER');await page.locator('[name="form_action"][value="save_draft"]').click();await page.waitForLoadState('networkidle');checks.push({check:'missing_organizer_error',pass:await page.locator('.auth-errors').count()>0&&!((await state()).created.some(e=>e.name==='QA26 BROWSER MISSING ORGANIZER'))});await page.screenshot({path:'__QA26_EVIDENCE__/form-error-390.png',fullPage:true});
// The past archive reader must use captured district after a real Place movement.
phase='archive_snapshot';await session('public');const pastFacts=(await state()).past;const bakuDateParts=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Baku',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(pastFacts.start));const bakuDateValues=Object.fromEntries(bakuDateParts.map(p=>[p.type,p.value]));const pastDay=bakuDateValues.year+'-'+bakuDateValues.month+'-'+bakuDateValues.day;const archivePath=fixtures.paths.ru.landing+'?date='+pastDay+'&district='+encodeURIComponent(pastFacts.snapshot.district);r=await page.request.get(origin+archivePath,{maxRedirects:0});const archive=await r.text();checks.push({check:'past_archive_snapshot_district',status:r.status(),pass:r.status()===200&&archive.includes('QA26 PAST')&&!archive.includes('QA26 TODAY ADDRESS')});checks.push({check:'archive_query_no_canonical_stripping',pass:r.status()===200&&r.url()===origin+archivePath});
// Actual second Chromium context selects UTC independently of the Baku default.
phase='UTC_timezone';const utc=await page.context().browser().newContext({timezoneId:'UTC',viewport:{width:390,height:900}});
await utc.route('**/*',async route=>{const url=new URL(route.request().url());if(url.origin===origin)return route.continue();events.stubs.push(url.origin);if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});if(url.pathname==='/qa-font.ttf')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.ttf'})});return route.fulfill({status:200,contentType:url.pathname.endsWith('.css')?'text/css':'application/javascript',body:''})});
const utcPage=await utc.newPage();utcPage.on('pageerror',e=>events.errors.push({error:String(e),phase:'UTC_timezone'}));utcPage.on('requestfailed',r=>events.failed.push({url:r.url(),error:r.failure()?.errorText,phase:'UTC_timezone'}));
await utc.request.get(origin+'/qa26/session/owner?lang=en');await utcPage.goto(origin+fixtures.paths.en.create,{waitUntil:'networkidle'});checks.push({check:'actual_UTC_browser_context',pass:await utcPage.evaluate(()=>Intl.DateTimeFormat().resolvedOptions().timeZone)==='UTC'});
await utcPage.locator('[name="organizer_organization"]').selectOption(String(fixtures.ids.org));await utcPage.locator('[name="event_format"]').selectOption('online');await utcPage.locator('[name="name_az"]').fill('QA26 BROWSER UTC');await utcPage.locator('[name="category"]').selectOption(fixtures.ids.category);await utcPage.locator('[name="event_date"]').fill(fixtures.date);await utcPage.locator('[name="start_time_input"]').fill('23:30');await utcPage.locator('[name="end_date"]').fill(fixtures.end_date);await utcPage.locator('[name="end_time_input"]').fill('01:30');
await utcPage.locator('[name="end_time_input"]').dispatchEvent('change');const duration=await utcPage.locator('[data-owner-event-datetime-summary]').innerText();checks.push({check:'EN_duration_copy',pass:duration.includes('Duration')&&!/[чм]ин?\.|ч\./.test(duration)});
await utcPage.locator('[name="form_action"][value="save_draft"]').click();await utcPage.waitForLoadState('networkidle');const utcSaved=(await state()).created.find(e=>e.name==='QA26 BROWSER UTC');checks.push({check:'UTC_browser_persists_Baku_dates',pass:!!utcSaved&&new Date(utcSaved.start).getTime()===new Date(fixtures.start).getTime()&&new Date(utcSaved.end).getTime()===new Date(fixtures.end).getTime()});
phase='UTC_midnight';await utcPage.clock.install({time:new Date('2035-02-03T20:30:00Z')});await utcPage.goto(origin+fixtures.paths.en.create,{waitUntil:'networkidle'});
await utcPage.locator('[name="event_date"]').fill('2035-02-04');await utcPage.locator('[name="start_time_input"]').fill('00:00');await utcPage.locator('[name="end_date"]').fill('2035-02-04');await utcPage.locator('[name="end_time_input"]').fill('01:00');await utcPage.locator('[name="end_time_input"]').dispatchEvent('change');
const pastValidation=await utcPage.evaluate(()=>({date:document.querySelector('[name="event_date"]').validationMessage,start:document.querySelector('[name="start_time_input"]').validationMessage,timezone:Intl.DateTimeFormat().resolvedOptions().timeZone}));checks.push({check:'UTC_near_midnight_Baku_past_rejected',pass:pastValidation.timezone==='UTC'&&!!(pastValidation.date||pastValidation.start)});
await utcPage.screenshot({path:'__QA26_EVIDENCE__/UTC-midnight-past-rejected.png',fullPage:true});await utcPage.locator('[name="start_time_input"]').fill('00:45');await utcPage.locator('[name="start_time_input"]').dispatchEvent('change');checks.push({check:'UTC_near_midnight_Baku_future_valid',pass:await utcPage.evaluate(()=>document.querySelector('[name="event_date"]').validity.valid&&document.querySelector('[name="start_time_input"]').validity.valid&&document.querySelector('[name="end_time_input"]').validity.valid)});await utc.close();
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
