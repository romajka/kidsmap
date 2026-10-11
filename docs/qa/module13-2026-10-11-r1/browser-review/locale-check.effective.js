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

for(const lang of ['az','en'])for(const width of [360,390,768,1024,1280,1440]){const t=await context('admin',lang,width);try{const http=await visit(t.p,prefix(lang)+'/admin/catalog/place/2/change/'),body=await t.p.locator('body').innerText(),russian=body.includes('Карта пока не активна')&&body.includes('Геокодирование не настроено'),g=await geometry(t.p),s=await shot(t.p,['locale',lang,width,'admin-map-notice'].join('-'),false);add('admin-map-notice-language',http===200&&g.htmlLang===lang&&!russian,{existing_id:'PLACE-QA-06',shared_dependency:'SITE-QA-07',classification:'environment/generated assets; fresh runtime issue with current .mo',actual_russian_notice:russian,htmlLang:g.htmlLang,source:'src/catalog/domain_admin/place.py:2535; correct AZ/EN .po keys exist',expected_language:lang},'admin',lang,width,t.p.url(),s);}finally{await t.c.close();}}
for(const width of [360,390,768,1024,1280,1440]){const t=await context('owner','ru',width);try{const http=await visit(t.p,'/ru/account/places/2/edit/?fresh=1'),placeholder=await t.p.locator('#id_district option').first().innerText(),g=await geometry(t.p),input=t.p.locator('#id_district');await input.scrollIntoViewIfNeeded();const s=await shot(t.p,['locale','ru',width,'owner-district-placeholder'].join('-'),false);add('owner-district-placeholder-language',http===200&&g.htmlLang==='ru'&&!placeholder.includes('Rayon seçin'),{existing_id:'UNKNOWN: parent reconciliation assigns canonical finding',classification:'missing active RU translation; default AZ fallback, no storage-language inference',actual:placeholder,htmlLang:g.htmlLang,source:'src/catalog/services/locations.py:561; RU .po entry obsolete at18354',expected_language:'ru'},'owner','ru',width,t.p.url(),s);}finally{await t.c.close();}}
return{rows,screens,attestation:await(await original.request.get(B+'/qa/version/')).json()};}
