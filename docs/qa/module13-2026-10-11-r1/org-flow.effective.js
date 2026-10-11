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
 if(role!=='guest'){await p.goto(B+'/ru/auth/login/');await p.locator('input[name=username]').fill(F.actors[role].email);await p.locator('input[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForTimeout(100);await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);}
 return{c,p};
}
async function shot(p,name){const file='screenshots/'+name+'.png';await p.screenshot({path:ROOT+'/'+file,fullPage:true,animations:'disabled'});return file;}
async function visit(p,path){const r=await p.goto(B+path);await p.waitForTimeout(120);return r?.status()??null;}
async function geometry(p){return p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflow:[...document.querySelectorAll('h1,h2,h3,p,label,button,input,select,textarea,.km-header-inner,.footer-inner')].map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.trim().slice(0,70),r:e.getBoundingClientRect()})).filter(x=>x.r.width&&x.r.left>=0&&x.r.right>innerWidth+2).slice(0,10).map(x=>({...x,r:{left:x.r.left,right:x.r.right,width:x.r.width}}))}));}
async function head(p){return p.evaluate(()=>({title:document.title,h1:[...document.querySelectorAll('h1')].map(e=>e.textContent.trim()),description:document.querySelector('meta[name=description]')?.content,ogTitle:document.querySelector('meta[property="og:title"]')?.content,ogDescription:document.querySelector('meta[property="og:description"]')?.content,ogImage:document.querySelector('meta[property="og:image"]')?.content,twTitle:document.querySelector('meta[name="twitter:title"]')?.content,canonical:document.querySelector('link[rel=canonical]')?.href,robots:document.querySelector('meta[name=robots]')?.content,alternates:[...document.querySelectorAll('link[hreflang]')].map(e=>({lang:e.hreflang,href:e.href})),jsonld:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>{try{return JSON.parse(e.textContent)}catch{return {parseError:true}}}),xss:window.__QA13_XSS__||0}));}

const {c,p}=await context('owner');let phase='create';const entities={};
async function field(n){const l=p.locator('[data-org-create-form] [name='+n+']');if(!await l.isVisible()){await l.locator('xpath=ancestor::details').locator('summary').first().click();}return l;}
async function nav(l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}
try{
await visit(p,'/ru/account/organizations/create/');await (await field('name_az')).fill('Uydurma QA13 network');await p.reload();add('organization-partial-reload',await (await field('name_az')).inputValue()==='Uydurma QA13 network',{},'owner');
await (await field('website')).fill('bad-url');await nav(p.locator('[data-org-create-form] button[type=submit]'));add('organization-invalid-url-retains-input',(await p.locator('.org-field-error,[role=alert],.errorlist').allTextContents()).join('').length>0&&await (await field('name_az')).inputValue()==='Uydurma QA13 network',{},'owner');await p.setViewportSize({width:390,height:950});await shot(p,'org-create-error-390');
await (await field('website')).fill('https://example.invalid/qa13');await (await field('name_ru')).fill('Вымышленная QA13 сеть');await (await field('name_en')).fill('Fictional QA13 network');await (await field('phone')).fill('+994000000013');await (await field('description_az')).fill('Uydurma ailə şəbəkəsi. '.repeat(20));await nav(p.locator('[data-org-create-form] button[type=submit]'));entities.organization=Number(p.url().match(/organizations\/(\d+)/)?.[1]);add('organization-created-without-branches',!!entities.organization&&await p.locator('a[href*="/branches/"]').count()===0,{id:entities.organization},'owner');
await p.reload();add('organization-draft-reload',await p.locator('[data-org-edit-form] [name=name_az]').inputValue()==='Uydurma QA13 network',{},'owner');phase='submit';await nav(p.locator('[data-org-edit-form] button[name=submit]'));await shot(p,'org-pending-390');
const admin=await context('admin');await visit(admin.p,'/admin/catalog/organization/'+entities.organization+'/change/');await shot(admin.p,'org-review-1440');await Promise.all([admin.p.waitForNavigation({waitUntil:'domcontentloaded'}),admin.p.locator('button[value=reject]').click({noWaitAfter:true})]).catch(()=>null);entities.adminAfterReject=admin.p.url();entities.adminFields=await admin.p.locator('input,textarea,button').evaluateAll(es=>es.filter(e=>e.type!=='hidden').map(e=>({name:e.name,value:e.value,text:e.innerText?.slice(0,90)})));await admin.c.close();
return{rows,entities,phase};
}catch(e){await shot(p,'org-flow-error');return{rows,entities,phase,error:String(e),url:p.url(),errors:await p.locator('[role=alert],.errorlist').allTextContents()};}finally{await c.close();}
}
