async(original)=>{
__COMMON__
const lang='en',E=__CASES__[lang+'-layout'];
const owner=await context('owner',lang,1440),member=await context('longmember',lang,1440),recipient=await context('recipient',lang,1440);
const p=owner.p,path=prefix(lang)+'/account/organizations/'+E.organization_id+'/',contexts=[owner.c,member.c,recipient.c];
const proof=async()=>await(await p.request.get(B+'/qa/grant-proof/'+E.organization_id+'/')).json();
const manager=p=>p.locator('[data-team-management]');
const addRow=(id,ok,d={},width=1440)=>add(lang+':'+id,ok,d,'owner',lang,width);
async function refresh(){await p.locator('[data-team-management-refresh]').click();await p.waitForFunction(()=>document.querySelector('[data-team-management]')?.getAttribute('aria-busy')==='false');}
async function invite(email){const f=p.locator('[data-team-form]');await f.locator('[name=email]').fill(email);await f.locator('[name=scope]').selectOption('all_network');const r=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/invite/'));await f.locator('[type=submit]').click();await r;await p.waitForFunction(()=>document.querySelector('[data-team-form]')?.getAttribute('aria-busy')==='false');}
try{
 await visit(p,path);await invite(F.actors.longmember.email);
 await visit(member.p,prefix(lang)+'/account/notifications/');await navigate(member.p,member.p.locator('form[action$="/accept/"] button[type=submit]'));
 await refresh();let data=await proof();const grant=data.grants.find(g=>g.member_id===F.actors.longmember.id);
 await invite(F.actors.recipient.email);data=await proof();let pending=data.invitations.find(i=>i.email===F.actors.recipient.email&&i.status==='PENDING');
 for(const width of [360,390,768,1024,1280,1440]){
  await p.setViewportSize({width,height:950});await p.reload();
  const row=p.locator('[data-grant-row="'+grant.id+'"]');await row.scrollIntoViewIfNeeded();
  const bounds=await geometry(p);const forms=await row.locator('[data-team-operation=role]').isVisible();
  addRow('layout-'+width,bounds.document<=width+1&&forms,{geometry:bounds,screenshot:await shot(p,lang+'-'+width+'-layout')},width);
  const trigger=p.locator('[data-team-confirm-open="org-grant-revoke-'+grant.id+'"]');await trigger.focus();await p.keyboard.press('Enter');
  const focus=await p.evaluate(()=>({name:document.activeElement?.textContent,rect:document.activeElement?.getBoundingClientRect().toJSON(),width:innerWidth,height:innerHeight}));
  const panel=p.locator('#org-grant-revoke-'+grant.id);
  addRow('keyboard-confirm-'+width,await panel.isVisible()&&await panel.locator('[data-team-confirm-close]').evaluate(e=>e===document.activeElement)&&focus.rect.left>=0&&focus.rect.right<=width&&focus.rect.top>=0&&focus.rect.bottom<=950,{focus,screenshot:await shot(p,lang+'-'+width+'-confirm')},width);
  await p.keyboard.press('Escape');addRow('keyboard-cancel-'+width,!await panel.isVisible()&&await trigger.evaluate(e=>e===document.activeElement),{},width);
  await p.locator('[data-team-confirm-open="org-invite-cancel-'+pending.id+'"]').click();
  const cancel=p.locator('#org-invite-cancel-'+pending.id);await cancel.locator('[data-team-confirm-close]').click();
  addRow('pending-confirm-cancel-'+width,!await cancel.isVisible(),{},width);
 }
 // Real accept wins while the owner retains a stale cancel confirmation.
 await p.locator('[data-team-confirm-open="org-invite-cancel-'+pending.id+'"]').click();
 await visit(recipient.p,prefix(lang)+'/account/notifications/');await navigate(recipient.p,recipient.p.locator('form[action$="/accept/"] button[type=submit]'));
 const conflict=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/cancel/'));
 await p.locator('#org-invite-cancel-'+pending.id+' [type=submit]').click();const c=await conflict;
 await p.waitForFunction(()=>document.querySelector('[data-team-management]')?.getAttribute('aria-busy')==='false');
 data=await proof();addRow('real-accept-wins-cancel-race',c.status()===409&&data.invitations.find(i=>i.id===pending.id).status==='ACCEPTED'&&data.grants.some(g=>g.member_id===F.actors.recipient.id&&g.is_active),{readback:data,screenshot:await shot(p,lang+'-accept-wins')});
 if(lang==='ru'){
  const url=B+prefix(lang)+'/account/business/team/organization/'+E.organization_id+'/grant/';
  let committed=0;
  await p.route(url,async route=>{await route.fetch();committed++;await route.abort();},{times:1});
  const form=p.locator('[data-grant-row="'+grant.id+'"] [data-team-operation=role]');
  await form.locator('[name=role]').selectOption('MANAGER');await form.locator('[type=submit]').click();
  await p.waitForFunction(()=>document.querySelector('[data-team-management]')?.getAttribute('aria-busy')==='false');
  data=await proof();const message=await p.locator('[data-team-management-status]').textContent();
  addRow('SIMULATED-response-lost-after-commit',committed===1&&data.grants.find(g=>g.id===grant.id).role==='MANAGER'&&message.includes('Не удалось подтвердить'),{message,readback:data,screenshot:await shot(p,'simulated-lost-response')});
  await refresh();addRow('uncertain-manual-readback',await p.locator('[data-grant-row="'+grant.id+'"] [name=role]').inputValue()==='MANAGER'&&committed===1);
  await p.route(B+path,route=>route.abort(),{times:1});
  const current=p.locator('[data-grant-row="'+grant.id+'"] [data-team-operation=role]');await current.locator('[name=role]').selectOption('EDITOR');await current.locator('[type=submit]').click();
  await p.waitForFunction(()=>document.querySelector('[data-team-management]')?.getAttribute('aria-busy')==='false');
  const partial=await p.locator('[data-team-management-status]').textContent();data=await proof();
  addRow('SIMULATED-success-with-list-failure',partial.includes('Роль сохранена')&&partial.includes('Не удалось обновить список')&&data.grants.find(g=>g.id===grant.id).role==='EDITOR',{message:partial,readback:data});
  await refresh();addRow('list-failure-manual-recovery',await p.locator('[data-grant-row="'+grant.id+'"] [name=role]').inputValue()==='EDITOR');
 }
 return{rows,errors,network,consoleEvents,lang,organization_id:E.organization_id};
}catch(e){return{rows,errors,network,consoleEvents,lang,error:String(e)};}
finally{for(const c of contexts)await c.close();}
}
