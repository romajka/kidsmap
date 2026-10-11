const F=__FIXTURES_JSON__,B='http://localhost:8842',ROOT='C:/kidsmap/docs/qa/place-qa08-fix-2026-10-11-r1';
const br=original.context().browser(),rows=[],consoleErrors=[],networkErrors=[],blocked=[];
function add(scenario,ok,detail={},lang='ru',width=1440,shot=''){rows.push({...detail,scenario,status:ok?'PASS':'FAIL',role:'owner',lang,width,shot});}
function prefix(lang){return lang==='az'?'':'/'+lang;}
async function context(lang,width=1440){
 const c=await br.newContext({viewport:{width,height:950}});
 await c.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='localhost')return r.continue();blocked.push({method:r.request().method(),url:u.origin+u.pathname});return r.abort();});
 await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);
 const p=await c.newPage();p.setDefaultTimeout(12000);p.setDefaultNavigationTimeout(25000);
 p.on('pageerror',e=>consoleErrors.push({lang,width,type:'pageerror',message:String(e)}));
 p.on('console',m=>{if(m.type()==='error')consoleErrors.push({lang,width,type:'console',message:m.text()});});
 p.on('response',r=>{if(r.status()>=400)networkErrors.push({lang,width,url:r.url().split('?')[0],status:r.status()});});
 p.on('dialog',d=>d.accept());
 await p.goto(B+'/ru/auth/login/');
 await p.locator('input[name=username]').fill(F.actors.owner.email);
 await p.locator('input[name=password]').fill('__LOCAL_PASSWORD__');
 await p.locator('.register-form--login button[type=submit]').click();
 await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));
 await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);
 return {c,p};
}
async function state(p){const r=await p.request.get(B+'/qa/state/');if(!r.ok())throw new Error('read-only state HTTP '+r.status());return r.json();}
async function shot(p,name){const file='screenshots/'+name+'.png';await p.screenshot({path:ROOT+'/'+file,animations:'disabled'});return file;}
async function edit(p,lang){await p.goto(B+prefix(lang)+'/account/places/'+F.place+'/edit/');await p.locator('#id_district').waitFor({state:'visible'});}
