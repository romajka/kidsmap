async (page) => {
  const origin='http://127.0.0.1:33325',rules=__RULES__,rows=[];
  const measure=async()=>await page.evaluate(()=>{
    const rect=s=>{const e=document.querySelector(s),r=e.getBoundingClientRect();return {right:r.right+scrollX,width:r.width,scrollWidth:e.scrollWidth};};
    const grid=document.querySelector('.review-form-grid');
    return {documentWidth:document.documentElement.scrollWidth,viewport:innerWidth,
      grid:rect('.review-form-grid'),hero:rect('.reviews-polished-hero'),toolbar:rect('.reviews-polished-toolbar-wrap'),
      tracks:getComputedStyle(grid).gridTemplateColumns,rootOverflow:getComputedStyle(document.documentElement).overflowX,
      bodyOverflow:getComputedStyle(document.body).overflowX,panelOverflow:getComputedStyle(document.querySelector('.site-reviews-page')).overflowX};
  });
  await page.goto(origin+'/qa/login/author/');
  for(const [lang,prefix,width] of [['ru','/ru',768],['az','',768],['en','/en',768],
    ['ru','/ru',360],['ru','/ru',760],['ru','/ru',761],['ru','/ru',1024]]){
    await page.setViewportSize({width,height:844});await page.goto(origin+prefix+'/reviews/');
    await page.evaluate(()=>document.fonts.ready);
    const stateBefore=await(await page.request.get(origin+'/qa/state/')).json();
    const before=await measure();
    const tag=await page.addStyleTag({content:rules});
    const preview=await measure();
    const png='/mnt/c/kidsmap/.tmp/social05-pc-plan-r1/png/preview-SIMULATED-'+lang+'-'+width+'.png';
    await page.screenshot({path:png,fullPage:true});
    await tag.evaluate(e=>e.remove());
    const restored=await measure(),stateAfter=await(await page.request.get(origin+'/qa/state/')).json();
    const checks={preview_document_fits:preview.documentWidth<=width+1,preview_grid_fits:preview.grid.right<=width+1,
      preview_hero_fits:preview.hero.right<=width+1,preview_toolbar_fits:preview.toolbar.right<=width+1,
      no_clipping_change:['rootOverflow','bodyOverflow','panelOverflow'].every(k=>before[k]===preview[k]),
      restored_original_geometry:JSON.stringify(before)===JSON.stringify(restored),
      no_business_write:JSON.stringify(stateBefore)===JSON.stringify(stateAfter)};
    rows.push({lang,width,attribution:'SIMULATED client-side CSS hypothesis probe; not application patch/acceptance',
      checks,before,preview,restored,stateBefore,stateAfter,png});
  }
  return rows;
}
