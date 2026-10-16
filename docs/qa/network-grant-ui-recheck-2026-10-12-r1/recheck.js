async (original) => {
__COMMON__
const owner=await context('owner','ru',390),member=await context('member','ru',390),contexts=[owner.c,member.c];
const p=owner.p,proof=async(id)=>await (await p.request.get(B+'/qa/grant-proof/'+id+'/')).json();
let orgId;
try {
 const name='NETWORK fictional '+Date.now();
 await visit(p,'/ru/account/organizations/create/');
 await p.locator('[name=name_az]').fill(name);
 await navigate(p,p.locator('[data-org-create-form] button[type=submit]'));
 orgId=Number(p.url().match(/organizations\/(\d+)\//)[1]);
 const path='/ru/account/organizations/'+orgId+'/';
 const branch=p.locator('#org-create-branch form');
 await branch.locator('[name=name_az]').fill(name+' branch');
 await branch.locator('[name=category_id]').selectOption('EDU');
 await navigate(p,branch.locator('button[type=submit]'));
 let before=await proof(orgId);
 add('native-create-org-and-branch',before.branches.length===1,{readback:before},'owner','ru',390);
 await visit(p,path+'#org-team');
 const team=p.locator('[data-team-form]');
 await team.locator('[name=email]').fill(F.actors.member.email);
 await team.locator('[name=role]').selectOption('EDITOR');
 await team.locator('[name=scope]').selectOption('all_network');
 const invited=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/business/team/'));
 await team.locator('[type=submit]').click();const response=await invited;
 await p.waitForFunction(()=>document.querySelector('[data-team-status]')?.textContent==='Приглашение отправлено');
 add('native-invite',response.status()===200,{readback:await proof(orgId),screenshot:await shot(p,'invited')},'owner','ru',390);
 await visit(member.p,'/ru/account/notifications/');
 const accept=member.p.locator('form[action$="/accept/"] button[type=submit]');
 await navigate(member.p,accept);
 const after=await proof(orgId);
 add('native-inbox-accept-and-effective-access',after.grants.length===1&&after.grants[0].is_active&&after.branches[0].member_edit,{readback:after,screenshot:await shot(member.p,'member-accepted')},'member','ru',390);
 const placeId=after.branches[0].id;
 const memberStatus=await visit(member.p,'/ru/account/places/'+placeId+'/edit/');
 add('member-real-branch-editor',memberStatus===200,{http:memberStatus,screenshot:await shot(member.p,'member-branch-editor')},'member','ru',390);
 const oldVisible=await p.locator('#org-team').innerText();
 add('same-tab-accepted-member-list',oldVisible.includes(F.actors.member.username),{visible_text:oldVisible,screenshot:await shot(p,'owner-before-reload')},'owner','ru',390);
 await p.reload();await p.locator('#org-team').scrollIntoViewIfNeeded();
 const teamText=await p.locator('#org-team').innerText();
 const controls=await p.locator('#org-team').evaluate(e=>Array.from(e.querySelectorAll('button,a,input[type=submit],form')).map(x=>({tag:x.tagName,text:x.textContent.trim().slice(0,160),action:x.getAttribute('action'),href:x.getAttribute('href')})));
 const revoke=controls.filter(x=>/отоз|удалить сотруд|revoke|remove member/i.test(x.text+' '+(x.action||'')));
 add('reload-accepted-member-visible',teamText.includes(F.actors.member.username),{visible_text:teamText,screenshot:await shot(p,'owner-after-reload')},'owner','ru',390);
 add('native-revoke-control',revoke.length>0,{controls,readback:await proof(orgId)},'owner','ru',390);
 const fresh=await context('owner','ru',1440);contexts.push(fresh.c);await visit(fresh.p,path+'#org-team');
 add('desktop-native-revoke-control',await fresh.p.locator('#org-team').getByRole('button',{name:/Отозвать/}).count()>0,{screenshot:await shot(fresh.p,'owner-desktop')},'owner','ru',1440);
 return {rows,errors,network,consoleEvents,organization_id:orgId};
}catch(e){return{rows,errors,network,consoleEvents,organization_id:orgId,error:String(e)};}
finally{for(const c of contexts)await c.close();}
}
