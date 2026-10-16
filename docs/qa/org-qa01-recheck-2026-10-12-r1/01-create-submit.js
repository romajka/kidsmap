async (original) => {
__COMMON__
const {c,p}=await context('owner','ru',1440);
const name='ORGQA01 fictional '+Date.now();
await visit(p,'/ru/account/organizations/create/');
await p.locator('[name=name_az]').fill(name);
await p.locator('#disclosure-translations summary').click();
await p.locator('[name=name_en]').fill(name+' EN');
await navigate(p,p.locator('[data-org-create-form] button[type=submit]'));
const orgId=Number(p.url().match(/organizations\/(\d+)\//)[1]);
const edit=p.locator('[data-org-edit-form]');
await edit.locator('[name=name_en]').fill(name+' EN draft');
await p.waitForFunction(()=>document.querySelector('[data-draft-status]')?.textContent.includes('Сохранено на сервере'));
const dataset=await edit.evaluate(e=>({...e.dataset}));
add('native-create-autosave',dataset.draftId.length===36&&dataset.sourceVersion==='1',{organization_id:orgId,dataset,screenshot:await shot(p,'before-submit')});
await navigate(p,edit.locator('button[name=submit]'));
add('native-submit',await p.locator('.org-alert--pending').isVisible(),{screenshot:await shot(p,'submitted')});
await c.close();
return {rows,errors,network,consoleEvents,entities:{id:__PLACE_ID__,organization_id:orgId,name}};
}
