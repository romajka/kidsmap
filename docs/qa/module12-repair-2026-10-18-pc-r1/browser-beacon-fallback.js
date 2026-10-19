async original=>{
 const B='http://127.0.0.1:33780',rows=[],errors=[],contexts=[],br=original.context().browser();const state=async c=>await(await c.request.get(B+'/qa/m12/state/')).json();
 try{
  for(const lang of ['az','ru','en'])for(const width of [390,1440]){
   const c=await br.newContext({viewport:{width,height:900},userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153.0.0.0 Safari/537.36'});contexts.push(c);await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const p=await c.newPage(),s=await state(c);await p.goto(B+s.urls[lang].place);await p.evaluate(()=>{window.__qaRejected=0;navigator.sendBeacon=()=>{window.__qaRejected++;return false}});const before=await state(c);const[r]=await Promise.all([p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/events/track/')),p.locator('[data-track-event=directions_click]:visible').first().click()]);const after=await state(c);rows.push({id:'beacon-false-'+lang+'-'+width,lang,width,checks:{http200:r.status()===200,simulated_rejection:await p.evaluate(()=>window.__qaRejected===1),one_fallback_event:after.events_total-before.events_total===1,directions_delta:after.metrics.directions-before.metrics.directions===1}});await c.close();contexts.pop();
  }
 }catch(e){errors.push(String(e))}finally{for(const c of contexts)await c.close()}return{rows,errors,simulation:'Explicit navigator.sendBeacon=false; native tracked link triggers existing real same-origin fetch fallback. No real queue overflow claimed.'};
}
