async (page) => {
 const B='__BASE__',ROOT='__HERE__',F=__FIXTURES__,rows=[],errors=[],network=[];
 await page.context().route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
 page.on('pageerror',e=>errors.push(String(e)));page.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)network.push({url:r.url().split('?')[0],status:r.status()});});
 await page.goto(B+'/admin/login/');await page.locator('[name=username]').fill('start_admin');await page.locator('[name=password]').fill('__PASSWORD__');await Promise.all([page.waitForNavigation(),page.locator('[type=submit]').click()]);
 for(const lang of ['ru','az','en']){
  await page.context().addCookies([{name:'django_language',value:lang,url:B}]);await page.setViewportSize({width:1024,height:950});
  await page.goto(B+'/admin/catalog/place/?q=QA02+LOCAL+BULK');await page.waitForTimeout(500);
  const g=await page.evaluate(()=>{const f=document.querySelector('#changelist-search'),t=document.querySelector('.km-toolbar');return {viewport:innerWidth,document:document.documentElement.scrollWidth,form:f?.getBoundingClientRect().width,formScroll:f?.scrollWidth,wrap:f&&getComputedStyle(f).flexWrap,toolbar:t?.getBoundingClientRect().width,bodyClasses:document.body.className};});
  const screenshot='screenshots/'+lang+'-1024-toolbar.png';await page.screenshot({path:ROOT+'/'+screenshot});rows.push({id:'ORG-QA-03',lang,geometry:g,screenshot,status:g.document>1025?'CONFIRMED OPEN':'NOT REPRODUCED'});
  await page.goto(B+'/admin/catalog/organization/'+F.organization_id+'/change/');await page.waitForTimeout(400);
  const headings=await page.locator('h1,h2,h3,legend,.nav-tabs,.readonly,label').allTextContents();const visible=await page.locator('body').innerText();
  const ss='screenshots/'+lang+'-1024-organization.png';await page.screenshot({path:ROOT+'/'+ss});
  rows.push({id:'ORG-QA-04',lang,headings:headings.map(x=>x.trim()).filter(Boolean),residual:['Названия','Организации','Владение','Проверка данных','Связанные разделы','Текущие и предложенные данные'].filter(x=>visible.includes(x)),screenshot:ss,status:lang==='ru'?'BASELINE':visible.includes('Названия')?'CONFIRMED OPEN':'NOT REPRODUCED'});
 }
 return {rows,errors,network,url:page.url()};
}
