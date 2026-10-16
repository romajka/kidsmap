async(page)=>{
 const base='http://127.0.0.1:44245/',errors=[],requests=[];
 const ctx=await page.context().browser().newContext({javaScriptEnabled:false,storageState:await page.context().storageState(),viewport:{width:390,height:900}});
 await ctx.route('**/*',r=>r.request().url().startsWith(base)||r.request().url()==='about:blank'?r.continue():r.abort('blockedbyclient'));
 const p=await ctx.newPage();p.on('pageerror',e=>errors.push({text:String(e),stack:e.stack||'',url:p.url()}));
 for(const path of ['ru/account/notifications/','ru/account/places/team/','ru/account/notifications/','ru/account/organizations/','ru/account/notifications/']){
  const r=await p.goto(base+path);await p.waitForLoadState('networkidle');requests.push({path,status:r.status()});
 }
 await ctx.close();return{rows:[{name:'JS-disabled read-only account navigation without decision',status:requests.every(r=>r.status===200)?'PASS':'FAIL',detail:requests}],error:null,diagnostics:{pageerrors:errors},browser:page.context().browser().version(),note:'No reject/accept/invite/transfer POST. Browser JS disabled, own context only; source unchanged.'};
}