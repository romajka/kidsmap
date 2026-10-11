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

const{c,p}=await context('guest');const actions=[],requests=[];
async function state(){return(await c.request.get(B+'/qa/state/')).json();}
await visit(p,F.urls.ru.place);
const controls=await p.locator('[data-phone-reveal],[data-track-event]').evaluateAll(es=>es.map(e=>({tag:e.tagName,text:e.textContent.trim().slice(0,80),event:e.dataset.trackEvent,reveal:e.dataset.phoneReveal,href:e.getAttribute('href')})));
p.on('response',async r=>{if(r.url().includes('/events/track/'))requests.push({status:r.status(),body:await r.text()});});
const reveal=p.locator('[data-phone-reveal="1"]').first();if(await reveal.count()){
 const b=await state();await reveal.click();await p.waitForTimeout(400);const a=await state();actions.push({name:'reveal',before:b,after:a});add('native-phone-reveal',await p.locator('a[data-track-event="phone_click"]').count()>0,{before:b.metrics['1'],after:a.metrics['1']});await shot(p,'native-phone-open-ru-1440');
 const call=p.locator('a[data-track-event="phone_click"]').first();if(await call.count()){
  const before=await state();await call.click();await p.waitForTimeout(350);const after=await state();actions.push({name:'native-phone-call-unadapted',before,after,requests:[...requests]});add('native-phone-call-unadapted',after.metrics['1'].contact_actions-before.metrics['1'].contact_actions===1,{delta:after.metrics['1'].contact_actions-before.metrics['1'].contact_actions,requests:[...requests]});
 }
}
await p.route('**/events/track/',async route=>{const h={...route.request().headers(),origin:'http://localhost',referer:'http://localhost'+F.urls.ru.place};const response=await route.fetch({headers:h});await route.fulfill({response});});
async function event(payload,extra={}){return p.evaluate(async({payload,extra})=>{const r=await fetch('/ru/events/track/',{method:'POST',headers:{'Content-Type':'application/json',...extra},body:typeof payload==='string'?payload:JSON.stringify(payload)});return{status:r.status,body:r.status===500?'server-error':await r.text()};},{payload,extra});}
const cases=[['phone_click',{event_type:'phone_click',place_id:1},200,1],['repeat-phone',{event_type:'phone_click',place_id:1},200,1],['whatsapp_click',{event_type:'whatsapp_click',place_id:1},200,1],['website_click',{event_type:'website_click',place_id:1},200,1],['social_click',{event_type:'social_click',place_id:1},200,1],['directions_click',{event_type:'directions_click',place_id:1},200,1],['invalid-json','{',400,0],['array',[],400,0],['unsupported',{event_type:'unknown',place_id:1},400,0],['missing-id',{event_type:'phone_click'},400,0],['inactive-id',{event_type:'phone_click',place_id:3},400,0],['deleted-id',{event_type:'phone_click',place_id:5},400,0],['unknown-id',{event_type:'phone_click',place_id:999999},400,0],['private-draft-id',{event_type:'phone_click',place_id:2},400,0],['private-archived-id',{event_type:'phone_click',place_id:4},400,0],['spoofed-client-view',{event_type:'place_view',place_id:1},400,0]];
for(const[name,payload,status,delta]of cases){const before=await state(),result=await event(payload),after=await state();actions.push({name,before,after,result,SIMULATED:'Origin/Referer remove port only'});add('adapter-'+name,result.status===status&&after.event_count-before.event_count===delta,{result,expectedStatus:status,eventDelta:after.event_count-before.event_count,expectedDelta:delta,SIMULATED:true});}
const before=await state(),failure=await event({event_type:'phone_click',place_id:1},{'X-QA-Failure':'event-store'}),after=await state();actions.push({name:'backend-failure',before,after,result:failure,SIMULATED:true});add('backend-failure-no-write',failure.status===500&&before.event_count===after.event_count,{result:failure,eventDelta:after.event_count-before.event_count,SIMULATED:true});
await p.goto('http://localhost:8830'+F.urls.ru.place);const db=await state(),dr=await event({event_type:'phone_click',place_id:1}),da=await state();add('disabled-valid-event',dr.status===200&&db.event_count===da.event_count,{result:dr,eventDelta:da.event_count-db.event_count,SIMULATED:'port header adapter'});actions.push({name:'disabled-valid-event',before:db,after:da,result:dr});
await c.close();return{rows,actions,controls,requests,transportAdapter:'SIMULATED nondefaultport headers only; real unadapted phone action retained'};
}
