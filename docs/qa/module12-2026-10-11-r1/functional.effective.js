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

const actions=[];async function state(c){return (await c.request.get(B+'/qa/state/')).json();}
function count(s,id=1,type='place_view'){return s.events.filter(x=>x.subject_id===id&&x.event_type===type).reduce((a,x)=>a+x.total,0);}
async function act(c,p,name,action,expect={},role='guest'){
 const before=await state(c),result=await action(),after=await state(c);
 const delta={raw:count(after)-count(before),views:after.metrics['1'].views-before.metrics['1'].views,unique:after.metrics['1'].unique_visitors-before.metrics['1'].unique_visitors,contacts:after.metrics['1'].contact_actions-before.metrics['1'].contact_actions};
 actions.push({name,role,before,after,delta,result});const ok=Object.entries(expect).every(([k,v])=>delta[k]===v);
 add(name,ok,{delta,expected:expect,result},role,'ru',1440,p.url());return{before,after,delta,result};
}
const contexts={};for(const role of ['guest','outsider','owner','staff']){const q=await context(role);contexts[role]=q;await act(q.c,q.p,'card-first-'+role,()=>visit(q.p,F.urls.ru.place),{raw:1,views:role==='staff'?0:1},role);}
const{c,p}=contexts.guest;
await act(c,p,'reload',async()=>{const r=await p.reload();return r.status();},{raw:1,views:1,unique:0});
await act(c,p,'back',async()=>{await p.goto(B+'/ru/about/');const r=await p.goBack();return r?.status()??null;},{raw:1,views:1,unique:0});
await act(c,p,'forward',async()=>{await p.goForward();const r=await p.goBack();return r?.status()??null;},{raw:1,views:1,unique:0});
await act(c,p,'two-tabs',async()=>{const tab=await c.newPage();const s=await visit(tab,F.urls.ru.place);await tab.close();return s;},{raw:1,views:1,unique:0});
for(const lang of ['az','en','ru'])await act(c,p,'language-'+lang,()=>visit(p,F.urls[lang].place),{raw:1,views:1,unique:0});
await act(c,p,'query-redirect',()=>visit(p,F.urls.ru.place+'?unwanted=fictional'),{raw:1,views:1,unique:0});
const endpoint='/ru/events/track/';async function event(payload,headers={}){return p.evaluate(async({endpoint,payload,headers})=>{const r=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json',...headers},body:typeof payload==='string'?payload:JSON.stringify(payload)});return{status:r.status,body:r.status===500?'server-error':await r.text()};},{endpoint,payload,headers});}
for(const type of ['phone_click','whatsapp_click','website_click','social_click','directions_click']){
 const before=await state(c),result=await event({event_type:type,place_id:1,path:F.urls.ru.place,source:'place-detail'}),after=await state(c);actions.push({name:'endpoint-'+type,before,after,result});add('endpoint-'+type,result.status===200&&count(after,1,type)-count(before,1,type)===1,{result,delta:count(after,1,type)-count(before,1,type)});
}
const repeated=await act(c,p,'repeat-click-request',()=>event({event_type:'phone_click',place_id:1,source:'phone-reveal'}),{contacts:1});
const cases=[['invalid-json','{',400],['array',[],400],['unsupported',{event_type:'unknown',place_id:1},400],['missing-id',{event_type:'phone_click'},400],['inactive-id',{event_type:'phone_click',place_id:F.places.inactive},400],['deleted-id',{event_type:'phone_click',place_id:F.places.deleted},400],['unknown-id',{event_type:'phone_click',place_id:999999},400],['private-draft-id',{event_type:'phone_click',place_id:F.places.draft},400],['private-archived-id',{event_type:'phone_click',place_id:F.places.archived},400]];
for(const[name,payload,status]of cases){const before=await state(c),result=await event(payload),after=await state(c);actions.push({name,before,after,result});add(name,result.status===status&&after.event_count===before.event_count,{result,expectedStatus:status,eventDelta:after.event_count-before.event_count});}
const beforeFailure=await state(c),failure=await event({event_type:'phone_click',place_id:1},{'X-QA-Failure':'event-store'}),afterFailure=await state(c);actions.push({name:'backend-failure',before:beforeFailure,after:afterFailure,result:failure});add('backend-failure',failure.status===500&&beforeFailure.event_count===afterFailure.event_count,{result:failure,SIMULATED:true});
const networkBefore=await state(c);await p.route('**/events/track/',r=>r.abort('failed'));const network=await event({event_type:'phone_click',place_id:1}).catch(e=>String(e).split('\n')[0]);await p.unroute('**/events/track/');const networkAfter=await state(c);actions.push({name:'network-failure',before:networkBefore,after:networkAfter,result:network});add('network-failure',networkAfter.event_count===networkBefore.event_count,{SIMULATED:true,eventDelta:networkAfter.event_count-networkBefore.event_count});
await shot(p,'public-ru-1440-functional');
for(const role of ['outsider','owner','staff']){const q=contexts[role];const st=await visit(q.p,'/ru/account/places/1/analytics/');add('owner-analytics-acl-'+role,st===(role==='owner'?200:404),{http:st,body:(await q.p.locator('body').innerText()).slice(-300)},role);await shot(q.p,'analytics-acl-'+role+'-1440');}
const admin=await context('admin');for(const role of ['staff','admin']){const q=role==='staff'?contexts.staff:admin;const st=await visit(q.p,'/admin/catalog/siteanalytics/?period=90');add('admin-analytics-acl-'+role,st===(role==='admin'?200:403),{http:st,kpi:await q.p.locator('[data-kpi-value]').allTextContents()},role);await shot(q.p,'admin-analytics-'+role+'-1440');}
const disabled=await context('guest');await disabled.p.goto('http://localhost:8830'+F.urls.ru.place);const db=await state(disabled.c);const disabledResult=await disabled.p.evaluate(async()=>{const r=await fetch('/ru/events/track/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event_type:'phone_click',place_id:1})});return r.status;});const da=await state(disabled.c);actions.push({name:'disabled',before:db,after:da,result:disabledResult});add('disabled-collection',disabledResult===200&&db.event_count===da.event_count,{status:disabledResult,eventDelta:da.event_count-db.event_count});
const version=await(await c.request.get(B+'/qa/version/')).json();for(const q of [...Object.values(contexts),admin,disabled])await q.c.close();return{rows,actions,version};
}
