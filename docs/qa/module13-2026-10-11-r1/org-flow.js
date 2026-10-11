async original=>{
__QA13_COMMON__
const {c,p}=await context('owner');let phase='create';const entities={};
async function field(n){const l=p.locator('[data-org-create-form] [name='+n+']');if(!await l.isVisible()){await l.locator('xpath=ancestor::details').locator('summary').first().click();}return l;}
async function nav(l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}
try{
await visit(p,'/ru/account/organizations/create/');await (await field('name_az')).fill('Uydurma QA13 network');await p.reload();add('organization-partial-reload',await (await field('name_az')).inputValue()==='Uydurma QA13 network',{},'owner');
await (await field('website')).fill('bad-url');await nav(p.locator('[data-org-create-form] button[type=submit]'));add('organization-invalid-url-retains-input',(await p.locator('.org-field-error,[role=alert],.errorlist').allTextContents()).join('').length>0&&await (await field('name_az')).inputValue()==='Uydurma QA13 network',{},'owner');await p.setViewportSize({width:390,height:950});await shot(p,'org-create-error-390');
await (await field('website')).fill('https://example.invalid/qa13');await (await field('name_ru')).fill('Вымышленная QA13 сеть');await (await field('name_en')).fill('Fictional QA13 network');await (await field('phone')).fill('+994000000013');await (await field('description_az')).fill('Uydurma ailə şəbəkəsi. '.repeat(20));await nav(p.locator('[data-org-create-form] button[type=submit]'));entities.organization=Number(p.url().match(/organizations\/(\d+)/)?.[1]);add('organization-created-without-branches',!!entities.organization&&await p.locator('a[href*="/branches/"]').count()===0,{id:entities.organization},'owner');
await p.reload();add('organization-draft-reload',await p.locator('[data-org-edit-form] [name=name_az]').inputValue()==='Uydurma QA13 network',{},'owner');phase='submit';await nav(p.locator('[data-org-edit-form] button[name=submit]'));await shot(p,'org-pending-390');
const admin=await context('admin');await visit(admin.p,'/admin/catalog/organization/'+entities.organization+'/change/');await shot(admin.p,'org-review-1440');await Promise.all([admin.p.waitForNavigation({waitUntil:'domcontentloaded'}),admin.p.locator('button[value=reject]').click({noWaitAfter:true})]).catch(()=>null);entities.adminAfterReject=admin.p.url();entities.adminFields=await admin.p.locator('input,textarea,button').evaluateAll(es=>es.filter(e=>e.type!=='hidden').map(e=>({name:e.name,value:e.value,text:e.innerText?.slice(0,90)})));await admin.c.close();
return{rows,entities,phase};
}catch(e){await shot(p,'org-flow-error');return{rows,entities,phase,error:String(e),url:p.url(),errors:await p.locator('[role=alert],.errorlist').allTextContents()};}finally{await c.close();}
}
