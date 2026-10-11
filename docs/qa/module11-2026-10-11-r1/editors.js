async original=>{
 __QA11_COMMON__
 const owner=await context('owner'),admin=await context('admin'),data=[];
 for(const [role,path] of [['owner','/ru/account/organizations/1/#org-edit'],['owner','/ru/account/organizations/1/programs/1/'],['admin','/admin/catalog/sitevisibilitysettings/1/change/'],['admin','/admin/catalog/catalogcontentsettings/1/change/'],['admin','/admin/catalog/event/1/change/']]){
 const p=role==='owner'?owner.p:admin.p,status=await visit(p,path);
 data.push({role,path,status,heading:await p.locator('h1').allTextContents(),inputs:await p.locator('input,textarea,select').evaluateAll(es=>es.filter(e=>e.name!=='csrfmiddlewaretoken').map(e=>({tag:e.tagName,name:e.name,id:e.id,type:e.type,value:e.type==='password'?'[omitted]':e.value,checked:e.checked,visible:!!e.getClientRects().length}))),buttons:await p.locator('button,a[data-org-edit-toggle]').evaluateAll(es=>es.map(e=>({tag:e.tagName,name:e.name,value:e.value,text:e.textContent.trim(),visible:!!e.getClientRects().length,attrs:[...e.attributes].filter(a=>a.name.startsWith('data-')).map(a=>[a.name,a.value])}))),snapshot:status>=400?'Error route; full DEBUG settings omitted':(await p.locator('main').last().innerText()).slice(0,14000)});
 }
 await owner.c.close();await admin.c.close();return {data};
}

