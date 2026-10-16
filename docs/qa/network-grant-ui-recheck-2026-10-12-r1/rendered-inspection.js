async (original)=>{
__COMMON__
const orgId=3;
for(const width of [390,1440]){
 const owner=await context('owner','ru',width);
 await visit(owner.p,'/ru/account/organizations/'+orgId+'/#org-team');
 const row=owner.p.locator('#org-team .org-row').filter({hasText:F.actors.member.username});
 await row.scrollIntoViewIfNeeded();
 add('owner-grant-row-'+width,await row.isVisible(),{screenshot:await shot(owner.p,'grant-row-'+width),text:await row.innerText()},'owner','ru',width);
 await owner.c.close();
}
const member=await context('member','ru',390);
const status=await visit(member.p,'/ru/account/organizations/'+orgId+'/');
add('member-has-no-organization-management',status===404,{http:status,screenshot:await shot(member.p,'member-org-denied')},'member','ru',390);
await member.c.close();return{rows,errors,network,consoleEvents};
}
