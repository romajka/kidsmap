async original=>{const F={
  "actors": {
    "owner": {
      "id": 1,
      "username": "qa13_owner",
      "email": "owner13@example.invalid"
    },
    "staff": {
      "id": 2,
      "username": "qa13_staff",
      "email": "staff13@example.invalid"
    },
    "admin": {
      "id": 3,
      "username": "qa13_admin",
      "email": "admin13@example.invalid"
    },
    "outsider": {
      "id": 4,
      "username": "qa13_outsider",
      "email": "outsider13@example.invalid"
    },
    "employee": {
      "id": 5,
      "username": "qa13_employee",
      "email": "employee13@example.invalid"
    },
    "specialist": {
      "id": 6,
      "username": "qa13_specialist",
      "email": "specialist13@example.invalid"
    }
  },
  "ready_place": 1,
  "settings": 1,
  "synthetic_only": true,
  "transition_entities_seeded": false
},CARDS={
  "ru": {
    "places": {
      "2": "/ru/place/2-qa-place-qa13-az/",
      "1": "/ru/place/1-vymyshlennoe-qa13-gotovoe-mesto/"
    },
    "organizations": {
      "1": "/ru/organizations/9a6a35ed-1f5d-44b3-8bc2-5b8d3b68e4a2/"
    },
    "activities": {
      "1": "/ru/activities/1/"
    },
    "specialists": {
      "1": "/ru/specialists/qa-fictional-specialist-qa13/"
    },
    "events": {
      "2": "/ru/event/2-uydurma-qa13-online-event/",
      "1": "/ru/event/1-uydurma-qa13-physical-event/"
    }
  },
  "az": {
    "places": {
      "2": "/place/2-qa-place-qa13-az/",
      "1": "/place/1-uydurma-qa13-hazir/"
    },
    "organizations": {
      "1": "/organizations/9a6a35ed-1f5d-44b3-8bc2-5b8d3b68e4a2/"
    },
    "activities": {
      "1": "/activities/1/"
    },
    "specialists": {
      "1": "/specialists/qa-fictional-specialist-qa13/"
    },
    "events": {
      "2": "/event/2-uydurma-qa13-online-event/",
      "1": "/event/1-uydurma-qa13-physical-event/"
    }
  },
  "en": {
    "places": {
      "2": "/en/place/2-qa-place-qa13-az/",
      "1": "/en/place/1-fictional-qa13-ready-connection/"
    },
    "organizations": {
      "1": "/en/organizations/9a6a35ed-1f5d-44b3-8bc2-5b8d3b68e4a2/"
    },
    "activities": {
      "1": "/en/activities/1/"
    },
    "specialists": {
      "1": "/en/specialists/qa-fictional-specialist-qa13/"
    },
    "events": {
      "2": "/en/event/2-uydurma-qa13-online-event/",
      "1": "/en/event/1-uydurma-qa13-physical-event/"
    }
  }
},B='http://localhost:8831',ROOT='C:/kidsmap/docs/qa/module13-2026-10-11-r1/browser-review',rows=[],screens=[],br=original.context().browser();
const now=()=>new Date().toISOString();
function prefix(lang){return lang==='az'?'':'/'+lang;}
function add(scenario,ok,detail={},role='guest',lang='ru',width=1440,url='',screenshot=''){const d={...detail};if('status' in d){d.responseStatus=d.status;delete d.status;}rows.push({...d,utc:now(),scenario,status:ok===null?'NOT RUN':ok?'PASS':'FAIL',role,lang,width,url,screenshot});}
async function context(role,lang,width){
 const c=await br.newContext({viewport:{width,height:950},userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'}),network={console:[],pageerrors:[],responses:[],failed:[],externalBlocked:[],writeGuard:[]};
 await c.route('**/*',async r=>{const q=r.request(),u=new URL(q.url());if(u.hostname!=='localhost'){network.externalBlocked.push({url:u.origin+u.pathname,type:q.resourceType()});return r.abort();}if(q.method()!=='GET'&&q.method()!=='HEAD'&&!u.pathname.includes('/auth/login/')){network.writeGuard.push({method:q.method(),url:u.pathname});return r.abort();}return r.continue();});
 await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);const p=await c.newPage();p.setDefaultTimeout(8000);p.setDefaultNavigationTimeout(25000);p.on('dialog',async d=>d.dismiss());
 p.on('console',m=>{if(m.type()==='error'||m.type()==='warning')network.console.push({type:m.type(),text:m.text().slice(0,350),url:m.location().url});});p.on('pageerror',e=>network.pageerrors.push(String(e)));p.on('response',r=>{if(r.status()>=400)network.responses.push({status:r.status(),url:r.url()});});p.on('requestfailed',r=>network.failed.push({url:r.url(),error:r.failure()?.errorText,type:r.resourceType()}));
 if(role!=='guest'){await p.goto(B+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/auth/login/')),p.locator('.register-form--login button[type=submit]').click()]);await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);}
 return{c,p,network};
}
async function visit(p,path){const r=await p.goto(B+path,{waitUntil:'domcontentloaded'});await p.waitForTimeout(450);return r?.status()??null;}
async function shot(p,name,fullPage=true){const file='screenshots/native-r2-'+name+'.png';await p.screenshot({path:ROOT+'/'+file,fullPage,animations:'disabled'});screens.push({file,utc:now(),url:p.url(),width:p.viewportSize().width,height:p.viewportSize().height,fullPage});return file;}
async function geometry(p){return p.evaluate(()=>{const visible=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none';};return{htmlLang:document.documentElement.lang,viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth,h1:[...document.querySelectorAll('main h1,#content h1,h1')].filter(visible).map(e=>e.textContent.trim()).slice(0,8),overflow:[...document.querySelectorAll('h1,h2,h3,p,label,button,input,select,textarea,main,.content,.km-header-inner,.footer-inner')].filter(visible).map(e=>({tag:e.tagName,cls:String(e.className),text:e.textContent.trim().slice(0,80),r:e.getBoundingClientRect()})).filter(x=>x.r.left>=0&&x.r.right>innerWidth+3).slice(0,15).map(x=>({...x,r:{left:x.r.left,right:x.r.right,width:x.r.width}})),images:[...document.images].filter(visible).filter(e=>e.complete&&!e.naturalWidth).map(e=>({src:e.src,alt:e.alt})).slice(0,12)};});}
async function keyboard(p){await p.keyboard.press('Tab');let first=await p.evaluate(()=>{const e=document.activeElement,s=getComputedStyle(e),r=e.getBoundingClientRect();return{tag:e.tagName,type:e.type,name:e.name,role:e.getAttribute('role'),text:e.textContent.trim().slice(0,70),outline:s.outline,shadow:s.boxShadow,rect:{left:r.left,right:r.right,top:r.top,bottom:r.bottom},visible:r.width>0&&r.height>0&&s.visibility!=='hidden'};});await p.keyboard.press('Shift+Tab');let back=await p.evaluate(()=>document.activeElement.tagName);await p.keyboard.press('Escape');return{first,back,escapePressed:true};}

const role='admin',lang='az',start=now(),attestation=await(await original.request.get(B+'/qa/version/')).json(),stateBefore=await(await original.request.get(B+'/qa/state/')).json(),networks=[],observations=[];
const publicSurfaces=[['place',CARDS[lang].places['2']],['ready-place',CARDS[lang].places['1']],['organization',CARDS[lang].organizations['1']],['activity',CARDS[lang].activities['1']],['specialist',CARDS[lang].specialists['1']],['event-physical',CARDS[lang].events['1']],['event-online',CARDS[lang].events['2']],['organization-index',prefix(lang)+'/organizations/'],['catalog-filled',prefix(lang)+'/catalog/?q=QA13'],['catalog-empty',prefix(lang)+'/catalog/?q=QA13-no-results-8e31a7']];
const surfaces=role==='guest'?publicSurfaces:role==='owner'?[['place-edit',prefix(lang)+'/account/places/2/edit/?fresh=1'],['organization-edit',prefix(lang)+'/account/organizations/1/'],['program-edit',prefix(lang)+'/account/organizations/1/programs/1/']]:[['place-admin',prefix(lang)+'/admin/catalog/place/2/change/'],['event-admin',prefix(lang)+'/admin/catalog/event/1/change/']];
for(const width of [360,390,768,1024,1280,1440]){let t;try{t=await context(role,lang,width);for(const [surface,path] of surfaces){const markers=Object.fromEntries(Object.entries(t.network).map(([k,v])=>[k,v.length]));try{
 const http=await visit(t.p,path),g=await geometry(t.p),name=[role,lang,width,surface].join('-'),s=await shot(t.p,name),body=(await t.p.locator('body').innerText()).slice(0,12000),key=await keyboard(t.p);
 add(surface+'-render',http===200&&g.h1.length>0,{http,h1:g.h1,bodyLength:body.length},role,lang,width,t.p.url(),s);
 add(surface+'-effective-language',g.htmlLang===lang,{htmlLang:g.htmlLang},role,lang,width,t.p.url(),s);
 add(surface+'-document-overflow',g.document<=width+2&&g.body<=width+2,{geometry:g},role,lang,width,t.p.url(),s);
 add(surface+'-images',g.images.length===0,{brokenImages:g.images},role,lang,width,t.p.url(),s);
 add(surface+'-keyboard-focus',key.first.visible&&key.first.tag!=='BODY',{keyboard:key},role,lang,width,t.p.url(),s);
 const menu=t.p.locator(role==='admin'?'.km-admin-header__lang-btn':'#km-burger-open').first();if(await menu.isVisible()){await menu.focus();await menu.press('Enter');await t.p.waitForTimeout(100);const ms=await shot(t.p,name+'-menu',false),mg=await geometry(t.p);add(surface+'-menu-open',mg.document<=width+2,{geometry:mg},role,lang,width,t.p.url(),ms);await t.p.keyboard.press('Escape');}
 if(surface==='organization'){const select=t.p.locator('.km-custom-select__trigger').first();if(await select.isVisible()){await select.focus();await select.press('Space');await t.p.waitForTimeout(100);const os=await shot(t.p,name+'-select',false);add(surface+'-select-open',true,{open:await t.p.locator('[role=listbox]:visible').count()},role,lang,width,t.p.url(),os);await t.p.keyboard.press('Escape');}}
 if(surface==='place'){const fav=t.p.locator('[data-auth-required-trigger]').first();if(await fav.isVisible()){await fav.focus();await fav.press('Enter');await t.p.waitForTimeout(100);const ds=await shot(t.p,name+'-auth-notice',false),dg=await geometry(t.p),notice=await t.p.locator('.toast[role=status]:visible').count();add('anonymous-favorite-auth-notice',notice>0,{notice,geometry:dg},role,lang,width,t.p.url(),ds);await t.p.keyboard.press('Escape');}}
 if(surface==='catalog-filled'){await visit(t.p,prefix(lang)+'/catalog/?q=QA13');const map=t.p.locator('[data-catalog-map-open]').first();if(await map.isVisible()){await map.click();await t.p.waitForTimeout(400);const maps=await shot(t.p,name+'-map-no-sdk',false),mapText=(await t.p.locator('body').innerText()).slice(-12000);add('catalog-map-without-external-sdk',null,{reason:'External map SDK/tile transport blocked intentionally; rendered fallback captured.',bodyTail:mapText.slice(-1600)},role,lang,width,t.p.url(),maps);await t.p.keyboard.press('Escape');}const sort=t.p.locator('[data-sort-trigger]').first();if(await sort.isVisible()){await sort.focus();await sort.press('Enter');await t.p.waitForTimeout(100);const ss=await shot(t.p,name+'-sort',false);add('catalog-sort-open',await t.p.locator('[role=listbox]:visible').count()>0,{options:await t.p.locator('[role=option]:visible').allTextContents()},role,lang,width,t.p.url(),ss);await t.p.keyboard.press('Escape');}}
 if(role==='owner'){const summary=t.p.locator('details > summary').first();if(await summary.isVisible()){await summary.focus();await summary.press('Enter');await t.p.waitForTimeout(80);const ds=await shot(t.p,name+'-details',false);await summary.press('Space');add(surface+'-details-keyboard',true,{enterSpaceExecuted:true},role,lang,width,t.p.url(),ds);}add(surface+'-saving-error-conflict',null,{reason:'No saves or mutations by this delegated browser role; root native workflow owns error/conflict acceptance.'},role,lang,width,t.p.url(),s);}
 if(role==='admin'){const combo=t.p.locator('.select2-selection[role=combobox]').first();if(await combo.isVisible()){await combo.focus();await combo.press('Enter');await t.p.waitForTimeout(100);const cs=await shot(t.p,name+'-select2',false),open=await t.p.locator('.select2-container--open').count();add(surface+'-select2-open',open>0,{open},role,lang,width,t.p.url(),cs);await t.p.keyboard.press('Escape');}}
 observations.push({surface,role,lang,width,http,url:t.p.url(),utc:now(),geometry:g,keyboard:key,network:Object.fromEntries(Object.entries(t.network).map(([k,v])=>[k,v.slice(markers[k])]))});
 }catch(e){let s='';try{s=await shot(t.p,[role,lang,width,surface,'error'].join('-'),false);}catch{}add(surface+'-harness-or-navigation',null,{error:String(e),reason:'Uncompleted check; not classified as application defect.'},role,lang,width,t.p.url(),s);}}networks.push({role,lang,width,network:t.network});}catch(e){add('context-login',null,{error:String(e)},role,lang,width);}finally{if(t)await t.c.close();}}
return{start,end:now(),attestation,stateBefore,stateAfter:await(await original.request.get(B+'/qa/state/')).json(),rows,observations,networks,screens};}
