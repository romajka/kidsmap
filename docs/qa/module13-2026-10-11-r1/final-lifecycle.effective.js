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
},B='http://localhost:8831',ROOT='C:/kidsmap/docs/qa/module13-2026-10-11-r1',rows=[];
const br=original.context().browser();
function add(scenario,ok,detail={},role='guest',lang='ru',width=1440,url='',shot=''){const d={...detail};if('status' in d){d.responseStatus=d.status;delete d.status;}rows.push({...d,scenario,status:ok===null?'NOT RUN':ok?'PASS':'FAIL',role,lang,width,url,shot});}
function prefix(lang){return lang==='az'?'':('/'+lang);}
async function context(role='guest',lang='ru',width=1440){
 const c=await br.newContext({viewport:{width,height:950},userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());
 await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);const p=await c.newPage();p.setDefaultTimeout(10000);p.setDefaultNavigationTimeout(25000);p.on('dialog',async d=>{await d.accept();});
 if(role!=='guest'){await p.goto(B+'/ru/auth/login/');await p.locator('input[name=username]').fill(F.actors[role].email);await p.locator('input[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);}
 return{c,p};
}
async function shot(p,name){const file='screenshots/'+name+'.png';await p.screenshot({path:ROOT+'/'+file,fullPage:true,animations:'disabled'});return file;}
async function visit(p,path){const r=await p.goto(B+path);await p.waitForTimeout(120);return r?.status()??null;}
async function geometry(p){return p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflow:[...document.querySelectorAll('h1,h2,h3,p,label,button,input,select,textarea,.km-header-inner,.footer-inner')].map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.trim().slice(0,70),r:e.getBoundingClientRect()})).filter(x=>x.r.width&&x.r.left>=0&&x.r.right>innerWidth+2).slice(0,10).map(x=>({...x,r:{left:x.r.left,right:x.r.right,width:x.r.width}}))}));}
async function head(p){return p.evaluate(()=>({title:document.title,h1:[...document.querySelectorAll('h1')].map(e=>e.textContent.trim()),description:document.querySelector('meta[name=description]')?.content,ogTitle:document.querySelector('meta[property="og:title"]')?.content,ogDescription:document.querySelector('meta[property="og:description"]')?.content,ogImage:document.querySelector('meta[property="og:image"]')?.content,twTitle:document.querySelector('meta[name="twitter:title"]')?.content,canonical:document.querySelector('link[rel=canonical]')?.href,robots:document.querySelector('meta[name=robots]')?.content,alternates:[...document.querySelectorAll('link[hreflang]')].map(e=>({lang:e.hreflang,href:e.href})),jsonld:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>{try{return JSON.parse(e.textContent)}catch{return {parseError:true}}}),xss:window.__QA13_XSS__||0}));}

const owner=await context('owner'),employee=await context('employee'),person=await context('specialist'),guest=await context(),URLS={
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
};async function nav(p,l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}let phase='detach';const evidence={};try{let p=owner.p;await visit(p,'/ru/account/organizations/1/branches/2/detach-preview/');evidence.preview=await p.locator('#organization-connection-main').innerText();await shot(p,'detach-preview-1440');await p.locator('[name=consent]').check();await nav(p,p.locator('button[value=confirm]'));add('native-branch-detach',(await p.locator('#organization-connection-main').innerText()).includes('Отсоединено'),{},'owner','ru',1440,p.url(),await shot(p,'detach-result-1440'));await p.setViewportSize({width:390,height:950});await shot(p,'detach-result-390');const denied=await visit(employee.p,'/ru/account/places/2/edit/');add('network-employee-access-revoked-by-detach',denied===404,{http:denied},'employee');await visit(p,'/ru/account/places/2/edit/?fresh=1');evidence.tree=JSON.parse(await p.locator('[name=nested_pricing]').inputValue());const a=evidence.tree.activities[0];add('detached-program-snapshot-groups-prices-retained',a.program_id===null&&a.groups.length===2&&a.groups.map(x=>Number(x.pricing_plans[0].price)).join(',')==='20,80',{tree:evidence.tree},'owner');await visit(guest.p,URLS.az.activities['1']);add('detached-activity-public-approved-program-text-preserved',(await guest.p.locator('main').first().innerText()).includes('candidate curriculum'),{},'guest');
phase='cooperation';p=owner.p;await visit(p,'/ru/account/organizations/1/specialists/');await nav(p,p.locator('[name=action][value=cancel]').first());await visit(person.p,'/ru/account/specialists/1/invitations/');add('cooperation-native-cancellation-person-visible',(await person.p.locator('main').first().innerText()).includes('Участие отменено'),{},'specialist','ru',1440,person.p.url(),await shot(person.p,'cooperation-cancelled-1440'));const noDocs=await visit(p,'/ru/account/specialists/1/certificates/');add('cooperation-cancel-no-private-rights',noDocs===404,{http:noDocs},'owner');
phase='event cancel';p=owner.p;await visit(p,'/ru/account/places/events/1/manage/');await p.locator('[name=reason]').fill('QA13 fictional final cancellation');await nav(p,p.locator('button[formaction$="/cancel/"]'));add('event-native-cancel-no-repeat-action',await p.locator('button[formaction$="/cancel/"]').isDisabled(),{},'owner');const code=await visit(guest.p,URLS.ru.events['1']);add('cancelled-old-card-honest-state',code===200&&(await guest.p.locator('main').first().innerText()).includes('Отменено'),{http:code},'guest','ru',1440,guest.p.url(),await shot(guest.p,'event-cancelled-1440'));await guest.p.setViewportSize({width:390,height:950});await shot(guest.p,'event-cancelled-390');await visit(guest.p,'/ru/events/');add('cancelled-event-removed-from-upcoming',await guest.p.locator('a[href*="/event/1-"]').count()===0,{},'guest');return{rows,evidence};}catch(e){return{rows,evidence,phase,error:String(e),ownerUrl:owner.p.url(),employeeUrl:employee.p.url()};}finally{for(const a of[owner,employee,person,guest])await a.c.close();}}
