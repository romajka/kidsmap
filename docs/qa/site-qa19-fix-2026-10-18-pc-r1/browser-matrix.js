async original => {
 const base='http://127.0.0.1:33540',O='/mnt/c/kidsmap/docs/qa/site-qa19-fix-2026-10-18-pc-r1';
 const rows=[],pageerrors=[],local_errors=[],console_errors=[],blocked=[];const browser=original.context().browser();
 for(const role of ['super','editor','viewer','denied']){
  const c=await browser.newContext({viewport:{width:1440,height:950},serviceWorkers:'block'});
  await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));
  const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));p.on('console',m=>{if(m.type()==='error')console_errors.push(m.text());});p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)local_errors.push({path:new URL(r.url()).pathname,status:r.status()});});
  await p.goto(base+'/qa/site19/login/'+role+'/',{waitUntil:'domcontentloaded'});
  for(const lang of ['az','ru','en']){
   const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;
   await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
   const info=await (await p.request.get(base+'/qa/site19/info/')).json();
   for(const width of role==='super'?[360,390,768,1024,1280,1440]:[390,1440]){
    await p.setViewportSize({width,height:950});const before=await (await p.request.get(base+'/qa/site19/state/')).json();
    const response=await p.goto(base+'/admin/catalog/catalogcontentsettings/1/change/',{waitUntil:'domcontentloaded'});
    if(role!=='denied')await p.locator('#catalogcontentsettings_form').waitFor();
    const after=await (await p.request.get(base+'/qa/site19/state/')).json();
    const expected=role==='denied'?403:200;const id=role+'-'+lang+'-'+width;const textareas=await p.locator('#catalogcontentsettings_form textarea').count();
    const checks={expected_status:response.status()===expected,no_json_or_log_write:JSON.stringify(before)===JSON.stringify(after),expected_controls:role==='denied'?await p.locator('#catalogcontentsettings_form').count()===0:role==='viewer'?textareas===0:textareas===3};
    if(role!=='denied'){
     checks.language=await p.locator('html').getAttribute('lang')===lang;
     checks.localized_title=(await p.locator('.km-place-form-hero__title').innerText()).trim()===info.title;
     if(role==='viewer')checks.readonly_values=(await p.locator('#catalogcontentsettings_form').innerText()).includes('QA stansiya');
    }
    const geometry=await p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,fields:[...document.querySelectorAll('textarea')].map(e=>({id:e.id,left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})),save_controls:[...document.querySelectorAll('button[name="_continue"],button[name="_save"]')].map(e=>({name:e.name,visible:!!(e.offsetWidth||e.offsetHeight||e.getClientRects().length),disabled:e.disabled}))}));
    if(role!=='denied'&&role!=='viewer'){
     await p.locator('label[for=id_districts_json]').click();checks.native_label_focus=await p.locator('#id_districts_json').evaluate(e=>e===document.activeElement);
     await p.keyboard.press('Tab');checks.native_tab_next_field=await p.locator('#id_metro_stations_json').evaluate(e=>e===document.activeElement);
    }
    await p.screenshot({path:O+'/png/matrix-'+id+'.png',animations:'disabled'});
    rows.push({id,role,lang,width,status:response.status(),geometry,checks});
   }
  }
  await c.close();
 }
 return {rows,pageerrors,local_errors,console_errors,blocked,scope:'Native current-source editor/readonly/denial matrix. Geometry/save visibility observed separately; existing SITE08 not asserted repaired. Synthetic fixture login.'};
}
