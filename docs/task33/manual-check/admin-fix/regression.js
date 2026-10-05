async page => {
 const issues=[],checks=[],errors=[],network=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('console',e=>{if(e.type()==='error')errors.push(e.text());});
 page.on('requestfailed',r=>network.push({url:r.url(),reason:r.failure()?.errorText}));
 page.on('response',r=>{if(r.status()>=400)network.push({url:r.url(),status:r.status()});});
 const paths=['organization','program','activity','offeringgroup','organizationgrant','ownerteammembership'];
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});
  for(const model of paths){
   const response=await page.goto(`http://127.0.0.1:8780/admin/catalog/${model}/`);
   await page.waitForLoadState('networkidle');
   const data=await page.evaluate(()=>({
    headHeight:document.querySelector('#result_list thead')?.getBoundingClientRect().height||0,
    arrows:Array.from(document.querySelectorAll('#result_list .km-col-sort-badge svg')).map(el=>({width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height})),
    width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
    tableWidth:document.querySelector('#result_list')?.getBoundingClientRect().width||0,
    rows:document.querySelectorAll('#result_list tbody tr').length,
   }));
   const item={model,width,status:response.status(),...data};checks.push(item);
   if(response.status()!==200)issues.push({...item,issue:'HTTP'});
   if(data.headHeight>100||data.arrows.some(a=>a.width>24||a.height>24))issues.push({...item,issue:'oversized sorting icon'});
   if(data.scrollWidth>width)issues.push({...item,issue:'page horizontal overflow'});
  }
 }
 return {status:issues.length||errors.length||network.length?'FAIL':'PASS',checks,issues,errors,network};
}
