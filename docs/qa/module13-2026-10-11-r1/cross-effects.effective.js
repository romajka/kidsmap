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

const URLS={
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
},owner=await context('owner'),guest=await context(),admin=await context('admin');let phase='program conflict';async function nav(p,l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}const evidence={};try{
let p=owner.p;await visit(p,'/ru/account/organizations/1/programs/1/');const second=await owner.c.newPage();await visit(second,'/ru/account/organizations/1/programs/1/');await p.locator('[name=name_az]').fill('Uydurma QA13 candidate curriculum');if(await p.locator('[name=impact_confirmed]').count())await p.locator('[name=impact_confirmed]').check();await nav(p,p.locator('button[name=submit]'));await second.locator('[name=description_az]').fill('QA13 stale second tab retained input');if(await second.locator('[name=impact_confirmed]').count())await second.locator('[name=impact_confirmed]').check();const wr=second.waitForResponse(r=>r.url().endsWith('/save/')&&r.request().method()==='POST');await second.locator('button[name=submit]').click({noWaitAfter:true});const conflict=await wr;await second.waitForLoadState('domcontentloaded');add('program-stale-second-tab-conflict-input-retained',conflict.status()===409&&await second.locator('[name=description_az]').inputValue()==='QA13 stale second tab retained input',{http:conflict.status()},'owner','ru',390,second.url(),await shot(second,'program-conflict-1440'));await second.setViewportSize({width:390,height:950});await shot(second,'program-conflict-390');await second.close();await visit(guest.p,URLS.az.activities['1']);add('program-candidate-not-live-before-review',!(await guest.p.locator('main').first().innerText()).includes('candidate curriculum'),{},'guest');p=admin.p;await visit(p,'/admin/catalog/program/1/change/');await nav(p,p.locator('button[value=approve]'));await guest.p.reload();add('approved-program-propagates-to-activity',(await guest.p.locator('main').first().innerText()).includes('candidate curriculum'),{},'guest');
phase='staff invitation';p=owner.p;await visit(p,'/ru/account/organizations/1/');const form=p.locator('[data-team-form]');await form.locator('[name=email]').fill('employee13@example.invalid');await form.locator('[name=role]').selectOption('EDITOR');await form.locator('[name=scope]').selectOption('all_network');const ir=p.waitForResponse(r=>r.url().includes('/team/organization/1/invite/')&&r.request().method()==='POST');await form.locator('button[type=submit]').click();const invitation=await ir;add('organization-employee-native-invitation',invitation.status()===200,{http:invitation.status(),body:await invitation.json()},'owner');const employee=await context('employee');await visit(employee.p,'/ru/account/notifications/');evidence.notificationForms=await employee.p.locator('form').evaluateAll(es=>es.map(e=>({action:e.getAttribute('action'),text:e.innerText.slice(0,180)})));const accept=employee.p.locator('form[action*="/accept/"] button');if(await accept.count()){await nav(employee.p,accept.first());add('employee-native-invitation-accepted',true,{},'employee');const ed=await visit(employee.p,'/ru/account/places/2/edit/');add('network-employee-branch-edit-access',ed===200&&await employee.p.locator('[data-pc-offerings]').count()===1,{http:ed},'employee');}else add('employee-native-invitation-accepted',null,{forms:evidence.notificationForms},'employee');await employee.c.close();await p.reload();const team=p.locator('#org-team');const controls=await team.locator('button,a,input').evaluateAll(es=>es.map(e=>({tag:e.tagName,name:e.name,text:e.innerText?.slice(0,60)})));add('network-employee-revoke-control-available',controls.some(x=>/отозвать|удалить|revoke/i.test(x.text||'')),{controls,historical_ids:['ORG-QA-02','ACCESS-QA-03']},'owner','ru',1440,p.url(),await shot(p,'org-team-controls-1440'));add('network-employee-native-revocation',null,{reason:'No revoke control; no direct API substituted for requested UI transition'},'owner');
return{rows,evidence};}catch(e){return{rows,evidence,phase,error:String(e),url:owner.p.url()};}finally{await owner.c.close();await guest.c.close();await admin.c.close();}}
