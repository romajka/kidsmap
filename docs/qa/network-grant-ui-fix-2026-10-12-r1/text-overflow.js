async(original)=>{
__COMMON__
const cases=__CASES__;
for(const lang of ['ru','az','en']){
 const E=cases[lang+'-layout'],owner=await context('owner',lang,1440),p=owner.p;
 await visit(p,prefix(lang)+'/account/organizations/'+E.organization_id+'/');
 const data=await(await p.request.get(B+'/qa/grant-proof/'+E.organization_id+'/')).json(),grant=data.grants.find(g=>g.member_id===F.actors.longmember.id);
 for(const width of [360,390,768,1024,1280,1440]){
  await p.setViewportSize({width,height:950});await p.reload();await p.locator('[data-team-confirm-open="org-grant-revoke-'+grant.id+'"]').click();
  const paragraph=p.locator('#org-grant-revoke-'+grant.id+' p');
  const overflow=await paragraph.evaluate(e=>({client:e.clientWidth,scroll:e.scrollWidth,rect:e.getBoundingClientRect().toJSON(),parent:e.parentElement.getBoundingClientRect().toJSON(),viewport:innerWidth,text:e.textContent}));
  add(lang+':confirmation-text-'+width,overflow.scroll<=overflow.client+1&&overflow.rect.right<=overflow.parent.right+1&&overflow.rect.right<=width&&overflow.rect.left>=0,{overflow,screenshot:await shot(p,lang+'-'+width+'-text-wrap')},'owner',lang,width);
  await p.keyboard.press('Escape');
 }
 await owner.c.close();
}
return{rows,errors,network,consoleEvents};
}
