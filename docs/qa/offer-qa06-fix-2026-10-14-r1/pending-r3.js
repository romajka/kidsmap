async(page)=>{
const base='__BASE__',f=__FIXTURES__,here='__HERE__',rows=[],errors=[],network=[];
const check=(id,ok,detail)=>rows.push({id,status:ok?'PASS':'FAIL',detail});
page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))network.push({status:r.status(),url:r.url().split('?')[0]});});
for(const lang of ['ru','az','en']){
 await page.goto(base+'/admin/catalog/offeringgroup/'+f.offeringgroup+'/change/');await page.locator('.km-admin-header__lang-btn').click();const form=page.locator('#jazzy-languagemenu .km-admin-lang-switch-form').filter({has:page.locator('[name=language][value="'+lang+'"]')});await Promise.all([page.waitForNavigation(),form.locator('button').click()]);
 for(const status of ['pending'])for(const width of [360,1440]){
  await page.setViewportSize({width,height:900});await page.goto(base+'/admin/catalog/offeringgroup/'+f.variants[status]+'/change/');await page.locator('.nav-tabs a').first().click();
  const data=await page.locator('.tab-pane.active').evaluate(p=>({innerScroll:p.scrollWidth>p.clientWidth+1,badges:[...p.querySelectorAll('.km-status-badge')].map(e=>({text:e.textContent,inside:e.getBoundingClientRect().right<=e.parentElement.getBoundingClientRect().right+1,overflow:e.scrollWidth>e.clientWidth+1,dot:getComputedStyle(e,'::before').flexShrink,cls:e.className}))}));
  check(lang+'-'+status+'-'+width,!data.innerScroll&&data.badges.every(b=>b.inside&&!b.overflow)&&data.badges[0].cls.includes('km-status-'+status)&&(lang==='ru'||data.badges.every(b=>!/[А-Яа-яЁё]/.test(b.text))),data);await page.screenshot({path:here+'/screenshots/'+lang+'-'+status+'-'+width+'.png',fullPage:true});
 }
}
return{rows,errors,network};
}
