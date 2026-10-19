async (page) => {
  const origin='http://127.0.0.1:33326',rows=[],errors=[],failed=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push({url:r.url(),error:r.failure()?.errorText}));
  const state=async()=>await(await page.request.get(origin+'/qa/state/')).json();
  try {
    await page.goto(origin+'/qa/login/author/');await page.setViewportSize({width:390,height:844});
    await page.goto(origin+'/ru/reviews/');await page.evaluate(()=>document.fonts.ready);
    const form=page.locator('#site-reviews form.review-form'),text='Fictional retained network input';
    await form.locator('[name=text]').fill(text);
    const before=await state(),action=new URL(await form.getAttribute('action'),origin).href;
    let release,entered,n=0;const held=new Promise(r=>release=r),caught=new Promise(r=>entered=r);
    const blocker=async route=>{n++;entered();await held;await route.abort('failed');};
    await page.route(action,blocker);await form.locator('button[type=submit]').click();await caught;
    const pending={disabled:await form.locator('button[type=submit]').isDisabled(),aria_busy:await form.getAttribute('aria-busy')==='true'};
    await page.screenshot({path:'/mnt/c/kidsmap/.tmp/social05-pc-fix-r1/png/SIMULATED-submit-pending-ru-390.png'});
    release();await page.locator('[data-review-live][role=alert]:not([hidden])').waitFor();
    await page.waitForFunction(()=>!document.querySelector('#site-reviews form button[type=submit]').disabled);
    const after=await state();
    rows.push({id:'SIMULATED-submit-delay-abort',checks:{...pending,one_request:n===1,
      form_visible:await form.isVisible(),input_retained:await form.locator('[name=text]').inputValue()===text,
      error_visible:await page.locator('[data-review-live][role=alert]').isVisible(),
      button_reenabled:!(await form.locator('button[type=submit]').isDisabled()),no_write:JSON.stringify(before)===JSON.stringify(after)},
      facts:{before,after,attribution:'SIMULATED request held then aborted before server delivery'}});
    await page.screenshot({path:'/mnt/c/kidsmap/.tmp/social05-pc-fix-r1/png/SIMULATED-submit-error-ru-390.png'});
    await page.unroute(action,blocker);
    return {rows,pageerrors:errors,request_failed:failed};
  }catch(e){return {rows,pageerrors:errors,request_failed:failed,fatal:{message:e.message}};}
}
