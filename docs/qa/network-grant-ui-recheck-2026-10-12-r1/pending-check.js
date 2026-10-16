async(original)=>{
__COMMON__
const owner=await context('owner','ru',390),p=owner.p,orgId=3;
await visit(p,'/ru/account/organizations/'+orgId+'/#org-team');
const grant=p.locator('#org-team .org-row').filter({hasText:F.actors.member.username});
add('native-member-role-management',await grant.locator('select,button,form').count()>0,{text:await grant.innerText()},'owner','ru',390);
const team=p.locator('[data-team-form]');
await team.locator('[name=email]').fill(F.actors.outsider.email);
const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/business/team/'));
await team.locator('[type=submit]').click();const r=await response;
await p.waitForFunction(()=>document.querySelector('[data-team-status]')?.textContent==='Приглашение отправлено');
const invite=p.locator('[data-team-invitations] .org-row').filter({hasText:F.actors.outsider.email});
await invite.scrollIntoViewIfNeeded();
add('native-second-pending-invite',r.status()===200&&await invite.isVisible(),{screenshot:await shot(p,'pending-invitation')},'owner','ru',390);
add('native-owner-pending-cancel',await invite.locator('button,form,a').count()>0,{text:await invite.innerText()},'owner','ru',390);
await owner.c.close();return{rows,errors,network,consoleEvents};
}
