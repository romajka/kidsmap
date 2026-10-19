async page=>{
const base='http://127.0.0.1:33390',rows=[],consoleErrors=[],pageerrors=[];
await page.context().route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());page.on('pageerror',e=>pageerrors.push(String(e)));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
for(const lang of ['az','ru','en'])for(const width of [360,390,768,1024,1280,1440]){
 await page.setViewportSize({width,height:950});const prefix=lang==='az'?'':'/'+lang,url=base+prefix+'/account/notifications/?tab=all';const first=await page.request.get(url,{maxRedirects:0});const r=await page.goto(url);
 const file='/mnt/c/kidsmap/.tmp/social10-pc-plan-r1/png/login404-'+lang+'-'+width+'.png';await page.screenshot({path:file});const finalUrl=page.url();const valid=await page.goto(base+prefix+'/auth/login/');const actions=[];
 for(const action of ['read','accept','reject']){const path=prefix+'/account/notifications/999999/'+action+'/';const rr=await page.request.get(base+path,{maxRedirects:0});actions.push({action,http:rr.status(),location:rr.headers().location});}
 rows.push({lang,width,initialHttp:first.status(),location:first.headers().location,finalHttp:r.status(),finalUrl,actualLoginHttp:valid.status(),actualLoginForm:await page.locator('[name=username]').isVisible(),actions,bugConfirmed:first.status()===302&&r.status()===404&&valid.status()===200,requiredRecoveryPass:r.status()===200,screenshot:'png/login404-'+lang+'-'+width+'.png'});
}
return{rows,consoleErrors,pageerrors,utc:new Date().toISOString()};}
