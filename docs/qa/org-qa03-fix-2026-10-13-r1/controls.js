async(page)=>{
 const B='__BASE__',ROOT='__HERE__',rows=[];
 for(const lang of ['ru','az','en']){
  await page.context().addCookies([{name:'django_language',value:lang,url:B}]);
  for(const width of [390,1024]){
   await page.setViewportSize({width,height:950});await page.goto(B+'/admin/catalog/place/?q=QA02+LOCAL+BULK');
   for(const selector of ['#searchbar','#km-toggle-filters-btn','#km-sort-menu summary','#km-columns-menu summary']){
    const l=page.locator(selector);if(!await l.count()){rows.push({id:lang+'-'+width+'-'+selector,status:'NOT RUN',reason:'selector unavailable'});continue;}
    await l.focus();const f=await l.evaluate(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return{focused:document.activeElement===e,outline:s.outlineStyle,outlineWidth:s.outlineWidth,shadow:s.boxShadow,searchFocusBorder:e.closest('.km-search-box')?getComputedStyle(e.closest('.km-search-box')).borderColor:null,rect:{left:r.left,right:r.right,top:r.top,bottom:r.bottom},viewport:innerWidth};});rows.push({id:lang+'-'+width+'-'+selector,status:f.focused&&f.rect.left>=0&&f.rect.right<=width?'PASS':'FAIL',focus:f});
   }
   await page.locator('#km-columns-menu summary').press('Enter');const cb=page.locator('[data-toggle-col=column-col_location]');await cb.uncheck();const hidden=await page.locator('#result_list .column-col_location').first().isVisible().catch(()=>null);rows.push({id:'columns-hide-'+lang+'-'+width,status:!await cb.isChecked()&&hidden===false?'PASS':'FAIL',hidden});await cb.check();rows.push({id:'columns-restore-'+lang+'-'+width,status:await cb.isChecked()?'PASS':'FAIL'});await page.locator('#km-columns-menu summary').press('Enter');const mobileScroll=await page.locator('.card-body.table-responsive').first().evaluate(e=>({overflowX:getComputedStyle(e).overflowX,scroll:e.scrollWidth,client:e.clientWidth}));rows.push({id:'table-scroll-'+lang+'-'+width,status:width>768||['auto','scroll'].includes(mobileScroll.overflowX)?'PASS':'FAIL',mobileScroll});
   const screenshot='screenshots/'+lang+'-'+width+'-keyboard-'+Date.now()+'.png';await page.screenshot({path:ROOT+'/'+screenshot});rows[rows.length-1].screenshot=screenshot;
  }
 }
 return{rows};
}
