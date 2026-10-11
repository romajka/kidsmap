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

const admin=await context('admin'),reason='QA01R исправьте адрес <img src=x onerror="window.QA01R_XSS=1">',label={ru:'Причина отказа',az:'İmtina səbəbi',en:'Reason for rejection'};
const nav=async(p,l)=>Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);
try{await visit(admin.p,'/ru/admin/volunteer/review/2/');await admin.p.locator('[name=note]').fill(reason);await nav(admin.p,admin.p.locator('button[value=reject]'));
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){const x=await context('owner',lang,width);try{await visit(x.p,prefix(lang)+'/account/places/2/edit/');await x.p.waitForTimeout(300);const text=await x.p.locator('body').innerText();const image=await shot(x.p,'rejected-'+lang+'-'+width);add('PLACE-QA-01 reason escaped after native rejection',text.includes(reason)&&await x.p.evaluate(()=>!window.QA01R_XSS),{reasonVisible:text.includes(reason),labelVisible:text.includes(label[lang])},'owner',lang,width,x.p.url(),image);await x.p.reload();add('PLACE-QA-01 reload retains reason',(await x.p.locator('body').innerText()).includes(reason),{},'owner',lang,width,x.p.url());}finally{await x.c.close();}}
const own=await context('owner');try{await visit(own.p,'/ru/account/places/2/edit/');await own.p.locator('[name=description_az]').fill('QA01R corrected fictional description. '.repeat(15));await own.p.waitForTimeout(1600);await own.p.locator('[data-pc-submit]').click();await own.p.waitForURL('**/account/places/');add('rejected place corrected and resubmitted natively',true,{},'owner');await visit(admin.p,'/ru/admin/volunteer/review/2/');await nav(admin.p,admin.p.locator('button[value=approve]'));add('place approved through native review',true,{},'admin');await visit(own.p,'/ru/account/places/2/edit/');add('reason cleared after successful resubmission',!(await own.p.locator('body').innerText()).includes(reason),{},'owner');}finally{await own.c.close();}
return{rows,consoleErrors,networkErrors};}catch(e){return{rows,consoleErrors,networkErrors,error:String(e)};}finally{await admin.c.close();}}
