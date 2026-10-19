async original=>{
 const B='http://127.0.0.1:33810',rows=[],errors=[],pageerrors=[],badResponses=[],contexts=[],br=original.context().browser();
 try{
  const data=await(await original.context().request.get(B+'/qa/m13/cross/')).json();
  for(const lang of ['az','ru','en'])for(const width of [360,390,768,1024,1280,1440]){
   const c=await br.newContext({viewport:{width,height:950},userAgent:'Mozilla/5.0 Chrome/153.0.0.0 Safari/537.36'});contexts.push(c);await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(12000);p.on('pageerror',e=>pageerrors.push(String(e)));p.on('response',r=>{if(r.status()>=500)badResponses.push({status:r.status(),path:new URL(r.url()).pathname})});
   for(const[key,path]of Object.entries(data.urls[lang])){
    const res=await p.goto(B+path,{waitUntil:'load'});const checks={http_ok:res.status()===200,one_main:await p.locator('main').count()===1,one_h1:await p.locator('h1').count()===1,language:await p.locator('html').getAttribute('lang')===lang,no_overflow:await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),title_present:(await p.title()).length>0};
    const link=p.locator('main a[href]').filter({visible:true}).first();if(await link.count()){await link.focus();checks.keyboard_focus=await link.evaluate(e=>e===document.activeElement)}
    rows.push({id:'cross-public-'+key,lang,width,checks});
    if(width===390||width===1440)await p.screenshot({path:'/mnt/c/kidsmap/docs/qa/module13-repair-2026-10-19-pc-r1/png/final-'+key+'-'+lang+'-'+width+'.png',fullPage:true});
   }
   await c.close();contexts.pop();
  }
 }catch(e){errors.push(String(e))}finally{for(const c of contexts)await c.close()}
 return{rows,errors,pageerrors,badResponses,scope:'Current cross-module entities; primary internal links keyboard sampled. External map/provider transport blocked.'};
}
