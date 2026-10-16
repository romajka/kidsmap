async(original)=>{
__COMMON__
const lang='az',width=1440,cell=lang+'-'+width,E=__CASES__[cell];
const all=[],open=async(role)=>{const x=await context(role,lang,width);all.push(x.c);return x;};
const owner=await open('owner'),member=await open('member'),recipient=await open('recipient');
const p=owner.p,path=prefix(lang)+'/account/organizations/'+E.organization_id+'/';
const proof=async()=>await(await p.request.get(B+'/qa/grant-proof/'+E.organization_id+'/')).json();
const row=(id,ok,d={})=>add(cell+':'+id,ok,d,'owner',lang,width);
const manager=p=>p.locator('[data-team-management]');
async function refresh(p){await manager(p).locator('[data-team-management-refresh]').click();await p.waitForFunction(()=>document.querySelector('[data-team-management]')?.getAttribute('aria-busy')==='false');}
async function operation(p,button){
 const pending=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/business/team/'));
 await button.click();const r=await pending;
 await p.waitForFunction(()=>document.querySelector('[data-team-management]')?.getAttribute('aria-busy')==='false');
 return {http:r.status(),message:await manager(p).locator('[data-team-management-status]').textContent(),body:await r.json()};
}
async function invite(email){
 const f=p.locator('[data-team-form]');await f.locator('[name=email]').fill(email);await f.locator('[name=scope]').selectOption(E.scope);
 if(E.scope==='selected_places')await f.locator('[name=place_ids][value="'+E.places[1]+'"]').check();
 const pending=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/invite/'));
 await f.locator('[type=submit]').click();const r=await pending;await p.waitForFunction(()=>document.querySelector('[data-team-form]')?.getAttribute('aria-busy')==='false');return r;
}
try{
 await visit(p,path);
 const candidate='Fictional candidate '+cell;
 await p.locator('[data-org-edit-form] [name=name_en]').fill(candidate);
 await p.waitForFunction(()=>document.querySelector('[data-draft-status]')?.textContent?.match(/Сохранено на сервере|Serverdə saxlanıb|Saved on server/));
 await navigate(p,p.locator('[data-org-edit-form] button[name=submit]'));
 const before=await proof();row('native-candidate-baseline',before.revision?.status==='pending'&&before.live_name_en==='Fictional live '+cell,{readback:before});
 const invitation=await invite(F.actors.member.email);row('native-invite',invitation.status()===200);
 await visit(member.p,prefix(lang)+'/account/notifications/');
 await navigate(member.p,member.p.locator('form[action$="/accept/"] button[type=submit]'));
 await refresh(p);
 let data=await proof(),grant=data.grants.find(g=>g.member_id===F.actors.member.id);
 row('native-accept-refresh-list',grant?.is_active&&await p.locator('[data-grant-row="'+grant.id+'"]').isVisible(),{readback:data,screenshot:await shot(p,cell+'-accepted')});
 row('scope-before-change',data.branches.find(b=>b.id===E.places[1]).member_edit&&(E.scope==='all_network'||!data.branches.find(b=>b.id===E.places[2]).member_edit));
 const stale=await open('owner');await visit(stale.p,path);
 const working='Working input '+cell;
 await p.locator('[data-org-edit-form] [name=name_en]').fill(working);
 await p.waitForFunction(()=>document.querySelector('[data-draft-status]')?.textContent?.match(/Сохранено на сервере|Serverdə saxlanıb|Saved on server/));
 let role=p.locator('[data-grant-row="'+grant.id+'"] [data-team-operation=role]');
 await role.locator('[name=role]').selectOption('MANAGER');
 const changed=await operation(p,role.locator('[type=submit]'));
 data=await proof();row('native-role-change',changed.http===200&&data.grants[0].role==='MANAGER'&&data.grants[0].version===2,{...changed,readback:data,screenshot:await shot(p,cell+'-role')});
 row('refresh-preserves-edit-input',await p.locator('[data-org-edit-form] [name=name_en]').inputValue()===working);
 const old=stale.p.locator('[data-grant-row="'+grant.id+'"] [data-team-operation=role]');
 await old.locator('[name=role]').selectOption('MODERATOR');
 const conflict=await operation(stale.p,old.locator('[type=submit]'));
 data=await proof();row('real-two-tab-grant-conflict',conflict.http===409&&data.grants[0].role==='MANAGER'&&data.grants[0].version===2,{...conflict,screenshot:await shot(stale.p,cell+'-stale-conflict')});
 const trigger=p.locator('[data-team-confirm-open="org-grant-revoke-'+grant.id+'"]');
 await trigger.focus();await p.keyboard.press('Enter');
 const panel=p.locator('#org-grant-revoke-'+grant.id);
 row('keyboard-confirmation-focus',await panel.isVisible()&&await panel.locator('[data-team-confirm-close]').evaluate(e=>e===document.activeElement),{screenshot:await shot(p,cell+'-confirmation')});
 await p.keyboard.press('Escape');
 row('escape-restores-trigger',!await panel.isVisible()&&await trigger.evaluate(e=>e===document.activeElement));
 await trigger.click();const revoked=await operation(p,panel.locator('[type=submit]'));
 data=await proof();row('native-revoke',revoked.http===200&&!data.grants[0].is_active&&data.grants[0].version===3,{...revoked,readback:data,screenshot:await shot(p,cell+'-revoked')});
 row('network-versus-direct-access',data.branches.find(b=>b.id===E.places[0]).member_edit&&!data.branches.find(b=>b.id===E.places[1]).member_edit&&!data.branches.find(b=>b.id===E.places[2]).member_edit);
 await p.reload();row('revoke-persists-reload',await p.locator('[data-grant-row="'+grant.id+'"] [data-team-operation]').count()===0);
 const deny=await visit(member.p,prefix(lang)+'/account/places/'+E.places[1]+'/edit/');
 row('revoked-editor-denied',deny>=400||!member.p.url().endsWith('/'+E.places[1]+'/edit/'),{http:deny,url:member.p.url(),screenshot:await shot(member.p,cell+'-denied')});
 const direct=await visit(member.p,prefix(lang)+'/account/places/'+E.places[0]+'/edit/');row('direct-place-access-remains',direct===200);
 await invite(F.actors.recipient.email);
 data=await proof();const pending=data.invitations.find(i=>i.email===F.actors.recipient.email&&i.status==='PENDING');
 await visit(recipient.p,prefix(lang)+'/account/notifications/');
 const staleAccept=recipient.p.locator('form[action$="/accept/"] button[type=submit]');
 await p.locator('[data-team-confirm-open="org-invite-cancel-'+pending.id+'"]').click();
 const canceled=await operation(p,p.locator('#org-invite-cancel-'+pending.id+' [type=submit]'));
 data=await proof();row('native-pending-cancel',canceled.http===200&&data.invitations.find(i=>i.id===pending.id).status==='CANCELED',{...canceled,readback:data,screenshot:await shot(p,cell+'-cancelled')});
 const refused=recipient.p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/accept/'));
 await staleAccept.click();const refuse=await refused;
 row('cancel-versus-stale-recipient-accept',refuse.status()===403,{http:refuse.status()});
 await p.reload();row('cancel-persists-reload',await p.locator('[data-team-invitation="'+pending.id+'"]').count()===0);
 data=await proof();row('content-ownership-candidate-preserved',data.ownership_version===1&&data.content_version===1&&data.live_name_en===before.live_name_en&&JSON.stringify(data.revision)===JSON.stringify(before.revision),{readback:data});
 return{rows,errors,network,consoleEvents,cell,organization_id:E.organization_id};
}catch(e){return{rows,errors,network,consoleEvents,cell,error:String(e)};}
finally{for(const c of all)await c.close();}
}
