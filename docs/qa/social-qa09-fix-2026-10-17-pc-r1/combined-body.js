async(page)=>{
 const o='http://127.0.0.1:33370',expected=__EXPECTED__,rows=[],errors=[],failed=[],consoleErrors=[];
 const onError=e=>errors.push(e.message),onFail=r=>failed.push(r.url()),onConsole=m=>{if(m.type()==='error')consoleErrors.push({text:m.text(),url:m.location().url});};
 page.on('pageerror',onError);page.on('requestfailed',onFail);page.on('console',onConsole);
 const state=async()=>await(await page.request.get(o+'/qa/state/')).json();const texts=async()=>(await page.locator('.place-reviews-list .review-text').allTextContents()).map(x=>x.trim());const active=async()=>Number((await page.locator('.pagination .page-item.active').textContent()).trim());const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 const finite=async()=>{await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all(document.getAnimations().filter(a=>a.playState==='running'&&Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{}))));};
 await page.setViewportSize({width:390,height:844});
 for(const role of ['guest','author'])for(const lang of ['ru','az','en']){
  const prefix=lang==='az'?'':'/'+lang,base=o+prefix+'/place-reviews/';await page.goto(o+'/qa/login/'+role+'/');const before=await state();
  const first=await page.goto(base+'?sort=likes&page=2');await finite();const p2={url:page.url(),active:await active(),texts:await texts(),selected:await page.locator('select[name="sort"]').inputValue()};
  const canonical=await page.locator('link[rel="canonical"]').getAttribute('href');
  const reload2=await page.reload();await finite();const p2stable=reload2.status()===200&&page.url()===p2.url&&await active()===2&&eq(await texts(),p2.texts);
  const p2png='/mnt/c/kidsmap/.tmp/social09-pc-fix-r1/png/combined2-'+role+'-'+lang+'.png';await page.locator('.pagination').scrollIntoViewIfNeeded();await page.screenshot({path:p2png});
  const page3=page.locator('.pagination a.page-item[href="?sort=likes&page=3"]');const hasSort=await page3.count()===1;
  const [third]=await Promise.all([page.waitForResponse(r=>r.url()===base+'?sort=likes&page=3'),page3.click()]);await finite();const p3={url:page.url(),active:await active(),texts:await texts()};
  const reload3=await page.reload();await finite();const p3stable=reload3.status()===200&&page.url()===p3.url&&await active()===3&&eq(await texts(),p3.texts);
  const p3png='/mnt/c/kidsmap/.tmp/social09-pc-fix-r1/png/combined3-'+role+'-'+lang+'.png';await page.locator('.pagination').scrollIntoViewIfNeeded();await page.screenshot({path:p3png});
  const page1=page.locator('.pagination a.page-item[href="?sort=likes&page=1"]');await page1.focus();const [back]=await Promise.all([page.waitForResponse(r=>r.url()===base+'?sort=likes&page=1'),page1.press('Enter')]);await finite();
  const after=await state();rows.push({id:role+'-'+lang,checks:{initial200:first.status()===200,page2_query:new URL(p2.url).searchParams.get('sort')==='likes'&&new URL(p2.url).searchParams.get('page')==='2',page2_selected:p2.selected==='likes',page2_active:p2.active===2,page2_items:eq(p2.texts,expected.likes.place.slice(12,24)),reload_page2:p2stable,sort_in_page3_link:hasSort,page3_200:third.status()===200,page3_active:p3.active===3,page3_last5:eq(p3.texts,expected.likes.place.slice(24)),reload_page3:p3stable,page1_keyboard:back.status()===200&&await active()===1,page1_items:eq(await texts(),expected.likes.place.slice(0,12)),document_fits:await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),no_business_write:eq(before,after),canonical_base:canonical===base},facts:{p2,p3,before,after,pngs:[p2png,p3png]}});
 }
 page.off('pageerror',onError);page.off('requestfailed',onFail);page.off('console',onConsole);return {rows,pageerrors:errors,requestfailed:failed,consoleErrors};
}
