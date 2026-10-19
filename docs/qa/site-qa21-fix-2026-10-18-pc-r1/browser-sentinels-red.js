async original=>{
 const base='http://127.0.0.1:33560',O='/mnt/c/kidsmap/docs/qa/site-qa21-fix-2026-10-18-pc-r1',phase='red',baseline=null,rows=[],pageerrors=[],local_errors=[],blocked=[];
 const c=await original.context().browser().newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)local_errors.push({path:new URL(r.url()).pathname,status:r.status()});});await p.goto(base+'/qa/site21/login/super/');
 for(const lang of ['az','ru','en']){
  const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
  for(const width of [390,1440])for(const [name,path] of [['branding','/admin/catalog/sitebrandingsettings/1/change/'],['analytics','/admin/catalog/siteanalytics/1/change/'],['gallery-add','/admin/catalog/sitegalleryimage/add/']]){
   await p.setViewportSize({width,height:1000});const before=await(await p.request.get(base+'/qa/site21/state/')).json(),response=await p.goto(base+path,{waitUntil:'domcontentloaded'});await p.locator('#content-main').first().waitFor();await p.waitForTimeout(100);
   const geometry=await p.evaluate(()=>{const root=document.querySelector('#content-main'),r=root.getBoundingClientRect();return{root_class:root.className,left:r.left,right:r.right,width:r.width,height:r.height,document:document.documentElement.scrollWidth,visible_controls:[...document.querySelectorAll('#content-main input,#content-main textarea,#content-main select,#content-main button')].filter(e=>e.getClientRects().length).map(e=>({tag:e.tagName,name:e.name,type:e.type}))};});
   const after=await(await p.request.get(base+'/qa/site21/state/')).json(),id=name+'-'+lang+'-'+width,checks={get200:response.status()===200,language:await p.locator('html').getAttribute('lang')===lang,no_catalog_write:JSON.stringify(before)===JSON.stringify(after)};
   if(baseline){const old=baseline.find(r=>r.id===id).geometry;checks.root_class_unchanged=geometry.root_class===old.root_class;checks.root_bounds_unchanged=['left','right','width','height','document'].every(k=>Math.abs(geometry[k]-old[k])<.75);checks.controls_unchanged=JSON.stringify(geometry.visible_controls)===JSON.stringify(old.visible_controls);}
   await p.screenshot({path:O+'/png/sentinel-'+phase+'-'+id+'.png',animations:'disabled'});rows.push({id,name,lang,width,geometry,checks});
  }
 }
 await c.close();return{rows,pageerrors,local_errors,blocked,scope:'Own pre/post sentinel GETs; known mobile overflow preserved/classified, not an assertion of broad layout closure.'};
}
