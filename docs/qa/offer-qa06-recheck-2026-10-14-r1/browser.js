async(page)=>{
 const base='__BASE__',f=__FIXTURES__,here='__HERE__',rows=[],errors=[],network=[],blocked=[];
 await page.context().route('**/*',r=>r.request().url().startsWith(base)||r.request().url().startsWith('data:')?r.continue():(blocked.push(r.request().url().split('?')[0]),r.abort()));
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))network.push({status:r.status(),url:r.url().split('?')[0]});});
 await page.locator('[name=username]').fill(f.username);await page.locator('[name=password]').fill('__PASSWORD__');await Promise.all([page.waitForNavigation(),page.locator('[type=submit]').click()]);
 for(const lang of ['ru','az','en']){
 await page.goto(base+'/admin/catalog/offeringgroup/'+f.offeringgroup+'/change/');await page.locator('.km-admin-header__lang-btn').click();const form=page.locator('#jazzy-languagemenu .km-admin-lang-switch-form').filter({has:page.locator('[name=language][value="'+lang+'"]')});await Promise.all([page.waitForNavigation(),form.locator('button').click()]);
 for(const kind of ['program','activity','offeringgroup']){
 await page.setViewportSize({width:390,height:900});await page.goto(base+'/admin/catalog/'+kind+'/'+f[kind]+'/change/');await page.locator('.nav-tabs a').first().click();await page.locator('.tab-pane.active .km-status-badge').first().waitFor({state:'visible'});
 const texts=await page.locator('.tab-pane.active .km-status-badge').allTextContents(),htmlLang=await page.locator('html').getAttribute('lang');const file=kind+'-'+lang+'-390.png';await page.screenshot({path:here+'/screenshots/'+file,fullPage:true});rows.push({kind,lang,htmlLang,texts,screenshot:file,status:lang==='ru'||texts.every(t=>!/[А-Яа-яЁё]/.test(t))?'PASS':'FAIL'});
 }
 }
 return{rows,errors,network,blocked:[...new Set(blocked)],scope:'Native admin State tabs on current verified isolated locales; no POST/save/source change.'};
}
