async original=>{
 const F=__FIXTURES_JSON__,B='http://localhost:8823',c=await original.context().browser().newContext({viewport:{width:1440,height:950}});
 await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();
 await p.goto(B+'/ru/auth/login/');await p.locator('input[name=username]').fill(F.actors.admin.email);await p.locator('input[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForTimeout(300);
 const sr=await p.request.get(B+'/qa/state/');const st=await sr.text();if(sr.status()!==200)return{stateError:sr.status(),reason:st.match(/<pre class="exception_value">([\s\S]*?)<\/pre>/)?.[1]};const output={state:JSON.parse(st),pages:[]};
 for(const path of ['/admin/catalog/sitesettings/','/admin/catalog/sitebrandingsettings/1/change/','/admin/catalog/sitevisibilitysettings/1/change/','/admin/catalog/sitegalleryimage/','/ru/','/ru/about/','/ru/contacts/','/ru/catalog/?q=QA10-NO-MATCH']){
  const response=await p.goto(B+path);await p.waitForTimeout(150);
  output.pages.push({path,url:p.url(),status:response.status(),head:(await p.locator('body').innerText()).slice(0,1200),fields:await p.locator('input:not([type=hidden]),textarea,select').evaluateAll(es=>es.map(e=>({tag:e.tagName,type:e.type,name:e.name,id:e.id}))),buttons:await p.locator('button').evaluateAll(es=>es.map(e=>({text:e.innerText,name:e.name,type:e.type,cls:e.className}))),imageInputs:await p.locator('input[type=file]').evaluateAll(es=>es.map(e=>({name:e.name,field:e.dataset.field,placement:e.dataset.placement,html:e.outerHTML})))});
 }
 await c.close();return output;
}
