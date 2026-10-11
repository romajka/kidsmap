async original=>{
const F={
  "actors": {
    "owner": {
      "id": 1,
      "username": "qa12_owner",
      "email": "owner12@example.invalid"
    },
    "staff": {
      "id": 2,
      "username": "qa12_staff",
      "email": "staff12@example.invalid"
    },
    "admin": {
      "id": 3,
      "username": "qa12_admin",
      "email": "admin12@example.invalid"
    },
    "outsider": {
      "id": 4,
      "username": "qa12_outsider",
      "email": "outsider12@example.invalid"
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
  "organization_public_id": "949e735a-611f-480a-b81f-38f643bac48f",
  "urls": {
    "ru": {
      "place": "/ru/place/1-vymyshlennoe-qa12-live/",
      "specialist": "/ru/specialists/fictional-qa12-specialist/",
      "event": "/ru/event/1-uydurma-qa12-tedbir/",
      "organization": "/ru/organizations/949e735a-611f-480a-b81f-38f643bac48f/"
    },
    "az": {
      "place": "/place/1-uydurma-qa12-live/",
      "specialist": "/specialists/fictional-qa12-specialist/",
      "event": "/event/1-uydurma-qa12-tedbir/",
      "organization": "/organizations/949e735a-611f-480a-b81f-38f643bac48f/"
    },
    "en": {
      "place": "/en/place/1-fictional-qa12-live/",
      "specialist": "/en/specialists/fictional-qa12-specialist/",
      "event": "/en/event/1-uydurma-qa12-tedbir/",
      "organization": "/en/organizations/949e735a-611f-480a-b81f-38f643bac48f/"
    }
  },
  "settings": 1,
  "synthetic_only": true
},B='http://localhost:8829',ROOT='C:/kidsmap/docs/qa/module12-2026-10-11-r1',rows=[];
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
async function head(p){return p.evaluate(()=>({title:document.title,h1:[...document.querySelectorAll('h1')].map(e=>e.textContent.trim()),description:document.querySelector('meta[name=description]')?.content,ogTitle:document.querySelector('meta[property="og:title"]')?.content,ogDescription:document.querySelector('meta[property="og:description"]')?.content,ogImage:document.querySelector('meta[property="og:image"]')?.content,twTitle:document.querySelector('meta[name="twitter:title"]')?.content,canonical:document.querySelector('link[rel=canonical]')?.href,robots:document.querySelector('meta[name=robots]')?.content,alternates:[...document.querySelectorAll('link[hreflang]')].map(e=>({lang:e.hreflang,href:e.href})),jsonld:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>{try{return JSON.parse(e.textContent)}catch{return {parseError:true}}}),xss:window.__QA12_XSS__||0}));}

const telemetry=[],actions=[];
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440])for(const role of ['guest','owner','admin']){
 const{c,p}=await context(role,lang,width),errors=[],responses=[],external=[];
 p.on('pageerror',e=>errors.push(String(e)));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});p.on('response',r=>{if(new URL(r.url()).hostname==='localhost'&&r.status()>=400)responses.push({status:r.status(),url:r.url()});});p.on('requestfailed',r=>{if(new URL(r.url()).hostname!=='localhost')external.push(new URL(r.url()).hostname);});
 const before=await(await c.request.get(B+'/qa/state/')).json(),url=role==='guest'?F.urls[lang].place:role==='owner'?prefix(lang)+'/account/places/1/analytics/':'/admin/catalog/siteanalytics/?qa_ga=filled';const st=await visit(p,url);await p.waitForTimeout(150);const after=await(await c.request.get(B+'/qa/state/')).json();actions.push({name:'telemetry-'+role+'-'+lang+'-'+width,before,after});const localErrors=errors.filter(x=>!x.includes('ERR_FAILED')&&!x.includes('net::ERR_ABORTED'));add('console-network',st===200&&responses.length===0&&localErrors.length===0,{http:st,localErrors,localErrorResponses:responses,blockedExternal:[...new Set(external)],external:'SIMULATED blocked transport',viewDelta:after.metrics['1'].views-before.metrics['1'].views},role,lang,width,p.url());
 if(role==='guest'&&(width===390||width===1440)){const reveal=p.locator('[data-phone-reveal="1"]').first();if(await reveal.count()){await reveal.click();await p.waitForTimeout(250);const g=await geometry(p),s=await shot(p,'phone-dialog-'+lang+'-'+width);add('phone-dialog-geometry',g.document<=width+1,{geometry:g},role,lang,width,p.url(),s);await p.keyboard.press('Escape');}}
 telemetry.push({role,lang,width,errors,responses,blockedExternal:[...new Set(external)]});await c.close();
}
return{rows,telemetry,actions};
}
