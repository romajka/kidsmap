async (page) => {
  const origin='http://127.0.0.1:33314',rows=[];
  for(const [lang,prefix] of [['ru','/ru'],['az',''],['en','/en']]){
    const item=__CASES__.find(c=>c.key===lang+'-transport'),url=origin+prefix+'/account/notifications/';
    const state=async()=>await(await page.request.get(origin+'/qa/state/'+item.key+'/')).json();
    const before=await state();
    await page.context().clearCookies();
    const guest=await page.request.get(url,{maxRedirects:0});
    const guestPost=await page.request.post(origin+prefix+'/account/notifications/'+item.notice_id+'/read/',{maxRedirects:0});
    await page.goto(origin+'/qa/login/outsider/');await page.goto(url);
    const outsiderRows=await page.locator('.account-main-content .org-row').count();
    const token=await page.locator('[name="csrfmiddlewaretoken"]').first().count()
      ? await page.locator('[name="csrfmiddlewaretoken"]').first().inputValue():null;
    // Empty inbox has no form token. Obtain a valid token from the ordinary profile form.
    if(!token)await page.goto(origin+prefix+'/account/profile/');
    const csrf=token||await page.locator('[name="csrfmiddlewaretoken"]').first().inputValue();
    const read=origin+prefix+'/account/notifications/'+item.notice_id+'/read/';
    const validOutsider=await page.request.post(read,{form:{csrfmiddlewaretoken:csrf},maxRedirects:0});
    await page.goto(origin+'/qa/login/'+item.key+'/');await page.goto(url);
    const missing=await page.request.post(read,{form:{},maxRedirects:0});
    const recipientToken=await page.locator('form[action$="/read/"] [name="csrfmiddlewaretoken"]').inputValue();
    const getAction=await page.request.get(read,{maxRedirects:0});
    const after=await state();
    const checks={guest_get_login:guest.status()===302,guest_post_denied:[302,403].includes(guestPost.status()),
      outsider_no_rows:outsiderRows===0,outsider_valid_csrf_404:validOutsider.status()===404,
      recipient_missing_csrf_403:missing.status()===403,get_action_405:getAction.status()===405,
      recipient_has_csrf:Boolean(recipientToken),no_business_write:JSON.stringify(before)===JSON.stringify(after)};
    rows.push({lang,checks,statuses:{guest:guest.status(),guestPost:guestPost.status(),outsider:validOutsider.status(),
      missingCsrf:missing.status(),getAction:getAction.status()},before,after});
  }
  return rows;
}
