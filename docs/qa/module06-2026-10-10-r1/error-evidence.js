async original=>{
 const B='http://localhost:8818',D='C:/kidsmap/docs/qa/module06-2026-10-10-r1/screenshots/',rows=[];
 for(const lang of ['ru','az','en'])for(const width of [390,1440]){
  const c=await original.context().browser().newContext({viewport:{width,height:950}});await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(15000);const prefix=lang==='az'?'/':'/'+lang+'/';await p.goto(B+prefix+'catalog/?q=Aurora');await p.locator('[data-catalog-map-open]').click();await p.locator('[data-catalog-map]').scrollIntoViewIfNeeded();await p.waitForTimeout(lang==='ru'&&width===390?15000:2200);const text=await p.locator('[data-catalog-map]').innerText(),screenshot='sdk-error-visible-'+lang+'-'+width+'.png';await p.screenshot({path:D+screenshot});rows.push({id:'SDK-error-visible',role:'anonymous',lang,width,status:await p.locator('.catalog-map-loading').count()?'FAIL':'PASS',text,screenshot,classification:'SIMULATED SDK transport abort; actual configured application branch'});await c.close();
 }
 return{rows};
}
