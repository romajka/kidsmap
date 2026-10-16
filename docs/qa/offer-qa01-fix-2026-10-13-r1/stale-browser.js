async original=>{
 const B='__BASE__',F=__FIXTURES__,D='__HERE__/screenshots/',browser=original.context().browser(),rows=[],shots=[],errors=[],network=[],blocked=[],contexts=[];
 let phase='start',lastPost=null,lastPage=null;
 const check=(id,ok,extra={})=>{rows.push({id,status:ok?'PASS':'FAIL',...extra});if(!ok)throw Error(id);};
 async function context(role){const c=await browser.newContext();contexts.push(c);await c.route('**/*',r=>{if(r.request().url().startsWith(B+'/'))return r.continue();blocked.push(r.request().url().split('?')[0]);return r.abort();});const p=await c.newPage();p.setDefaultTimeout(12000);p.on('pageerror',e=>errors.push(String(e)));p.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)network.push({url:r.url().replace(B,''),status:r.status()});});if(role){await p.goto(B+(role==='admin'?'/admin/login/?next=/admin/':'/ru/auth/login/'));await p.locator('[name=username]').fill(role==='admin'?F.users.admin.username:F.users[role].email);await p.locator('[name=password]').fill('__PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('login')),p.locator(role==='admin'?'[type=submit]':'button[data-loading-button]').click()]);}return p;}
 async function snap(p,id){const file=id+'.png';await p.screenshot({path:D+file,fullPage:true});shots.push({file});}
 async function open(l){if(await l.getAttribute('open')===null)await l.locator(':scope > summary').click();}
 async function submit(p){const response=p.waitForResponse(r=>r.url().includes('/save-photos/')&&r.request().method()==='POST');const nav=p.waitForNavigation({waitUntil:'domcontentloaded'}).catch(()=>null);await p.locator('button[name=form_action][value=save_and_publish]').click();const result=await response;lastPost={status:result.status(),body:await result.json().catch(()=>null)};if(result.status()===200)await nav;return result.status();}
 try{
  const owner=await context('owner'),admin=await context('admin'),pub=await context(null);
  const cell=F.extras.find(x=>x.key==='stale-conflict');phase='stale conflict';
  await owner.goto(B+'/ru/account/places/'+cell.place+'/edit/?fresh=1');
  const stale=await context('owner');lastPage=stale;await stale.goto(owner.url());
  const activity=owner.locator('.pc-activity-card').first();await open(activity);const group=activity.locator('.pc-group-card').last();await open(group);await group.getByRole('button',{name:'Удалить группу',exact:true}).click();
  check('cas-main-submit',await submit(owner)===200);await admin.goto(B+'/admin/volunteer/review/'+cell.place+'/');await Promise.all([admin.waitForNavigation(),admin.locator('button[value=approve]').click()]);
  await stale.locator('[name=name_az]').fill('Uydurma stale preserved');check('stale-native-rejected-422',await submit(stale)===422,{response:lastPost});check('stale-input-retained',await stale.locator('[name=name_az]').inputValue()==='Uydurma stale preserved');await snap(stale,'stale-conflict-ru-1440');await stale.close();
  await pub.goto(B+'/ru/activities/'+cell.activity+'/');check('stale-does-not-resurrect-group',!(await pub.locator('main').first().innerText()).includes(cell.groups[1].label));
  check('no-stale-pageerrors',errors.length===0,{errors});return{rows,shots,errors,network,blocked:[...new Set(blocked)]};
 }catch(e){return{rows,shots,error:String(e),phase,lastPost,errors,network};}finally{for(const c of contexts)await c.close();}
}