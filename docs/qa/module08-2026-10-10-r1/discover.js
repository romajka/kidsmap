async original=>{
 const B='http://localhost:8821',F=__FIXTURES_JSON__;
 const p=original;await p.goto(B+'/ru/admin/login/');await p.locator('[name=username]').fill(F.actors.admin.username);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/login/')),p.locator('button[type=submit],input[type=submit]').first().click()]);
 const out={version:await (await p.request.get(B+'/qa/version/')).json(),browser:p.context().browser().version(),pages:[]};
 for(const path of ['admin/volunteer/moderation/','admin/volunteer/moderation/?page=2','admin/volunteer/moderation/content/'+F.revisions.live+'/','admin/catalog/place/','admin/catalog/event/','admin/catalog/specialist/','admin/catalog/organization/']){
  const r=await p.goto(B+'/ru/'+path);out.pages.push({path,status:r.status(),text:(await p.locator('body').innerText()).slice(0,1500),controls:await p.locator('button,input,select,summary,a').evaluateAll(es=>es.filter(e=>e.getBoundingClientRect().width&&e.getBoundingClientRect().height).map(e=>({tag:e.tagName,name:e.name,id:e.id,text:(e.innerText||e.value||'').slice(0,80),href:e.getAttribute('href')})).slice(-35))});
 }
 out.state=await (await p.request.get(B+'/qa/state/')).json();return out;
}
