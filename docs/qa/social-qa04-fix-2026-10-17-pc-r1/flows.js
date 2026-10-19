async (page) => {
  const item=__ITEM__,origin='http://127.0.0.1:33314',url=origin+item.prefix+'/account/notifications/';
  const pageerrors=[],failed=[],posts=[],httpFailures=[];
  const onError=e=>pageerrors.push({message:e.message});
  const onFailed=r=>failed.push({url:r.url(),error:r.failure()?.errorText});
  const onRequest=r=>{if(r.method()==='POST')posts.push({url:r.url(),method:r.method()});};
  const onResponse=r=>{if(r.status()>=400)httpFailures.push({url:r.url(),status:r.status()});};
  page.on('pageerror',onError);page.on('requestfailed',onFailed);page.on('request',onRequest);page.on('response',onResponse);
  await page.setViewportSize({width:item.width,height:844});
  await page.goto(origin+'/qa/login/'+item.key+'/');await page.goto(url);
  await page.evaluate(()=>document.fonts.ready);
  const state=async()=>await(await page.request.get(origin+'/qa/state/'+item.key+'/')).json();
  let before=await state(),fixtureEvent=null,loading=null;
  let selector=item.action.startsWith('accept')?'form[action$="/accept/"]':
    (item.action.startsWith('decline')||['invalid400','stale409'].includes(item.action))?'form[action$="/reject/"]':
    item.action==='join'?'form[action*="/requests/"][action$="/confirm/"]':'form[action$="/read/"]';
  const form=page.locator('.account-main-content '+selector).first();
  if(item.action==='invalid400')await form.evaluate(f=>{const input=document.createElement('input');input.name='unexpected';input.value='fixture';input.type='hidden';f.appendChild(input);});
  if(item.action==='stale409'){
    const token=await form.locator('[name="csrfmiddlewaretoken"]').inputValue();
    const r=await page.request.post(origin+'/qa/revoke/'+item.key+'/',{form:{csrfmiddlewaretoken:token}});
    fixtureEvent={status:r.status(),kind:'SIMULATED concurrent owner cancellation through actual service'};
    if(r.status()!==200)throw new Error('Own cancellation fixture failed');
    before=await state();
  }
  const actionURL=new URL(await form.getAttribute('action'),origin).href;
  let status=null,pendingSnapshot=null;
  if(item.action==='transport'){
    await page.route(actionURL,route=>route.abort('failed'));
    const fail=page.waitForEvent('requestfailed',r=>r.method()==='POST'&&r.url()===actionURL);
    await form.locator('button').click();await fail;
    await page.unroute(actionURL);
  }else{
    let intercepted;
    if(item.action==='loading'){
      let resolve;
      intercepted=new Promise(r=>resolve=r);
      await page.route(actionURL,async route=>{
        const body=new URLSearchParams(route.request().postData()||'');
        loading={simulated_ms:500,csrf_present:body.has('csrfmiddlewaretoken')};
        resolve();await new Promise(r=>setTimeout(r,500));await route.continue();
      });
    }
    const response=page.waitForResponse(r=>r.url()===actionURL&&r.request().method()==='POST');
    const click=form.locator('button').click();
    if(item.action==='loading'){await intercepted;pendingSnapshot=await state();}
    await click;status=(await response).status();
    if(item.action==='loading')await page.unroute(actionURL);
  }
  const after=await state();
  let error=null;
  if(['invalid400','stale409'].includes(item.action)){
    error=await page.locator('[role="alert"]').evaluate(e=>({
      class:e.className,text:e.textContent.trim(),border:getComputedStyle(e).borderTopWidth,
      background:getComputedStyle(e).backgroundColor
    }));
  }
  const same=JSON.stringify(before)===JSON.stringify(after);
  const checks={one_native_action_post:posts.filter(r=>r.url===actionURL).length===1};
  if(['mark_read','loading'].includes(item.action))Object.assign(checks,{
    actual302:status===302,read_saved:before.unread===1&&after.unread===0&&after.read===1});
  else if(item.action==='transport')Object.assign(checks,{simulated_abort_seen:failed.some(f=>f.url===actionURL),no_write:same});
  else if(item.action.startsWith('accept'))Object.assign(checks,{actual302:status===302,accepted:after.invitation_status==='ACCEPTED',
    one_current_grant:after.own_memberships+after.own_grants===1,actions_removed:after.accept===0&&after.reject===0});
  else if(item.action.startsWith('decline'))Object.assign(checks,{actual302:status===302,rejected:after.invitation_status==='REJECTED',
    no_grant:after.own_memberships+after.own_grants===0,actions_removed:after.accept===0&&after.reject===0});
  else if(item.action==='join')Object.assign(checks,{actual302:status===302,joined:after.join_status==='approved'&&after.linked_org===item.org_id,confirmation_removed:after.join===0});
  else Object.assign(checks,{actual_error:status===(item.action==='invalid400'?400:409),no_write:same,error_styled:error?.class.includes('account-notifications__error')&&parseFloat(error.border)>=1});
  if(loading)Object.assign(checks,{finite_loading_no_early_write:JSON.stringify(pendingSnapshot)===JSON.stringify(before),payload_has_csrf:loading.csrf_present});
  let errorPng=null;
  if(error){
    errorPng='/mnt/c/kidsmap/.tmp/social04-pc-fix-r1/png/error-'+item.key+'.png';
    await page.screenshot({path:errorPng,fullPage:true});
  }
  await page.goto(url);await page.evaluate(()=>document.fonts.ready);
  const reloaded=await state();
  checks.reload_matches_saved=JSON.stringify(reloaded)===JSON.stringify(after);
  const presentation=await page.evaluate(()=>({
    overflow:document.documentElement.scrollWidth>innerWidth+1,
    readButtons:document.querySelectorAll('form[action$="/read/"]').length,
    badges:document.querySelectorAll('.account-notifications__unread').length,
    errors:document.querySelectorAll('[role="alert"]').length,
    layout:getComputedStyle(document.querySelector('.account-main-layout')).display
  }));
  Object.assign(checks,{styled_reload:presentation.layout==='flex',no_overflow:!presentation.overflow,
    read_state_badges:presentation.badges===after.unread&&presentation.readButtons===after.unread,
    error_cleared_by_get:presentation.errors===0});
  const png='/mnt/c/kidsmap/.tmp/social04-pc-fix-r1/png/flow-'+item.key+'.png';
  await page.screenshot({path:png,fullPage:true});
  page.off('pageerror',onError);page.off('requestfailed',onFailed);page.off('request',onRequest);page.off('response',onResponse);
  return {item,status,checks,before,after,reloaded,presentation,fixtureEvent,loading,pendingSnapshot,error,pageerrors,
    request_failed:failed,posts,http_failures:httpFailures,png,errorPng};
}
