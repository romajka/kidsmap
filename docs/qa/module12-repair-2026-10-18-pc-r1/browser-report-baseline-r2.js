async (page) => {
 const base='http://127.0.0.1:33780',rows=[],errors=[],pageerrors=[];
 await page.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort());
 page.on('pageerror',e=>pageerrors.push(String(e)));
 try {
  await page.goto(base+'/qa/m12/login/admin/');
  for(const lang of ['az','ru','en']){
   await page.context().addCookies([{name:'django_language',value:lang,domain:'127.0.0.1',path:'/'}]);
   for(const width of [360,390,768,1024,1280,1440]){
    await page.setViewportSize({width,height:900});const r=await page.goto(base+'/admin/catalog/siteanalytics/?period=90');
    const state=await page.locator('.km-statistics-page').getAttribute('data-analytics-state');
    const values=await page.locator('[data-kpi-value]').allTextContents();
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
    rows.push({id:'disabled-'+lang+'-'+width,lang,width,role:'admin',checks:{http200:r.status()===200,explicit_disabled:state==='disabled',unavailable_not_zero:values.length===3&&values.every(v=>v.trim()==='—'),no_overflow:!overflow}});
    if([360,1440].includes(width))await page.screenshot({path:'/mnt/c/kidsmap/docs/qa/module12-repair-2026-10-18-pc-r1/png/baseline-disabled-'+lang+'-'+width+'.png',fullPage:true});
   }
  }
 }catch(e){errors.push(String(e))}
 return {rows,errors,pageerrors,provider:'disabled; no real GA connection'};
}
