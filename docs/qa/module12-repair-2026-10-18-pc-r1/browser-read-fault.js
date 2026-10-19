async page=>{
 const B='http://127.0.0.1:33780',rows=[],errors=[],pageerrors=[];await page.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());page.on('pageerror',e=>pageerrors.push(String(e)));const state=async()=>await(await page.request.get(B+'/qa/m12/state/')).json();
 try{
  const initial=await state();
  for(const role of ['owner','admin']){
   await page.goto(B+'/qa/m12/login/'+role+'/');
   for(const lang of ['az','ru','en'])for(const width of [360,390,768,1024,1280,1440]){
    await page.context().addCookies([{name:'django_language',value:lang,domain:'127.0.0.1',path:'/'}]);await page.setViewportSize({width,height:900});const url=role==='owner'?(lang==='az'?'':'/'+lang)+'/account/places/'+initial.ids.place+'/analytics/':'/admin/catalog/siteanalytics/?period=90';const r=await page.goto(B+url);const checks={http200:r.status()===200,no_overflow:await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)};
    if(role==='owner'){checks.unavailable_notice=await page.locator('.owner-analytics__notice[role=status]').count()===1;checks.no_false_zero=await page.locator('.owner-analytics__grid').count()===0}else{checks.independent_ga_ready=await page.locator('[data-analytics-state=ready]').count()===1;checks.ga90=(await page.locator('[data-kpi-value=unique_sessions]').innerText()).trim()==='90'}
    rows.push({id:'read-fault-'+role+'-'+lang+'-'+width,role,lang,width,checks});if([360,1440].includes(width))await page.screenshot({path:'/mnt/c/kidsmap/docs/qa/module12-repair-2026-10-18-pc-r1/png/read-fault-'+role+'-'+lang+'-'+width+'.png',fullPage:true});
   }
  }
  const final=await state();rows.push({id:'read-fault-preserved',checks:{actual_read_fault:final.simulation.read_fault_calls>initial.simulation.read_fault_calls,no_event:initial.events_total===final.events_total,entities_unchanged:initial.sha===final.sha}});
 }catch(e){errors.push(String(e))}return{rows,errors,pageerrors,simulation:'Actual _period_values dependency raises SIMULATED DatabaseError; independent GA snapshot explicitly SIMULATED ready. No production/real provider.'};
}
