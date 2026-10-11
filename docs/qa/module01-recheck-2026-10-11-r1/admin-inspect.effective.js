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

const out=[];for(const lang of ['ru','az','en']){const x=await context('admin',lang);try{await visit(x.p,prefix(lang)+'/admin/catalog/place/2/change/');out.push({lang,labels:await x.p.locator('label[for*=description]').evaluateAll(es=>es.map(e=>({for:e.htmlFor,text:e.textContent,visible:!!e.getClientRects().length}))),fields:await x.p.locator('[id*=description]').evaluateAll(es=>es.map(e=>({id:e.id,aria:e.getAttribute('aria-label')})))});}finally{await x.c.close();}}return{out};}
