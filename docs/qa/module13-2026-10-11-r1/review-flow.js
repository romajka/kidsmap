async original=>{
__QA13_COMMON__
const admin=await context('admin'),owner=await context('owner');let phase='place reject';
async function nav(p,l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}
try{
let p=admin.p;await visit(p,'/admin/volunteer/review/2/');await p.locator('[name=note]').fill('QA13 fictional rejection reason');await nav(p,p.locator('button[value=reject]'));p=owner.p;await visit(p,'/ru/account/places/2/edit/');await p.waitForTimeout(300);add('place-rejection-reason-visible',(await p.locator('body').innerText()).includes('QA13 fictional rejection reason'),{},'owner');await shot(p,'place-rejected-1440');await p.reload();add('place-rejection-reason-after-reload',(await p.locator('body').innerText()).includes('QA13 fictional rejection reason'),{},'owner');
await p.locator('[name=description_az]').fill('QA13 corrected fictional description. '.repeat(15));await p.waitForTimeout(1400);await p.locator('[data-pc-submit]').click();await p.waitForURL('**/account/places/');add('place-resubmitted-after-rejection',true,{},'owner');p=admin.p;await visit(p,'/admin/volunteer/review/2/');await nav(p,p.locator('button[value=approve]'));add('place-approved-through-native-review',true,{},'admin');
phase='org reject';await visit(p,'/admin/volunteer/moderation/?kind=organization');const a=p.locator('a[href*="/moderation/content/"]').first();const href=await a.getAttribute('href');await visit(p,href);const fields=await p.locator('input,textarea,button').evaluateAll(es=>es.filter(e=>e.type!=='hidden').map(e=>({name:e.name,value:e.value,text:e.innerText?.slice(0,80)})));await shot(p,'org-unified-review-1440');return{rows,phase,href,fields};
}catch(e){return{rows,phase,error:String(e),url:admin.p.url(),ownerUrl:owner.p.url()};}finally{await admin.c.close();await owner.c.close();}
}
