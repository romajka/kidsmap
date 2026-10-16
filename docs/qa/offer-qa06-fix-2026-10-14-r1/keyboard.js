async(page)=>{
const B='__BASE__',F=__FIXTURES__,H='__HERE__',rows=[];
for(const lang of ['ru','az','en']){
await page.goto(B+'/admin/catalog/offeringgroup/'+F.offeringgroup+'/change/');await page.locator('.km-admin-header__lang-btn').click();const form=page.locator('#jazzy-languagemenu .km-admin-lang-switch-form').filter({has:page.locator('[name=language][value="'+lang+'"]')});await Promise.all([page.waitForNavigation(),form.locator('button').click()]);await page.setViewportSize({width:390,height:900});const tabs=page.locator('.nav-tabs a');await tabs.nth(1).focus();await page.keyboard.press('Enter');await page.locator('#id_name_ru').waitFor({state:'visible'});rows.push({id:lang+'-keyboard-group',status:'PASS',href:await page.evaluate(()=>document.activeElement.getAttribute('href'))});await tabs.first().focus();await page.keyboard.press('Enter');await page.locator('.tab-pane.active .km-status-badge').first().waitFor({state:'visible'});const data=await page.locator('.tab-pane.active').evaluate(p=>({overflow:p.scrollWidth>p.clientWidth+1,texts:[...p.querySelectorAll('.km-status-badge')].map(e=>e.textContent)}));rows.push({id:lang+'-keyboard-status',status:!data.overflow&&(lang==='ru'||data.texts.every(t=>!/[А-Яа-яЁё]/.test(t)))?'PASS':'FAIL',data});await page.screenshot({path:H+'/screenshots/keyboard-'+lang+'.png',fullPage:true});
}
return{rows};
}
