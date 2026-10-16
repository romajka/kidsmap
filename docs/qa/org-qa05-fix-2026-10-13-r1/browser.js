async(page)=>{
 const B='__BASE__',ROOT='__HERE__',rows=[],errors=[],consoleEvents=[],network=[],blocked={};
 await page.context().route('**/*',r=>{const url=r.request().url();if(url.startsWith(B+'/'))return r.continue();try{const o=new URL(url).origin;blocked[o]=(blocked[o]||0)+1;}catch{}return r.abort();});
 page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(['warning','error'].includes(m.type()))consoleEvents.push({type:m.type(),text:m.text().slice(0,300),url:m.location().url});});page.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)network.push({url:r.url().split('?')[0],status:r.status()});});
 await page.goto(B+'/admin/login/?next=/admin/');await page.locator('[name=username]').fill('start_admin');await page.locator('[name=password]').fill('__PASSWORD__');await Promise.all([page.waitForNavigation(),page.locator('[type=submit]').click()]);
 for(const lang of ['ru','az','en']){
  await page.context().addCookies([{name:'django_language',value:lang,url:B}]);
  for(const width of [360,390,768,1024,1280,1440]){
   await page.setViewportSize({width,height:950});await page.goto(B+'/admin/catalog/place/?q=QA02+LOCAL+BULK');
   for(const sidebar of ['default','toggled']){
    if(sidebar==='toggled'){await page.locator('[data-widget=pushmenu]').first().click();await page.waitForTimeout(350);}
    const trigger=page.locator('#km-columns-menu summary');await trigger.focus();await page.keyboard.press('Enter');
    const g=await page.locator('.km-columns-dropdown').evaluate(e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,viewport:innerWidth,document:document.documentElement.scrollWidth};});
    const cb=page.locator('[data-toggle-col=column-col_location]');await cb.uncheck();const hidden=!await page.locator('.column-col_location').first().isVisible();await cb.check();const shown=await page.locator('.column-col_location').first().isVisible();
    await cb.focus();const focus=await cb.evaluate(e=>{const r=e.getBoundingClientRect();const s=getComputedStyle(e);return{focused:e===document.activeElement,left:r.left,right:r.right,outline:s.outlineStyle,outlineWidth:s.outlineWidth};});await page.keyboard.press('Space');const keyboardHide=!await cb.isChecked()&&!await page.locator('.column-col_location').first().isVisible();await page.keyboard.press('Space');const keyboardRestore=await cb.isChecked();
    const screenshot='screenshots/'+lang+'-'+width+'-'+sidebar+'-columns.png';await page.screenshot({path:ROOT+'/'+screenshot});
    const ok=g.left>=0&&g.right<=width&&g.document<=width+1&&hidden&&shown&&keyboardHide&&keyboardRestore&&focus.focused&&focus.left>=0&&focus.right<=width;
    rows.push({id:lang+'-'+width+'-'+sidebar,lang,width,sidebar,status:ok?'PASS':'FAIL',geometry:g,mouseHide:hidden,mouseRestore:shown,keyboardHide,keyboardRestore,focus,screenshot});await trigger.press('Enter');
   }
   await page.reload();await page.locator('#km-columns-menu summary').press('Enter');rows.push({id:'reload-'+lang+'-'+width,lang,width,status:await page.locator('[data-toggle-col=column-col_location]').isChecked()?'PASS':'FAIL'});await page.locator('#km-columns-menu summary').press('Enter');
  }
  for(const model of ['event','specialist','placeownershiprequest','placereview']){
   await page.setViewportSize({width:390,height:950});const r=await page.goto(B+'/admin/catalog/'+model+'/');await page.locator('#km-columns-menu summary').press('Enter');const g=await page.locator('.km-columns-dropdown').evaluate(e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,viewport:innerWidth};});rows.push({id:'shared-'+model+'-'+lang,lang,model,status:r.status()===200&&g.left>=0&&g.right<=390?'PASS':'FAIL',geometry:g});
  }
 }
 return{rows,errors,consoleEvents,network,blockedExternalOrigins:blocked};
}
