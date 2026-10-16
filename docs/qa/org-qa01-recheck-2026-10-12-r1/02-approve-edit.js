async (original) => {
__COMMON__
const E=__ENTITIES__,revision=6;
const admin=await context('admin','ru',1440);
await visit(admin.p,'/ru/admin/volunteer/moderation/content/'+revision+'/');
await admin.p.locator('[name=reason]').fill('Own fictional ORGQA01 acceptance reproduction');
await navigate(admin.p,admin.p.locator('button[value=approve]'));
add('native-moderator-approve',!admin.p.url().includes('/content/'+revision+'/'),{screenshot:await shot(admin.p,'approved')},'admin');
await admin.c.close();
const owner=await context('owner','ru',1440),path='/ru/account/organizations/'+E.organization_id+'/';
await visit(owner.p,path);
const form=owner.p.locator('[data-org-edit-form]');
const before=await form.evaluate(e=>({...e.dataset}));
const newName=E.name+' EN after approval';
const response=owner.p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/drafts/'));
await form.locator('[name=name_en]').fill(newName);
const r=await response;
const status=await form.locator('[data-draft-status]').textContent();
add('post-approval-autosave',r.status()===200,{expected_http:200,actual_http:r.status(),dataset:before,status,response:await r.json(),screenshot:await shot(owner.p,'autosave-conflict')});
await owner.p.reload();
const same=await owner.p.locator('[data-org-edit-form] [name=name_en]').inputValue();
add('same-tab-local-recovery',same===newName,{value:same,screenshot:await shot(owner.p,'same-tab-reload')});
const fresh=await context('owner','ru',1440);
await visit(fresh.p,path);
const independent=await fresh.p.locator('[data-org-edit-form] [name=name_en]').inputValue();
add('independent-context-server-persistence',independent===newName,{expected:newName,actual:independent,screenshot:await shot(fresh.p,'independent-context')});
await owner.c.close();await fresh.c.close();
return{rows,errors,network,consoleEvents,organization_id:E.organization_id};
}
