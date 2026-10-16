async (original) => {
__COMMON__
const E=__ENTITIES__,owner=await context('owner','ru',390),p=owner.p;
await visit(p,'/ru/account/organizations/'+E.organization_id+'/');
const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/drafts/'));
await p.locator('[data-org-edit-form] [name=name_en]').fill(E.name+' EN mobile pending');
const r=await response;
await p.waitForFunction(()=>document.querySelector('[data-draft-status]')?.textContent.includes('Конфликт'));
const message=await p.locator('[data-draft-status]').textContent();
await p.locator('[data-draft-status]').scrollIntoViewIfNeeded();
add('mobile-post-approval-autosave',r.status()===200,{expected_http:200,actual_http:r.status(),message,screenshot:await shot(p,'mobile-conflict')},'owner','ru',390);
await owner.c.close();return{rows,errors,network,consoleEvents};
}
