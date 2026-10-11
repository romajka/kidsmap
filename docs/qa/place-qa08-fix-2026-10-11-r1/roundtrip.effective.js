async original=>{const F={
  "actors": {
    "owner": {
      "id": 1,
      "email": "owner08@example.invalid",
      "username": "qa08_owner"
    }
  },
  "place": 1,
  "public_urls": {
    "ru": "/ru/place/1-vymyshlennoe-qa08-mesto-raiona/",
    "az": "/place/1-uydurma-qa08-rayon-mekani/",
    "en": "/en/place/1-fictional-qa08-district-fixture/"
  },
  "initial_seed_only": true,
  "synthetic_only": true
},B='http://localhost:8842',ROOT='C:/kidsmap/docs/qa/place-qa08-fix-2026-10-11-r1';
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

const states=[];
try{
 for(const lang of ['ru','az','en']){
  const {c,p}=await context(lang,lang==='ru'?390:1440);
  try{
   const before=await state(p);
   await p.goto(B+F.public_urls[lang]);
   const publicBefore=await p.locator('body').innerText();
   add('Initial public address rendered',publicBefore.includes(before.live.address),{address:before.live.address,url:p.url()},lang,lang==='ru'?390:1440);
   await edit(p,lang);
   await p.locator('#id_region').selectOption('baku');
   await p.locator('#id_district').selectOption('baku_yasamal');
   await p.waitForTimeout(1700);
   const nav=p.waitForNavigation({waitUntil:'domcontentloaded'});
   await p.locator('[name=form_action][value=save_draft]').click({noWaitAfter:true});
   await nav;await p.reload({waitUntil:'domcontentloaded'});
   const capture=await shot(p,'district-saved-'+lang+(lang==='ru'?'-390':'-1440'));
   add('Native save/reload retains district machine code',await p.locator('#id_district').inputValue()==='baku_yasamal',{code:await p.locator('#id_district').inputValue(),url:p.url()},lang,lang==='ru'?390:1440,capture);
   const after=await state(p);states.push({lang,before,after});
   add('Native save keeps live location and candidate effective district',JSON.stringify(before.live)===JSON.stringify(after.live)&&after.candidate_effective_district==='baku_yasamal'&&after.candidate_effective_address===before.live.address,{before,after},lang,lang==='ru'?390:1440);
   await p.goto(B+F.public_urls[lang]);
   add('Public address remains unchanged after native save',await p.locator('body').innerText().then(t=>t.includes(before.live.address)),{address:before.live.address,url:p.url()},lang,lang==='ru'?390:1440,await shot(p,'public-after-'+lang+(lang==='ru'?'-390':'-1440')));
  }finally{await c.close();}
 }
 return{rows,states,consoleErrors,networkErrors,blocked};
}catch(e){return{rows,error:String(e),consoleErrors,networkErrors,blocked};}
}
