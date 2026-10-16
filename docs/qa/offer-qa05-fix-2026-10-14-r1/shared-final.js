async(page)=>{
 const base='__BASE__',f=__FIXTURES__,here='__HERE__',rows=[],errors=[],consoleErrors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))network.push({status:r.status(),url:r.url().split('?')[0]});});
 for(const width of [390,1440])for(const kind of ['offeringgroup','place']){
 await page.setViewportSize({width,height:900});await page.goto(base+(kind==='place'?'/admin/catalog/place/'+f.place+'/change/':'/admin/catalog/offeringgroup/'));await page.locator('#content').waitFor({state:'visible'});
 const detail=kind==='offeringgroup'?await page.locator('.km-status-badge').first().evaluate(e=>({whiteSpace:getComputedStyle(e).whiteSpace,text:e.textContent})):await page.locator('form').evaluateAll(es=>({forms:es.length}));
 rows.push({id:kind==='offeringgroup'?'list-badge-'+width:'shared-place-form-'+width,status:kind==='offeringgroup'?(detail.whiteSpace==='nowrap'?'PASS':'FAIL'):(detail.forms>0?'PASS':'FAIL'),detail});await page.screenshot({path:here+'/screenshots/shared-final-'+kind+'-'+width+'.png',fullPage:true});
 }
 return{rows,errors,consoleErrors,network,fixtureCorrection:'Synthetic ready-place image added only to owned media; initial 404 observations retained.',external:'requests blocked; external font console failures excluded from local errors below'};
}
