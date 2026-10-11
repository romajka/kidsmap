async original=>{
const F={
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

const owner=await context('owner'),admin=await context('admin'),other=await context('outsider');let phase='confirm';const entities={};async function nav(p,l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}
try{let p=other.p;await visit(p,'/ru/account/places/');entities.pendingForms=await p.locator('form').evaluateAll(es=>es.map(e=>({action:e.getAttribute('action'),text:e.innerText.slice(0,200)})));let cf=p.locator('form[action*="/requests/"][action$="/confirm/"] button');if(!await cf.count()){await visit(p,'/ru/account/organizations/1/requests/1/recovery/');cf=p.locator('form[action$="/confirm/"] button');}if(await cf.count()){await nav(p,cf.first());add('distinct-place-owner-confirm-native',true,{},'outsider');}else add('distinct-place-owner-confirm-native',null,{url:p.url(),forms:entities.pendingForms},'outsider');
phase='program';p=owner.p;await visit(p,'/ru/account/organizations/1/programs/create/');const f=p.locator('form[action$="/programs/create/"]');await f.locator('[name=name_az]').fill('Uydurma QA13 musiqi');await nav(p,f.locator('button[type=submit]'));entities.program=Number(p.url().match(/programs\/(\d+)/)?.[1]);await p.locator('[name=name_ru]').fill('Вымышленная QA13 музыка');await p.locator('[name=name_en]').fill('Fictional QA13 music');await p.locator('[name=description_az]').fill('QA13 shared music curriculum');await p.locator('[name=category]').selectOption('MUS');await nav(p,p.locator('button[name=submit]'));await p.reload();add('program-submit-reload',!!entities.program&&await p.locator('.org-status--candidate').count()===1,{id:entities.program},'owner');p=admin.p;await visit(p,'/admin/catalog/program/'+entities.program+'/change/');await nav(p,p.locator('button[value=approve]'));add('program-native-approved',true,{},'admin');return{rows,entities};}catch(e){return{rows,entities,phase,error:String(e),ownerUrl:owner.p.url(),otherUrl:other.p.url()};}finally{await owner.c.close();await admin.c.close();await other.c.close();}}
