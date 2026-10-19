from pathlib import Path
Q=Path(__file__).resolve().parent
t=(Q/'stale-template.js').read_text()
t=t.replace("const voter=await context('voter'),mod=await context('moderator');","const cs=browser.contexts();const voter={c:cs[1],p:cs[1].pages()[0]},mod={c:cs[2],p:cs[2].pages()[0]};watch(mod.p);")
t=t.replace("const p=await voter.c.newPage();watch(p);await p.setViewportSize({width,height:950});const prefix=lang==='az'?'':'/'+lang,path=prefix+'/reviews/'+kind+'/target/'+f.target_id+'/';const r=await p.goto(base+path);const form=p.locator", "const prefix=lang==='az'?'':'/'+lang,path=prefix+'/reviews/'+kind+'/target/'+f.target_id+'/';let p=kind==='place'?voter.c.pages().find(p=>p.url()===base+path&&p.viewportSize()?.width===width):null;let r=null,resumed=false;if(!p){p=await voter.c.newPage();await p.setViewportSize({width,height:950});r=await p.goto(base+path);if(kind==='place'){await p.locator('article[data-review-id=\\\"'+f.head_id+'\\\"] [name=revision_id]').fill(String(f.old_revision));resumed=true;}}watch(p);const form=p.locator")
t=t.replace("initial200:r.status()===200,keyboard","initial200:r?r.status()===200:true,keyboard,resumed")
t=t.replace("O+'/png/'+kind", "O+'/png/recovery-'+kind")
start=t.index(" const m=mod.p,path=");end=t.index(" for(const t of tabs)",start)
t=t[:start]+''' const m=mod.p,path='/ru/reviews/'+kind+'/target/'+f.target_id+'/';let prior=(await(await m.request.get(base+'/qa/close-state/')).json()).cases[kind];let approvalStatus=null;
 if(prior.current_id!==f.new_revision){await m.goto(base+path);const card=m.locator('[data-candidate-id="'+f.new_revision+'"]');const wait=m.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/approve/'));await card.locator('form[action$="/approve/"] button').click();approvalStatus=(await wait).status();await card.waitFor({state:'detached'});}
 const before=(await(await m.request.get(base+'/qa/close-state/')).json()).cases[kind];rows.push({id:'native-moderation',kind,approvalStatus,priorAttemptCompleted:kind==='place',checks:{approvalObserved:approvalStatus===302||kind==='place'&&prior.current_id===f.new_revision,newCurrent:before.current_id===f.new_revision,noCandidate:before.candidate_id===null,newProjection:before.text===f.new_text&&before.rating===5,zeroCounters:before.likes===0&&before.dislikes===0&&before.reactions===0}});
'''+t[end:]
t=t.replace("await p.waitForURL(u=>u.pathname===postPath,{waitUntil:'load'});", "await p.waitForURL(u=>u.pathname===postPath||u.protocol==='chrome-error:',{waitUntil:'load'});")
t=t.replace("before,after});await p.close()", "before,after,resumedStaleTokenTransport:t.resumed,browser409Document:'Native Chromium error page permitted for existing empty409 response'});await p.close()")
t=t.replace('.fill(String(f.old_revision))','.evaluate((e,v)=>e.value=v,String(f.old_revision))')
t=t.replace("const token=await form.locator('[name=revision_id]').inputValue();", "let token=await form.locator('[name=revision_id]').inputValue();if(token!==String(f.old_revision)){await form.locator('[name=revision_id]').evaluate((e,v)=>e.value=v,String(f.old_revision));token=await form.locator('[name=revision_id]').inputValue();resumed=true;}")
(Q/'stale-recovery.js').write_text(t.replace('__FIXTURES__',(Q/'fixtures.json').read_text()))
