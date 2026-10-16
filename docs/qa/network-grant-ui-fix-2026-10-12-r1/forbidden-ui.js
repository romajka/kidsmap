async(original)=>{
__COMMON__
const cases=__CASES__;
for(const lang of ['ru','az','en']){
 const width=390,E=cases[lang+'-layout'],owner=await context('owner',lang,width),p=owner.p;
 const proof=async()=>await(await p.request.get(B+'/qa/grant-proof/'+E.organization_id+'/')).json();
 await visit(p,prefix(lang)+'/account/organizations/'+E.organization_id+'/');const before=await proof(),grant=before.grants.find(g=>g.member_id===F.actors.longmember.id);
 const url=B+prefix(lang)+'/account/business/team/organization/'+E.organization_id+'/grant/';
 for(const status of [403,404]){
  await p.route(url,route=>route.fulfill({status,contentType:'application/json',body:JSON.stringify({error:'forbidden'})}),{times:1});
  const form=p.locator('[data-grant-row="'+grant.id+'"] [data-team-operation=role]');await form.locator('[name=role]').selectOption('MANAGER');await form.locator('[type=submit]').click();
  await p.waitForFunction(()=>document.querySelector('[data-team-management]')?.getAttribute('aria-busy')==='false');
  const message=await p.locator('[data-team-management-status]').textContent(),after=await proof();
  const expected={ru:'Нет права',az:'icazə yoxdur',en:'do not have permission'}[lang];
  add(lang+':SIMULATED-forbidden-'+status,message.includes(expected)&&JSON.stringify(after.grants)===JSON.stringify(before.grants),{message,screenshot:await shot(p,lang+'-simulated-'+status),simulated_transport:true},'owner',lang,width);
  await p.locator('[data-team-management-refresh]').click();await p.waitForFunction(()=>document.querySelector('[data-team-management]')?.getAttribute('aria-busy')==='false');
  add(lang+':forbidden-manual-readback-'+status,await p.locator('[data-grant-row="'+grant.id+'"] [name=role]').inputValue()===grant.role,{},'owner',lang,width);
 }
 await owner.c.close();
}
return{rows,errors,network,consoleEvents};
}
