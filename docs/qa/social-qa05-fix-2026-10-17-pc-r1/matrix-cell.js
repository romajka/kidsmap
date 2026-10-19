async (page) => {
  const item=__ITEM__,origin='http://127.0.0.1:33326';
  const pageerrors=[],failed=[],httpFailures=[];
  const onError=e=>pageerrors.push({message:e.message});
  const onFailed=r=>failed.push({url:r.url(),error:r.failure()?.errorText});
  const onResponse=r=>{if(r.status()>=400)httpFailures.push({url:r.url(),status:r.status()});};
  page.on('pageerror',onError);page.on('requestfailed',onFailed);page.on('response',onResponse);
  await page.setViewportSize({width:item.width,height:844});
  await page.goto(origin+'/qa/login/'+item.role+'/');
  const state=async()=>await(await page.request.get(origin+'/qa/state/')).json();
  const before=await state(),response=await page.goto(origin+item.url);
  await page.locator('.site-reviews-page h1').waitFor();await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all(document.getAnimations().filter(a=>a.playState==='running'&&Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{}))));
  const facts=await page.evaluate(()=>{
    const rect=e=>{if(!e)return null;const r=e.getBoundingClientRect();return {left:r.left+scrollX,right:r.right+scrollX,width:r.width,scrollWidth:e.scrollWidth};};
    const grid=document.querySelector('.review-form-grid'),form=document.querySelector('#site-reviews form.review-form');
    return {viewport:innerWidth,documentWidth:document.documentElement.scrollWidth,scrollX,
      panel:rect(document.querySelector('.site-reviews-page')),hero:rect(document.querySelector('.reviews-polished-hero')),
      toolbar:rect(document.querySelector('.reviews-polished-toolbar-wrap')),
      sort:rect(document.querySelector('.reviews-polished-toolbar')),grid:rect(grid),form:rect(form),
      gridTracks:grid?getComputedStyle(grid).gridTemplateColumns:null,gridLabels:grid?grid.querySelectorAll(':scope>label').length:0,
      fields:form?[...form.querySelectorAll('input:not([type=hidden]),textarea,[data-review-stars]')].map(rect):[],
      reactions:[...document.querySelectorAll('.site-reviews-page .review-reaction-btn')].map(rect),
      authorForm:Boolean(form),csrf:form?Boolean(form.querySelector('[name="csrfmiddlewaretoken"]')):null,
      post:form?.method,action:form?.action,heading:document.querySelector('.site-reviews-page h1').textContent.trim(),
      cards:document.querySelectorAll('.site-reviews-page .review-item').length,
      rootOverflow:getComputedStyle(document.documentElement).overflowX,bodyOverflow:getComputedStyle(document.body).overflowX,
      panelOverflow:getComputedStyle(document.querySelector('.site-reviews-page')).overflowX,
      css:[...document.styleSheets].map(s=>s.href).filter(Boolean)};
  });
  const after=await state();
  const fits=r=>!r||(r.left>=-1&&r.right<=item.width+1);
  const controls={status200:response.status()===200,canonical_url:page.url()===origin+item.url,
    localized_heading:facts.heading===item.heading,expected_form:facts.authorForm===(item.role==='author'),
    expected_two_grid_fields:facts.gridLabels===(item.role==='author'?2:0),two_public_cards:facts.cards===2,
    author_csrf_post:item.role==='guest'||(facts.csrf&&facts.post==='post'&&facts.action.endsWith('/review/')),
    site_css_loaded:facts.css.some(s=>s.includes('/static/css/site.css')),no_business_write:JSON.stringify(before)===JSON.stringify(after)};
  const layout={document_fits:facts.documentWidth<=item.width+1,hero_fits:fits(facts.hero),toolbar_fits:fits(facts.toolbar),
    sort_fits:fits(facts.sort),reactions_fit:facts.reactions.every(fits)};
  if(facts.form)Object.assign(layout,{form_fits:fits(facts.form),grid_fits:fits(facts.grid),fields_fit:facts.fields.every(fits)});
  const png='/mnt/c/kidsmap/.tmp/social05-pc-fix-r1/png/site-'+item.role+'-'+item.lang+'-'+item.width+'.png';
  await page.screenshot({path:png,fullPage:true});
  page.off('pageerror',onError);page.off('requestfailed',onFailed);page.off('response',onResponse);
  return {item,controls,layout,facts,before,after,pageerrors,request_failed:failed,http_failures:httpFailures,png};
}
