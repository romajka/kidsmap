async(page)=>{
const origin='http://127.0.0.1:8785',events={errors:[],failed:[],staticFailures:[],stubs:[],expectedErrors:[]};let expectedResponseFailure=false,phase='start';
page.on('pageerror',e=>events.errors.push({error:String(e),stack:e.stack,url:page.url(),phase}));
page.on('console',m=>{if(m.type()==='error'){if(expectedResponseFailure&&/Failed to load resource.*400/.test(m.text()))events.expectedErrors.push(m.text());else events.errors.push(m.text())}});
page.on('requestfailed',r=>events.failed.push({url:r.url(),error:r.failure()?.errorText}));
page.on('response',r=>{if(r.status()>=400&&r.url().includes('/static/'))events.staticFailures.push({url:r.url(),status:r.status()})});
await page.context().route('**/*',async route=>{
 const url=new URL(route.request().url());if(url.origin===origin)return route.continue();
 events.stubs.push(url.origin);
 if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});
 if(url.pathname==='/qa-font.ttf')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.ttf'})});
 return route.fulfill({status:200,contentType:url.pathname.endsWith('.css')?'text/css':'application/javascript',body:''});
});
const fixtures=await(await page.request.get(origin+'/qa25/fixtures')).json(),rows=[],checks=[];
const session=async(role,lang='ru')=>page.request.get(origin+'/qa25/session/'+role+'?lang='+lang);
const state=async()=>(await(await page.request.get(origin+'/qa25/state')).json());
const surfaces={person:'person',index:'person'};
for(const width of [320,360,390,768,1024,1280,1440])for(const lang of ['az','ru','en'])for(const [screen,actor] of Object.entries(surfaces)){
 phase=screen+'-'+lang+'-'+width;
 await page.setViewportSize({width,height:900});await session(actor,lang);
 const response=await page.goto(origin+fixtures.paths[lang][screen],{waitUntil:'networkidle'});
 await page.evaluate(()=>document.fonts.ready);
 const facts=await page.evaluate(()=>({lang:document.documentElement.lang,heading:document.querySelector('h1')?.innerText,body:document.body.innerText,
   viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,iconFontLoaded:document.fonts.check('24px "Material Symbols Rounded"'),
   privateMediaLinks:[...document.querySelectorAll('a[href]')].filter(e=>/\/media\/(protected_docs|specialist-documents|private-media)/i.test(e.href)).length,
   csrf:[...document.querySelectorAll('form[method="post"]')].every(e=>!!e.querySelector('[name="csrfmiddlewaretoken"]')),
   forms:document.querySelectorAll('form[method="post"]').length,
   controls:[...document.querySelectorAll('main input:not([type="hidden"]),main select,main textarea,main button')].filter(e=>e.getBoundingClientRect().width).map(e=>({tag:e.tagName,name:e.name,label:!!(e.labels?.length||e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')||e.tagName==='BUTTON')}))}));
 const issues=[];if(response.status()!==200)issues.push('HTTP_'+response.status());
 if(facts.lang!==lang)issues.push('language');if(facts.scrollWidth>width+1)issues.push('overflow');
 if(screen==='person'&&facts.heading!==({az:'Profili redaktə et',ru:'Редактировать профиль',en:'Edit profile'})[lang])issues.push('person_heading_language');
 if(lang==='ru'&&facts.body.includes('Profili redaktə et'))issues.push('az_fallback_in_ru_copy');
 if(lang!=='ru'&&['Кабинет специалиста','Специалисты организации','Это мой профиль','Дипломы и сертификаты','Проверка KidsMap','Текущее сотрудничество','История сотрудничества','Подтвердить сотрудничество','Выбор публикации','Причина отклонения'].some(text=>facts.body.includes(text)))issues.push('untranslated_new_copy');
 if(!facts.csrf)issues.push('missing_csrf');if(facts.privateMediaLinks)issues.push('private_media_link');
 if(!facts.iconFontLoaded)issues.push('icon_font_not_loaded');
 if(facts.controls.some(e=>!e.label))issues.push('unlabelled_controls');
 if(screen==='public'){
  if(facts.body.includes('QA25 PRIVATE IDENTITY')||facts.body.includes('QA25 PENDING CERTIFICATE'))issues.push('private_metadata_leak');
  if(!facts.body.includes('QA25 PUBLIC CERTIFICATE'))issues.push('public_certificate_missing');
  if(facts.body.includes('QA25 PENDING ROLE'))issues.push('pending_presented_publicly');
  const history=page.getByText('QA25 HISTORICAL ROLE',{exact:false});
  if(!await history.count())issues.push('history_missing');
  if(!await page.locator('#specialist-past-employment').getByText('QA25 HISTORICAL ROLE').count()||await page.locator('#specialist-current-employment').getByText('QA25 HISTORICAL ROLE').count())issues.push('history_presented_as_current');
  if(!await page.locator('#specialist-current-employment').getByText('QA25 CURRENT ROLE').count())issues.push('current_employment_missing');
 }
 const focusable=page.locator('main input:not([type="hidden"]):visible,main select:visible,main textarea:visible,main button:visible,main a[href]:visible').first();
 if(await focusable.count()){
  await focusable.focus();checks.push({check:'focus',screen,width,lang,pass:await focusable.evaluate(e=>document.activeElement===e)});
  await page.keyboard.press('Tab');checks.push({check:'tab',screen,width,lang,pass:await page.evaluate(()=>!!document.activeElement&&document.activeElement!==document.body&&scrollX===0)});
 }
 rows.push({screen,actor,width,lang,status:response.status(),issues,facts});
 if(lang==='ru'&&[390,1440].includes(width))await page.screenshot({path:'__QA25_EVIDENCE__/'+screen+'-'+lang+'-'+width+'.png',fullPage:true});
}
return {rows,total:rows.length,passed:rows.filter(r=>!r.issues.length).length,checks,checksPassed:checks.filter(r=>r.pass).length,events,externalTransport:'cached fonts and empty CDN stubs; no real external integration; person/index localization followup only'};
}
