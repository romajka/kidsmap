async page=>{
 const B='http://127.0.0.1:33780',rows=[],errors=[],pageerrors=[];await page.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());page.on('pageerror',e=>pageerrors.push(String(e)));const state=async()=>await(await page.request.get(B+'/qa/m12/state/')).json();
 try{
  await page.goto(B+'/qa/m12/login/admin/');const initial=await state();
  for(const lang of ['az','ru','en'])for(const width of [360,390,768,1024,1280,1440]){
   await page.context().addCookies([{name:'django_language',value:lang,domain:'127.0.0.1',path:'/'}]);await page.setViewportSize({width,height:900});await page.goto(B+'/admin/catalog/siteanalytics/?period=90');const before=await state();const retry=page.locator('[role=status] a');await retry.focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');const focus=await retry.evaluate(e=>document.activeElement===e&&e.matches(':focus-visible'));
   const[r]=await Promise.all([page.waitForResponse(r=>r.request().isNavigationRequest()&&r.url().includes('/siteanalytics/?period=90')),page.keyboard.press('Enter')]);await page.waitForLoadState('domcontentloaded');const after=await state();rows.push({id:'retry-'+lang+'-'+width,lang,width,checks:{http200:r.status()===200,focus_visible:focus,period_retained:new URL(page.url()).searchParams.get('period')==='90',retry_attempted:after.simulation.provider_stub_calls>before.simulation.provider_stub_calls,honest_error:await page.locator('[data-analytics-state="unavailable"]').count()===1,no_event:after.events_total===before.events_total}});
  }
  const final=await state();rows.push({id:'retry-preserved',checks:{entities_unchanged:initial.sha===final.sha,events_unchanged:initial.events_total===final.events_total}});
 }catch(e){errors.push(String(e))}return{rows,errors,pageerrors,provider:'Explicitly SIMULATED unavailable provider; native keyboard retry issues actual same-period report request'};
}
