async original=>{
const base='http://127.0.0.1:33490',O='/mnt/c/kidsmap/docs/qa/site-qa15-recheck-2026-10-18-pc-r1',rows=[],pageerrors=[],local_errors=[],blocked=[],console_errors=[],browser=original.context().browser();
let cell=0;for(const c of browser.contexts())if(c!==original.context())await c.close();
try {
for(const role of ['content']) {
 const c=await browser.newContext({viewport:{width:1440,height:950},serviceWorkers:'block'});
 await c.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='127.0.0.1')return r.continue();blocked.push(u.hostname);return r.abort();});
 const a=await c.newPage(),b=await c.newPage();for(const p of [a,b]){p.setDefaultTimeout(10000);p.on('pageerror',e=>pageerrors.push(String(e)));p.on('console',m=>{if(m.type()==='error')console_errors.push(m.text());});p.on('response',r=>{const u=new URL(r.url());if(u.hostname==='127.0.0.1'&&r.status()>=400)local_errors.push({path:u.pathname,status:r.status()});});}
 await a.goto(base+'/qa/site15/login/'+role+'/');const state=async()=>(await a.request.get(base+'/qa/site15/state/')).json();
 const path='/admin/catalog/sitefootersettings/1/change/';
 async function save(p){
 const button=p.locator('button[name=_continue]');
 const visible=await button.isVisible();p.site15SaveMethod=visible?'native button click':'native Enter in text input (existing mobile buttons hidden)';
 const action=()=>visible?button.click():p.locator('[name=footer_phone]').press('Enter');
 const [response]=await Promise.all([p.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===path),p.waitForNavigation({waitUntil:'domcontentloaded'}),action()]);
 return response.status();
}
 for(const lang of ['az','ru','en']) {
  const csrf=(await c.cookies()).find(x=>x.name==='csrftoken')?.value;
  await a.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
  for(const width of [390,1440])for(const scenario of ['same','disjoint']) {
   const id=++cell;for(const p of [a,b])await p.setViewportSize({width,height:950});
   await a.goto(base+path);await b.goto(base+path);const before=await state();
   const avalue='+99450015'+String(id).padStart(3,'0'),bvalue=scenario==='same'?'+99450025'+String(id).padStart(3,'0'):'site15-tab-b-'+id+'@example.invalid',bfield=scenario==='same'?'footer_phone':'footer_email';
   await a.locator('[name=footer_phone]').fill(avalue);const aStatus=await save(a),afterA=await state();await a.screenshot({path:O+'/png/'+id+'-'+lang+'-'+width+'-'+scenario+'-A-saved.png',animations:'disabled'});
   await b.locator('[name='+bfield+']').fill(bvalue);await b.screenshot({path:O+'/png/'+id+'-'+lang+'-'+width+'-'+scenario+'-B-draft.png',animations:'disabled'});
   const bStatus=await save(b),afterB=await state(),bound=await b.locator('[name='+bfield+']').inputValue();
   rows.push({id:'two-tab-'+scenario,role,lang,width,bfield,aStatus,bStatus,aInteraction:a.site15SaveMethod,bInteraction:b.site15SaveMethod,before,afterA,afterB,bDraft:bvalue,bBound:bound,checks:{A302:aStatus===302,AStored:afterA.footer_phone===avalue,B409:bStatus===409,APreserved:afterB.footer_phone===avalue,BNotWritten:scenario==='same'?afterB.footer_phone!==bvalue:afterB.footer_email!==bvalue,draftRetained:bound===bvalue,documentLanguage:await b.locator('html').getAttribute('lang')===lang}});
   await b.screenshot({path:O+'/png/'+id+'-'+lang+'-'+width+'-'+scenario+'-B-after.png',animations:'disabled'});
  }
 }
 await c.close();
}
return{rows,pageerrors,local_errors,console_errors,blocked,scope:'Current unpatched SITE15 behavior after retained SITE01 fix; auth helper SIMULATED, native settings form saves real, fresh owned normalDB only'};
}catch(e){return{rows,pageerrors,local_errors,console_errors,blocked,error:String(e)};}
}
