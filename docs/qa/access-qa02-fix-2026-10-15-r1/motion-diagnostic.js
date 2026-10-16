async(page)=>{
 const base='http://127.0.0.1:44245/',errors=[],consoleRows=[],requests=[];
 const handler=e=>errors.push({text:String(e),stack:e.stack||'',url:page.url()});
 page.on('pageerror',handler);const ctx=page.context();
 await ctx.route('**/*',r=>r.request().url().startsWith(base)||r.request().url()==='about:blank'?r.continue():r.abort('blockedbyclient'));
 for(const path of ['ru/account/notifications/','ru/account/places/team/','ru/account/notifications/','ru/account/organizations/','ru/account/notifications/']){
  const r=await page.goto(base+path);await page.waitForLoadState('networkidle');requests.push({path,status:r.status()});
 }
 page.off('pageerror',handler);
 return{rows:[{name:'read-only account navigation without invitation decision',status:requests.every(r=>r.status===200)?'PASS':'FAIL',detail:requests}],error:null,diagnostics:{pageerrors:errors},browser:ctx.browser().version(),note:'No reject/accept/invite/transfer request; no fixture or application mutation.'};
}