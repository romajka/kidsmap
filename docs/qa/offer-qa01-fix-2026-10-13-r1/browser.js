async original=>{
 const B='__BASE__',F=__FIXTURES__,D='__HERE__/screenshots/',browser=original.context().browser(),rows=[],shots=[],errors=[],network=[],blocked=[],contexts=[];
 let phase='start',lastPost=null;
 const check=(id,ok,extra={})=>{rows.push({id,status:ok?'PASS':'FAIL',...extra});if(!ok)throw Error(id);};
 async function context(role){const c=await browser.newContext();contexts.push(c);await c.route('**/*',r=>{if(r.request().url().startsWith(B+'/'))return r.continue();blocked.push(r.request().url().split('?')[0]);return r.abort();});const p=await c.newPage();p.setDefaultTimeout(12000);p.on('pageerror',e=>errors.push(String(e)));p.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)network.push({url:r.url().replace(B,''),status:r.status()});});if(role){await p.goto(B+(role==='admin'?'/admin/login/?next=/admin/':'/ru/auth/login/'));await p.locator('[name=username]').fill(role==='admin'?F.users.admin.username:F.users[role].email);await p.locator('[name=password]').fill('__PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('login')),p.locator(role==='admin'?'[type=submit]':'button[data-loading-button]').click()]);}return p;}
 async function snap(p,id){const file=id+'.png';await p.screenshot({path:D+file,fullPage:true});shots.push({file});}
 async function open(l){if(await l.getAttribute('open')===null)await l.locator(':scope > summary').click();}
 async function submit(p){const response=p.waitForResponse(r=>r.url().includes('/save-photos/')&&r.request().method()==='POST');const nav=p.waitForNavigation({waitUntil:'domcontentloaded'}).catch(()=>null);await p.locator('button[name=form_action][value=save_and_publish]').click();const result=await response;lastPost={status:result.status(),body:await result.json().catch(()=>null)};if(result.status()===200)await nav;return result.status();}
 try{
  const owner=await context('owner'),admin=await context('admin'),pub=await context(null);
  for(const cell of F.cells){const key=cell.lang+'-'+cell.width,keep=cell.groups[0].label,remove=cell.groups[1].label;phase=key+' baseline';
   for(const p of [owner,admin,pub])await p.setViewportSize({width:cell.width,height:950});
   await pub.goto(B+'/'+cell.lang+'/activities/'+cell.activity+'/');check(key+'-public-before',(await pub.locator('main').first().innerText()).includes(remove));
   await owner.goto(B+'/'+cell.lang+'/account/places/'+cell.place+'/edit/?fresh=1');check(key+'-language',await owner.locator('html').getAttribute('lang')===cell.lang);
   const activity=owner.locator('.pc-activity-card').first();await open(activity);const group=activity.locator('.pc-group-card').last();await open(group);
   const ui=await owner.locator('#pw-copy').evaluate(e=>JSON.parse(e.textContent));const button=group.getByRole('button',{name:ui.remove_group,exact:true});await button.focus();check(key+'-remove-focus',await button.evaluate(e=>e===document.activeElement));await owner.keyboard.press('Enter');await owner.waitForFunction(()=>document.querySelectorAll('[data-pc-offerings] .pc-group-card').length===1);check(key+'-editor-removal',await owner.locator('[data-pc-offerings] .pc-group-card').count()===1);
   await snap(owner,key+'-removed-before-submit');phase=key+' submit';check(key+'-submit',await submit(owner)===200);
   await pub.reload();check(key+'-pending-live-preserved',(await pub.locator('main').first().innerText()).includes(remove));await snap(pub,key+'-pending-public');
   await owner.goto(B+'/'+cell.lang+'/account/places/'+cell.place+'/edit/?fresh=1');const pending=await owner.locator('[name=nested_pricing]').inputValue();check(key+'-candidate-reopen',!pending.includes(remove)&&pending.includes(keep));
   phase=key+' approve';await admin.goto(B+'/admin/volunteer/review/'+cell.place+'/');check(key+'-moderator-approval-available',await admin.locator('button[value=approve]').count()===1);
   await Promise.all([admin.waitForNavigation({waitUntil:'domcontentloaded'}),admin.locator('button[value=approve]').click()]);await snap(admin,key+'-approved');
   await pub.reload();const text=await pub.locator('main').first().innerText();check(key+'-approved-public',!text.includes(remove)&&text.includes(keep));await snap(pub,key+'-approved-public');
   await owner.goto(B+'/'+cell.lang+'/account/places/'+cell.place+'/edit/?fresh=1');check(key+'-owner-reload',await owner.locator('[data-pc-offerings] .pc-group-card').count()===1&&(await owner.locator('[name=nested_pricing]').inputValue()).includes(keep));await snap(owner,key+'-owner-reloaded');
   check(key+'-public-geometry',await pub.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  }
  check('no-application-pageerrors',errors.length===0,{errors});
  return{rows,shots,errors,network,blocked:[...new Set(blocked)]};
 }catch(e){return{rows,shots,error:String(e),phase,lastPost,errors,network,blocked:[...new Set(blocked)]};}finally{for(const c of contexts)await c.close();}
}
