async page => {
 const rows=[],errors=[],network=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('console',e=>{if(e.type()==='error')errors.push(e.text());});
 page.on('requestfailed',r=>network.push({url:r.url(),error:r.failure()?.errorText}));
 page.on('response',r=>{if(r.status()>=400)network.push({url:r.url(),status:r.status()});});
 const assert=(v,m)=>{if(!v)throw Error(m);};
 for(const lang of ['ru','az','en']){
  await page.goto('http://127.0.0.1:8780/admin/catalog/organization/');
  await page.locator('.km-admin-header__lang-btn').click();
  await page.locator(`form.km-admin-lang-switch-form:has(input[name="language"][value="${lang}"]) button`).first().click();
  for(const width of [320,360,390]){
   await page.setViewportSize({width,height:844});
   for(const model of ['place','staffaccessuser','seoissue']){
    await page.goto(`http://127.0.0.1:8780/admin/catalog/${model}/`);await page.waitForLoadState('networkidle');
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
    assert(overflow<=0,`${lang}/${width}/${model} overflow ${overflow}`);
    if(model==='place'){
     const rowHeight=await page.locator('#result_list tbody tr').first().evaluate(e=>e.getBoundingClientRect().height);
     assert(rowHeight<=120,`Collapsed Place columns stretch row: ${rowHeight}`);
     const statuses=page.locator('.km-status-tabs__more');
     await statuses.locator('summary').click();
     const statusMenu=statuses.locator('.km-status-tabs__dropdown');
     assert(await statusMenu.isVisible(),'Status menu hidden');
     const statusBounds=await statusMenu.boundingBox();
     assert(statusBounds.x>=0&&statusBounds.x+statusBounds.width<=width,'Status menu outside viewport');
     await statuses.locator('summary').click();
     assert(!await statusMenu.isVisible(),'Closed status menu still visible');
     const more=page.locator('.km-action-more-btn').first();await more.scrollIntoViewIfNeeded();await more.click();
     const menu=page.locator('#km-row-actions-dropdown');assert(await menu.isVisible(),'Row menu hidden');
     const bounds=await menu.boundingBox();assert(bounds.x>=0&&bounds.x+bounds.width<=width,'Row menu outside viewport');
     if(lang==='ru'&&width===390)await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/admin-place-menu-mobile.png'});
     await page.locator('.km-admin-header__lang-btn').click();
    } else if(model==='seoissue'){
     await page.locator('#changelist-search .select2-selection').first().click();
     const popup=page.locator('.select2-dropdown');assert(await popup.isVisible(),'Filter options hidden');
     const bounds=await popup.boundingBox();assert(bounds.x>=0&&bounds.x+bounds.width<=width,'Filter outside viewport');
     await page.keyboard.press('Escape');assert(!await popup.isVisible(),'Filter Escape did not close');
    } else {
     const add=page.locator('.km-staff-add-btn');assert(await add.isVisible(),'Staff add button hidden');
     await add.scrollIntoViewIfNeeded();const bounds=await add.boundingBox();assert(bounds.x>=0&&bounds.x+bounds.width<=width,'Staff add button clipped');
    }
    rows.push({lang,width,model,status:'PASS'});
   }
  }
 }
 assert(!errors.length&&!network.length,JSON.stringify({errors,network}));
 return {status:'PASS',rows,errors,network};
}
