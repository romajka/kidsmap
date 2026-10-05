async(page)=>{
const origin='http://127.0.0.1:8788',includeAdmin=true,events={errors:[],failed:[],staticFailures:[],stubs:[],expectedErrors:[]};let phase='start',expectedStatus=0;
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
const fixtures=await(await page.request.get(origin+'/qa28/fixtures')).json(),rows=[],checks=[];
const runtimeCssResponse=await page.request.get(origin+'/static/admin/css/pages/kidsmap_admin_form_shell.css?v=8',{headers:{'Cache-Control':'no-cache'}});const runtimeCss=await runtimeCssResponse.text();
const runtimeAssets={};for(const name of ['css/events_landing.css','js/temporary_event_timer.js']){const response=await page.request.get(origin+'/static/'+name,{headers:{'Cache-Control':'no-cache'}});runtimeAssets['static/'+name]={status:response.status(),text:await response.text()}};
const session=async(role,lang='ru')=>page.request.get(origin+'/qa28/session/'+role+'?lang='+lang);
const state=async()=>(await(await page.request.get(origin+'/qa28/state')).json());
const surfaces={create:'owner',edit:'owner',physical:'public',past:'public',cancelled:'public',rescheduled:'public',online:'public',calendar:'public',list:'public',zero:'public',archive:'public'};
if(includeAdmin){surfaces.admin='reviewer';surfaces.admin_add='reviewer'}
const labels={az:{past:'Başa çatıb',cancelled:'Ləğv edilib',rescheduled:'Vaxtı dəyişdirilib'},ru:{past:'Завершено',cancelled:'Отменено',rescheduled:'Перенесено'},en:{past:'Ended',cancelled:'Cancelled',rescheduled:'Rescheduled'}};
for(const width of [320,360,390,768,1024,1280,1440])for(const lang of ['az','ru','en'])for(const [screen,actor] of Object.entries(surfaces)){
 phase=screen+'-'+lang+'-'+width;await page.setViewportSize({width,height:900});await session(actor,lang);
 let target=fixtures.paths[lang][screen];
 if(['calendar','list','zero','archive'].includes(screen)){
  const query=new URLSearchParams({view:screen==='list'?'list':'calendar',month:screen==='archive'?fixtures.calendar.archive_month:fixtures.calendar.month,q:screen==='zero'?'QA27 NO SUCH EVENT':screen==='archive'?'QA27 ARCHIVE':'QA27 CALENDAR',category:fixtures.ids.category,age_from:'7',age_to:'10'});
  if(screen!=='list')query.set('date',screen==='archive'?fixtures.calendar.archive_date:fixtures.calendar.date);
  target=fixtures.paths[lang].landing+'?'+query;
 }
 const response=await page.goto(origin+target,{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
 if(['calendar','zero','archive'].includes(screen)||(lang==='ru'&&[390,1440].includes(width)))await page.waitForFunction(()=>[...document.querySelectorAll('.panel.reveal-item')].every(e=>getComputedStyle(e).opacity==='1'),null,{timeout:7000});
 const facts=await page.evaluate(()=>({lang:document.documentElement.lang,heading:document.querySelector('h1')?.innerText,body:document.body.innerText,viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,iconFontLoaded:[...document.querySelectorAll('[class*="material-symbols"],.fa,.fas')].filter(e=>e.getBoundingClientRect().width).every(e=>{const style=getComputedStyle(e),family=style.fontFamily.split(',')[0].trim();return document.fonts.check(style.fontWeight+' 24px '+family)}),csrf:[...document.querySelectorAll('form[method="post"]')].every(e=>!!e.querySelector('[name="csrfmiddlewaretoken"]')),controls:[...document.querySelectorAll('main input:not([type="hidden"]),main select,main textarea,main button')].filter(e=>e.getBoundingClientRect().width&&getComputedStyle(e).visibility!=='hidden').map(e=>({name:e.name,tag:e.tagName,label:!!(e.labels?.length||e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')||e.tagName==='BUTTON')})),schema:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>{try{return JSON.parse(e.textContent)}catch{return null}}),timers:document.querySelectorAll('[data-temporary-event-timer]').length}));
 const issues=[];if(response.status()!==200)issues.push('HTTP_'+response.status());if(facts.lang!==lang)issues.push('language');if(facts.scrollWidth>width+1)issues.push('overflow');if(!facts.csrf)issues.push('missing_csrf');if(!facts.iconFontLoaded)issues.push('icon_font_not_loaded');if(facts.controls.some(e=>!e.label))issues.push('unlabelled_controls');
 if(['calendar','list','zero','archive'].includes(screen)){
  facts.heroStat=await page.locator('.events-hero__stat').evaluate(e=>({right:e.getBoundingClientRect().right,scroll:e.scrollWidth,client:e.clientWidth,strongRight:e.querySelector('strong').getBoundingClientRect().right}));
  if(facts.heroStat.right>width+1||facts.heroStat.scroll>facts.heroStat.client+1||facts.heroStat.strongRight>facts.heroStat.right+1)issues.push('hero_stat_clipped');
 }
 if(['calendar','zero','archive'].includes(screen)){
  if(await page.locator('#events-calendar').count()!==1)issues.push('calendar_missing');
  const calendarIDs=await page.locator('.events-calendar-grid [data-calendar-event-id]').evaluateAll(nodes=>[...new Set(nodes.map(e=>Number(e.dataset.calendarEventId||e.dataset.eventId)))].sort((a,b)=>a-b));
  const expected=screen==='zero'?[]:screen==='archive'?[fixtures.calendar.archive_id]:fixtures.calendar.matching_ids;
  if(JSON.stringify(calendarIDs)!==JSON.stringify([...expected].sort((a,b)=>a-b)))issues.push('calendar_membership');
  const selectedIDs=await page.locator('#events-day-list [data-event-id]').evaluateAll(nodes=>[...new Set(nodes.map(e=>Number(e.dataset.calendarEventId||e.dataset.eventId)))].sort((a,b)=>a-b));
  const expectedDay=screen==='zero'?[]:screen==='archive'?[fixtures.calendar.archive_id]:fixtures.calendar.day_ids[fixtures.calendar.date];
  if(JSON.stringify(selectedIDs)!==JSON.stringify([...expectedDay].sort((a,b)=>a-b)))issues.push('selected_day_membership');
  if(width<=390&&(!await page.locator('#events-day-list').isVisible()||await page.locator('.events-calendar-entries:visible').count()>0))issues.push('mobile_day_layout');
  if(width>=768&&!await page.locator('.events-calendar-grid').isVisible())issues.push('desktop_month_hidden');
  facts.calendarIDs=calendarIDs;facts.selectedIDs=selectedIDs;
 }
 if(screen==='list'){
  const listIDs=await page.locator('#events-feed [data-event-id]').evaluateAll(nodes=>[...new Set(nodes.map(e=>Number(e.dataset.calendarEventId||e.dataset.eventId)))]);
  if(listIDs.length!==12)issues.push('list_page_not_twelve');
  if(!listIDs.every(id=>fixtures.calendar.matching_ids.includes(id)))issues.push('list_foreign_membership');
  facts.listIDs=listIDs;
 }
 if(['calendar','list'].includes(screen)){
  const badge=page.locator('[data-event-language="'+fixtures.calendar.labels.calendar01+'"]');if(lang==='az'?(await badge.count()>0):(await badge.count()===0))issues.push('AZ_fallback_marker');
 }
 if(['past','cancelled','rescheduled'].includes(screen)){
  if(!facts.body.includes(labels[lang][screen]))issues.push('occurrence_label');if(['cancelled','rescheduled'].includes(screen)&&facts.timers)issues.push('misleading_countdown');
 }
 if(['physical','past','cancelled','rescheduled','online'].includes(screen)){
  facts.head=await page.evaluate(()=>({title:document.title,canonical:document.querySelector('link[rel="canonical"]')?.href,alternates:[...document.querySelectorAll('link[rel="alternate"][hreflang]')].map(e=>e.hreflang)}));
  if(!facts.head.title||!facts.head.canonical||new URL(facts.head.canonical).hostname!=='kidsmap.az')issues.push('event_seo_head');
  if(!['az','ru','en'].every(l=>facts.head.alternates.includes(l)))issues.push('event_hreflang');
  if(JSON.stringify(facts.head).includes('QA27 PENDING EDIT')||JSON.stringify(facts.head).includes('QA27 FOREIGN PENDING'))issues.push('private_seo_metadata');
  if(!await page.locator('.event-detail-contact a[href="tel:+994501234567"]').count())issues.push('actual_event_contact_missing');
  const schema=facts.schema.find(s=>s?.['@type']==='Event');if(!schema)issues.push('event_schema_missing');
  else{
   if(screen==='online'){
    if(JSON.stringify(schema.location)!==JSON.stringify({'@type':'VirtualLocation'}))issues.push('invented_online_geography');if(facts.body.includes('QA27 HISTORIC ADDRESS')||facts.body.includes('QA27 TODAY ADDRESS'))issues.push('online_physical_address');if(schema.organizer?.['@type']!=='Person'||!facts.body.includes(schema.organizer?.name))issues.push('person_organizer_parity');
   }else{
    if(!facts.body.includes('QA27 HISTORIC ADDRESS')||facts.body.includes('QA27 TODAY ADDRESS'))issues.push('snapshot_drift');if(schema.location?.address?.streetAddress!=='QA27 HISTORIC ADDRESS')issues.push('snapshot_schema_parity');
    if(schema.location?.geo?.latitude!==40.4||schema.location?.geo?.longitude!==49.8)issues.push('snapshot_coords');if(schema.organizer?.name!=='QA27 ORGANIZER '+lang.toUpperCase()||!facts.body.includes(schema.organizer?.name))issues.push('organization_parity');
   }
   if(screen==='physical'){
    if(schema.aggregateRating?.reviewCount!==1||Number(schema.aggregateRating?.ratingValue)!==5||(schema.review||[]).length!==1)issues.push('typed_review_rating');if(!facts.body.includes('QA27 APPROVED REVIEW')||facts.body.includes('QA27 PENDING EDIT')||facts.body.includes('QA27 FOREIGN PENDING'))issues.push('typed_review_visibility');
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
 rows.push({screen,actor,width,lang,status:response.status(),issues,facts});if(lang==='ru'&&[390,1440].includes(width))await page.screenshot({path:'__QA28_EVIDENCE__/'+screen+'-'+width+'.png',fullPage:true});
 if(screen==='calendar'&&lang==='ru'&&[320,390,768,1440].includes(width))await page.locator('.events-calendar-grid').screenshot({path:'__QA28_EVIDENCE__/calendar-grid-'+width+'.png'});
}
const sameIDs=(a,b)=>JSON.stringify([...new Set(a)].sort((x,y)=>x-y))===JSON.stringify([...new Set(b)].sort((x,y)=>x-y));
const cardIDs=async(selector)=>page.locator(selector+' [data-event-id],'+selector+' [data-calendar-event-id]').evaluateAll(nodes=>nodes.map(e=>Number(e.dataset.calendarEventId||e.dataset.eventId)));
for(const width of [320,360,390,768,1024,1280,1440])for(const lang of ['az','ru','en']){
 phase='calendar_interactions-'+lang+'-'+width;await session('public',lang);await page.setViewportSize({width,height:900});
 const filters={q:'QA27 CALENDAR',category:fixtures.ids.category,age_from:'7',age_to:'10'};
 const startURL=origin+fixtures.paths[lang].landing+'?'+new URLSearchParams({...filters,view:'calendar',month:fixtures.calendar.month,date:fixtures.calendar.date});
 await page.goto(startURL,{waitUntil:'networkidle'});
 const listMode=page.locator('[data-events-mode="list"]').first();const listHref=new URL(await listMode.getAttribute('href'),page.url());
 checks.push({check:'mode_keeps_filters_whole_month',lang,width,pass:Object.entries(filters).every(([k,v])=>listHref.searchParams.get(k)===v)&&listHref.searchParams.get('month')===fixtures.calendar.month&&!listHref.searchParams.has('date')&&!listHref.searchParams.has('page')});
 await listMode.focus();await Promise.all([page.waitForURL(listHref.href,{waitUntil:'networkidle'}),page.keyboard.press('Enter')]);const firstIDs=await cardIDs('#events-feed');
 const secondURL=new URL(page.url());secondURL.searchParams.set('page','2');const second=await page.request.get(secondURL.href,{maxRedirects:0});const secondHTML=await second.text();const secondIDs=[...secondHTML.matchAll(/data-event-id=["'](\d+)["']/g)].map(match=>Number(match[1]));
 checks.push({check:'same_month_calendar_paginated_list',lang,width,pass:firstIDs.length===12&&second.status()===200&&sameIDs([...firstIDs,...secondIDs],fixtures.calendar.matching_ids)});
 await page.goBack({waitUntil:'networkidle'});checks.push({check:'calendar_back_keeps_selection',lang,width,pass:new URL(page.url()).searchParams.get('date')===fixtures.calendar.date&&sameIDs(await cardIDs('.events-calendar-grid'),fixtures.calendar.matching_ids)});
 await page.goForward({waitUntil:'networkidle'});checks.push({check:'calendar_forward_list',lang,width,pass:new URL(page.url()).searchParams.get('view')==='list'&&(await cardIDs('#events-feed')).length===12});
 await page.goto(startURL,{waitUntil:'networkidle'});await page.reload({waitUntil:'networkidle'});checks.push({check:'calendar_reload_month_and_day',lang,width,pass:sameIDs(await cardIDs('.events-calendar-grid'),fixtures.calendar.matching_ids)&&sameIDs(await cardIDs('#events-day-list'),fixtures.calendar.day_ids[fixtures.calendar.date])});
 const nextDay=fixtures.calendar.multiday_dates[2];const dayLink=page.locator('.events-calendar-day[data-date="'+nextDay+'"]:visible').first();
 await dayLink.focus();const href=await dayLink.getAttribute('href');checks.push({check:'native_day_keyboard_focus',lang,width,pass:!!href&&await dayLink.evaluate(e=>document.activeElement===e)});await Promise.all([page.waitForURL(new URL(href,page.url()).href,{waitUntil:'networkidle'}),page.keyboard.press('Enter')]);
 checks.push({check:'selected_mobile_day_and_multiday',lang,width,pass:new URL(page.url()).searchParams.get('date')===nextDay&&sameIDs(await cardIDs('#events-day-list'),fixtures.calendar.day_ids[nextDay])});
 const dayBadge=page.locator('#events-day-list [data-event-language="'+fixtures.calendar.labels.calendar01+'"]');checks.push({check:'selected_day_AZ_fallback_marker',lang,width,pass:lang==='az'?await dayBadge.count()===0:await dayBadge.count()===1&&await dayBadge.isVisible()&&await dayBadge.getAttribute('lang')==='az'&&!!await dayBadge.getAttribute('aria-label')});
 const quick=page.locator('[data-events-quick]').first();const quickURL=new URL(await quick.getAttribute('href'),page.url());checks.push({check:'quick_chip_keeps_all_filters',lang,width,pass:Object.entries(filters).every(([k,v])=>quickURL.searchParams.get(k)===v)&&quickURL.searchParams.get('date_filter')===await quick.getAttribute('data-events-quick')&&!quickURL.searchParams.has('page')});
 const quickResponse=await page.request.get(quickURL.href,{maxRedirects:0});checks.push({check:'quick_period_full_HTTP',lang,width,pass:quickResponse.status()===200&&!(await quickResponse.text()).includes('data-event-id=')});
 const details=page.locator('#events-filters');if(!await details.evaluate(e=>e.open))await details.locator('summary').click();
 const form=details.locator('form');await form.locator('[name="format"]').selectOption('physical');await Promise.all([page.waitForURL(url=>url.searchParams.get('format')==='physical',{waitUntil:'networkidle'}),form.locator('button[type="submit"]').click()]);checks.push({check:'physical_filter_same_month',lang,width,pass:new URL(page.url()).searchParams.get('format')==='physical'&&sameIDs(await cardIDs('.events-calendar-grid'),fixtures.calendar.physical_ids)});
 const currentIDs=await cardIDs('.events-calendar-grid');checks.push({check:'cancel_reschedule_same_event_ids',lang,width,pass:currentIDs.includes(fixtures.calendar.labels.calendar_cancelled)&&currentIDs.includes(fixtures.calendar.labels.calendar_rescheduled)});
 const freeURL=new URL(await page.locator('[data-events-quick="free"]').getAttribute('href'),page.url());checks.push({check:'free_chip_retains_period_format_filters',lang,width,pass:Object.entries(filters).every(([k,v])=>freeURL.searchParams.get(k)===v)&&freeURL.searchParams.get('format')==='physical'&&freeURL.searchParams.get('free')==='1'&&freeURL.searchParams.get('month')===fixtures.calendar.month&&freeURL.searchParams.get('date')===nextDay});
 const nextMonth=page.locator('[data-events-month="next"]');const monthHref=new URL(await nextMonth.getAttribute('href'),page.url());checks.push({check:'month_keeps_all_filters',lang,width,pass:Object.entries(filters).every(([k,v])=>monthHref.searchParams.get(k)===v)&&monthHref.searchParams.get('format')==='physical'&&monthHref.searchParams.get('view')==='calendar'&&monthHref.searchParams.get('month')!==fixtures.calendar.month&&!monthHref.searchParams.has('page')});
 await Promise.all([page.waitForURL(monthHref.href,{waitUntil:'networkidle'}),nextMonth.click()]);checks.push({check:'next_month_zero_state_actual',lang,width,pass:(await cardIDs('.events-calendar-grid')).length===0&&await page.locator('#events-day-list .events-empty').count()>0});await page.goBack({waitUntil:'networkidle'});checks.push({check:'month_back_keeps_physical_filter',lang,width,pass:new URL(page.url()).searchParams.get('format')==='physical'&&sameIDs(await cardIDs('.events-calendar-grid'),fixtures.calendar.physical_ids)});
}
for(const lang of ['az','ru','en'])for(const width of [390,1440]){
 phase='list_period_form-'+lang+'-'+width;await session('public',lang);await page.setViewportSize({width,height:900});
 await page.goto(origin+fixtures.paths[lang].landing+'?'+new URLSearchParams({view:'list',month:fixtures.calendar.month,q:'QA27 CALENDAR',category:fixtures.ids.category,age_from:'7',age_to:'10'}),{waitUntil:'networkidle'});
 const period=page.locator('.events-period');await period.locator('summary').click();const form=period.locator('form');await form.locator('[name="date_from"]').fill(fixtures.calendar.date);await form.locator('[name="date_to"]').fill(fixtures.calendar.date);await Promise.all([page.waitForURL(url=>url.searchParams.get('date_from')===fixtures.calendar.date,{waitUntil:'networkidle'}),form.locator('button[type="submit"]').click()]);
 const url=new URL(page.url());checks.push({check:'actual_list_period_form',lang,width,pass:url.searchParams.get('date_from')===fixtures.calendar.date&&url.searchParams.get('date_to')===fixtures.calendar.date&&!url.searchParams.has('month')&&!url.searchParams.has('date')&&sameIDs(await cardIDs('#events-feed'),fixtures.calendar.day_ids[fixtures.calendar.date])});
 checks.push({check:'list_period_keeps_filter_values',lang,width,pass:url.searchParams.get('q')==='QA27 CALENDAR'&&url.searchParams.get('category')===fixtures.ids.category&&url.searchParams.get('age_from')==='7'&&url.searchParams.get('age_to')==='10'});
}
phase='multiday_exclusive_end';await session('public');
for(const [index,date]of fixtures.calendar.multiday_dates.entries()){
 const path=fixtures.paths.ru.landing+'?'+new URLSearchParams({view:'calendar',month:fixtures.calendar.month,date,q:'QA27 CALENDAR MULTI DAY'});await page.goto(origin+path,{waitUntil:'networkidle'});checks.push({check:'multiday_same_id_included',date,pass:sameIDs(await cardIDs('#events-day-list'),[fixtures.calendar.labels.calendar_multi])});
}
const excludedDay=String(Number(fixtures.calendar.date.slice(-2))+2).padStart(2,'0');const excludedDate=fixtures.calendar.date.slice(0,8)+excludedDay;await page.goto(origin+fixtures.paths.ru.landing+'?'+new URLSearchParams({view:'calendar',month:fixtures.calendar.month,date:excludedDate,q:'QA27 CALENDAR MULTI DAY'}),{waitUntil:'networkidle'});checks.push({check:'multiday_end_exclusive',pass:(await cardIDs('#events-day-list')).length===0});
phase='online_calendar_filter';await page.goto(origin+fixtures.paths.ru.landing+'?'+new URLSearchParams({view:'calendar',month:fixtures.calendar.month,date:fixtures.calendar.date,q:'QA27 CALENDAR',format:'online'}),{waitUntil:'networkidle'});checks.push({check:'online_calendar_no_fake_venue',pass:sameIDs(await cardIDs('.events-calendar-grid'),[fixtures.calendar.labels.calendar_online])&&!await page.locator('#events-day-list').innerText().then(text=>text.includes('QA27 HISTORIC ADDRESS'))});
phase='cohort_off';await page.request.post(origin+'/qa28/cohort?token='+fixtures.token+'&enabled=0');let off=await page.request.get(origin+fixtures.paths.ru.landing+'?view=calendar');checks.push({check:'feature_off_route_closed',status:off.status(),pass:off.status()===410&&!(await off.text()).includes('id="events-calendar"')});await page.request.post(origin+'/qa28/cohort?token='+fixtures.token+'&enabled=1');checks.push({check:'feature_on_restored_local_only',pass:(await page.request.get(origin+fixtures.paths.ru.landing)).status()===200});
phase='private_boundary';for(const kind of ['draft','pending','rejected','deleted']){await session('public');const r=await page.request.get(origin+fixtures.paths.ru[kind]);checks.push({check:'unpublished_closed',kind,status:r.status(),pass:r.status()===404})}
await session('venue');let r=await page.request.get(origin+fixtures.paths.ru.edit);checks.push({check:'venue_owner_no_event_rights',status:r.status(),pass:r.status()===403});
// Browser submits real rendered form controls and real CSRF; no forced validator bypass.
phase='online_create';await session('owner');await page.goto(origin+fixtures.paths.ru.create);await page.locator('[name="organizer_organization"]').selectOption(String(fixtures.ids.org));await page.locator('[name="event_format"]').selectOption('online');
checks.push({check:'online_address_not_required_visible',pass:await page.locator('[name="address"]').evaluate(e=>!e.getBoundingClientRect().width||(!e.required&&!e.closest('label').innerText.includes('*')))});
await page.locator('[name="name_az"]').fill('QA27 BROWSER ONLINE');await page.locator('[name="category"]').selectOption(fixtures.ids.category);await page.locator('[name="event_date"]').fill(fixtures.date);await page.locator('[name="start_time_input"]').fill('23:30');await page.locator('[name="end_date"]').fill(fixtures.end_date);await page.locator('[name="end_time_input"]').fill('01:30');
await page.locator('[name="form_action"][value="save_draft"]').click();await page.waitForLoadState('networkidle');
const saved=(await state()).created.find(e=>e.name==='QA27 BROWSER ONLINE');checks.push({check:'real_online_draft_save',pass:!!saved&&saved.status==='draft'&&saved.resolved==='resolved'&&!saved.has_place&&!saved.has_coords&&saved.address===''});
checks.push({check:'browser_Baku_save_uses_Baku_dates',pass:!!saved&&new Date(saved.start).getTime()===new Date(fixtures.start).getTime()&&new Date(saved.end).getTime()===new Date(fixtures.end).getTime()});
phase='edit_versions';await page.goto(origin+fixtures.paths.ru.edit);const old=await page.locator('form[data-event-form]').evaluate(e=>Object.fromEntries([...new FormData(e)].filter(([,value])=>typeof value==='string')));await page.locator('[name="name_az"]').fill('QA27 BROWSER EDIT');await page.locator('[name="form_action"][value="save_draft"]').click();await page.waitForLoadState('networkidle');checks.push({check:'actual_edit_save',pass:(await state()).draft.name==='QA27 BROWSER EDIT'});
old.form_action='save_draft';old.name_az='QA27 BROWSER STALE';r=await page.request.post(origin+fixtures.paths.ru.edit,{form:old});const staleBody=await r.text();checks.push({check:'stale_edit_denied',status:r.status(),pass:(await state()).draft.name==='QA27 BROWSER EDIT'&&/reload|перезаг|обнов|yenilə/i.test(staleBody)});
phase='owner_previously_approved_precision';await page.goto(origin+fixtures.paths.ru.owner_precision_edit,{waitUntil:'networkidle'});
const ownerPrecisionBefore=(await state()).owner_precision;
await page.locator('[name="name_az"]').fill('QA28 OWNER PRECISION ORDINARY EDIT');
await Promise.all([page.waitForResponse(response=>response.request().method()==='POST'&&response.url().includes(fixtures.paths.ru.owner_precision_edit)),page.locator('[name="form_action"][value="save_draft"]').click()]);await page.waitForLoadState('networkidle');
const ownerPrecisionAfter=(await state()).owner_precision;
checks.push({check:'owner_previously_approved_draft_ordinary_edit',pass:ownerPrecisionAfter.name==='QA28 OWNER PRECISION ORDINARY EDIT'&&ownerPrecisionAfter.version!==ownerPrecisionBefore.version&&ownerPrecisionAfter.status==='draft'});
checks.push({check:'owner_previously_approved_exact_precision_preserved',pass:ownerPrecisionBefore.start===ownerPrecisionAfter.start&&ownerPrecisionBefore.end===ownerPrecisionAfter.end&&ownerPrecisionBefore.start.includes('.123456')&&ownerPrecisionBefore.end.includes('.654321')});
await page.screenshot({path:'__QA28_EVIDENCE__/owner-precision-after-edit.png',fullPage:false});
phase='csrf';r=await page.request.post(origin+fixtures.paths.ru.create,{form:{name_az:'QA27 BROWSER NO CSRF',form_action:'save_draft'}});checks.push({check:'csrf_enforced',status:r.status(),pass:r.status()===403&&!((await state()).created.some(e=>e.name==='QA27 BROWSER NO CSRF'))});
phase='organizer_error';await page.goto(origin+fixtures.paths.ru.create);await page.locator('[name="name_az"]').fill('QA27 BROWSER MISSING ORGANIZER');await page.locator('[name="form_action"][value="save_draft"]').click();await page.waitForLoadState('networkidle');checks.push({check:'missing_organizer_error',pass:await page.locator('.auth-errors').count()>0&&!((await state()).created.some(e=>e.name==='QA27 BROWSER MISSING ORGANIZER'))});await page.screenshot({path:'__QA28_EVIDENCE__/form-error-390.png',fullPage:true});
// The past archive reader must use captured district after a real Place movement.
phase='archive_snapshot';await session('public');const pastFacts=(await state()).past;const bakuDateParts=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Baku',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(pastFacts.start));const bakuDateValues=Object.fromEntries(bakuDateParts.map(p=>[p.type,p.value]));const pastDay=bakuDateValues.year+'-'+bakuDateValues.month+'-'+bakuDateValues.day;const archivePath=fixtures.paths.ru.landing+'?date='+pastDay+'&district='+encodeURIComponent(pastFacts.snapshot.district);r=await page.request.get(origin+archivePath,{maxRedirects:0});const archive=await r.text();checks.push({check:'past_archive_snapshot_district',status:r.status(),pass:r.status()===200&&archive.includes('QA27 PAST')&&!archive.includes('QA27 TODAY ADDRESS')});checks.push({check:'archive_query_no_canonical_stripping',pass:r.status()===200&&r.url()===origin+archivePath});
// Actual second Chromium context selects UTC independently of the Baku default.
phase='UTC_timezone';const utc=await page.context().browser().newContext({timezoneId:'UTC',viewport:{width:390,height:900}});
await utc.route('**/*',async route=>{const url=new URL(route.request().url());if(url.origin===origin)return route.continue();events.stubs.push(url.origin);if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});if(url.pathname==='/qa-font.ttf')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.ttf'})});return route.fulfill({status:200,contentType:url.pathname.endsWith('.css')?'text/css':'application/javascript',body:''})});
const utcPage=await utc.newPage();utcPage.on('pageerror',e=>events.errors.push({error:String(e),phase:'UTC_timezone'}));utcPage.on('requestfailed',r=>events.failed.push({url:r.url(),error:r.failure()?.errorText,phase:'UTC_timezone'}));
await utc.request.get(origin+'/qa28/session/owner?lang=en');await utcPage.goto(origin+fixtures.paths.en.create,{waitUntil:'networkidle'});checks.push({check:'actual_UTC_browser_context',pass:await utcPage.evaluate(()=>Intl.DateTimeFormat().resolvedOptions().timeZone)==='UTC'});
await utcPage.locator('[name="organizer_organization"]').selectOption(String(fixtures.ids.org));await utcPage.locator('[name="event_format"]').selectOption('online');await utcPage.locator('[name="name_az"]').fill('QA27 BROWSER UTC');await utcPage.locator('[name="category"]').selectOption(fixtures.ids.category);await utcPage.locator('[name="event_date"]').fill(fixtures.date);await utcPage.locator('[name="start_time_input"]').fill('23:30');await utcPage.locator('[name="end_date"]').fill(fixtures.end_date);await utcPage.locator('[name="end_time_input"]').fill('01:30');
await utcPage.locator('[name="end_time_input"]').dispatchEvent('change');const duration=await utcPage.locator('[data-owner-event-datetime-summary]').innerText();checks.push({check:'EN_duration_copy',pass:duration.includes('Duration')&&!/[чм]ин?\.|ч\./.test(duration)});
await utcPage.locator('[name="form_action"][value="save_draft"]').click();await utcPage.waitForLoadState('networkidle');const utcSaved=(await state()).created.find(e=>e.name==='QA27 BROWSER UTC');checks.push({check:'UTC_browser_persists_Baku_dates',pass:!!utcSaved&&new Date(utcSaved.start).getTime()===new Date(fixtures.start).getTime()&&new Date(utcSaved.end).getTime()===new Date(fixtures.end).getTime()});
phase='UTC_midnight';await utcPage.clock.install({time:new Date('2035-02-03T20:30:00Z')});await utcPage.goto(origin+fixtures.paths.en.create,{waitUntil:'networkidle'});
await utcPage.locator('[name="event_date"]').fill('2035-02-04');await utcPage.locator('[name="start_time_input"]').fill('00:00');await utcPage.locator('[name="end_date"]').fill('2035-02-04');await utcPage.locator('[name="end_time_input"]').fill('01:00');await utcPage.locator('[name="end_time_input"]').dispatchEvent('change');
const pastValidation=await utcPage.evaluate(()=>({date:document.querySelector('[name="event_date"]').validationMessage,start:document.querySelector('[name="start_time_input"]').validationMessage,timezone:Intl.DateTimeFormat().resolvedOptions().timeZone}));checks.push({check:'UTC_near_midnight_Baku_past_rejected',pass:pastValidation.timezone==='UTC'&&!!(pastValidation.date||pastValidation.start)});
await utcPage.screenshot({path:'__QA28_EVIDENCE__/UTC-midnight-past-rejected.png',fullPage:true});await utcPage.locator('[name="start_time_input"]').fill('00:45');await utcPage.locator('[name="start_time_input"]').dispatchEvent('change');checks.push({check:'UTC_near_midnight_Baku_future_valid',pass:await utcPage.evaluate(()=>document.querySelector('[name="event_date"]').validity.valid&&document.querySelector('[name="start_time_input"]').validity.valid&&document.querySelector('[name="end_time_input"]').validity.valid)});await utc.close();
if(includeAdmin){
 phase='admin_publish';await session('reviewer');await page.goto(origin+fixtures.paths.ru.admin);const form=page.locator('#event_form');
 const beforeAdminSave=(await state()).draft;const adminEnteredName='QA27 BROWSER ADMIN SAVE';await form.locator('[name="name"]').fill(adminEnteredName);
 // Date data and organizer were already supplied by actual owner edit service.
 await form.locator('[name="photo"]').setInputFiles({name:'qa27.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=','base64')});
 await form.locator('[name="_continue"]:visible').first().click();await page.waitForLoadState('networkidle');
 const adminSaved=(await state()).draft;const adminSaveErrors=await page.locator('.errorlist,.errornote').allTextContents();checks.push({check:'admin_actual_save_online',errors:adminSaveErrors,pass:adminSaved.version!==beforeAdminSave.version&&adminSaved.admin_name===adminEnteredName&&adminSaved.has_photo&&adminSaveErrors.length===0&&adminSaved.format==='online'&&!adminSaved.has_place&&!adminSaved.has_coords&&adminSaved.address===''});
 await page.goto(origin+fixtures.paths.ru.admin,{waitUntil:'networkidle'});const publish=page.locator('[name="_publish_event"]:visible').first();
 const publishCount=await publish.count();const publishDisabled=publishCount?await publish.isDisabled():null;checks.push({check:'admin_online_publish_enabled',count:publishCount,disabled:publishDisabled,pass:publishCount>0&&!publishDisabled});
 if(await publish.count()&&!await publish.isDisabled()){await publish.click();await page.waitForLoadState('networkidle')}
 const published=(await state()).draft;checks.push({check:'admin_actual_publication',pass:published.status==='published'&&JSON.stringify(published.snapshot)==='{}'});
 await page.screenshot({path:'__QA28_EVIDENCE__/admin-after-publication.png',fullPage:true});
 r=await page.request.get(origin+fixtures.paths.ru.draft);checks.push({check:'admin_publication_visible_actual_detail',pass:r.status()===200});
}
phase='published_admin_precision';await session('reviewer');await page.goto(origin+fixtures.paths.ru.precision_admin,{waitUntil:'networkidle'});
const precisionBefore=(await state()).precision,precisionForm=page.locator('#event_form');
await precisionForm.locator('[name="name"]').fill('QA28 PRECISION ORDINARY EDIT');
await precisionForm.locator('[name="photo"]').setInputFiles({name:'qa28-precision.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=','base64')});
await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/admin/catalog/event/')),precisionForm.locator('[name="_continue"]:visible').first().click()]);await page.waitForLoadState('networkidle');
const precisionAfter=(await state()).precision,precisionErrors=await page.locator('.errorlist,.errornote').allTextContents();
checks.push({check:'published_admin_ordinary_edit_precision',errors:precisionErrors,pass:precisionAfter.admin_name==='QA28 PRECISION ORDINARY EDIT'&&precisionAfter.version!==precisionBefore.version&&precisionAfter.status==='published'&&precisionErrors.length===0});
checks.push({check:'published_admin_exact_seconds_microseconds_preserved',pass:precisionBefore.start===precisionAfter.start&&precisionBefore.end===precisionAfter.end&&precisionBefore.start.includes('.123456')&&precisionBefore.end.includes('.654321')});
await page.screenshot({path:'__QA28_EVIDENCE__/admin-precision-after-edit.png',fullPage:false});
return {runtime:fixtures.runtime,runtimeCss,runtimeAssets,total:rows.length,passed:rows.filter(r=>!r.issues.length).length,checksPassed:checks.filter(c=>c.pass).length,checks,rows,events,externalTransport:'External CDN and integrations stubbed; cached Material Symbols font only. Actual local CSS/JS/Django routes.'};
}
