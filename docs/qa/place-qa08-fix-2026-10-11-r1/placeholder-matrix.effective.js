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

const labels={ru:'Выберите район',az:'Rayon seçin',en:'Select district'},states=[];
try{
 for(const lang of ['ru','az','en']){
  const {c,p}=await context(lang,390);
  try{
   const before=await state(p);
   await c.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='localhost'&&r.request().method()==='GET')return r.continue();blocked.push({method:r.request().method(),url:u.origin+u.pathname,reason:'SIMULATED unsaved; non-GET blocked after login'});return r.abort();});
   for(const width of [360,390,768,1024,1280,1440]){
    await p.setViewportSize({width,height:950});await edit(p,lang);
    const s=p.locator('#id_district'),label=(await s.locator('option[value=""]').innerText()).trim();
    const codes=await s.locator('option').evaluateAll(options=>options.map(o=>o.value));
    add('PLACE-QA-08 localized empty district option',label===labels[lang],{label,expected:labels[lang],url:p.url(),codes},lang,width);
    await s.scrollIntoViewIfNeeded();await s.click();await s.press('Escape');
    add('Native select opens and Escape retains focus',await s.evaluate(e=>document.activeElement===e),{url:p.url()},lang,width);
    await s.click();await s.press('Home');await s.press('Enter');
    add('Native keyboard selects empty district option',await s.inputValue()==='',{integration:'SIMULATED unsaved; non-GET blocked',url:p.url()},lang,width);
    await s.focus();
    const capture=await shot(p,'district-empty-'+lang+'-'+width);
    const geom=await s.evaluate(e=>{const r=e.getBoundingClientRect(),css=getComputedStyle(e);return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,viewport:innerWidth,document:document.documentElement.scrollWidth,focus:document.activeElement===e,outline:css.outline,boxShadow:css.boxShadow,disabled:e.disabled,selectedText:e.selectedOptions[0]?.textContent};});
    add('Empty district label visible and focused within viewport',geom.selectedText.trim()===labels[lang]&&geom.focus&&!geom.disabled&&geom.left>=0&&geom.right<=width+1&&geom.top>=0&&geom.bottom<=950&&geom.document<=width+1,{geometry:geom,integration:'SIMULATED unsaved',url:p.url()},lang,width,capture);
   }
   const after=await state(p);states.push({lang,before,after});
   add('Unsaved placeholder checks preserve candidate and live',JSON.stringify(before)===JSON.stringify(after),{before,after,integration:'SIMULATED unsaved; non-GET blocked'},lang,1440);
  }finally{await c.close();}
 }
 return {rows,states,consoleErrors,networkErrors,blocked};
}catch(e){return{rows,error:String(e),consoleErrors,networkErrors,blocked};}
}
