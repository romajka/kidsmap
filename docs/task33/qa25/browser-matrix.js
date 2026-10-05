async(page)=>{
const origin='http://127.0.0.1:8795',base='/docs/task33/design/specialist/';
const events={errors:[],failed:[],staticFailures:[],external:[]};
page.on('pageerror',e=>events.errors.push(String(e)));
page.on('console',m=>{if(m.type()==='error')events.errors.push(m.text())});
page.on('requestfailed',r=>events.failed.push({url:r.url(),error:r.failure()?.errorText}));
page.on('response',r=>{if(r.status()>=400)events.staticFailures.push({url:r.url(),status:r.status()})});
await page.context().route('**/*',route=>{
 const url=new URL(route.request().url());
 if(url.origin===origin)return route.continue();
 events.external.push(url.origin);return route.abort();
});
const files=__QA25_FILES__,rows=[],checks=[];
for(const path of ['/.env','/.git/config','/docs/task33/design/specialist/','/media/protected_docs/demo.pdf','/docs/task33/design/%2e%2e/%2e%2e/%2e%2e/.env','/docs/task33/design/specialist/%2e%2e/%2e%2e/%2e%2e/%2e%2e/.git/config']){
 const response=await page.request.get(origin+path);checks.push({check:'preview_allowlist_deny',path,status:response.status(),pass:response.status()===404});
}
for(const path of [base+'index.html','/static/img/logo-mark.svg','/static/fonts/MaterialSymbolsRounded.woff2','/static/fonts/chiron/ChironGoRoundTC-PublicSubset.woff2']){
 const response=await page.request.get(origin+path);checks.push({check:'preview_allowlist_asset',path,status:response.status(),pass:response.status()===200});
}
for(const width of [320,360,390,768,1024,1280,1440])for(const lang of ['az','ru','en'])for(const file of files){
 await page.setViewportSize({width,height:900});
 const response=await page.goto(origin+base+file+'?lang='+lang,{waitUntil:'networkidle'});
 await page.evaluate(()=>document.fonts.ready);
 const facts=await page.evaluate(()=>({lang:document.documentElement.lang,title:document.title,h1:document.querySelector('h1')?.textContent.trim(),width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
  fields:[...document.querySelectorAll('input:not([type=hidden]),select,textarea')].map(e=>({id:e.id,name:e.name,label:!!e.labels?.length||!!e.getAttribute('aria-label')||!!e.getAttribute('aria-labelledby')})),
  rawPrivateURLs:[...document.querySelectorAll('a[href]')].filter(e=>/\/media\/(protected_docs|specialist-documents|private-media)/.test(e.href)).length,
  brokenImages:[...document.images].filter(e=>!e.complete||e.naturalWidth===0).map(e=>e.getAttribute('src')),
  main:!!document.querySelector('main'),focusable:[...document.querySelectorAll('a[href],button,input,select,textarea,summary')].filter(e=>!e.disabled&&!e.hidden&&e.getBoundingClientRect().width>0).length}));
 const issues=[];
 if(response.status()!==200)issues.push('http_'+response.status());
 if(facts.lang!==lang)issues.push('shell_language');
 if(!facts.h1||!facts.main)issues.push('missing_structure');
 if(facts.scrollWidth>width+1)issues.push('horizontal_overflow');
 if(facts.rawPrivateURLs)issues.push('raw_private_url');
 if(facts.brokenImages.length)issues.push('broken_images');
 if(facts.fields.some(e=>!e.label))issues.push('unlabelled_field');
 await page.keyboard.press('Tab');
 checks.push({file,lang,width,check:'keyboard_first_focus',pass:await page.evaluate(()=>document.activeElement!==document.body&&['A','BUTTON','INPUT','SELECT','TEXTAREA','SUMMARY'].includes(document.activeElement.tagName))});
 rows.push({file,lang,width,issues,facts});
 if(lang==='ru'&&[390,1440].includes(width)){await page.locator('main').focus();await page.screenshot({path:'__QA25_EVIDENCE__/'+file.replace('.html','')+'-'+lang+'-'+width+'.png',fullPage:true});}
}
const record=(file,lang,width,check,pass)=>checks.push({file,lang,width,check,pass});
const stateCases={profile:['empty','history','pending','revoked'],person:['denied','error','conflict','loading','saved'],organization:['empty','pending','active','history','denied'],claim:['pending','approved','rejected','withdrawn','denied'],documents:['empty','pending','approved','revoked','rejected','denied'],review:['approved','rejected','denied'],reconciliation:['empty','loading','error','conflict']};
for(const width of [390,1440])for(const lang of ['az','ru','en'])for(const [file,states] of Object.entries(stateCases))for(const state of states){
 await page.setViewportSize({width,height:900});await page.goto(origin+base+file+'.html?lang='+lang+'&state='+state,{waitUntil:'networkidle'});
 const facts=await page.evaluate(()=>({lang:document.documentElement.lang,state:document.body.dataset.state,h1:!!document.querySelector('h1'),scroll:document.documentElement.scrollWidth,width:innerWidth}));
 record(file,lang,width,'state_'+state+'_renders_responsive',facts.lang===lang&&facts.state===state&&facts.h1&&facts.scroll<=facts.width+1);
 if(lang==='ru'&&((file==='organization'&&state==='active')||(file==='documents'&&state==='approved')||(file==='claim'&&state==='pending')||(file==='review'&&state==='denied'))){await page.locator('main').focus();await page.screenshot({path:'__QA25_EVIDENCE__/'+file+'-'+state+'-'+lang+'-'+width+'.png',fullPage:true});}
}
for(const width of [390,1440])for(const lang of ['az','ru','en']){
 const load=async(file,state='default')=>{await page.setViewportSize({width,height:900});await page.goto(origin+base+file+'.html?lang='+lang+'&state='+state,{waitUntil:'networkidle'});};
 const action=a=>page.locator('[data-action="'+a+'"]');
 const state=()=>page.locator('body').getAttribute('data-state');
 const focused=id=>page.locator('#'+id).evaluate(e=>document.activeElement===e);
 const msg=id=>page.locator('#'+id).textContent();
 const confirmedCopy={ru:'Подтверждено',en:'Confirmed',az:'Təsdiqlənib'}[lang];
 const consentCount=async()=>{const values=await page.locator('#cooperation-card .consent .pill').allTextContents();return values.filter(v=>v===confirmedCopy).length;};
 await load('person');await page.locator('#person-name').fill('');await action('save-person').click();
 record('person',lang,width,'invalid_name_error_and_focus',await page.locator('#person-name').getAttribute('aria-invalid')==='true'&&await focused('person-name')&&!!await msg('form-result'));
 await page.locator('#person-name').fill('QA25 Synthetic Person');await action('save-person').click();
 record('person',lang,width,'demo_save_clears_invalid',await page.locator('#person-name').getAttribute('aria-invalid')===null&&!!await msg('form-result'));
 await page.locator('#practice-mode').selectOption('online');
 record('person',lang,width,'online_preserves_history_without_current_office',!await page.locator('#office-fields').isVisible()&&await page.locator('#online-note').isVisible()&&await page.locator('details.history').first().isVisible());
 await load('organization');await page.locator('#demo-actor').selectOption('person');
 record('organization',lang,width,'person_has_own_consent_only_no_org_authority',await action('org-consent').count()===0&&await action('person-consent').count()===1&&await state()==='default'&&await consentCount()===0);
 await action('person-consent').click();record('organization',lang,width,'person_first_is_one_consent_still_pending',await state()==='pending'&&await consentCount()===1&&await action('person-consent').count()===0);
 const otherLang=lang==='ru'?'en':'ru';
 await page.locator('.locale a[lang="'+otherLang+'"]').click();await page.waitForLoadState('networkidle');
 record('organization',lang,width,'language_switch_preserves_pending_person_and_actor',await state()==='pending'&&await page.locator('#demo-actor').inputValue()==='person'&&new URL(page.url()).searchParams.get('consent')==='person');
 await page.locator('.locale a[lang="'+lang+'"]').click();await page.waitForLoadState('networkidle');
 record('organization',lang,width,'language_roundtrip_preserves_one_consent',await state()==='pending'&&await consentCount()===1);
 await page.locator('#demo-actor').selectOption('organization');await action('org-consent').click();record('organization',lang,width,'organization_second_activates_two_consents',await state()==='active'&&await consentCount()===2);
 await load('organization');await action('org-consent').click();
 record('organization',lang,width,'organization_only_stays_pending',await state()==='pending'&&await action('person-consent').count()===0&&await consentCount()===1);
 await page.locator('#demo-actor').selectOption('person');await action('person-consent').click();
 record('organization',lang,width,'second_party_explicit_consent_activates',await state()==='active'&&await consentCount()===2);
 await action('cancel-employment').click();
 record('organization',lang,width,'cancel_keeps_dated_history_not_current_work',await state()==='history'&&await page.locator('details.history').isVisible()&&await action('person-consent').count()===0&&(await page.locator('details.history').textContent()).includes('03.10.2026')&&(await page.locator('#cooperation-card').textContent()).includes('01.09.2026'));
 record('organization',lang,width,'active_cancel_preserves_both_consent_events',await page.locator('details.history li').count()===4);
 await load('organization');await page.locator('#demo-actor').selectOption('person');await action('person-consent').click();await action('cancel-employment').click();
 record('organization',lang,width,'one_consent_cancel_does_not_invent_other_consent',await state()==='history'&&await page.locator('details.history li').count()===3);
 await load('organization');await action('cancel-employment').click();record('organization',lang,width,'unconfirmed_cancel_does_not_invent_consents',await state()==='history'&&await page.locator('details.history li').count()===2);
 await load('organization');await page.locator('#employment-end').fill('2026-08-01');await action('invite').click();
 record('organization',lang,width,'period_validation_focus',await page.locator('#employment-end').getAttribute('aria-invalid')==='true'&&await focused('employment-end')&&!!await msg('invite-result'));
 await page.locator('#employment-end').fill('');await action('invite').click();
 record('organization',lang,width,'proposal_does_not_automatically_confirm',await state()==='default'&&!!await msg('invite-result')&&await consentCount()===0);
 record('organization',lang,width,'no_person_biography_contacts_document_edit_controls',await page.locator('#person-bio,#person-phone,input[type=file],#certificate-optin').count()===0);
 await load('claim');await action('submit-claim').click();
 record('claim',lang,width,'own_person_checkbox_required_and_focused',await page.locator('#claim-person').getAttribute('aria-invalid')==='true'&&await focused('claim-person'));
 await page.locator('#claim-person').check();await action('submit-claim').click();
 record('claim',lang,width,'claim_awaits_kidsmap_no_auto_person_editor',await state()==='pending'&&await page.locator('#person-form').count()===0);
 await action('withdraw-claim').click();record('claim',lang,width,'withdraw_preserves_profile_id_and_old_url',await state()==='withdrawn'&&(await page.locator('main').textContent()).includes('SP-1042')&&(await page.locator('main').textContent()).includes('/specialists/leyla-mammadova/'));
 await load('documents');await page.locator('#document-type').selectOption('identity');
 record('documents',lang,width,'identity_has_no_public_choice',!await page.locator('#upload-choice').isVisible()&&await page.locator('#identity-note').isVisible()&&!await page.locator('#upload-optin').isChecked());
 await page.locator('#document-type').selectOption('certificate');await page.locator('#document-name').fill('QA25 Synthetic Certificate');await action('upload-document').click();
 record('documents',lang,width,'file_required_focused_error',await page.locator('#document-file').getAttribute('aria-invalid')==='true'&&await focused('document-file'));
 await page.locator('#document-file').setInputFiles({name:'qa25.exe',mimeType:'application/octet-stream',buffer:Buffer.from('synthetic')});await action('upload-document').click();
 record('documents',lang,width,'unsupported_file_rejected',await page.locator('#document-result').getAttribute('role')==='alert'&&await focused('document-file'));
 await page.locator('#document-file').setInputFiles({name:'qa25.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-synthetic-only')});await action('upload-document').click();
 record('documents',lang,width,'valid_demo_file_remains_private_without_transport',await page.locator('#document-result').getAttribute('role')==='status'&&!!await msg('document-result'));
 await page.locator('#certificate-optin').check();
 const privateCopy={ru:'Приватный',en:'Private',az:'Məxfi'}[lang];
 record('documents',lang,width,'pending_optin_still_private',await page.locator('#certificate-visibility').textContent()===privateCopy);
 await load('documents','approved');await page.locator('#certificate-optin').uncheck();
 record('documents',lang,width,'approved_optin_withdraw_updates_private_badge',await page.locator('#certificate-visibility').textContent()===privateCopy&&!!await msg('optin-result'));
 await page.locator('#certificate-optin').check();record('documents',lang,width,'approved_explicit_optin_updates_public_badge',await page.locator('#certificate-visibility').textContent()==={ru:'Публичный',en:'Public',az:'İctimai'}[lang]);
 await load('review');await action('reject-claim').click();record('review',lang,width,'claim_rejection_requires_reason_focused',await page.locator('#claim-review-reason').getAttribute('aria-invalid')==='true'&&await focused('claim-review-reason'));
 await page.locator('#claim-review-reason').fill('Synthetic reason');await action('reject-claim').click();record('review',lang,width,'reasoned_claim_rejection',await state()==='rejected');
 await load('review');await action('approve-document').click();record('review',lang,width,'reviewer_approval_keeps_person_choice_private',!!await msg('document-review-result')&&await page.locator('#certificate-optin,#upload-optin').count()===0);
 await load('review','denied');record('review',lang,width,'ordinary_role_demo_denial_contains_no_private_controls',await page.locator('[data-action="approve-document"],[data-action="private-document"],textarea').count()===0);
 await load('profile');await action('certificate').click();record('profile',lang,width,'public_certificate_demo_only',!!await msg('certificate-result'));
 await load('profile','revoked');record('profile',lang,width,'withdrawn_certificate_not_public',await action('certificate').count()===0);
 await load('profile','pending');record('profile',lang,width,'pending_certificate_not_public',await action('certificate').count()===0);
 await load('reconciliation');await action('reconcile').click();record('reconciliation',lang,width,'synthetic_reconciliation_explicit_ids_no_auto_consent',!!await msg('reconciliation-result')&&/3/.test(await msg('reconciliation-result'))&&/2/.test(await msg('reconciliation-result'))&&/0/.test(await msg('reconciliation-result')));
 await page.locator('.locale a[lang="'+(lang==='ru'?'en':'ru')+'"]').click();await page.waitForLoadState('networkidle');record('navigation',lang,width,'real_language_link_changes_shell',await page.locator('html').getAttribute('lang')===(lang==='ru'?'en':'ru'));
}
return{rows,total:rows.length,passed:rows.filter(r=>!r.issues.length).length,checks,checksPassed:checks.filter(r=>r.pass).length,events};
}
