async original=>{
const base='http://127.0.0.1:33500',O='/mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1',rows=[],pageerrors=[],blocked=[],browser=original.context().browser();
for(const role of ['content','super']){
 const c=await browser.newContext({viewport:{width:1440,height:950},serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));
 const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));await p.goto(base+'/qa/site15/login/'+role+'/');
 for(const lang of ['az','ru','en']){
  const token=(await c.cookies()).find(x=>x.name==='csrftoken').value;await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':token},form:{language:lang,next:'/admin/'},maxRedirects:0});
  for(const width of [360,390,768,1024,1280,1440]){
   await p.setViewportSize({width,height:950});const response=await p.goto(base+'/admin/catalog/sitefootersettings/1/change/');
   const geometry=await p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth}));
   rows.push({role,lang,width,status:response.status(),geometry,checks:{status200:response.status()===200,language:await p.locator('html').getAttribute('lang')===lang}});
   if(lang==='ru'&&[390,1440].includes(width))await p.screenshot({path:O+'/png/red-baseline-'+role+'-'+lang+'-'+width+'.png',animations:'disabled'});
  }
 }
 await c.close();
}
return{rows,pageerrors,blocked,scope:'Prepatch read-only geometry baseline; existing mobile layout retained'};
}
