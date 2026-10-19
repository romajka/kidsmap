async original=>{
 const base='http://127.0.0.1:33550',O='/mnt/c/kidsmap/docs/qa/site-qa21-recheck-2026-10-18-pc-r1',url=base+'/admin/catalog/catalogcontentsettings/1/change/';
 const rows=[],pageerrors=[],local_errors=[],console_errors=[],blocked=[];const browser=original.context().browser();
 const measure=async p=>p.evaluate(()=>{
  const rect=e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,top:r.top+scrollY,bottom:r.bottom+scrollY,width:r.width,height:r.height};};
  const root=document.querySelector('#content-main.km-place-form-page'),main=document.querySelector('.km-place-form-main'),aside=document.querySelector('.km-place-form-sidebar'),r=rect(root),m=rect(main),a=rect(aside),s=getComputedStyle(root),ps=getComputedStyle(root.parentElement);
  const cards=[...document.querySelectorAll('.km-place-form-main > .km-place-section')].filter(e=>e.getClientRects().length).map(rect);
  const fields=[...document.querySelectorAll('#catalogcontentsettings_form textarea,.km-place-section .readonly')].map(rect);
  const visibleAside=!!(aside.offsetWidth||aside.offsetHeight||aside.getClientRects().length);
  const overlap=(x,y)=>Math.min(x.right,y.right)>Math.max(x.left,y.left)+.5&&Math.min(x.bottom,y.bottom)>Math.max(x.top,y.top)+.5;
  return{viewport:innerWidth,document:document.documentElement.scrollWidth,root:r,row:rect(root.parentElement),parent_display:ps.display,root_style:{flex:s.flex,width:s.width,maxWidth:s.maxWidth,paddingLeft:s.paddingLeft,paddingRight:s.paddingRight,boxSizing:s.boxSizing},main:m,aside:a,cards,fields,aside_visible:visibleAside,save_visible:!!document.querySelector('button[name=_continue]').getClientRects().length,root_classes:root.className,checks:{fills_row:r.width>=rect(root.parentElement).width-.75,visible_cards_within_main:cards.every(c=>c.left>=m.left-.75&&c.right<=m.right+.75),cards_not_covered_by_actions:!visibleAside||cards.every(c=>!overlap(c,a)),no_document_overflow:document.documentElement.scrollWidth<=innerWidth,fields_inside_cards:fields.every(f=>f.left>=m.left-.75&&f.right<=m.right+.75)}};
 });
 for(const role of ['super','viewer']){
  const c=await browser.newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));
  const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));p.on('console',m=>{if(m.type()==='error')console_errors.push(m.text());});p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)local_errors.push({path:new URL(r.url()).pathname,status:r.status()});});
  await p.goto(base+'/qa/site21/login/'+role+'/',{waitUntil:'domcontentloaded'});
  for(const lang of ['az','ru','en']){
   const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
   for(const width of [360,390,768,1024,1280,1440]){
    await p.setViewportSize({width,height:1000});const beforeState=await(await p.request.get(base+'/qa/site21/state/')).json();const response=await p.goto(url,{waitUntil:'domcontentloaded'});await p.locator('#catalogcontentsettings_form').waitFor();
    const baseline=await measure(p),id=role+'-'+lang+'-'+width;
    if([390,1440].includes(width))await p.screenshot({path:O+'/png/baseline-'+id+'.png',fullPage:true,animations:'disabled'});
    await p.evaluate(()=>document.querySelector('#content-main.km-place-form-page').classList.add('col-12'));
    const prototype=await measure(p);const controls={get200:response.status()===200,admin_language:await p.locator('html').getAttribute('lang')===lang,same_textarea_count:await p.locator('textarea').count()===(role==='viewer'?0:3)};
    if(role==='super'){
     await p.locator('label[for=id_districts_json]').click();controls.native_label_focus=await p.locator('#id_districts_json').evaluate(e=>e===document.activeElement);await p.keyboard.press('Tab');controls.native_tab=await p.locator('#id_metro_stations_json').evaluate(e=>e===document.activeElement);
    }
    if([390,1440].includes(width))await p.screenshot({path:O+'/png/prototype-'+id+'.png',fullPage:true,animations:'disabled'});
    await p.evaluate(()=>document.querySelector('#content-main.km-place-form-page').classList.remove('col-12'));
    const rollback=await measure(p);const afterState=await(await p.request.get(base+'/qa/site21/state/')).json();controls.no_fixture_write=JSON.stringify(beforeState)===JSON.stringify(afterState);controls.rollback_geometry=Math.abs(rollback.root.width-baseline.root.width)<.75&&rollback.checks.visible_cards_within_main===baseline.checks.visible_cards_within_main;
    rows.push({id,role,lang,width,baseline,prototype,checks:controls,provenance:'Current application GET→in-memory col-12 only→remove class. Prototype is not applied-source GREEN; all changes discarded each cell.'});
   }
  }
  await c.close();
 }
 return{rows,pageerrors,local_errors,console_errors,blocked,scope:'Native RED/current-source and explicitly labeled reversible DOM prototype. No template override/network stub/app source modification.'};
}
