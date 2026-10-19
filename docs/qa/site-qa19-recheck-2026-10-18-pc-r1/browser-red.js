async original => {
 const base='http://127.0.0.1:33530',O='/mnt/c/kidsmap/docs/qa/site-qa19-recheck-2026-10-18-pc-r1';
 const rows=[],pageerrors=[],local_errors=[],console_errors=[],blocked=[];
 const browser=original.context().browser();
 for(const role of ['super','editor','viewer','denied']){
  const context=await browser.newContext({viewport:{width:1440,height:950},serviceWorkers:'block'});
  await context.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():(blocked.push(new URL(route.request().url()).hostname),route.abort()));
  const p=await context.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));p.on('console',m=>{if(m.type()==='error')console_errors.push(m.text());});p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)local_errors.push({path:new URL(r.url()).pathname,status:r.status()});});
  await p.goto(base+'/qa/site19/login/'+role+'/',{waitUntil:'domcontentloaded'});
  for(const lang of ['az','ru','en']){
   const csrf=(await context.cookies()).find(x=>x.name==='csrftoken').value;
   await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
   for(const width of role==='super'?[360,390,768,1024,1280,1440]:[390,1440]){
    await p.setViewportSize({width,height:950});const before=await (await p.request.get(base+'/qa/site19/state/')).json();
    const response=await p.goto(base+'/admin/catalog/catalogcontentsettings/1/change/',{waitUntil:'domcontentloaded'});
    const form=await p.locator('#catalogcontentsettings_form').count();const body=await p.locator('body').innerText();
    const after=await (await p.request.get(base+'/qa/site19/state/')).json();
    const expected=role==='denied'?403:200;
    const id=role+'-'+lang+'-'+width;
    await p.screenshot({path:O+'/png/'+id+'.png',animations:'disabled'});
    rows.push({id,role,lang,width,status:response.status(),editor_form_present:form===1,observed_pre_render_typeerror:body.includes('__str__ returned non-string'),checks:{expected_status:response.status()===expected,no_json_or_log_write:JSON.stringify(before)===JSON.stringify(after)},editor_controls_beyond_500:'NOT RUN'});
   }
  }
  await context.close();
 }
 return {rows,pageerrors,local_errors,console_errors,blocked,scope:'Current unchanged app RED, no model patch or response stub. Auth is simulated synthetic fixture login. Missing editors/500 are failures, not accepted UI.'};
}
