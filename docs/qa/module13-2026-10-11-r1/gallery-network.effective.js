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

const owner=await context('owner'),admin=await context('admin'),guest=await context(),author=await context('outsider'),URLS={
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
};async function nav(p,l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}async function save(p,value){await p.waitForTimeout(1500);const r=p.waitForResponse(r=>r.url().includes('/save-photos/')&&r.request().method()==='POST'),n=p.waitForNavigation({waitUntil:'domcontentloaded'}).catch(()=>null);await p.locator('[name=form_action][value='+value+']').click({noWaitAfter:true});const x=await r;if(x.status()===200)await n;return x.status();}let phase='gallery';const evidence={};try{let p=owner.p;await visit(p,'/ru/account/places/2/edit/');await p.locator('[name=gallery_images]').setInputFiles(['C:/kidsmap/.tmp/module13-20261011-r1/assets/fixture.png','C:/kidsmap/.tmp/module13-20261011-r1/assets/replacement.png']);await p.waitForFunction(()=>document.querySelectorAll('[data-photo-items=gallery] [data-state=ready]').length===2);let r=await save(p,'save_draft');await p.reload();add('gallery-two-photos-draft-reload',r===200&&await p.locator('[data-photo-items=gallery] img').count()===2,{http:r},'owner','ru',1440,p.url(),await shot(p,'gallery-draft-1440'));evidence.galleryActions=await p.locator('[data-photo-items=gallery] [data-photo-action]').evaluateAll(es=>es.map(e=>({action:e.dataset.photoAction,text:e.innerText})));r=await save(p,'save_and_publish');add('gallery-candidate-submitted',r===200,{http:r},'owner');p=admin.p;await visit(p,'/admin/volunteer/review/2/');await nav(p,p.locator('button[value=approve]'));p=guest.p;await visit(p,URLS.ru.places['2']);const imgs=await p.locator('main img').evaluateAll(es=>es.filter(e=>e.src.includes('/media/places/')).map(e=>({src:e.getAttribute('src'),loaded:e.complete&&e.naturalWidth>0})));add('approved-gallery-public-loaded',imgs.length>=3&&imgs.every(x=>x.loaded),{images:imgs},'guest','ru',390,p.url(),await shot(p,'gallery-public-1440'));phase='network';p=owner.p;await visit(p,'/ru/account/places/2/edit/');const old=await p.locator('[name=name_az]').inputValue();await p.route('**/save-draft/**',r=>r.abort('failed'));await p.route('**/save-photos/**',r=>r.abort('failed'));await p.locator('[name=name_az]').fill('QA13 UNSENT network candidate');await p.waitForTimeout(2000);add('simulated-save-network-failure-keeps-input',await p.locator('[name=name_az]').inputValue()==='QA13 UNSENT network candidate',{classification:'SIMULATED transport',saveStatus:await p.locator('[data-pc-save-status]').innerText()},'owner','ru',1440,p.url(),await shot(p,'owner-network-error-1440'));await p.setViewportSize({width:390,height:950});await shot(p,'owner-network-error-390');await p.unroute('**/save-draft/**');await p.unroute('**/save-photos/**');await p.reload();add('failed-network-write-not-persisted',await p.locator('[name=name_az]').inputValue()===old,{old,reloaded:await p.locator('[name=name_az]').inputValue()},'owner');phase='rating';p=author.p;await visit(p,'/ru/reviews/place/target/2/');add('fresh-confirm-rating-form-missing-selected-value',await p.locator('#review-rating').inputValue()==='4',{actual:await p.locator('#review-rating').inputValue(),historical_id:'SOCIAL-QA-01'},'outsider','ru',390,p.url(),await shot(p,'review-rating-empty-1440'));await p.setViewportSize({width:390,height:950});await shot(p,'review-rating-empty-390');return{rows,evidence};}catch(e){return{rows,evidence,phase,error:String(e),ownerUrl:owner.p.url()};}finally{for(const a of[owner,admin,guest,author])await a.c.close();}}
