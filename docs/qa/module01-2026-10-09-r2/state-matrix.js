async original => {
 const base='http://localhost:8813',browser=original.context().browser(),rows=[],errors=[],network=[];
 for(const lang of ['ru','az','en']){
  const c=await browser.newContext({reducedMotion:'reduce'});const a=await c.newPage(),b=await c.newPage();
  await c.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());
  for(const p of [a,b]){p.setDefaultTimeout(9000);p.on('pageerror',e=>errors.push({lang,error:String(e)}));p.on('dialog',d=>d.accept());p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)network.push({status:r.status(),path:new URL(r.url()).pathname});});}
  const prefix=lang==='az'?'':'/'+lang;
  const state=p=>p.locator('[data-pc-save-status]').getAttribute('data-state');
  const wait=(p,s)=>p.waitForFunction(s=>document.querySelector('[data-pc-save-status]')?.dataset.state===s,s);
  try{
   await a.goto(base+'/ru/auth/login/');await a.locator('[name=username]').fill('owner@example.invalid');await a.locator('[name=password]').fill('__LOCAL_PASSWORD__');await a.getByRole('button',{name:'Войти',exact:true}).click();
   for(const width of [360,390,768,1024,1280,1440]){
    for(const p of [a,b])await p.setViewportSize({width,height:950});
    await a.goto(base+prefix+'/account/places/create/?type=permanent&fresh=1');
    const delay=async r=>{if(['POST','PATCH'].includes(r.request().method()))await new Promise(resolve=>setTimeout(resolve,1300));await r.continue();};
    await c.route('**/api/drafts/**',delay);
    await a.locator('[name=name_az]').fill('QA state '+lang+' '+width);await wait(a,'saving');
    let filename='state-owner-loading-'+lang+'-'+width+'.png';await a.screenshot({path:'C:/kidsmap/docs/qa/module01-2026-10-09-r2/screenshots/'+filename});
    rows.push({id:'owner/loading/'+lang+'/'+width,status:await state(a)==='saving'?'PASS':'FAIL',lang,width,screenshot:filename,transport:'SIMULATED 1300ms local delay; native autosave response'});
    await wait(a,'saved');await c.unroute('**/api/drafts/**',delay);const pointer=a.url();
    await b.goto(pointer);await wait(b,'saved');await a.locator('[name=name_az]').fill('QA state winner '+lang+' '+width);await wait(a,'saved');await b.locator('[name=name_az]').fill('QA state stale '+lang+' '+width);await wait(b,'conflict');
    filename='state-owner-conflict-'+lang+'-'+width+'.png';await b.locator('[data-pc-save-status]').scrollIntoViewIfNeeded();await b.screenshot({path:'C:/kidsmap/docs/qa/module01-2026-10-09-r2/screenshots/'+filename});
    rows.push({id:'owner/conflict/'+lang+'/'+width,status:(await b.locator('[name=name_az]').inputValue()).includes('stale')?'PASS':'FAIL',lang,width,screenshot:filename,message:await b.locator('[data-pc-save-status]').innerText()});
    await a.goto(pointer+'&draft_current=1');await wait(a,'saved');await c.setOffline(true);await a.locator('[name=name_az]').fill('QA offline '+lang+' '+width);await wait(a,'browser');
    filename='state-owner-offline-'+lang+'-'+width+'.png';await a.screenshot({path:'C:/kidsmap/docs/qa/module01-2026-10-09-r2/screenshots/'+filename});
    rows.push({id:'owner/offline/'+lang+'/'+width,status:(await a.locator('[name=name_az]').inputValue()).includes('offline')?'PASS':'FAIL',lang,width,screenshot:filename,message:await a.locator('[data-pc-save-status]').innerText(),transport:'SIMULATED Chromium offline'});
    await c.setOffline(false);
   }
  }catch(e){rows.push({id:'owner/state-matrix/'+lang,status:'NOT RUN',error:String(e)});}finally{await c.setOffline(false);await c.close();}
 }
 return {rows,errors,network};
}

