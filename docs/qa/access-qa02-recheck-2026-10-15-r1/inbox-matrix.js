async (page) => {
 const base='http://127.0.0.1:57239/',out='/home/ramin/kidsmap/docs/qa/access-qa02-recheck-2026-10-15-r1/screenshots/',rows=[],diagnostics={console:[],pageerrors:[],failedRequests:[],badResponses:[]};
 const f=await(await page.request.get(base+'qa/fixtures/')).json();
 page.on('console',m=>{if(m.type()==='error'||m.type()==='warning')diagnostics.console.push({type:m.type(),text:m.text()});});page.on('pageerror',e=>diagnostics.pageerrors.push(String(e)));page.on('requestfailed',r=>diagnostics.failedRequests.push({kind:r.url().startsWith(base)?'local':'external-blocked',error:r.failure()?.errorText}));page.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)diagnostics.badResponses.push({url:r.url(),status:r.status()});});
 const check=(lang,width,name,ok,detail={})=>rows.push({lang,width,name,status:ok?'PASS':'FAIL',detail});
 try {
 await page.context().clearCookies();await page.goto(base+'ru/auth/login/');await page.locator('#id_username').fill(f.users.recipient.username);await page.locator('#id_password').fill(f.password);await page.locator('form.register-form button[type=submit]').click();await page.waitForURL(u=>!u.pathname.endsWith('/auth/login/'));
 for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
  await page.setViewportSize({width,height:900});await page.goto(base+(lang==='az'?'':lang+'/')+'account/notifications/');await page.mouse.move(0,0);
  for(const item of f.notifications){
   const card=page.locator('#main-content li').filter({has:page.locator('form[action$="/'+item.id+'/accept/"]')});const accept=card.locator('form[action$="/accept/"] button');
   check(lang,width,item.target_type+': current invitation has native accept',await accept.count()===1&&await accept.isVisible());
   const decline=card.locator('form').filter({has:page.getByRole('button',{name:/Отклонить|Отказ|Decline|Reject|İmtina|Rədd/i})});const labels=await card.locator('button').allTextContents();
   check(lang,width,item.target_type+': current invitation has native decline',await decline.count()===1,{buttons:labels.map(x=>x.trim()),forms:await card.locator('form').evaluateAll(a=>a.map(e=>({action:new URL(e.action).pathname,method:e.method})))});
  }
  const first=page.locator('#main-content form[action$="/accept/"] button').first();await first.focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');
  const focus=await first.evaluate(e=>{const c=getComputedStyle(e);return {active:document.activeElement===e,visible:e.matches(':focus-visible'),outline:c.outline,boxShadow:c.boxShadow}});check(lang,width,'Existing accept reached by keyboard',focus.active&&focus.visible,focus);
  const geometry=await page.locator('#main-content').evaluate(e=>{const b=e.getBoundingClientRect();return {mainRight:b.right,viewport:innerWidth,bodyWidth:document.documentElement.scrollWidth,buttons:[...e.querySelectorAll('button')].map(x=>{const r=x.getBoundingClientRect();return {x:r.x,right:r.right,width:r.width}})}});check(lang,width,'Inbox controls within viewport',geometry.buttons.every(b=>b.x>=0&&b.right<=width+.5)&&geometry.bodyWidth<=width,geometry);
  await page.screenshot({path:out+'inbox-current-'+lang+'-'+width+'.png',fullPage:true});
 }
 return {rows,diagnostics,browser:page.context().browser().version(),simulation:'NONE for login/inbox/keyboard; outbound external requests blocked; native decline NOT RUN because control is absent'};
 }catch(e){return {rows,diagnostics,error:String(e),url:page.url()};}
}
