async original=>{const F={
  "actors": {
    "owner": {
      "id": 1,
      "username": "qa01r_owner",
      "email": "owner01r@example.invalid"
    },
    "staff": {
      "id": 2,
      "username": "qa01r_staff",
      "email": "staff01r@example.invalid"
    },
    "admin": {
      "id": 3,
      "username": "qa01r_admin",
      "email": "admin01r@example.invalid"
    },
    "outsider": {
      "id": 4,
      "username": "qa01r_outsider",
      "email": "outsider01r@example.invalid"
    },
    "employee": {
      "id": 5,
      "username": "qa01r_employee",
      "email": "employee01r@example.invalid"
    },
    "specialist": {
      "id": 6,
      "username": "qa01r_specialist",
      "email": "specialist01r@example.invalid"
    }
  },
  "ready_place": 1,
  "settings": 1,
  "synthetic_only": true,
  "transition_entities_seeded": false
},B='http://localhost:8841',ROOT='C:/kidsmap/docs/qa/module01-recheck-2026-10-11-r1',rows=[],consoleErrors=[],networkErrors=[];
const br=original.context().browser();
function add(scenario,ok,detail={},role='guest',lang='ru',width=1440,url='',shot=''){const d={...detail};if('status' in d){d.responseStatus=d.status;delete d.status;}rows.push({...d,scenario,status:ok===null?'NOT RUN':ok?'PASS':'FAIL',role,lang,width,url,shot});}
function prefix(lang){return lang==='az'?'':('/'+lang);}
async function context(role='guest',lang='ru',width=1440){
 const c=await br.newContext({viewport:{width,height:950},userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());
 await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);const p=await c.newPage();p.on('pageerror',e=>consoleErrors.push({role,lang,width,error:String(e)}));p.on('response',r=>{if(r.status()>=400)networkErrors.push({role,lang,width,url:r.url().split('?')[0],status:r.status()});});p.setDefaultTimeout(10000);p.setDefaultNavigationTimeout(25000);p.on('dialog',async d=>{await d.accept();});
 if(role!=='guest'){await p.goto(B+'/ru/auth/login/');await p.locator('input[name=username]').fill(F.actors[role].email);await p.locator('input[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);}
 return{c,p};
}
async function shot(p,name){const file='screenshots/'+name+'.png';await p.screenshot({path:ROOT+'/'+file,fullPage:true,animations:'disabled'});return file;}
async function visit(p,path){const r=await p.goto(B+path);await p.waitForTimeout(120);return r?.status()??null;}
async function geometry(p){return p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflow:[...document.querySelectorAll('h1,h2,h3,p,label,button,input,select,textarea,.km-header-inner,.footer-inner')].map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.trim().slice(0,70),r:e.getBoundingClientRect()})).filter(x=>x.r.width&&x.r.left>=0&&x.r.right>innerWidth+2).slice(0,10).map(x=>({...x,r:{left:x.r.left,right:x.r.right,width:x.r.width}}))}));}
async function head(p){return p.evaluate(()=>({title:document.title,h1:[...document.querySelectorAll('h1')].map(e=>e.textContent.trim()),description:document.querySelector('meta[name=description]')?.content,ogTitle:document.querySelector('meta[property="og:title"]')?.content,ogDescription:document.querySelector('meta[property="og:description"]')?.content,ogImage:document.querySelector('meta[property="og:image"]')?.content,twTitle:document.querySelector('meta[name="twitter:title"]')?.content,canonical:document.querySelector('link[rel=canonical]')?.href,robots:document.querySelector('meta[name=robots]')?.content,alternates:[...document.querySelectorAll('link[hreflang]')].map(e=>({lang:e.hreflang,href:e.href})),jsonld:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>{try{return JSON.parse(e.textContent)}catch{return {parseError:true}}}),xss:window.__QA01R_XSS__||0}));}

const URLS={
  "ru": {
    "places": {
      "2": "/ru/place/2-qa-place-qa01r-az/",
      "1": "/ru/place/1-vymyshlennoe-qa01r-gotovoe-mesto/"
    }
  },
  "az": {
    "places": {
      "2": "/place/2-qa-place-qa01r-az/",
      "1": "/place/1-uydurma-qa01r-hazir/"
    }
  },
  "en": {
    "places": {
      "2": "/en/place/2-qa-place-qa01r-az/",
      "1": "/en/place/1-fictional-qa01r-ready-connection/"
    }
  }
},owner=await context('owner'),guest=await context(),admin=await context('admin');async function nav(p,l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}async function save(p,value){await p.waitForTimeout(1500);const response=p.waitForResponse(r=>r.url().includes('/save-photos/')&&r.request().method()==='POST'),navigation=p.waitForNavigation({waitUntil:'domcontentloaded'}).catch(()=>null);await p.locator('[name=form_action][value='+value+']').click({noWaitAfter:true});const r=await response;if(r.status()===200)await navigation;return{http:r.status(),body:r.status()===200?{}:await r.json()};}const evidence={};let phase='draft';try{let p=guest.p;await visit(p,URLS.az.places['2']);evidence.beforeTitle=await p.locator('h1').first().innerText();p=owner.p;await visit(p,'/ru/account/places/2/edit/');await p.locator('[name=name_az]').fill('Uydurma QA01R final approved place');await p.locator('[name=address]').fill('QA01R fictional mixed address 18');await p.locator('[data-tariff-key=price]').first().fill('18');let r=await save(p,'save_draft');add('mixed-price-identity-native-draft-save',r.http===200,r,'owner');await p.reload();evidence.draft={name:await p.locator('[name=name_az]').inputValue(),address:await p.locator('[name=address]').inputValue(),price:await p.locator('[data-tariff-key=price]').first().inputValue()};add('mixed-price-identity-draft-reload',evidence.draft.name==='Uydurma QA01R final approved place'&&Number(evidence.draft.price)===18,evidence.draft,'owner','ru',1440,p.url(),await shot(p,'mixed-price-draft-1440'));await visit(guest.p,URLS.az.places['2']);evidence.liveBeforeReview=await guest.p.locator('main').first().innerText();add('mixed-identity-live-remains-before-review',await guest.p.locator('h1').first().innerText()===evidence.beforeTitle&&!evidence.liveBeforeReview.includes('mixed address 18'),{},'guest');r=await save(p,'save_and_publish');add('mixed-candidate-submitted',r.http===200,r,'owner');phase='approve';p=admin.p;await visit(p,'/admin/volunteer/review/2/');add('mixed-candidate-has-approve-control-no-self-conflict',await p.locator('[name=action][value=approve]').count()===1&&await p.locator('.alert-warning').count()===0,{historical_id:'PLACE-QA-03'},'admin','ru',1440,p.url(),await shot(p,'mixed-price-review-1440'));await nav(p,p.locator('[name=action][value=approve]'));await visit(guest.p,URLS.az.places['2']);evidence.liveAfterReview=await guest.p.locator('main').first().innerText();add('mixed-candidate-approved-public-readback',await guest.p.locator('h1').first().innerText()==='Uydurma QA01R final approved place'&&evidence.liveAfterReview.includes('mixed address 18'),{historical_id:'PLACE-QA-03'},'guest','az',1440,guest.p.url(),await shot(guest.p,'mixed-price-public-1440'));return{rows,evidence};}catch(e){return{rows,evidence,phase,error:String(e),ownerUrl:owner.p.url(),adminUrl:admin.p.url()};}finally{await owner.c.close();await guest.c.close();await admin.c.close();}}
