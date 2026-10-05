async(page)=>{
const origin='http://127.0.0.1:8788',events={errors:[],failed:[],staticFailures:[],stubs:[],expectedErrors:[]};let expectedResponseFailure=false,phase='start';
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
const fixtures=await(await page.request.get(origin+'/qa28/fixtures')).json(),rows=[],checks=[];
const session=async(role,lang='ru')=>page.request.get(origin+'/qa28/session/'+role+'?lang='+lang);
const state=async()=>(await(await page.request.get(origin+'/qa28/state')).json());
const surfaces={public:'public',person:'person',index:'person',invitations:'person',claims:'applicant',certificates:'person',org:'manager',review:'reviewer'};
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
  if(/\bNone\b/.test(facts.body))issues.push('unknown_experience_leaked');
  const experienceRows=await page.locator('.km-detail-stat-item').allTextContents();
  if(experienceRows.some(text=>/Təcrübə|Experience|Стаж работы/.test(text)))issues.push('unknown_experience_row_visible');
  facts.head=await page.evaluate(()=>({title:document.title,canonical:document.querySelector('link[rel="canonical"]')?.href,alternates:[...document.querySelectorAll('link[rel="alternate"][hreflang]')].map(e=>e.hreflang),schema:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>JSON.parse(e.textContent))}));
  if(!facts.head.title||!facts.head.canonical||new URL(facts.head.canonical).hostname!=='kidsmap.az')issues.push('public_seo_head');
  if(!facts.head.title.includes({az:'QA28 İxtisas',ru:'QA28 Специализация',en:'QA28 Specialization'}[lang]))issues.push('public_title_locale');
  if(!['az','ru','en'].every(l=>facts.head.alternates.includes(l)))issues.push('public_hreflang');
  if(!facts.head.schema.some(s=>s?.['@type']==='Organization')||!facts.head.schema.some(s=>s?.['@type']==='WebSite'))issues.push('global_schema_missing');
  if(JSON.stringify(facts.head).includes('QA25 PRIVATE IDENTITY')||JSON.stringify(facts.head).includes('QA25 PENDING CERTIFICATE'))issues.push('private_seo_metadata');
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
 if(lang==='ru'&&[390,1440].includes(width))await page.screenshot({path:'__QA28_EVIDENCE__/'+screen+'-'+lang+'-'+width+'.png',fullPage:true});
}
// Private HTTP boundary and nested foreign IDs through real application routes.
phase='private_http';
await page.setViewportSize({width:390,height:900});
for(const actor of ['public','person','manager','foreign','volunteer','staff','reviewer']){
 await session(actor);
 for(const kind of ['identity','pending','approved']){
  const r=await page.request.get(origin+fixtures.paths.ru['document_'+kind]);
  const expected=actor==='volunteer'?403:(['person','reviewer'].includes(actor)||kind==='approved'?200:404);
  checks.push({check:'private_document_boundary',actor,kind,status:r.status(),expected,pass:r.status()===expected&&(expected!==200||((await r.body()).toString()==='%PDF-synthetic-only'&&r.headers()['cache-control']==='private, no-store'))});
 }
}
await session('person');let r=await page.request.get(origin+fixtures.paths.ru.foreign_document);
checks.push({check:'foreign_document_denied',pass:r.status()===404,status:r.status()});
r=await page.request.get(origin+fixtures.paths.ru.foreign_certificates);
checks.push({check:'foreign_certificate_workspace_denied',pass:r.status()===403||r.status()===404,status:r.status()});
for(const lang of ['az','ru','en']){
 await session('person',lang);r=await page.request.get(origin+fixtures.paths[lang].legacy_editor);
 checks.push({check:'legacy_editor_url_preserved',lang,pass:r.status()===200,status:r.status()});
}
await session('manager');r=await page.request.get(origin+fixtures.paths.ru.person);
checks.push({check:'business_person_profile_denied',pass:[403,404].includes(r.status()),status:r.status()});
// Browser POSTs use real DOM hidden CSRF/version fields; no forced Django bypass.
phase='org_propose';
await session('manager');await page.goto(origin+fixtures.paths.ru.org);
const orgForm=page.locator('form').filter({has:page.locator('[name="action"][value="propose"]')}).first();
if(await orgForm.count()){
 await orgForm.locator('[name="specialist"]').selectOption(String(fixtures.ids.person));
 await orgForm.locator('[name="role"]').fill('QA25 BROWSER PROPOSAL');
 await orgForm.locator('[name="start_date"]').fill('2026-10-03');
 await orgForm.locator('button[type="submit"]').click();await page.waitForLoadState('networkidle');
 checks.push({check:'organization_invitation_is_pending',pass:(await state()).browser_proposal_pending===1});
 const row=page.locator('[data-employment-id]').filter({hasText:'QA25 BROWSER PROPOSAL'});
 const button=row.locator('[name="action"][value="confirm"]');
 if(await button.count()){phase='org_confirm';await button.click();await page.waitForLoadState('networkidle');checks.push({check:'organization_confirmation_alone_pending',pass:(await state()).browser_proposal_pending===1})}
 else checks.push({check:'organization_confirmation_alone_pending',pass:false,reason:'org confirmation button absent'});
}else checks.push({check:'organization_invitation_is_pending',pass:false,reason:'proposal form absent'});
await session('person');
phase='person_confirm';
await page.goto(origin+fixtures.paths.ru.invitations);
const before=await state();
r=await page.request.post(origin+fixtures.paths.ru.invitations,{form:{action:'confirm',employment_id:String(fixtures.ids.employment_pending),expected_version:String(before.employment_version)}});
checks.push({check:'csrf_missing_denied',status:r.status(),pass:r.status()===403});
const pendingForm=page.locator('form').filter({has:page.locator('[name="employment_id"][value="'+fixtures.ids.employment_pending+'"]')}).filter({has:page.locator('[name="action"][value="confirm"]')}).first();
if(await pendingForm.count()){
 await pendingForm.locator('button[type="submit"],input[type="submit"]').first().click();await page.waitForLoadState('networkidle');
 checks.push({check:'person_explicit_confirmation',pass:(await state()).employment_status==='active'});
}else checks.push({check:'person_explicit_confirmation',pass:false,reason:'confirm form absent'});
// Request claim without silently granting person ownership.
phase='claim_request';
await session('applicant');await page.goto(origin+fixtures.paths.ru.claims);
const claimForm=page.locator('form').filter({has:page.locator('[name="action"][value="request"]')}).first();
if(await claimForm.count()){
 await claimForm.locator('button[type="submit"],input[type="submit"]').first().click();await page.waitForLoadState('networkidle');
 const claimState=await state();checks.push({check:'claim_request_stays_pending',pass:claimState.claims_pending===1&&claimState.claims_approved===0});
}else checks.push({check:'claim_request_stays_pending',pass:false,reason:'claim form absent'});
phase='claim_approve';await session('reviewer');await page.goto(origin+fixtures.paths.ru.claim_review);
const claimApprove=page.locator('button[name="action"][value="claim_approve"]').first();
if(await claimApprove.count()){
 await claimApprove.click();await page.waitForLoadState('networkidle');
 const result=await state();checks.push({check:'dedicated_claim_review_verifies_person',pass:result.claims_pending===0&&result.claims_approved===1&&result.unclaimed_person_verified});
}else checks.push({check:'dedicated_claim_review_verifies_person',pass:false,reason:'claim approval absent'});
phase='certificate_negative_posts';await session('person');await page.goto(origin+fixtures.paths.ru.certificates);
const csrf=async()=>page.locator('[name="csrfmiddlewaretoken"]').first().inputValue();
let dstate=await state();
let token=await csrf();
r=await page.request.post(origin+fixtures.paths.ru.certificates,{form:{csrfmiddlewaretoken:token,action:'choice',document_id:String(fixtures.ids.identity),publish:'true',document_version:dstate.documents.identity.version}});
checks.push({check:'identity_never_public_post',pass:!(await state()).documents.identity.published&&[200,400,403,409].includes(r.status()),status:r.status()});
r=await page.request.post(origin+fixtures.paths.ru.certificates,{form:{csrfmiddlewaretoken:token,action:'choice',document_id:String(fixtures.ids.foreign_document),publish:'true',document_version:'pending|0|'}});
checks.push({check:'foreign_document_nested_post_denied',pass:[403,404].includes(r.status()),status:r.status()});
await session('public');r=await page.request.get(origin+fixtures.paths.ru.document_pending);
checks.push({check:'pending_optin_private_before_approval',pass:r.status()===404,status:r.status()});
phase='certificate_approve';await session('reviewer');await page.goto(origin+fixtures.paths.ru.review);
const pendingReview=page.locator('form').filter({has:page.locator('[name="document_id"][value="'+fixtures.ids.pending+'"]')}).first();
const approveButton=pendingReview.locator('[name="action"][value="document_approve"]');
if(await approveButton.count()){
 await approveButton.click();await page.waitForLoadState('networkidle');
 checks.push({check:'dedicated_review_approval',pass:(await state()).documents.pending.status==='approved'});
 await session('public');r=await page.request.get(origin+fixtures.paths.ru.document_pending);
 checks.push({check:'approved_person_optin_public',pass:r.status()===200,status:r.status()});
}else checks.push({check:'dedicated_review_approval',pass:false,reason:'approve button absent'});
phase='certificate_upload';await session('person');await page.goto(origin+fixtures.paths.ru.certificates);
const uploadForm=page.locator('form').filter({has:page.locator('input[type="file"][name="file"]')}).first();
if(await uploadForm.count()){
 const count=(await state()).document_count;
 await uploadForm.locator('[name="name"]').fill('QA25 UPLOADED SYNTHETIC CERTIFICATE');
 await uploadForm.locator('[name="document_type"]').selectOption('certificate');
 await uploadForm.locator('input[type="file"]').setInputFiles({name:'synthetic.exe',mimeType:'application/octet-stream',buffer:Buffer.from('synthetic-invalid')});
 phase='certificate_upload_invalid';
 expectedResponseFailure=true;
 await uploadForm.locator('button[type="submit"],input[type="submit"]').first().click();await page.waitForLoadState('networkidle');
 checks.push({check:'invalid_upload_rendered_error_preserves_state',pass:(await state()).document_count===count&&await page.locator('.errorlist,[role="alert"]').count()>0});
 await page.screenshot({path:'__QA28_EVIDENCE__/certificate-upload-error-ru-390.png',fullPage:true});
 expectedResponseFailure=false;
 await page.goto(origin+fixtures.paths.ru.certificates);
 await uploadForm.locator('[name="name"]').fill('QA25 UPLOADED SYNTHETIC CERTIFICATE');
 await uploadForm.locator('[name="document_type"]').selectOption('certificate');
 phase='certificate_upload_valid';
 await uploadForm.locator('input[type="file"]').setInputFiles({name:'synthetic.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-synthetic-only')});
 await uploadForm.locator('button[type="submit"],input[type="submit"]').first().click();await page.waitForLoadState('networkidle');
 checks.push({check:'real_private_certificate_upload',pass:(await state()).document_count===count+1});
}else checks.push({check:'real_private_certificate_upload',pass:false,reason:'upload form absent'});
await page.goto(origin+fixtures.paths.ru.certificates);
phase='certificate_opt_out';
// Approved certificate opt-out immediately removes public download; opt-in still uses server moderation.
const choice=page.locator('form').filter({has:page.locator('[name="document_id"][value="'+fixtures.ids.approved+'"]')}).first();
if(await choice.count()){
 const publish=choice.locator('[name="publish"]');
 if(await publish.count()){if(await publish.evaluate(e=>e.tagName)==='SELECT')await publish.selectOption('false');else if(await publish.getAttribute('type')==='checkbox')await publish.uncheck();}
 await choice.locator('button[type="submit"],input[type="submit"]').first().click();await page.waitForLoadState('networkidle');
 const current=await state();checks.push({check:'certificate_opt_out',pass:current.documents.approved.published===false});
 await session('public');r=await page.request.get(origin+fixtures.paths.ru.document_approved);checks.push({check:'certificate_opt_out_private_http',pass:r.status()===404,status:r.status()});
}else checks.push({check:'certificate_opt_out',pass:false,reason:'choice form absent'});
await session('manager');r=await page.request.get(origin+fixtures.paths.ru.certificates);checks.push({check:'business_person_documents_denied',pass:[403,404].includes(r.status()),status:r.status()});
await session('staff');r=await page.request.get(origin+fixtures.paths.ru.review);checks.push({check:'ordinary_staff_review_denied',pass:[403,404].includes(r.status()),status:r.status()});
await session('public');
for(const language of ['az','ru','en']){
 await page.goto(origin+fixtures.paths[language].zero_public,{waitUntil:'networkidle'});
 const facts=await page.locator('.km-detail-stat-item').allTextContents();
 checks.push({check:'zero_experience_visible_distinct_from_unknown',language,pass:facts.some(t=>/Təcrübə|Experience|Стаж работы/.test(t)&&/\b0\b/.test(t))});
}
return {rows,total:rows.length,passed:rows.filter(r=>!r.issues.length).length,checks,checksPassed:checks.filter(r=>r.pass).length,events,externalTransport:'cached fonts and empty CDN stubs; no real external integration'};
}
