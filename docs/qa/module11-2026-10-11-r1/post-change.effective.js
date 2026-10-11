async original=>{
 const F={
  "actors": {
    "owner": {
      "id": 1,
      "username": "qa11_owner",
      "email": "owner11@example.invalid"
    },
    "staff": {
      "id": 2,
      "username": "qa11_staff",
      "email": "staff11@example.invalid"
    },
    "admin": {
      "id": 3,
      "username": "qa11_admin",
      "email": "admin11@example.invalid"
    },
    "outsider": {
      "id": 4,
      "username": "qa11_outsider",
      "email": "outsider11@example.invalid"
    }
  },
  "places": {
    "live": 1,
    "draft": 2,
    "inactive": 3,
    "archived": 4,
    "deleted": 5
  },
  "specialist": 1,
  "event": 1,
  "organization": 1,
  "organization_public_id": "7b78e253-9a64-4772-a308-7e59ae9a390b",
  "urls": {
    "ru": {
      "place": "/ru/place/1-vymyshlennoe-qa11-live/",
      "specialist": "/ru/specialists/fictional-qa11-specialist/",
      "event": "/ru/event/1-uydurma-qa11-tedbir/",
      "organization": "/ru/organizations/7b78e253-9a64-4772-a308-7e59ae9a390b/",
      "activity": "/ru/activities/1/",
      "program": "/ru/account/organizations/1/programs/1/",
      "landing": "/ru/catalog/qa11-strong/",
      "extras": {
        "pending": "/ru/place/6-vymyshlennoe-qa11-pending/",
        "rejected": "/ru/place/7-vymyshlennoe-qa11-rejected/",
        "fallback": "/ru/place/8-vymyshlennoe-qa11-fallback/",
        "long": "/ru/place/9-vymyshlennoe-qa11-long-dlinnyitekst-dlinnyitekst-dlinnyiteks/",
        "escaping": "/ru/place/10-vymyshlennoe-qa11-escaping-scriptscriptwindow__qa11_xss__1sc/"
      }
    },
    "az": {
      "place": "/place/1-uydurma-qa11-live/",
      "specialist": "/specialists/fictional-qa11-specialist/",
      "event": "/event/1-uydurma-qa11-tedbir/",
      "organization": "/organizations/7b78e253-9a64-4772-a308-7e59ae9a390b/",
      "activity": "/activities/1/",
      "program": "/account/organizations/1/programs/1/",
      "landing": "/catalog/qa11-strong/",
      "extras": {
        "pending": "/place/6-uydurma-qa11-pending/",
        "rejected": "/place/7-uydurma-qa11-rejected/",
        "fallback": "/place/8-uydurma-qa11-fallback/",
        "long": "/place/9-uydurma-qa11-long-uzunmetn-uzunmetn-uzunmetn-uzunmetn-uzunme/",
        "escaping": "/place/10-uydurma-qa11-escaping-scriptscriptwindow__qa11_xss__1script/"
      }
    },
    "en": {
      "place": "/en/place/1-fictional-qa11-live/",
      "specialist": "/en/specialists/fictional-qa11-specialist/",
      "event": "/en/event/1-uydurma-qa11-tedbir/",
      "organization": "/en/organizations/7b78e253-9a64-4772-a308-7e59ae9a390b/",
      "activity": "/en/activities/1/",
      "program": "/en/account/organizations/1/programs/1/",
      "landing": "/en/catalog/qa11-strong/",
      "extras": {
        "pending": "/en/place/6-fictional-qa11-pending/",
        "rejected": "/en/place/7-fictional-qa11-rejected/",
        "fallback": "/en/place/8-uydurma-qa11-fallback/",
        "long": "/en/place/9-fictional-qa11-long-longtext-longtext-longtext-longtext-long/",
        "escaping": "/en/place/10-fictional-qa11-escaping-scriptscriptwindow__qa11_xss__1scrip/"
      }
    }
  },
  "settings": 1,
  "synthetic_only": true,
  "program": 1,
  "activity": 1,
  "extra_places": {
    "pending": 6,
    "rejected": 7,
    "fallback": 8,
    "long": 9,
    "escaping": 10
  }
},B='http://localhost:8827',ROOT='C:/kidsmap/docs/qa/module11-2026-10-11-r1',rows=[];
const br=original.context().browser();
function add(scenario,ok,detail={},role='guest',lang='ru',width=1440,url='',shot=''){const d={...detail};if('status' in d){d.responseStatus=d.status;delete d.status;}rows.push({...d,scenario,status:ok===null?'NOT RUN':ok?'PASS':'FAIL',role,lang,width,url,shot});}
function prefix(lang){return lang==='az'?'':('/'+lang);}
async function context(role='guest',lang='ru',width=1440){
 const c=await br.newContext({viewport:{width,height:950}});await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());
 await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);const p=await c.newPage();p.setDefaultTimeout(10000);p.setDefaultNavigationTimeout(25000);p.on('dialog',async d=>{await d.accept();});
 if(role!=='guest'){await p.goto(B+'/ru/auth/login/');await p.locator('input[name=username]').fill(F.actors[role].email);await p.locator('input[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForTimeout(100);await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);}
 return{c,p};
}
async function shot(p,name){const file='screenshots/'+name+'.png';await p.screenshot({path:ROOT+'/'+file,fullPage:true,animations:'disabled'});return file;}
async function visit(p,path){const r=await p.goto(B+path);await p.waitForTimeout(120);return r?.status()??null;}
async function geometry(p){return p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflow:[...document.querySelectorAll('h1,h2,h3,p,label,button,input,select,textarea,.km-header-inner,.footer-inner')].map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.trim().slice(0,70),r:e.getBoundingClientRect()})).filter(x=>x.r.width&&x.r.left>=0&&x.r.right>innerWidth+2).slice(0,10).map(x=>({...x,r:{left:x.r.left,right:x.r.right,width:x.r.width}}))}));}
async function head(p){return p.evaluate(()=>({title:document.title,h1:[...document.querySelectorAll('h1')].map(e=>e.textContent.trim()),description:document.querySelector('meta[name=description]')?.content,ogTitle:document.querySelector('meta[property="og:title"]')?.content,ogDescription:document.querySelector('meta[property="og:description"]')?.content,ogImage:document.querySelector('meta[property="og:image"]')?.content,twTitle:document.querySelector('meta[name="twitter:title"]')?.content,canonical:document.querySelector('link[rel=canonical]')?.href,robots:document.querySelector('meta[name=robots]')?.content,alternates:[...document.querySelectorAll('link[hreflang]')].map(e=>({lang:e.hreflang,href:e.href})),jsonld:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>{try{return JSON.parse(e.textContent)}catch{return {parseError:true}}}),xss:window.__QA11_XSS__||0}));}

 const samples=[];
 for(const lang of ['ru','az','en']){const {c,p}=await context('guest',lang);for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});for(const kind of ['place','organization','activity','specialist','event']){const url=kind==='specialist'?prefix(lang)+'/specialists/fictional-qa11-specialist-ui-renamed/':F.urls[lang][kind],s=await visit(p,url),h=await head(p),geom=await geometry(p),images=await p.locator('main img').evaluateAll(es=>es.map(e=>({src:e.src,alt:e.alt,loaded:e.complete&&e.naturalWidth>0})));const ss=await shot(p,'post-change-'+kind+'-'+lang+'-'+width);add('post-change-'+kind+'-entity-canonical',s===200&&h.canonical===B+url,{responseStatus:s,head:h,images},'guest',lang,width,p.url(),ss);add('post-change-'+kind+'-no-overflow',geom.document<=width+2,{geometry:geom},'guest',lang,width,p.url(),ss);if(width===1440)samples.push({kind,lang,url,head:h,images});if(kind==='event')add('event-social-image-entity-photo',images.some(x=>x.src===h.ogImage&&x.src.includes('/media/')),{actual:h.ogImage,visibleImages:images},'guest',lang,width,p.url(),ss);}}
 // Local image loading and error states, explicitly simulated transport.
 for(const width of [360,1440]){await p.setViewportSize({width,height:950});await p.route('**/media/places/qa11.png',async r=>{await new Promise(resolve=>setTimeout(resolve,1400));await r.continue();});await p.goto(B+F.urls[lang].place,{waitUntil:'domcontentloaded'});add('SIMULATED-image-loading-head-retained',(await head(p)).canonical===B+F.urls[lang].place,{classification:'SIMULATED 1400ms local image delay'},'guest',lang,width,p.url(),await shot(p,'loading-image-'+lang+'-'+width));await p.waitForLoadState('load');await p.unroute('**/media/places/qa11.png');await p.route('**/media/places/qa11.png',r=>r.fulfill({status:503,contentType:'text/plain',body:'Fictional QA11 image unavailable'}));await visit(p,F.urls[lang].place);add('SIMULATED-image-error-head-retained',(await head(p)).canonical===B+F.urls[lang].place,{classification:'SIMULATED local image503; live integration NOT RUN'},'guest',lang,width,p.url(),await shot(p,'error-image-'+lang+'-'+width));await p.unroute('**/media/places/qa11.png');}
 await c.close();}return {rows,samples};
}
