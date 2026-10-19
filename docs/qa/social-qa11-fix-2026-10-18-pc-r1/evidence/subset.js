async original=>{
const F={
  "synthetic_only": true,
  "specialist_id": 2,
  "cases": {
    "az": {
      "user_id": 43,
      "head_id": 2,
      "current_revision_id": 5,
      "public_text": "QA11 PUBLIC C az",
      "candidate_a": "QA11 CANDIDATE A az",
      "draft_b": "QA11 DRAFT B az"
    },
    "ru": {
      "user_id": 44,
      "head_id": 3,
      "current_revision_id": 6,
      "public_text": "QA11 PUBLIC C ru",
      "candidate_a": "QA11 CANDIDATE A ru",
      "draft_b": "QA11 DRAFT B ru"
    },
    "en": {
      "user_id": 45,
      "head_id": 4,
      "current_revision_id": 7,
      "public_text": "QA11 PUBLIC C en",
      "candidate_a": "QA11 CANDIDATE A en",
      "draft_b": "QA11 DRAFT B en"
    }
  },
  "revoked": {
    "notice_id": 6,
    "invitation_id": 2,
    "status": "CANCELED"
  },
  "business_counts_before_seed": {
    "notifications": 18,
    "unread": 17,
    "outbox": 15,
    "memberships": 5,
    "grants": 3
  },
  "business_counts_after_seed": {
    "notifications": 18,
    "unread": 17,
    "outbox": 15,
    "memberships": 5,
    "grants": 3
  }
},base='http://127.0.0.1:33422',O='/mnt/c/kidsmap/docs/qa/social-qa11-fix-2026-10-18-pc-r1',browser=original.context().browser(),rows=[],consoleErrors=[],pageerrors=[],http=[],failed=[],blocked=[];
const contexts=[];
async function make(role){const c=await browser.newContext({viewport:{width:390,height:950},serviceWorkers:'block'});contexts.push(c);await c.route('**/*',r=>{if(new URL(r.request().url()).hostname==='127.0.0.1')return r.continue();blocked.push(new URL(r.request().url()).hostname);return r.abort();});const p=await c.newPage();p.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});p.on('pageerror',e=>pageerrors.push(String(e)));p.on('response',r=>{if(r.status()>=400)http.push({path:new URL(r.url()).pathname,status:r.status()});});p.on('requestfailed',r=>failed.push({path:new URL(r.url()).pathname,error:r.failure()?.errorText}));await p.goto(base+'/qa/social11-login/'+role+'/');return p;}
async function keyboard(p,selector){const e=p.locator(selector).first();await e.focus();const focused=await e.evaluate(el=>document.activeElement===el);await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');return focused&&await e.evaluate(el=>document.activeElement===el);}
for(const lang of ['az','ru','en']){
 const f=F.cases[lang],prefix=lang==='az'?'':'/'+lang,path=prefix+'/reviews/specialist/target/'+F.specialist_id+'/',a=await make('conflict_'+lang),b=await a.context().newPage();
 b.on('response',r=>{if(r.status()>=400)http.push({path:new URL(r.url()).pathname,status:r.status()});});b.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});b.on('pageerror',e=>pageerrors.push(String(e)));b.on('requestfailed',r=>failed.push({path:new URL(r.url()).pathname,error:r.failure()?.errorText}));
 await a.goto(base+path);await b.goto(base+path);const stale=await b.locator('[name=expected_revision_id]').inputValue();
 await a.locator('#review-rating').selectOption('5');await a.locator('#review-text').fill(f.candidate_a);await a.locator('[data-review-edit] button').click();await a.waitForLoadState('domcontentloaded');
 const before=(await(await a.request.get(base+'/qa/social11-state/')).json()).cases[lang];
 await b.locator('#review-rating').selectOption('2');await b.locator('#review-text').fill(f.draft_b);const wait=b.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===path);await b.locator('[data-review-edit] button').click();const response=await wait;await b.waitForLoadState('domcontentloaded');
 const after=(await(await a.request.get(base+'/qa/social11-state/')).json()).cases[lang];
 const conflictChecks={status409:response.status()===409,singleMain:await b.getByRole('main').count()===1,noNested:await b.locator('main main').count()===0,alert:await b.locator('[data-review-conflict][role=alert]').isVisible(),draftBPreserved:await b.locator('#review-text').inputValue()===f.draft_b,ratingBPreserved:await b.locator('#review-rating').inputValue()==='2',latestA:await b.locator('[data-review-latest]').innerText()===f.candidate_a,freshToken:await b.locator('[name=expected_revision_id]').inputValue()===String(before.candidate_id)&&String(before.candidate_id)!==stale,dbUnchangedBy409:JSON.stringify(before)===JSON.stringify(after),publicCPreserved:after.current_id===f.current_revision_id&&after.current_text===f.public_text,candidateAOnly:after.candidate_text===f.candidate_a&&after.revision_count===2,reloadLinkGET:await b.locator('[data-review-reload]').getAttribute('href')===path,keyboard:await keyboard(b,'#review-text'),noOverflow:await b.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)};
 rows.push({id:'conflict409',lang,checks:conflictChecks});await b.screenshot({path:O+'/png/subset-'+lang+'-409.png',fullPage:true,animations:'disabled'});
 const guest=await make('guest');await guest.goto(base+path);rows.push({id:'public-after409',lang,checks:{publicC:await guest.locator('.typed-reviews').innerText().then(t=>t.includes(f.public_text)&&!t.includes(f.candidate_a)&&!t.includes(f.draft_b)),singleMain:await guest.getByRole('main').count()===1}});
 const author=await make('author');await author.goto(base+prefix+'/account/notifications/');const csrf=await author.locator('input[name=csrfmiddlewaretoken]').first().inputValue(),postPath=prefix+'/account/notifications/'+F.revoked.notice_id+'/accept/';
 const denialPromise=author.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===postPath);
 await author.evaluate(({path,token})=>{const form=document.createElement('form');form.method='POST';form.action=path;const field=document.createElement('input');field.name='csrfmiddlewaretoken';field.value=token;form.append(field);document.body.append(form);form.submit();},{path:postPath,token:csrf});
 const denial=await denialPromise;await author.waitForLoadState('domcontentloaded');
 rows.push({id:'revoked403',lang,transport:'QA-crafted stale native form; real backend POST/CSRF/ACL response',checks:{status403:denial.status()===403,singleMain:await author.getByRole('main').count()===1,noNested:await author.locator('main main').count()===0,alert:await author.locator('.account-notifications__error[role=alert]').isVisible(),idPreserved:await author.locator('div.account-main-content#main-content').count()===1,keyboard:await keyboard(author,'#main-content button'),noOverflow:await author.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)}});await author.screenshot({path:O+'/png/subset-'+lang+'-403.png',fullPage:true,animations:'disabled'});
 await guest.goto(base+'/qa/social11-login/guest/');const inboxPath=prefix+'/account/notifications/?tab=all',redirect=await guest.request.get(base+inboxPath,{maxRedirects:0});const loc=new URL(redirect.headers().location,base);const loginResponse=await guest.goto(base+inboxPath);rows.push({id:'guest-inbox-redirect',lang,checks:{status302:redirect.status()===302,namedLogin:loc.pathname===prefix+'/auth/login/',nextPreserved:loc.searchParams.get('next')===inboxPath,login200:loginResponse.status()===200,formVisible:await guest.locator('.register-form--login [name=username]').isVisible(),singleMain:await guest.getByRole('main').count()===1,keyboard:await keyboard(guest,'.register-form--login [name=username]')}});await guest.screenshot({path:O+'/png/subset-'+lang+'-guest-login.png',fullPage:true,animations:'disabled'});
}
for(const c of contexts)await c.close();return{rows,consoleErrors,pageerrors,http,failed,blocked,authentication:'SIMULATED fictional roles; native application POSTs real',expectedHTTP:'3x409 +3x403; corresponding browser console resource status errors expected'};
}
