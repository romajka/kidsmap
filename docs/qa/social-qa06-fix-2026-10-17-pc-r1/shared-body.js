async (page) => {
  const targets=__TARGETS__,origin='http://127.0.0.1:33337',rows=[],errors=[],http=[],failed=[];
  const state=async()=>await(await page.request.get(origin+'/qa/state/')).json();
  const finite=async()=>{await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all(document.getAnimations().filter(a=>a.playState==='running'&&Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{}))));};
  page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)http.push({url:r.url(),status:r.status()});});
  page.on('requestfailed',r=>failed.push({url:r.url(),error:r.failure()?.errorText}));
  try {
    await page.goto(origin+'/qa/login/author/');const before=await state();
    for(const target of targets){
      for(const [lang,prefix] of [['ru','/ru'],['az',''],['en','/en']]){
        for(const width of [390,768,1440]){
          await page.setViewportSize({width,height:844});
          const response=await page.goto(origin+prefix+target.url);await finite();
          const checks={status200:response.status()===200,
            site_widget_absent:await page.locator('.site-reviews-page .review-form-grid').count()===0,
            site_inline_handler_absent:!(await page.content()).includes('function choose(value, moveFocus = false)'),
            document_fits:await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)};
          let facts={};
          if(target.kind==='place_detail'){
            const star=page.locator('.detail-stars__btn[data-value="3"]');await star.focus();await page.keyboard.press('Space');
            checks.native_rating3=await page.locator('[data-review-rating-input]').inputValue()==='3';
            checks.native_selected3=await star.getAttribute('aria-checked')==='true';
            checks.five_existing_radios=await page.locator('.detail-stars__btn[role=radio]').count()===5;
            await page.locator('[data-review-stars]').scrollIntoViewIfNeeded();await finite();
          }else if(['activity','specialist','event'].includes(target.kind)){
            const field=page.locator('#review-text');await field.scrollIntoViewIfNeeded();await finite();
            checks.existing_editor=await field.isVisible();
            checks.csrf=await page.locator('form [name=csrfmiddlewaretoken]').count()>0;
            facts.heading=(await page.locator('h1').textContent()).trim();
            // Existing SOCIAL07 is recorded, not asserted GREEN or repaired here.
            facts.existing_social07=target.kind==='activity'&&facts.heading.includes('Activity object (');
          }else{
            checks.main_content=await page.locator('main').count()>0;
          }
          const png='/mnt/c/kidsmap/.tmp/social06-pc-fix-r1/png/shared-'+target.kind+'-'+lang+'-'+width+'.png';
          await page.screenshot({path:png});
          rows.push({id:target.kind+'-'+lang+'-'+width,kind:target.kind,lang,width,checks,facts,png});
        }
      }
    }
    return {rows,pageerrors:errors,http_failures:http,request_failed:failed,before,after:await state()};
  }catch(e){return {rows,pageerrors:errors,http_failures:http,request_failed:failed,fatal:{message:e.message,stack:e.stack}};}
}
