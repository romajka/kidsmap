async(page)=>{
const origin='http://127.0.0.1:8782';
const events={errors:[],failed:[],unexpectedResponses:[],expectedDenials:[]};
page.on('pageerror',error=>events.errors.push({url:page.url(),message:String(error),stack:error.stack}));
page.on('requestfailed',request=>events.failed.push({url:request.url(),error:request.failure()?.errorText}));
page.on('response',response=>{if([403,409,429].includes(response.status()))events.expectedDenials.push({url:response.url(),status:response.status()});else if(response.status()>=400)events.unexpectedResponses.push({url:response.url(),status:response.status()});});
await page.context().unroute('**/*');
await page.context().route('**/*',async route=>{
 const url=new URL(route.request().url());
 if(url.origin===origin)return route.continue();
 if(url.hostname==='kidsmap.az')return route.fulfill({response:await route.fetch({url:origin+url.pathname+url.search})});
 if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});
 return route.fulfill({status:200,contentType:'application/javascript',body:''});
});
const fixtures=await(await page.request.get(origin+'/qa22/fixtures')).json();
const rows=[];
const visit=async(actor,kind)=>{await page.request.get(origin+'/qa22/session/'+actor);await page.goto(origin+fixtures.paths.en[kind],{waitUntil:'networkidle'});};
const invariant=async kind=>(await(await page.request.get(origin+'/qa22/invariants')).json())[kind];
const post=async(path,values)=>await page.evaluate(async({path,values})=>{const csrf=document.querySelector('[name="csrfmiddlewaretoken"]').value;const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({...values,csrfmiddlewaretoken:csrf})});const result={status:response.status,redirected:response.redirected,retryAfter:response.headers.get('Retry-After')};await response.text();return result;},{path,values});
const submit=async button=>{
 const navigation=page.waitForEvent('framenavigated',{predicate:frame=>frame===page.mainFrame()});
 const response=page.waitForResponse(response=>response.request().method()==='POST');
 await button.click();const done=await response;await navigation;await page.waitForLoadState('networkidle');return done.status();
};
for(const kind of['place','activity','specialist','event']){
 await page.setViewportSize({width:390,height:900});
 await visit('author',kind);
 const oldExpected=await page.locator('[data-review-edit] [name="expected_revision_id"]').inputValue();
 await page.locator('#review-rating').selectOption('4');
 await page.locator('#review-text').fill('QA22 NEW EDIT '+kind);
 const submitStatus=await submit(page.locator('[data-review-edit] button'));
 let afterSubmit=await invariant(kind);
 rows.push({kind,check:'submit_preserves_approved',pass:submitStatus===302&&afterSubmit.approved_text.includes('QA22 APPROVED '+kind)&&afterSubmit.current===fixtures.initial[kind].approved&&afterSubmit.candidate!==Number(oldExpected)&&afterSubmit.likes===1,status:submitStatus});
 const stale=await post(fixtures.paths.en[kind],{rating:'3',text:'QA22 STALE EDIT',expected_revision_id:oldExpected});
 const afterStale=await invariant(kind);
 rows.push({kind,check:kind==='place'?'active_place_gate_precedes_stale_CAS':'stale_CAS',pass:stale.status===(kind==='place'?429:409)&&afterStale.revision_count===afterSubmit.revision_count&&afterStale.candidate===afterSubmit.candidate,status:stale.status});
 const currentExpected=await page.locator('[data-review-edit] [name="expected_revision_id"]').inputValue();
 const cooldown=await post(fixtures.paths.en[kind],{rating:'4',text:'QA22 NEW EDIT '+kind,expected_revision_id:currentExpected});
 rows.push({kind,check:kind==='specialist'?'legacy_specialist_second_submit_allowed':'cooldown',pass:kind==='specialist'?cooldown.status===200&&cooldown.redirected:cooldown.status===429&&Number(cooldown.retryAfter)>0,status:cooldown.status});
 if(kind==='specialist')afterSubmit=await invariant(kind);
 if(kind==='place'){
  const expiry=await(await page.request.post(origin+'/qa22/expire-place-gate?token='+fixtures.runToken)).json();
  const expiredStale=await post(fixtures.paths.en[kind],{rating:'3',text:'QA22 EXPIRED STALE EDIT',expected_revision_id:oldExpected});
  const state=await invariant(kind);
  rows.push({kind,check:'stale_CAS_after_local_gate_expiry',pass:expiry.synthetic_gate_expired===1&&expiredStale.status===409&&state.revision_count===afterSubmit.revision_count&&state.candidate===afterSubmit.candidate,status:expiredStale.status});
 }
 await visit('public',kind);
 let body=await page.locator('body').innerText();
 rows.push({kind,check:'pending_private_old_public',pass:body.includes('QA22 APPROVED '+kind)&&!body.includes('QA22 NEW EDIT')&&!body.includes('QA22 PRIVATE REPORT')});
 await visit('owner',kind);
 const head=fixtures.initial[kind].head;
 const action=action=>'/en/reviews/'+kind+'/'+head+'/'+action+'/';
 const denied=await post(action('approve'),{revision_id:String(afterSubmit.candidate)});
 rows.push({kind,check:'business_approve_denied',pass:denied.status===403,status:denied.status});
 if(kind==='place')for(const action of['approve','reject']){
  const legacy=await post(fixtures.legacy.en[action],{revision_id:String(afterSubmit.candidate)});
  rows.push({kind,check:'legacy_business_'+action+'_denied',pass:legacy.status===403,status:legacy.status});
 }
 const replyForm=page.locator('article[data-review-id="'+head+'"] form[action$="/reply/"]');
 await replyForm.locator('textarea').fill('QA22 BROWSER REPLY '+kind);
 const replyStatus=await submit(replyForm.locator('button'));
 const reportDetails=page.locator('article[data-review-id="'+head+'"] details');
 await reportDetails.locator('summary').click();
 const reportForm=reportDetails.locator('form');
 await reportForm.locator('textarea').fill('QA22 BROWSER PRIVATE REPORT '+kind);
 const reportStatus=await submit(reportForm.locator('button'));
 await visit('public',kind);body=await page.locator('body').innerText();
 rows.push({kind,check:'reply_public_report_private',pass:replyStatus===302&&reportStatus===302&&body.includes('QA22 BROWSER REPLY '+kind)&&!body.includes('QA22 BROWSER PRIVATE REPORT')});
 await visit('staff',kind);
 const candidate=page.locator('[data-candidate-id="'+afterSubmit.candidate+'"]');
 const approvalStatus=await submit(candidate.locator('form[action$="/approve/"] button'));
 const afterApprove=await invariant(kind);
 rows.push({kind,check:'reviewer_approve_new_revision',pass:approvalStatus===302&&afterApprove.approved_text==='QA22 NEW EDIT '+kind&&afterApprove.current===afterSubmit.candidate&&afterApprove.candidate===null&&afterApprove.likes===0&&afterApprove.original_reaction_retained,status:approvalStatus});
 const staleDecision=await post(action('approve'),{revision_id:String(afterSubmit.candidate)});
 rows.push({kind,check:'stale_reviewer_decision',pass:staleDecision.status===409,status:staleDecision.status});
 await visit('voter',kind);
 const staleReact=await post(action('react'),{revision_id:String(fixtures.initial[kind].approved),value:'1'});
 rows.push({kind,check:'stale_reaction',pass:staleReact.status===409,status:staleReact.status});
 const voteStatus=await submit(page.locator('article[data-review-id="'+head+'"] form[action$="/react/"] button[value="1"]'));
 const afterVote=await invariant(kind);
 rows.push({kind,check:'new_revision_reaction_independent',pass:voteStatus===302&&afterVote.likes===1&&afterVote.reaction_count===2&&afterVote.original_reaction_retained,status:voteStatus});
 await page.screenshot({path:'__QA22_EVIDENCE__/flow-'+kind+'-390.png',fullPage:true});
}
await page.setViewportSize({width:390,height:900});
await visit('staff','reject');
const rejectCandidate=page.locator('[data-candidate-id="'+fixtures.initial.reject.candidate+'"]');
const rejectionStatus=await submit(rejectCandidate.locator('form[action$="/reject/"] button'));
const rejected=await invariant('reject');
rows.push({check:'reviewer_reject_preserves_approved',pass:rejectionStatus===302&&rejected.current===fixtures.initial.reject.approved&&rejected.candidate===null&&rejected.approved_text.includes('QA22 APPROVED reject')&&rejected.original_reaction_retained&&rejected.revision_count===2,status:rejectionStatus});
await visit('public','reject');
rows.push({check:'rejected_candidate_private',pass:(await page.locator('body').innerText()).includes('QA22 APPROVED reject')&&!(await page.locator('body').innerText()).includes('QA22 PENDING reject')});
await visit('author','place');
await page.locator('#review-text').focus();
await page.keyboard.press('Tab');
rows.push({check:'review_form_keyboard',pass:await page.evaluate(()=>document.activeElement?.tagName==='BUTTON')});
await page.locator('#km-burger-open').focus();await page.keyboard.press('Enter');
await page.waitForFunction(()=>document.activeElement?.id==='km-burger-close');
rows.push({check:'mobile_drawer_keyboard',pass:await page.locator('#km-mobile-drawer').getAttribute('aria-hidden')==='false'});
await page.keyboard.press('Escape');
rows.push({check:'mobile_drawer_escape_focus',pass:await page.locator('#km-mobile-drawer').getAttribute('aria-hidden')==='true'&&await page.evaluate(()=>document.activeElement?.id==='km-burger-open')});
return{rows,total:rows.length,passed:rows.filter(row=>row.pass).length,events};
}
