async page => {
 const rows=[],issues=[],errors=[],network=[];
 let currentCase='setup';
 page.on('pageerror',e=>errors.push({case:currentCase,error:String(e)}));
 page.on('console',e=>{if(e.type()==='error')errors.push({case:currentCase,error:e.text()});});
 page.on('requestfailed',r=>network.push({case:currentCase,url:r.url(),reason:r.failure()?.errorText}));
 page.on('response',r=>{if(r.status()>=400)network.push({case:currentCase,url:r.url(),status:r.status()});});
 const base='http://127.0.0.1:8780';
 await page.goto(base+'/admin/catalog/organization/');
 const links=await page.locator('.main-sidebar a[href]').evaluateAll(es=>Array.from(new Set(es.map(e=>e.getAttribute('href')).filter(h=>h.startsWith('/admin/')&&!h.includes('/add/')&&!h.includes('/change/')))));
 const main=['organization','program','activity','offeringgroup'];
 const forms=[];
 for(const model of [...main,'place','event','specialist']){
  await page.goto(base+`/admin/catalog/${model}/`);
  const edit=await page.locator('#result_list tbody a[href*="/change/"]').first().getAttribute('href').catch(e=>{throw Error(model+' edit link: '+e.message);});
  forms.push({kind:model+' edit',url:edit},{kind:model+' add',url:`/admin/catalog/${model}/add/`});
 }
 const measure=async(url,lang,width,kind)=>{
  currentCase=`${lang} ${width} ${kind} ${url}`;
  await page.setViewportSize({width,height:1000});
  const response=await page.goto(base+url);await page.waitForLoadState('networkidle');
  const data=await page.evaluate(()=>({
   lang:document.documentElement.lang,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
   header:document.querySelector('#result_list thead')?.getBoundingClientRect().height||0,
   oversize:Array.from(document.querySelectorAll('#result_list .km-col-sort-badge svg')).filter(e=>e.getBoundingClientRect().width>24||e.getBoundingClientRect().height>24).length,
   heading:document.querySelector('h1')?.textContent.trim()||document.title,
  }));
  rows.push({case:kind,url,lang,width,status:response.status(),...data});
  if(response.status()!==200||data.lang!==lang||data.scrollWidth>width||data.oversize||data.header>100)issues.push(rows[rows.length-1]);
 };
 for(const lang of ['ru','az','en']){
  await page.goto(base+'/admin/catalog/organization/');
  await page.locator('.km-admin-header__lang-btn').click();
  await page.locator(`form.km-admin-lang-switch-form:has(input[name="language"][value="${lang}"]) button`).first().click();
  await page.waitForLoadState('networkidle');
  for(const width of [390,1440]){
   for(const url of links)await measure(url,lang,width,'sidebar');
   for(const item of forms)await measure(item.url,lang,width,item.kind);
  }
  for(const width of [768,1024,1280]){
   for(const model of main)await measure(`/admin/catalog/${model}/`,lang,width,model+' list');
   for(const item of forms.filter(i=>main.some(m=>i.kind===m+' edit')))await measure(item.url,lang,width,item.kind);
  }
 }
 await page.setViewportSize({width:1440,height:1000});
 await page.goto(base+'/admin/catalog/organization/');
 await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/admin-organizations-after.png'});
 return {status:issues.length||errors.length||network.length?'FAIL':'PASS',count:rows.length,sidebarLinks:links.length,forms:forms.length,
   rows:rows.map(({case:kind,url,lang,width,status,scrollWidth})=>({case:kind,url,lang,width,status,scrollWidth})),issues,errors,network};
}
