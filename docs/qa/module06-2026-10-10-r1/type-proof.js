async original=>{
 const B='http://localhost:8817',D='C:/kidsmap/docs/qa/module06-2026-10-10-r1/screenshots/',F=__FIXTURES_JSON__,rows=[];
 for(const lang of ['ru','az','en'])for(const width of [390,1440]){
  const c=await original.context().browser().newContext({viewport:{width,height:950}});await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(15000);const prefix=lang==='az'?'/':'/'+lang+'/';await p.goto(B+prefix+'catalog/?event_type=temporary');const links=await p.locator('main a[href]').evaluateAll(es=>[...new Set(es.map(e=>e.getAttribute('href')))]),countText=await p.locator('.results-count-text').innerText(),screenshot='temporary-results-'+lang+'-'+width+'.png';await p.screenshot({path:D+screenshot,fullPage:true});rows.push({id:'type-temporary-event-results',role:'anonymous',lang,width,status:countText.includes('2')&&links.includes(F.urls[lang].events.Scheduled)&&links.includes(F.urls[lang].events.Cancelled)?'PASS':'FAIL',countText,links,expectedUrls:[F.urls[lang].events.Scheduled,F.urls[lang].events.Cancelled],screenshot});await c.close();
 }
 return{rows};
}
