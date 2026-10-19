async original=>{
 const base='http://127.0.0.1:33560',O='/mnt/c/kidsmap/docs/qa/site-qa21-fix-2026-10-18-pc-r1',rows=[],pageerrors=[],local_errors=[],blocked=[];
 const browser=original.context().browser();
 for(const role of ['super','viewer']){
  const c=await browser.newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));
  const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)local_errors.push({path:new URL(r.url()).pathname,status:r.status()});});await p.goto(base+'/qa/site21/login/'+role+'/',{waitUntil:'domcontentloaded'});
  for(const lang of ['az','ru','en']){
   const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
   for(const width of [360,390,768,1024,1280,1440]){
    await p.setViewportSize({width,height:1000});const before=await(await p.request.get(base+'/qa/site21/state/')).json();const response=await p.goto(base+'/admin/catalog/catalogcontentsettings/1/change/',{waitUntil:'domcontentloaded'});await p.locator('#catalogcontentsettings_form').waitFor();
    const geometry=await p.evaluate(()=>{
     const rect=e=>e.getBoundingClientRect(),root=document.querySelector('#content-main.km-place-form-page'),main=rect(document.querySelector('.km-place-form-main')),asideElement=document.querySelector('.km-place-form-sidebar'),aside=rect(asideElement),visible=e=>e.getClientRects().length>0;
     const cards=[...document.querySelectorAll('.km-place-form-main > .km-place-section')].filter(visible).map(rect),fields=[...document.querySelectorAll('#catalogcontentsettings_form textarea,.km-place-section .readonly')].filter(visible).map(rect),rootRect=rect(root),max=parseFloat(getComputedStyle(root).maxWidth)||Infinity;
     const overlap=(a,b)=>Math.min(a.right,b.right)>Math.max(a.left,b.left)+.5&&Math.min(a.bottom,b.bottom)>Math.max(a.top,b.top)+.5;
     return{root_width:rootRect.width,row_width:rect(root.parentElement).width,visible_field_widths:fields.map(f=>f.width),checks:{fills_available_column:rootRect.width>=Math.min(rect(root.parentElement).width,max)-.75,visible_cards_within_main:cards.every(c=>c.left>=main.left-.75&&c.right<=main.right+.75),cards_not_covered_by_actions:!visible(asideElement)||cards.every(c=>!overlap(c,aside)),no_document_overflow:document.documentElement.scrollWidth<=innerWidth,visible_fields_within_main:fields.every(f=>f.left>=main.left-.75&&f.right<=main.right+.75)}};
    });
    const checks={...geometry.checks,get200:response.status()===200,admin_language:await p.locator('html').getAttribute('lang')===lang,appropriate_fields:await p.locator('textarea').count()===(role==='viewer'?0:3)};
    if(role==='super'){await p.locator('label[for=id_districts_json]').click();checks.label_focus=await p.locator('#id_districts_json').evaluate(e=>e===document.activeElement);await p.keyboard.press('Tab');checks.keyboard_tab=await p.locator('#id_metro_stations_json').evaluate(e=>e===document.activeElement);}
    const after=await(await p.request.get(base+'/qa/site21/state/')).json();checks.no_fixture_write=JSON.stringify(before)===JSON.stringify(after);const id=role+'-'+lang+'-'+width;await p.screenshot({path:O+'/png/acceptance-'+id+'.png',fullPage:true,animations:'disabled'});rows.push({id,role,lang,width,geometry,checks});
   }
  }
  await c.close();
 }
 return{rows,pageerrors,local_errors,blocked,scope:'Prepared for independent fix profile33560: actual-source layout acceptance, NO injected classes/styles/transport/template overrides. Must run fresh RED before apply and same checks GREEN after approval. NOT RUN in PLAN.'};
}
