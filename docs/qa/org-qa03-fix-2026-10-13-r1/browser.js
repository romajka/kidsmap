async(page)=>{
 const B='__BASE__',ROOT='__HERE__',F=__FIXTURES__,rows=[],errors=[],consoleEvents=[],network=[];
 await page.context().route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(['warning','error'].includes(m.type()))consoleEvents.push({type:m.type(),text:m.text(),url:m.location().url});});page.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)network.push({url:r.url().split('?')[0],status:r.status()});});
 await page.goto(B+'/admin/login/?next=/admin/');await page.locator('[name=username]').fill('start_admin');await page.locator('[name=password]').fill('__PASSWORD__');await Promise.all([page.waitForNavigation(),page.locator('[type=submit]').click()]);
 const add=(id,ok,detail={})=>rows.push({id,status:ok?'PASS':'FAIL',...detail});
 const geometry=()=>page.evaluate(()=>{const f=document.querySelector('#changelist-search'),t=document.querySelector('.km-table-container');return{viewport:innerWidth,document:document.documentElement.scrollWidth,form:f?.getBoundingClientRect().width,formScroll:f?.scrollWidth,wrap:f&&getComputedStyle(f).flexWrap,tableOverflow:t&&getComputedStyle(t).overflowX};});
 const nav=async l=>Promise.all([page.waitForNavigation(),l.click()]);
 for(const lang of ['ru','az','en']){
  await page.context().addCookies([{name:'django_language',value:lang,url:B}]);
  for(const width of [360,390,768,1024,1280,1440]){
   await page.setViewportSize({width,height:950});await page.goto(B+'/admin/catalog/place/?q=QA02+LOCAL+BULK');
   for(const sidebar of ['default','toggled']){
    if(sidebar==='toggled'){await page.locator('[data-widget=pushmenu]').first().click();await page.waitForTimeout(350);}
    const g=await geometry();const screenshot='screenshots/'+lang+'-'+width+'-'+sidebar+'.png';await page.screenshot({path:ROOT+'/'+screenshot});add('place-layout-'+lang+'-'+width+'-'+sidebar,g.document<=width+1&&g.formScroll<=g.form+1,{lang,width,sidebar,geometry:g,screenshot});
   }
  }
  await page.setViewportSize({width:1024,height:950});await page.goto(B+'/admin/catalog/place/');
  await page.locator('#searchbar').fill('QA02 LOCAL BULK');await Promise.all([page.waitForNavigation(),page.locator('#searchbar').press('Enter')]);add('native-search-'+lang,(await page.locator('input[name=_selected_action]').count())===3,{lang});
  const box=page.locator('input[name=_selected_action]').first();await box.focus();await page.keyboard.press('Space');add('keyboard-selection-'+lang,await box.isChecked(),{lang});
  await page.locator('button[name=connection_selection]').focus();await Promise.all([page.waitForNavigation(),page.keyboard.press('Enter')]);add('native-selection-target-'+lang,await page.locator('[name=organization_id]').count()===1,{lang});
  await page.locator('[name=organization_id]').selectOption(String(F.organization_id));await nav(page.locator('button[value=preview]'));add('native-preview-'+lang,await page.locator('[name=preview_id]').count()===1,{lang});
  const ss='screenshots/'+lang+'-preview.png';await page.screenshot({path:ROOT+'/'+ss});add('preview-without-confirm-'+lang,await page.locator('[name=consent]').count()===1,{lang,screenshot:ss});await page.goBack();add('preview-cancel-navigation-'+lang,!page.url().includes('preview='),{lang});
  await page.goto(B+'/admin/catalog/place/?q=QA02+LOCAL+BULK');
  await page.locator('#km-sort-menu summary').focus();await page.keyboard.press('Enter');add('keyboard-sort-'+lang,await page.locator('#km-sort-menu').getAttribute('open')!==null,{lang});await page.locator('#km-sort-menu summary').press('Enter');
  await page.locator('#km-toggle-filters-btn').click();add('filters-open-'+lang,await page.locator('#km-toggle-filters-btn').getAttribute('aria-expanded')==='true',{lang});await page.locator('#km-toggle-filters-btn').click();
  for(const model of ['event','specialist','placeownershiprequest','placereview'])for(const width of [768,1024]){
   await page.setViewportSize({width,height:950});const response=await page.goto(B+'/admin/catalog/'+model+'/');const g=await geometry();add('shared-'+model+'-'+lang+'-'+width,response.status()===200&&g.document<=width+1&&(!g.form||g.formScroll<=g.form+1),{lang,width,model,geometry:g,http:response.status()});
  }
 }
 return {rows,errors,consoleEvents,network};
}
