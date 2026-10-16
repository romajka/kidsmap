async(page)=>{
 const base='__BASE__',f=__FIXTURES__,here='__HERE__',rows=[];
 for(const lang of ['ru','az','en']){
 await page.goto(base+'/admin/catalog/offeringgroup/'+f.offeringgroup+'/change/');await page.locator('.km-admin-header__lang-btn').click();const form=page.locator('#jazzy-languagemenu .km-admin-lang-switch-form').filter({has:page.locator('[name=language][value="'+lang+'"]')});await Promise.all([page.waitForNavigation(),form.locator('button').click()]);await page.setViewportSize({width:390,height:900});
 const tabs=page.locator('.nav-tabs a');await tabs.first().click();await tabs.nth(1).focus();await page.keyboard.press('Enter');
 try{await page.locator('#id_name_ru').waitFor({state:'visible',timeout:3000});rows.push({id:lang+'-keyboard-tab',status:'PASS',active:await page.evaluate(()=>document.activeElement.getAttribute('href')),note:'Native Enter, visibility awaited for Bootstrap pane transition before assertion'});}catch(e){rows.push({id:lang+'-keyboard-tab',status:'FAIL',error:e.message.slice(0,400)});}
 await tabs.first().focus();await page.keyboard.press('Enter');await page.locator('.tab-pane.active .km-status-badge').first().waitFor({state:'visible'});rows.push({id:lang+'-keyboard-state',status:await page.locator('.tab-pane.active').evaluate(p=>p.scrollWidth<=p.clientWidth+1)?'PASS':'FAIL'});await page.screenshot({path:here+'/screenshots/'+lang+'-keyboard.png',fullPage:true});
 }
 return{rows};
}
