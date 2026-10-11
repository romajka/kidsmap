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

const owner=await context('owner'),admin=await context('admin');const k=(s,n)=>s.locator('[data-offering-key='+n+']').first();async function nav(p,l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}async function save(p,value){await p.waitForTimeout(1500);const resp=p.waitForResponse(r=>r.url().includes('/save-photos/')&&r.request().method()==='POST'),nav=p.waitForNavigation({waitUntil:'domcontentloaded'}).catch(()=>null);await p.locator('button[name=form_action][value='+value+']').click({noWaitAfter:true});const r=await resp;if(r.status()===200)await nav;return{http:r.status(),body:r.status()===200?{}:await r.json()};}let phase='groups';try{let p=owner.p;await visit(p,'/ru/account/places/2/edit/?fresh=1');await p.locator('[data-pc-add-activity]').click();const a=p.locator('.pc-activity-card').last();await k(a,'program_id').selectOption('1');for(let i=0;i<2;i++){if(i)await a.getByRole('button',{name:'Добавить группу',exact:true}).click();const g=a.locator('.pc-group-card').nth(i);await k(g,'name_az').fill('Uydurma QA13 '+(i?'Older':'Junior'));await k(g,'age_from').fill(i?'12':'4');await k(g,'age_to').fill(i?'15':'6');await k(g,'schedule_text').fill(i?'Wednesday 18:00–19:00':'Monday 16:00–17:00');await k(g,'conditions_az').fill('QA13 fictional local conditions '+i);await k(g,'title_az').fill('QA13 lesson '+i);await k(g,'price').fill(i?'80':'20');}let r=await save(p,'save_draft');add('linked-activity-two-groups-draft-save',r.http===200,r,'owner');await p.reload();const tree=JSON.parse(await p.locator('[name=nested_pricing]').inputValue());add('linked-program-groups-prices-reload',tree.activities.at(-1)?.program_id===1&&tree.activities.at(-1)?.groups.length===2,{tree},'owner');await shot(p,'activity-groups-reload-1440');const hours=await p.locator('[name=schedule_mode]').inputValue();add('lesson-schedule-separate-from-place-hours',hours==='always_open'&&tree.activities.at(-1)?.groups[0].schedule_text==='Monday 16:00–17:00',{hours},'owner');phase='submit';r=await save(p,'save_and_publish');add('linked-activity-submit',r.http===200,r,'owner');p=admin.p;await visit(p,'/admin/volunteer/review/2/');await nav(p,p.locator('button[value=approve]'));add('linked-activity-native-approve',true,{},'admin');return{rows};}catch(e){await shot(owner.p,'activity-flow-error');return{rows,phase,error:String(e),url:owner.p.url(),errors:await owner.p.locator('[data-pc-errors]').allTextContents()};}finally{await owner.c.close();await admin.c.close();}}
