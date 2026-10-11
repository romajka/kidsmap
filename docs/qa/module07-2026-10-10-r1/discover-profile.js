async original=>{
 const B='http://localhost:8820',F=__FIXTURES_JSON__,c=await original.context().browser().newContext({viewport:{width:390,height:950}}),p=await c.newPage(),rows=[];await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
 for(const role of ['owner','network','person']){
  await p.goto(B+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>u.pathname.includes('/account/')),p.locator('.auth-form button[type=submit]:visible').click()]);
  for(const path of role==='network'?['/ru/account/organizations/'+F.organization+'/']:role==='person'?['/ru/account/specialists/'+F.specialist+'/certificates/']:['/ru/account/profile/','/ru/account/settings/']){
   await p.goto(B+path);rows.push({role,path,forms:await p.locator('form').evaluateAll(es=>es.map(f=>({action:f.getAttribute('action'),id:f.id,controls:[...f.querySelectorAll('input:not([type=hidden]),button,select')].map(e=>({tag:e.tagName,name:e.name,type:e.type,text:e.tagName==='BUTTON'?e.textContent.trim():undefined}))}))),buttons:await p.locator('main button').allTextContents(),dialogs:await p.locator('[role=dialog],.km-modal,.modal').evaluateAll(es=>es.map(e=>({id:e.id,classes:e.className})))});
  }
  await p.request.post(B+'/ru/auth/logout/',{form:{csrfmiddlewaretoken:(await c.cookies()).find(x=>x.name==='module07_r1_csrf')?.value||''}});
 }
 await c.close();return{rows};
}
