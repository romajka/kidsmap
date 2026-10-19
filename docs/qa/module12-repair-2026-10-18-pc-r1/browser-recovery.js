async page=>{
 const B='http://127.0.0.1:33780',rows=[],errors=[];await page.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const state=async()=>await(await page.request.get(B+'/qa/m12/state/')).json();
 try{
  await page.goto(B+'/qa/m12/login/owner/');const s=await state();
  for(const lang of ['az','ru','en']){const a=await state(),r=await page.goto(B+s.urls[lang].place),z=await state();rows.push({id:'recovery-'+lang,checks:{http200:r.status()===200,real_write_recovered:z.events_total-a.events_total===1,metric_recovered:z.metrics.views-a.metrics.views===1}});const owner=await page.goto(B+(lang==='az'?'':'/'+lang)+'/account/places/'+s.ids.place+'/analytics/');rows.push({id:'owner-recovered-'+lang,checks:{http200:owner.status()===200,available_grid:await page.locator('.owner-analytics__grid').count()===1,collection_start_visible:(await page.locator('.owner-analytics__meta').innerText()).includes('20.08.2026')}})}
 }catch(e){errors.push(String(e))}return{rows,errors,scope:'Healthy actual storage after SIMULATED failures/disable; real persisted view delta and truthful explicit fictional collection-start metadata.'};
}
