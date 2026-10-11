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
},widths=[360,390,768,1024,1280,1440],langs=['ru','az','en'],flags=['organizations_section_enabled','specialists_section_enabled','events_section_enabled'];
const{c:ac,p:a}=await context('admin');let phase='off',saved=[];const errors=[];
async function toggle(on){await visit(a,'/ru/admin/catalog/sitevisibilitysettings/1/change/');for(const f of flags)await a.locator('[name='+f+']').setChecked(on);const save=a.locator('[name=_continue]').first();await Promise.all([a.waitForNavigation(),save.click()]);await a.reload();const read=await Promise.all(flags.map(f=>a.locator('[name='+f+']').isChecked()));add('sections-native-save-reload-'+(on?'on':'off'),read.every(v=>v===on),{read},'admin','ru',1440,a.url(),await shot(a,'sections-settings-'+(on?'on':'off')+'-1440'));saved.push({on,read});}
async function matrix(on){for(const lang of langs){const{c,p}=await context('guest',lang);const base=prefix(lang),surfaces=[['organizations-list',base+'/organizations/',on?200:404],['organization-card',URLS[lang].organizations['1'],on?200:404],['specialists-list',base+'/specialists/',on?200:404],['specialist-card',URLS[lang].specialists['1'],on?200:404],['events-list',base+'/events/',on?200:410],['event-card',URLS[lang].events['2'],on?200:410]];try{for(const width of widths){await p.setViewportSize({width,height:950});for(const[surface,path,expected]of surfaces){const http=await visit(p,path),g=await geometry(p);const file='screenshots/sections-'+(on?'on':'off')+'-'+lang+'-'+width+'-'+surface+'.png';if(width===390||width===1440)await p.screenshot({path:ROOT+'/'+file,animations:'disabled'});add('sections-'+(on?'on':'off')+'-'+surface,http===expected&&g.document<=width+1,{http,expected,geometry:g},'guest',lang,width,p.url(),width===390||width===1440?file:'');}await visit(p,base+'/');const menu=await p.locator('header').evaluate(h=>[...h.querySelectorAll('a[href]')].filter(x=>/\/(organizations|specialists|events)\//.test(new URL(x.href).pathname)).map(x=>x.href));add('sections-'+(on?'on':'off')+'-navigation',on?menu.length>0:menu.length===0,{menu},'guest',lang,width,p.url());}}
finally{await c.close();}}}
try{await toggle(false);await matrix(false);const{c:oc,p:o}=await context('owner');const http=await visit(o,'/ru/account/organizations/1/');add('hidden-sections-owner-workspace-preserved',http===200,{http},'owner','ru',1440,o.url(),await shot(o,'hidden-sections-owner-1440'));await oc.close();phase='on';await toggle(true);await matrix(true);return{rows,saved};}catch(e){errors.push({phase,error:String(e),url:a.url()});return{rows,saved,errors};}finally{if(!saved.some(x=>x.on===true)){try{await toggle(true);}catch(e){errors.push({restore:String(e)});}}await ac.close();}}
