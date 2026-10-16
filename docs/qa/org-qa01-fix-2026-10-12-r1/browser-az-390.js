async (original) => {
__COMMON__
const lang='az',width=390,cell=lang+'-'+width;
const savedCopy={ru:'Сохранено на сервере',az:'Serverdə saxlanıb',en:'Saved on server'};
const conflictCopy={ru:'Конфликт:',az:'Konflikt:',en:'Conflict:'};
const allContexts=[];
const remember=async(role)=>{const x=await context(role,lang,width);allContexts.push(x.c);return x;};
const row=(id,ok,d={})=>add(cell+':'+id,ok,d,'owner',lang,width);
const proof=async(p,id)=>await (await p.request.get(B+'/qa/org-proof/'+id+'/')).json();
const edit=p=>p.locator('[data-org-edit-form]');
const input=p=>edit(p).locator('[name=name_en]');
async function autosave(p,value,code){
 const pending=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/api/drafts/'));
 await input(p).fill(value);const r=await pending;
 await p.waitForFunction(({copy,code})=>document.querySelector('[data-draft-status]')?.textContent.startsWith(copy),
  {copy:code===409?conflictCopy[lang]:savedCopy[lang],code});
 return {http:r.status(),body:await r.json(),message:await edit(p).locator('[data-draft-status]').textContent()};
}
async function shotStatus(p,name){await edit(p).locator('[data-draft-status]').scrollIntoViewIfNeeded();return shot(p,cell+'-'+name);}
let organizationId;
try {
 const owner=await remember('owner'),p=owner.p;
 const initial='ORGQA01 fictional '+cell+' '+Date.now(),submitted=initial+' candidate';
 await visit(p,prefix(lang)+'/account/organizations/create/');
 await p.locator('[name=name_az]').fill(initial);
 await p.locator('#disclosure-translations summary').click();
 await p.locator('[name=name_en]').fill(initial+' live');
 await navigate(p,p.locator('[data-org-create-form] button[type=submit]'));
 organizationId=Number(p.url().match(/organizations\/(\d+)\//)[1]);
 const path=prefix(lang)+'/account/organizations/'+organizationId+'/';
 const first=await autosave(p,submitted,201);
 row('initial-autosave',first.http===201,{actual_http:first.http});
 await navigate(p,edit(p).locator('button[name=submit]'));
 const pending=await proof(p,organizationId);
 row('native-submit-keeps-live',pending.revision_status==='pending'&&pending.live_name_en===initial+' live'&&pending.content_version===1,{readback:pending});
 const admin=await remember('admin');
 await visit(admin.p,'/ru/admin/volunteer/moderation/content/'+pending.revision_id+'/');
 await admin.p.locator('[name=reason]').fill('Own fictional '+cell+' approval');
 await navigate(admin.p,admin.p.locator('button[value=approve]'));
 await visit(p,path);
 const approved=await proof(p,organizationId),dataset=await edit(p).evaluate(e=>({...e.dataset}));
 row('native-approve-fresh-binding',approved.status==='published'&&approved.content_version===2&&dataset.sourceVersion==='2'&&dataset.draftId===''&&dataset.draftVersion==='0',{dataset,readback:approved});
 const newName=initial+' after approval';
 const fresh=await autosave(p,newName,201);
 row('post-approval-server-autosave',fresh.http===201&&fresh.body.draft_id!==first.body.draft_id,{actual_http:fresh.http,message:fresh.message,screenshot:await shotStatus(p,'fresh-saved')});
 await p.reload();
 row('reload-server-saved',await input(p).inputValue()===newName,{screenshot:await shot(p,cell+'-reload')});
 const second=await remember('owner');await visit(second.p,path);
 row('independent-context-resume',await input(second.p).inputValue()===newName,{screenshot:await shot(second.p,cell+'-independent')});
 const unchanged=await proof(p,organizationId);
 row('autosave-preserves-live-and-old-draft',unchanged.live_name_en===submitted&&unchanged.revision_name_en===submitted&&unchanged.drafts.some(d=>d.id===first.body.draft_id&&d.source_version===1&&d.version===1&&d.fields.name_en===submitted),{readback:unchanged});
 await input(p).click();await p.keyboard.press('Tab');
 const focus=await p.evaluate(()=>({name:document.activeElement?.name,rect:document.activeElement?.getBoundingClientRect().toJSON(),viewport:innerWidth}));
 row('keyboard-focus-next-field',focus.name==='phone'&&focus.rect.width>0,{focus});
 const winner=initial+' winner',loser=initial+' losing input';
 const win=await autosave(p,winner,200);
 row('first-concurrent-save',win.http===200,{actual_http:win.http});
 const lose=await autosave(second.p,loser,409);
 row('real-cas-conflict-retains-input',lose.http===409&&await input(second.p).inputValue()===loser&&lose.body.submitted_fields.name_en===loser,{actual_http:lose.http,message:lose.message,screenshot:await shotStatus(second.p,'real-conflict')});
 await second.p.reload();
 row('conflict-local-recovery',await input(second.p).inputValue()===loser);
 const third=await remember('owner');await visit(third.p,path);
 row('conflict-winner-on-server',await input(third.p).inputValue()===winner,{screenshot:await shot(third.p,cell+'-winner')});
 const latest=await proof(p,organizationId);
 row('concurrency-keeps-public-unmodified',latest.live_name_en===submitted&&latest.content_version===2&&latest.revision_name_en===submitted,{readback:latest});
 const guest=await remember('guest');await visit(guest.p,'/en/organizations/'+latest.public_id+'/');
 row('public-page-before-review',await guest.p.locator('body').innerText().then(t=>t.includes(submitted)&&!t.includes(winner)),{screenshot:await shot(guest.p,cell+'-public-before-review')});
 await navigate(third.p,edit(third.p).locator('button[name=submit]'));
 const resubmitted=await proof(third.p,organizationId);
 row('native-resubmit-keeps-live',resubmitted.revision_status==='pending'&&resubmitted.live_name_en===submitted&&resubmitted.revision_name_en===winner);
 await visit(admin.p,'/ru/admin/volunteer/moderation/content/'+resubmitted.revision_id+'/');
 await admin.p.locator('[name=reason]').fill('Own fictional '+cell+' second approval');
 await navigate(admin.p,admin.p.locator('button[value=approve]'));
 const final=await proof(p,organizationId);
 await guest.p.reload();
 row('native-second-approve-public-reload',final.content_version===3&&final.live_name_en===winner&&await guest.p.locator('body').innerText().then(t=>t.includes(winner)),{readback:final,screenshot:await shot(guest.p,cell+'-public-approved')});
 return {rows,errors,network,consoleEvents,organization_id:organizationId};
} catch(e){return {rows,errors,network,consoleEvents,organization_id:organizationId,error:String(e)};}
finally{for(const c of allContexts)await c.close();}
}
