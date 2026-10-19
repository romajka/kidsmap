async(page)=>{
 const o='http://127.0.0.1:33359',cases=__CASES__,changed=__CHANGED__,rows=[],errors=[],failed=[],consoleErrors=[];
 const onError=e=>errors.push(e.message),onFail=r=>failed.push({url:r.url(),error:r.failure()?.errorText}),onConsole=m=>{if(m.type()==='error')consoleErrors.push({text:m.text(),url:m.location().url});};
 page.on('pageerror',onError);page.on('requestfailed',onFail);page.on('console',onConsole);
 const oc=await page.context().browser().newContext({viewport:{width:1280,height:900},serviceWorkers:'block'});
 await oc.route('**/*',r=>{const u=new URL(r.request().url());return u.hostname==='127.0.0.1'&&u.port==='33359'?r.continue():r.abort('blockedbyclient');});
 const owner=await oc.newPage();owner.on('pageerror',onError);owner.on('requestfailed',onFail);owner.on('console',onConsole);
 const state=async key=>await(await page.request.get(o+'/qa/state/'+key+'/')).json();
 const login=async(key,role)=>await page.goto(o+'/qa/login/'+key+'/'+role+'/');
 const token=async()=> (await page.context().cookies(o)).find(c=>c.name==='csrftoken')?.value;
 try{
 for(const item of cases){
  const prefix=item.lang==='az'?'':'/'+item.lang;
  await login(item.key,'recipient');await page.goto(o+prefix+'/account/notifications/');
  const initial=await state(item.key),path=prefix+'/account/notifications/'+initial.notice_id+'/accept/',before=await state(item.key);
  const get=await page.request.get(o+path,{maxRedirects:0});
  const csrf=await page.request.post(o+path,{form:{},maxRedirects:0});
  await login(item.key,'outsider');const foreign=await page.request.post(o+path,{form:{csrfmiddlewaretoken:await token()},maxRedirects:0});
  const foreignBody=await foreign.text();
  await login(item.key,'guest');const anon=await page.request.post(o+path,{form:{csrfmiddlewaretoken:await token()},maxRedirects:0});
  const edge=changed.find(c=>c.kind===item.kind&&c.lang===item.lang);await login(edge.key,'recipient');
  const changedResponse=await page.request.post(o+prefix+'/account/notifications/'+edge.notice_id+'/accept/',{form:{csrfmiddlewaretoken:await token()},maxRedirects:0});
  const negativeAfter=await state(item.key);
  const negative={GET405:get.status()===405,csrf403:csrf.status()===403,foreign404:foreign.status()===404,foreign_no_unavailable_copy:!foreignBody.includes('invitation is no longer available')&&!foreignBody.includes('Приглашение больше недоступно')&&!foreignBody.includes('Dəvət artıq əlçatan deyil'),anonymous302:anon.status()===302,anonymous_login_location:(anon.headers().location||'').includes('login'),changed_email404:changedResponse.status()===404,negative_no_write:JSON.stringify(before)===JSON.stringify(negativeAfter)};
  rows.push({id:item.kind+'-'+item.lang+'-guards',checks:negative,facts:{mode:'real browser-context HTTP requests for method/CSRF/ACL guards',statuses:{get:get.status(),csrf:csrf.status(),foreign:foreign.status(),anonymous:anon.status(),changed_email:changedResponse.status()},before,after:negativeAfter}});
  await owner.goto(o+'/qa/login/'+item.key+'/owner/');await owner.goto(o+prefix+(item.kind==='place'?'/account/places/team/':'/account/organizations/'+item.target_id+'/'));
  const form=owner.locator(item.kind==='place'?'.owner-team-invite-form':'[data-team-form]');await form.locator('input[name="email"]').fill(item.email);
  if(item.kind==='place')await form.locator('select[name="place"]').selectOption(String(item.target_id));
  const [invite]=await Promise.all([owner.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/invite/')),form.locator('button[type="submit"]').click()]);
  const pending=await state(item.key);
  await login(item.key,'recipient');await page.setViewportSize({width:390,height:844});await page.goto(o+prefix+'/account/notifications/');
  const acceptPath=prefix+'/account/notifications/'+pending.notice_id+'/accept/',accept=page.locator('form[action="'+acceptPath+'"] button[type="submit"]');await accept.focus();
  const [accepted]=await Promise.all([page.waitForResponse(r=>r.url()===o+acceptPath&&r.request().method()==='POST'),accept.press('Enter')]);await page.waitForURL(o+prefix+'/account/notifications/');
  const reload=await page.reload();await page.evaluate(()=>document.fonts.ready);const after=await state(item.key);
  const png='/mnt/c/kidsmap/.tmp/social08-pc-fix-r1/png/current-'+item.kind+'-'+item.lang+'.png';await page.locator('h1').scrollIntoViewIfNeeded();await page.screenshot({path:png});
  rows.push({id:item.kind+'-'+item.lang+'-current',checks:{native_owner_invite:invite.status()===(item.kind==='place'?302:200),pending_valid:pending.status==='PENDING',native_accept302:accepted.status()===302,inbox_reloaded200:reload.status()===200,accepted_status:after.status==='ACCEPTED',single_target_grant:item.kind==='place'?after.memberships===1&&after.grants===0:after.grants===1&&after.memberships===0,accepted_action_hidden:await page.locator('form[action="'+acceptPath+'"]').count()===0,document_fits:await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)},facts:{mode:'actual native owner invite and recipient keyboard Accept → GET inbox reload',pending,after,png}});
 }
 }finally{await oc.close();page.off('pageerror',onError);page.off('requestfailed',onFail);page.off('console',onConsole);}
 return {rows,pageerrors:errors,requestfailed:failed,consoleErrors};
}
