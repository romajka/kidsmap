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

const{c:ac,p:a}=await context('admin'),{c,p}=await context('guest');const maps=[],flags=['organizations_section_enabled','specialists_section_enabled','events_section_enabled'];async function toggle(on){await visit(a,'/ru/admin/catalog/sitevisibilitysettings/1/change/');for(const f of flags)await a.locator('[name='+f+']').setChecked(on);await Promise.all([a.waitForNavigation(),a.locator('[name=_continue]').first().click()]);}
try{for(const on of [true,false,true]){await toggle(on);await visit(p,'/ru/catalog/');const query=p.locator('#catalog-hero-search-input');if(await query.count()){await query.fill('QA13');await Promise.all([p.waitForNavigation(),p.locator('#catalog-hero-search-form [type=submit]').click()]);}else await visit(p,'/ru/catalog/?q=QA13');const ids=await p.locator('main a[href*="/place/"]').evaluateAll(xs=>[...new Set(xs.map(x=>x.getAttribute('href')))]);const mr=await p.request.get(B+'/ru/api/catalog/map/?q=QA13');const map=await mr.json();const sr=await p.request.get(B+'/ru/api/catalog/suggestions/?q=QA13');const suggestions=await sr.json();maps.push({on,ids,map,suggestions});add('sections-search-map-'+(on?'on':'off'),ids.length>=2&&mr.status()===200&&sr.status()===200,{ids,mapCount:map.count,httpMap:mr.status(),httpSuggestions:sr.status(),nativeSearch:await query.count()>0},'guest','ru',1440,p.url(),await shot(p,'sections-search-'+(on?'on':'off')+'-1440'));await p.setViewportSize({width:390,height:950});await shot(p,'sections-search-'+(on?'on':'off')+'-390');await p.setViewportSize({width:1440,height:950});}
add('section-toggles-preserve-map-place-projection',JSON.stringify(maps[0].map)===JSON.stringify(maps[1].map)&&JSON.stringify(maps[1].map)===JSON.stringify(maps[2].map),{mapCounts:maps.map(x=>x.map.count)},'guest');return{rows,maps};}catch(e){return{rows,maps,error:String(e)};}finally{await toggle(true);await c.close();await ac.close();}}
