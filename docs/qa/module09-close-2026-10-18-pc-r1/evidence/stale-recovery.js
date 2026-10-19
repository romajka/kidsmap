async original=>{
const F={
  "synthetic_only": true,
  "author_id": 46,
  "voter_id": 47,
  "cases": {
    "place": {
      "target_id": 11,
      "head_id": 29,
      "old_revision": 30,
      "new_revision": 31,
      "new_text": "QA09 CLOSE NEW place"
    },
    "specialist": {
      "target_id": 3,
      "head_id": 5,
      "old_revision": 11,
      "new_revision": 12,
      "new_text": "QA09 CLOSE NEW specialist"
    }
  }
},base='http://127.0.0.1:33430',O='/mnt/c/kidsmap/docs/qa/module09-close-2026-10-18-pc-r1',rows=[],consoleErrors=[],pageerrors=[],http=[],failed=[],blocked=[],browser=original.context().browser();
async function context(role){const c=await browser.newContext({serviceWorkers:'block'});await c.route('**/*',r=>{if(new URL(r.request().url()).hostname==='127.0.0.1')return r.continue();blocked.push(new URL(r.request().url()).hostname);return r.abort();});const p=await c.newPage();watch(p);await p.goto(base+'/qa/close-login/'+role+'/');return{c,p};}
function watch(p){p.setDefaultTimeout(10000);p.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});p.on('pageerror',e=>pageerrors.push(String(e)));p.on('response',r=>{if(r.status()>=400)http.push({path:new URL(r.url()).pathname,status:r.status()});});p.on('requestfailed',r=>failed.push({path:new URL(r.url()).pathname,error:r.failure()?.errorText}));}
const cs=browser.contexts();const voter={c:cs[1],p:cs[1].pages()[0]},mod={c:cs[2],p:cs[2].pages()[0]};watch(mod.p);
for(const [kind,f]of Object.entries(F.cases)){
 const tabs=[];
 for(const lang of ['az','ru','en'])for(const width of [390,1440]){
  const prefix=lang==='az'?'':'/'+lang,path=prefix+'/reviews/'+kind+'/target/'+f.target_id+'/';let p=kind==='place'?voter.c.pages().find(p=>p.url()===base+path&&p.viewportSize()?.width===width):null;let r=null,resumed=false;if(!p){p=await voter.c.newPage();await p.setViewportSize({width,height:950});r=await p.goto(base+path);if(kind==='place'){await p.locator('article[data-review-id=\"'+f.head_id+'\"] [name=revision_id]').evaluate((e,v)=>e.value=v,String(f.old_revision));resumed=true;}}watch(p);const form=p.locator('article[data-review-id="'+f.head_id+'"] form[action$="/react/"]');let token=await form.locator('[name=revision_id]').inputValue();if(token!==String(f.old_revision)){await form.locator('[name=revision_id]').evaluate((e,v)=>e.value=v,String(f.old_revision));token=await form.locator('[name=revision_id]').inputValue();resumed=true;}const focused=form.locator('button[value="1"]');await focused.focus();await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');const keyboard=await focused.evaluate(e=>document.activeElement===e);await p.screenshot({path:O+'/png/recovery-'+kind+'-'+lang+'-'+width+'-before.png',animations:'disabled'});tabs.push({p,lang,width,path,token,initial200:r?r.status()===200:true,keyboard,resumed});
 }
 const m=mod.p,path='/ru/reviews/'+kind+'/target/'+f.target_id+'/';let prior=(await(await m.request.get(base+'/qa/close-state/')).json()).cases[kind];let approvalStatus=null;
 if(prior.current_id!==f.new_revision){await m.goto(base+path);const card=m.locator('[data-candidate-id="'+f.new_revision+'"]');const wait=m.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/approve/'));await card.locator('form[action$="/approve/"] button').click();approvalStatus=(await wait).status();await card.waitFor({state:'detached'});}
 const before=(await(await m.request.get(base+'/qa/close-state/')).json()).cases[kind];rows.push({id:'native-moderation',kind,approvalStatus,priorAttemptCompleted:kind==='place',checks:{approvalObserved:approvalStatus===302||kind==='place'&&prior.current_id===f.new_revision,newCurrent:before.current_id===f.new_revision,noCandidate:before.candidate_id===null,newProjection:before.text===f.new_text&&before.rating===5,zeroCounters:before.likes===0&&before.dislikes===0&&before.reactions===0}});
 for(const t of tabs){
  const p=t.p,button=p.locator('article[data-review-id="'+f.head_id+'"] form[action$="/react/"] button[value="1"]'),postPath=new URL(await button.locator('..').getAttribute('action'),base).pathname;
  const wait=p.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===postPath);await button.click();const response=await wait;await p.waitForURL(u=>u.pathname===postPath||u.protocol==='chrome-error:',{waitUntil:'load'});await p.screenshot({path:O+'/png/recovery-'+kind+'-'+t.lang+'-'+t.width+'-409.png',animations:'disabled'});
  const after=(await(await m.request.get(base+'/qa/close-state/')).json()).cases[kind];const reload=await p.goto(base+t.path);const fresh=p.locator('article[data-review-id="'+f.head_id+'"] form[action$="/react/"]');await p.screenshot({path:O+'/png/recovery-'+kind+'-'+t.lang+'-'+t.width+'-recovered.png',animations:'disabled'});
  rows.push({id:'stale-reaction',kind,lang:t.lang,width:t.width,checks:{initial200:t.initial200,oldToken:t.token===String(f.old_revision),keyboard:t.keyboard,status409:response.status()===409,stateUnchanged:JSON.stringify(before)===JSON.stringify(after),noReaction:after.reactions===0&&after.likes===0&&after.dislikes===0,reload200:reload.status()===200,freshToken:await fresh.locator('[name=revision_id]').inputValue()===String(f.new_revision),newPublicText:(await p.locator('.typed-reviews').innerText()).includes(f.new_text),singleMain:await p.getByRole('main').count()===1,noOverflow:await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)},before,after,resumedStaleTokenTransport:t.resumed,browser409Document:'Native Chromium error page permitted for existing empty409 response'});await p.close();
 }
}
await voter.c.close();await mod.c.close();return{rows,consoleErrors,pageerrors,http,failed,blocked,authentication:'SIMULATED own fictional role login; native moderation and stale POST real',expectedConsoleHTTP:'12x409; bare empty409 response is existing contract, not missing-main defect'};
}
