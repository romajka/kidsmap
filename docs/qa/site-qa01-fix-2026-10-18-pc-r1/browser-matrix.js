async original=>{
const base='http://127.0.0.1:33480',O='/mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1',rows=[],blocked=[],pageerrors=[],local_errors=[],console_errors=[],browser=original.context().browser();
for(const role of ['none','viewer','addviewer','content','super']) {
 const c=await browser.newContext({viewport:{width:1440,height:950},serviceWorkers:'block'});
 await c.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='127.0.0.1')return r.continue();blocked.push(u.hostname);return r.abort();});
 const p=await c.newPage();p.setDefaultTimeout(10000);
 p.on('pageerror',e=>pageerrors.push({role,message:String(e)}));
 p.on('console',m=>{if(m.type()==='error')console_errors.push({role,message:m.text()});});
 p.on('response',r=>{const u=new URL(r.url());if(u.hostname==='127.0.0.1'&&r.status()>=400&&!(role==='none'&&r.status()===403))local_errors.push({role,path:u.pathname,status:r.status()});});
 await p.goto(base+'/qa/site01/login/'+role+'/');
 for(const lang of ['az','ru','en']) {
  const csrf=(await c.cookies()).find(x=>x.name==='csrftoken')?.value;
  const sw=await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
  if(sw.status()!==302)throw Error('Language cookie switch failed');
  for(const width of [360,390,768,1024,1280,1440]) {
   await p.setViewportSize({width,height:950});const response=await p.goto(base+'/admin/catalog/sitegalleryimage/');
   await p.locator('h1').first().waitFor();
   const main=await p.locator('.km-media-upload-btn,.km-media-delete-btn').count(),add=await p.locator('.km-gallery-add').count(),links=await p.locator('.km-gallery-card-actions a').count();
   const htmlLang=await p.locator('html').getAttribute('lang');
   const geometry=await p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth}));
   let keyboard=null;
   if(role!=='none') {
    await p.keyboard.press('Tab');
    keyboard=await p.evaluate(()=>{const e=document.activeElement,r=e.getBoundingClientRect(),s=getComputedStyle(e);return {tag:e.tagName,visible:r.width>0&&r.height>0&&s.visibility!=='hidden',focusStyle:s.outlineStyle,tabindex:e.tabIndex};});
    await p.keyboard.press('Shift+Tab');
   }
   rows.push({role,lang,width,status:response.status(),mainControls:main,galleryAdd:add,galleryLinks:links,htmlLang,geometry,keyboard,checks:{access:response.status()===(role==='none'?403:200),language:role==='none'||htmlLang===lang,mainCapabilities:['content','super'].includes(role)?main>0:main===0,addCapabilities:['addviewer','content','super'].includes(role)?add>0:add===0,galleryLinks:['content','super'].includes(role)?links>0:links===0,noOverflow:role==='none'||geometry.document<=width+1,keyboard:role==='none'||keyboard.visible}});
   await p.screenshot({path:O+'/png/green-hub-'+role+'-'+lang+'-'+width+'.png',animations:'disabled'});
  }
 }
 await c.close();
}
return {rows,pageerrors,local_errors,console_errors,blocked,scope:'90 real Chromium role/language/width cells; fictional login helper SIMULATED; actual admin rendering and ACL real'};
}
