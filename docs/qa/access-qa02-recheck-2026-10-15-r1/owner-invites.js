async (page) => {
 const base='http://127.0.0.1:57239/',out='/home/ramin/kidsmap/docs/qa/access-qa02-recheck-2026-10-15-r1/screenshots/',rows=[];
 const f=await(await page.request.get(base+'qa/fixtures/')).json();
 async function login(role){await page.context().clearCookies();await page.goto(base+'ru/auth/login/');await page.locator('#id_username').fill(f.users[role].username);await page.locator('#id_password').fill(f.password);await page.locator('form.register-form button[type=submit]').click();await page.waitForURL(u=>!u.pathname.endsWith('/auth/login/'));}
 try {
  await page.setViewportSize({width:1440,height:1000});await login('owner');await page.goto(base+'ru/account/places/team/');
  const form=page.locator('form.owner-team-invite-form');await form.locator('select[name=place]').selectOption(String(f.place_id));await form.locator('input[name=email]').fill(f.users.recipient.email);
  const role=await form.locator('select[name=role] option').evaluateAll(a=>a.find(o=>o.value.toLowerCase()==='editor').value);await form.locator('select[name=role]').selectOption(role);
  const placeResponse=page.waitForResponse(r=>r.url().endsWith('/account/places/team/invite/')&&r.request().method()==='POST');await form.locator('button[type=submit]').click();const pr=await placeResponse;await page.waitForLoadState('domcontentloaded');
  rows.push({name:'Owner sends place invitation through native UI',status:pr.status()===302?'PASS':'FAIL',http:pr.status()});await page.screenshot({path:out+'owner-place-invited-ru-1440.png',fullPage:true});
  await page.goto(base+'ru/account/organizations/'+f.organization_id+'/');const orgForm=page.locator('form[data-team-form]');await orgForm.locator('input[name=email]').fill(f.users.recipient.email);await orgForm.locator('select[name=scope]').selectOption('all_network');
  const orgResponse=page.waitForResponse(r=>r.url().endsWith('/account/business/team/organization/'+f.organization_id+'/invite/')&&r.request().method()==='POST');await orgForm.locator('button[type=submit]').click();const or=await orgResponse;const orgData=await or.json();rows.push({name:'Owner sends organization invitation through native UI',status:or.status()===200&&orgData.status==='PENDING'?'PASS':'FAIL',http:or.status(),invitation_status:orgData.status});
  await page.screenshot({path:out+'owner-organization-invited-ru-1440.png',fullPage:true});await login('recipient');await page.goto(base+'ru/account/notifications/');
  const actions=await page.locator('#main-content form').evaluateAll(a=>a.map(e=>({action:new URL(e.action).pathname,method:e.method,buttons:[...e.querySelectorAll('button')].map(b=>b.innerText)})));
  const accepts=actions.filter(a=>a.action.endsWith('/accept/'));rows.push({name:'Both owner-created invitations are actionable in recipient inbox',status:accepts.length===2?'PASS':'FAIL',accept_forms:accepts.length});
  await page.screenshot({path:out+'recipient-pending-both-ru-1440.png',fullPage:true});return {rows,actions,browser:page.context().browser().version(),simulation:'NONE for owner invite/login/inbox; ORM only fictional users/targets fixture setup'};
 }catch(e){return {rows,error:String(e),url:page.url()};}
}
