async (page)=>{
 const base='__BASE__', f=__FIXTURES__,here='__HERE__',rows=[],errors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))network.push({status:r.status(),url:r.url().split('?')[0]});});
 for(const lang of ['ru','az','en']){
  await page.goto(base+'/admin/catalog/offeringgroup/'+f.offeringgroup+'/change/');
  await page.locator('.km-admin-header__lang-btn').click();
  const form=page.locator('#jazzy-languagemenu .km-admin-lang-switch-form').filter({has:page.locator('[name=language][value="'+lang+'"]')});
  await Promise.all([page.waitForNavigation(),form.locator('button').click()]);
  for(const kind of ['offeringgroup','program','activity'])for(const width of kind==='offeringgroup'?[360,390,768,1024,1280,1440]:[390]){
   await page.setViewportSize({width,height:900});await page.goto(base+'/admin/catalog/'+kind+'/'+f[kind]+'/change/');
   await page.locator('.nav-tabs a').first().click();await page.locator('.tab-pane.active .km-status-badge').first().waitFor({state:'visible'});
   const data=await page.locator('.tab-pane.active').evaluate(p=>({pane:{right:p.getBoundingClientRect().right,width:p.clientWidth,scrollWidth:p.scrollWidth,scrollLeft:p.scrollLeft,overflow:getComputedStyle(p).overflowX},badges:[...p.querySelectorAll('.km-status-badge')].map(e=>{const r=e.getBoundingClientRect();return{text:e.textContent,right:r.right,width:r.width,whiteSpace:getComputedStyle(e).whiteSpace,clipped:r.right>p.getBoundingClientRect().right+1};}),documentOverflow:document.documentElement.scrollWidth>innerWidth}));
   const screenshot=kind+'-'+lang+'-'+width+'.png';await page.screenshot({path:here+'/screenshots/'+screenshot,fullPage:true});rows.push({kind,lang,width,...data,screenshot,status:data.badges.some(b=>b.clipped)?'FAIL':'PASS'});
  }
 }
 return{rows,errors,network,scope:'Native State tab read-only, no application patch or save. External font requests blocked.'};
}
