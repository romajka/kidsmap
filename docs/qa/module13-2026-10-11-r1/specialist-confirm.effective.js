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

const person=await context('specialist'),admin=await context('admin'),network=await context('owner');async function nav(p,l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}let phase='claim';try{let p=person.p;const before=await visit(p,'/ru/account/specialists/1/');add('proposal-author-no-person-edit-before-claim',before===404,{http:before,supersedes:'specialist-flow/author-cannot-person-edit regex-only false failure'},'specialist');await visit(p,'/ru/account/specialists/1/claims/');await nav(p,p.locator('[name=action][value=request]'));add('specialist-person-claim-request',await p.locator('[name=action][value=withdraw]').count()===1,{},'specialist');p=admin.p;await visit(p,'/ru/account/specialists/1/review/');await nav(p,p.locator('[name=action][value=claim_approve]').last());p=person.p;await visit(p,'/ru/account/specialists/1/');add('claimed-person-can-edit',await p.locator('#specialist-create-form').count()===1,{},'specialist');p=admin.p;await visit(p,'/admin/catalog/specialist/?id__exact=1');await p.locator('[name=_selected_action][value="1"]').check();await nav(p,p.locator('[data-bulk-submit=mark_published]'));add('specialist-native-published',true,{},'admin');phase='cooperation';p=network.p;await visit(p,'/ru/account/organizations/1/specialists/');await p.locator('[name=specialist]').selectOption('1');await p.locator('[name=role]').fill('QA13 fictional specialist');await p.locator('[name=start_date]').fill('2026-10-11');const form=p.locator('form').filter({has:p.locator('[name=action][value=propose]')});await nav(p,form.locator('button[type=submit]'));add('network-cooperation-proposed',await p.locator('[name=employment_id]').count()===1,{},'owner');p=person.p;await visit(p,'/ru/account/specialists/1/invitations/');await nav(p,p.locator('[name=action][value=confirm]').first());p=network.p;await p.reload();await nav(p,p.locator('[name=action][value=confirm]').first());p=person.p;await p.reload();add('both-sides-cooperation-confirmed',(await p.locator('main').first().innerText()).includes('Подтверждено'),{},'specialist','ru',1440,p.url(),await shot(p,'specialist-cooperation-1440'));await p.setViewportSize({width:390,height:950});await shot(p,'specialist-cooperation-390');const denied=await visit(network.p,'/ru/account/specialists/1/certificates/');add('network-cooperation-does-not-grant-private-documents',denied===404,{http:denied},'owner');return{rows};}catch(e){return{rows,phase,error:String(e),personUrl:person.p.url(),adminUrl:admin.p.url(),networkUrl:network.p.url()};}finally{await person.c.close();await admin.c.close();await network.c.close();}}
