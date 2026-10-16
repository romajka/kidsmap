async(page)=>{
 const B='__BASE__',ROOT='__HERE__',rows=[];
 for(const lang of ['ru','az','en']){
  await page.context().addCookies([{name:'django_language',value:lang,url:B}]);
  for(const width of [360,390,768,1024,1280,1440]){
   await page.setViewportSize({width,height:950});await page.goto(B+'/admin/catalog/place/?q=QA02+LOCAL+BULK');await page.addStyleTag({content:'.km-columns-details {margin-left:auto;}'});await page.locator('#km-columns-menu summary').press('Enter');
   const g=await page.locator('.km-columns-dropdown').evaluate(e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,viewport:innerWidth};});
   const cb=page.locator('[data-toggle-col=column-col_location]');await cb.uncheck();const hidden=await page.locator('.column-col_location').first().isVisible();await cb.check();
   const screenshot='screenshots/proposed-columns-'+lang+'-'+width+'.png';await page.screenshot({path:ROOT+'/'+screenshot});rows.push({lang,width,geometry:g,mouse_toggle:!hidden,mouse_restore:await cb.isChecked(),status:g.left>=0&&g.right<=width&&!hidden&&await cb.isChecked()?'PASS':'FAIL',screenshot});
  }
 }
 return{rows,mode:'Temporary QA addStyleTag for proposed ORG-QA-05, application unchanged'};
}
