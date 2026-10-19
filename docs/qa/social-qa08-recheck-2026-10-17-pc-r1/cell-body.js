async(page)=>{
 const item=__ITEM__,o='http://127.0.0.1:33358',prefix=item.lang==='az'?'':'/'+item.lang,errors=[],failed=[],http=[];
 const onError=e=>errors.push(e.message),onFail=r=>failed.push({url:r.url(),error:r.failure()?.errorText}),onResponse=r=>{if(r.status()>=400)http.push({url:r.url(),status:r.status()});};
 page.on('pageerror',onError);page.on('requestfailed',onFail);page.on('response',onResponse);
 const ownerContext=await page.context().browser().newContext({viewport:{width:1280,height:900},serviceWorkers:'block'});
 await ownerContext.route('**/*',r=>{const u=new URL(r.request().url());return u.hostname==='127.0.0.1'&&u.port==='33358'?r.continue():r.abort('blockedbyclient');});
 const owner=await ownerContext.newPage();owner.on('pageerror',onError);owner.on('requestfailed',onFail);owner.on('response',onResponse);
 const state=async()=>await(await page.request.get(o+'/qa/state/'+item.key+'/')).json();
 const finite=async()=>{await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all(document.getAnimations().filter(a=>a.playState==='running'&&Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{}))));};
 let row;
 try{
 await owner.goto(o+'/qa/login/'+item.key+'/owner/');
 await owner.goto(o+prefix+(item.kind==='place'?'/account/places/team/':'/account/organizations/'+item.target_id+'/'));
 const form=owner.locator(item.kind==='place'?'.owner-team-invite-form':'[data-team-form]');
 await form.locator('input[name="email"]').fill(item.email);
 if(item.kind==='place')await form.locator('select[name="place"]').selectOption(String(item.target_id));
 const [inviteResponse]=await Promise.all([owner.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/invite/')),form.locator('button[type="submit"]').click()]);
 let pending=await state();
 if(!pending.notice_id)throw Error('Native invite produced no recipient notification: '+JSON.stringify(pending));
 await page.setViewportSize({width:item.width,height:844});await page.goto(o+'/qa/login/'+item.key+'/recipient/');
 const inboxResponse=await page.goto(o+prefix+'/account/notifications/');await finite();
 const acceptPath=prefix+'/account/notifications/'+pending.notice_id+'/accept/';
 const accept=page.locator('form[action="'+acceptPath+'"] button[type="submit"]');
 const liveButton=await accept.count()===1;
 await accept.scrollIntoViewIfNeeded();await page.screenshot({path:'/mnt/c/kidsmap/.tmp/social08-pc-plan-r1/png/pending-'+item.key+'.png'});
 if(item.kind==='organization'){
  await owner.goto(o+prefix+'/account/organizations/'+item.target_id+'/');
  await owner.locator('[data-team-confirm-open="org-invite-cancel-'+pending.invitation_id+'"]').click();
 }
 const cancelForm=owner.locator(item.kind==='place'?'form[action$="/invitations/'+pending.invitation_id+'/cancel/"]':'form[data-team-operation="cancel"][data-invitation-id="'+pending.invitation_id+'"]');
 const [cancelResponse]=await Promise.all([owner.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/cancel/')),cancelForm.locator('button[type="submit"]').click()]);
 const canceled=await state();
 await accept.focus();const focused=await accept.evaluate(e=>document.activeElement===e);
 const [denial]=await Promise.all([page.waitForResponse(r=>r.url()===o+acceptPath&&r.request().method()==='POST'),accept.press('Enter')]);await page.waitForURL(u=>u.href===o+acceptPath||u.protocol==='chrome-error:',{waitUntil:'domcontentloaded'});await finite();
 const after=await state(),body=(await page.locator('body').textContent()).trim(),links=await page.locator('a').count(),alert=page.locator('[role="alert"]');
 const feedback=await alert.count()? (await alert.first().textContent()).trim():'';
 const translated={ru:'Приглашение больше недоступно. Обновите список.',az:'Dəvət artıq əlçatan deyil. Siyahını yeniləyin.',en:'The invitation is no longer available. Refresh the list.'}[item.lang];
 const hasBack=await page.locator('a[href="'+prefix+'/account/notifications/"]').count()>0;
 const denialPng='/mnt/c/kidsmap/.tmp/social08-pc-plan-r1/png/denied-'+item.key+'.png';await page.screenshot({path:denialPng});
 const controls={owner_invite_native:inviteResponse.status()===(item.kind==='place'?302:200),pending_inbox200:inboxResponse.status()===200,pending_accept_button:liveButton,owner_cancel_native:cancelResponse.status()===(item.kind==='place'?302:200),canceled_status:canceled.status==='CANCELED',accept_keyboard_focused:focused,denial403:denial.status()===403,no_membership:after.memberships===0,no_org_grant:after.grants===0,no_denial_write:JSON.stringify(canceled)===JSON.stringify(after)};
 const source={localized_feedback:feedback===translated,usable_inbox_link:hasBack,account_shell:await page.locator('.account-notifications h1').count()===1};
 const recovery=await page.goto(o+prefix+'/account/notifications/');const reload=await page.reload();await finite();
 controls.get_recovery200=recovery.status()===200&&reload.status()===200;controls.revoked_action_hidden=await page.locator('form[action="'+acceptPath+'"]').count()===0;controls.recovery_no_grant=(await state()).memberships===0&&(await state()).grants===0;
 row={item,controls,source,facts:{pending,canceled,after,denial_status:denial.status(),response_body_length:Number(denial.headers()['content-length']),rendered_url:page.url(),rendered_body_length:body.length,links,feedback},pngs:['pending-'+item.key+'.png','denied-'+item.key+'.png'],pageerrors:errors,request_failed:failed,http_failures:http};
 }finally{await ownerContext.close();page.off('pageerror',onError);page.off('requestfailed',onFail);page.off('response',onResponse);}
 return row;
}


