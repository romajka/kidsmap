async(page)=>{
const base='__BASE__',f=__FIXTURES__,here='__HERE__',rows=[],errors=[],network=[];
const check=(id,ok,detail)=>rows.push({id,status:ok?'PASS':'FAIL',detail});
page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))network.push({status:r.status(),url:r.url().split('?')[0]});});
for(const lang of ['ru','az','en']){
 await page.goto(base+'/admin/catalog/offeringgroup/'+f.offeringgroup+'/change/');await page.locator('.km-admin-header__lang-btn').click();const form=page.locator('#jazzy-languagemenu .km-admin-lang-switch-form').filter({has:page.locator('[name=language][value="'+lang+'"]')});await Promise.all([page.waitForNavigation(),form.locator('button').click()]);
 for(const status of ['pending','published'])for(const width of [360,390]){
  await page.setViewportSize({width,height:900});await page.goto(base+'/admin/catalog/offeringgroup/'+f.variants[status]+'/change/');await page.locator('.nav-tabs a').first().click();
  const data=await page.locator('.tab-pane.active').evaluate(p=>({innerScroll:p.scrollWidth>p.clientWidth+1,badges:[...p.querySelectorAll('.km-status-badge')].map(e=>({text:e.textContent,inside:e.getBoundingClientRect().right<=e.parentElement.getBoundingClientRect().right+1,overflow:e.scrollWidth>e.clientWidth+1,dot:getComputedStyle(e,'::before').flexShrink,cls:e.className}))}));
  check(lang+'-'+status+'-'+width,!data.innerScroll&&data.badges.every(b=>b.inside&&!b.overflow)&&data.badges[0].cls.includes('km-status-'+status),data);await page.screenshot({path:here+'/screenshots/'+lang+'-'+status+'-'+width+'.png',fullPage:true});
 }
 await page.goto(base+'/admin/catalog/offeringgroup/'+f.offeringgroup+'/change/');await page.setViewportSize({width:390,height:900});
 const tabs=page.locator('.nav-tabs a');await tabs.nth(1).focus();await page.keyboard.press('Enter');check(lang+'-keyboard-tab',await page.locator('#id_name_ru').isVisible(),{active:await page.evaluate(()=>document.activeElement.getAttribute('href'))});
 const value='Вымышленная группа '+lang+' native';await page.locator('#id_name_ru').fill(value);const save=page.locator('[name=_save_draft]');await save.scrollIntoViewIfNeeded();
 const box=await save.boundingBox();check(lang+'-save-control',box&&box.height>=32&&box.width>=100,box);
 await Promise.all([page.waitForNavigation(),save.click()]);check(lang+'-save-no-form-error',await page.locator('.errorlist').count()===0,{url:page.url()});
 await page.reload();await page.locator('.nav-tabs a').nth(1).click();check(lang+'-reload-retains-candidate',await page.locator('#id_name_ru').inputValue()===value,{value:await page.locator('#id_name_ru').inputValue()});
 await page.locator('.nav-tabs a').first().click();check(lang+'-save-still-readable',await page.locator('.tab-pane.active').evaluate(p=>p.scrollWidth<=p.clientWidth+1),{});await page.screenshot({path:here+'/screenshots/'+lang+'-save-reload.png',fullPage:true});
}
for(const width of [390,1440]){
 await page.setViewportSize({width,height:900});await page.goto(base+'/admin/catalog/offeringgroup/');const badge=page.locator('.km-status-badge').first();check('list-badge-'+width,await badge.count()>0&&await badge.evaluate(e=>getComputedStyle(e).whiteSpace==='nowrap'),{url:page.url()});await page.screenshot({path:here+'/screenshots/list-'+width+'.png',fullPage:true});
 await page.goto(base+'/admin/catalog/place/'+f.place+'/change/');check('shared-place-form-'+width,await page.locator('#id_name').count()>0||await page.locator('#id_name_ru').count()>0,{url:page.url()});await page.screenshot({path:here+'/screenshots/place-'+width+'.png',fullPage:true});
}
return{rows,errors,network,external:'blocked, NOT RUN'};
}
