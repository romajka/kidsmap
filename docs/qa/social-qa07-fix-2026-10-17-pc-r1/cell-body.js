async (page) => {
  const item=__ITEM__,origin='http://127.0.0.1:33348',errors=[],http=[],failed=[];
  const onError=e=>errors.push(e.message),onHTTP=r=>{if(r.status()>=400)http.push({url:r.url(),status:r.status()});},onFailed=r=>failed.push({url:r.url(),error:r.failure()?.errorText});
  page.on('pageerror',onError);page.on('response',onHTTP);page.on('requestfailed',onFailed);
  const finite=async()=>{await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all(document.getAnimations().filter(a=>a.playState==='running'&&Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{}))));};
  const state=async()=>await(await page.request.get(origin+'/qa/state/')).json();
  await page.setViewportSize({width:item.width,height:844});await page.goto(origin+'/qa/login/'+item.role+'/');
  const before=await state(),pngs=[];let controls={},source={},facts={};
  if(item.kind==='activity'){
    const detailResponse=await page.goto(origin+item.prefix+item.detail);await finite();
    const detailHeading=(await page.locator('h1').textContent()).trim();
    const detailFits=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1);
    await page.locator('h1').scrollIntoViewIfNeeded();
    const dp='/mnt/c/kidsmap/.tmp/social07-pc-fix-r1/png/detail-'+item.id+'.png';await page.screenshot({path:dp});pngs.push(dp);
    const url=origin+item.prefix+item.reviews,link=page.locator('a[href="'+item.prefix+item.reviews+'"]').first();
    const exists=await link.count()===1;
    const [reviewResponse]=await Promise.all([page.waitForResponse(r=>r.url()===url&&r.request().method()==='GET'),link.click()]);
    await page.waitForURL(url);await finite();
    const heading=(await page.locator('h1').textContent()).trim(),title=await page.title();
    const reloadResponse=await page.reload();await finite();
    const reloaded=(await page.locator('h1').textContent()).trim();
    await page.locator('h1').scrollIntoViewIfNeeded();
    const rp='/mnt/c/kidsmap/.tmp/social07-pc-fix-r1/png/reviews-'+item.id+'.png';await page.screenshot({path:rp});pngs.push(rp);
    controls={detail_status200:detailResponse.status()===200,review_status200:reviewResponse.status()===200&&reloadResponse.status()===200,
      public_detail_human_name:detailHeading===item.expected,real_native_review_link:exists&&page.url()===url,
      localized_review_prefix:heading.startsWith(item.headingPrefix),
      expected_author_editor:await page.locator('#review-text').count()===(item.role==='author'?1:0),
      both_documents_fit:detailFits&&await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),
      reload_stable:heading===reloaded,no_business_write:JSON.stringify(before)===JSON.stringify(await state())};
    source={human_heading:heading===item.headingPrefix+' '+item.expected,
      human_document_title:title.includes(item.expected),no_technical_object_id:!heading.includes('Activity object (')&&!title.includes('Activity object (')};
    facts={detailHeading,heading,title,reloaded};
  }else{
    const response=await page.goto(origin+item.prefix+item.reviews);await finite();
    const heading=(await page.locator('h1').textContent()).trim();
    const png='/mnt/c/kidsmap/.tmp/social07-pc-fix-r1/png/shared-'+item.id+'.png';await page.screenshot({path:png});pngs.push(png);
    controls={status200:response.status()===200,human_heading:heading===item.headingPrefix+' '+item.expected,
      no_technical_object_id:!/\b(?:Activity|Place|Specialist|Event) object \(\d+\)/.test(heading),
      expected_editor:await page.locator('#review-text').count()===(item.role==='author'?1:0),
      document_fits:await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),
      no_business_write:JSON.stringify(before)===JSON.stringify(await state())};
    facts={heading};
  }
  const after=await state();
  page.off('pageerror',onError);page.off('response',onHTTP);page.off('requestfailed',onFailed);
  return {item,controls,source,facts,before,after,pngs,pageerrors:errors,http_failures:http,request_failed:failed};
}
