async original=>{
 const base='http://127.0.0.1:33560',O='/mnt/c/kidsmap/docs/qa/site-qa21-fix-2026-10-18-pc-r1',url=base+'/admin/catalog/catalogcontentsettings/1/change/';
 const rows=[],pageerrors=[],local_errors=[],blocked=[];const c=await original.context().browser().newContext({viewport:{width:1440,height:950},serviceWorkers:'block'});
 await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));
 const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)local_errors.push({path:new URL(r.url()).pathname,status:r.status()});});
 await p.goto(base+'/qa/site21/login/editor/',{waitUntil:'domcontentloaded'});
 for(const lang of ['az','ru','en']){
  const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
  await p.setViewportSize({width:1440,height:950});await p.goto(url,{waitUntil:'domcontentloaded'});const before=await(await p.request.get(base+'/qa/site21/state/')).json();
  await p.locator('[name=districts_json]').fill('{mobile-error');
  const [response]=await Promise.all([p.waitForResponse(r=>r.url()===url&&r.request().method()==='POST'),p.locator('button[name=_continue]').click()]);await p.waitForLoadState('domcontentloaded');await p.locator('.errorlist').first().waitFor();
  for(const width of [360,390]){
   await p.setViewportSize({width,height:950});await p.locator('label[for=id_districts_json]').click();
   const after=await(await p.request.get(base+'/qa/site21/state/')).json();
   const geometry=await p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,textarea:{left:document.querySelector('#id_districts_json').getBoundingClientRect().left,right:document.querySelector('#id_districts_json').getBoundingClientRect().right},focused:document.activeElement.id,summary_focused:document.activeElement.getAttribute('role')==='alert'}));
   const id='error-'+lang+'-'+width;await p.screenshot({path:O+'/png/mobile-'+id+'.png',animations:'disabled'});
   rows.push({id,lang,width,role:'editor',geometry,save_visible:await p.locator('button[name=_continue]').isVisible(),checks:{desktop_native_post200:response.status()===200,error_visible:await p.locator('.errorlist').first().isVisible(),draft_retained:await p.locator('[name=districts_json]').inputValue()==='{mobile-error',native_label_focus:geometry.focused==='id_districts_json',no_json_or_log_write:JSON.stringify(before)===JSON.stringify(after),no_horizontal_overflow:geometry.document<=geometry.viewport,textarea_within_viewport:geometry.textarea.left>=0&&geometry.textarea.right<=geometry.viewport},submission_provenance:'Native desktop invalid POST then actual viewport resize; native mobile submit NOT RUN because existing SITE08 sidebar is hidden.'});
  }
 }
 await c.close();return{rows,pageerrors,local_errors,blocked,scope:'Real server error page at mobile widths after desktop native submit. No forced hidden controls or fabricated response.'};
}
