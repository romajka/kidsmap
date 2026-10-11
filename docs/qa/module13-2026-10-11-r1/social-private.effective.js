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

const author=await context('outsider'),admin=await context('admin'),guest=await context(),person=await context('specialist'),network=await context('owner');async function nav(p,l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}let phase='reviews';const evidence={};try{for(const[kind,id]of[['place',2],['activity',1],['specialist',1],['event',1]]){let p=author.p;await visit(p,'/ru/reviews/'+kind+'/target/'+id+'/');await p.locator('#review-rating').selectOption('4');await p.locator('#review-text').fill('QA13 fictional '+kind+' review <b>literal</b>');await nav(p,p.locator('[data-review-edit] button'));await p.reload();add('review-'+kind+'-draft-text-reload',await p.locator('#review-text').inputValue()==='QA13 fictional '+kind+' review <b>literal</b>',{},'outsider');add('review-'+kind+'-rating-reload',await p.locator('#review-rating').inputValue()==='4',{actual:await p.locator('#review-rating').inputValue(),historical_id:'SOCIAL-QA-01'},'outsider');p=admin.p;await visit(p,'/ru/reviews/'+kind+'/target/'+id+'/');const candidate=p.locator('[data-candidate-id]').first();const exists=await candidate.count();if(exists){await nav(p,candidate.locator('form[action$="/approve/"] button'));add('review-'+kind+'-native-moderation',true,{},'admin');}else add('review-'+kind+'-native-moderation',null,{reason:'No candidate control'},'admin');await visit(guest.p,'/ru/reviews/'+kind+'/target/'+id+'/');const text=await guest.p.locator('main').first().innerText();add('review-'+kind+'-public-literal-escaped',text.includes('QA13 fictional '+kind+' review <b>literal</b>')&&await guest.p.locator('article[data-review-id] b').count()===0,{},'guest','ru',1440,guest.p.url(),await shot(guest.p,'review-'+kind+'-public-1440'));}
phase='favorites';let p=author.p;await visit(p,'/ru/catalog/');const like=p.locator('form[action$="/place/2/like/"] button').first();await like.dblclick();await p.waitForTimeout(450);await visit(p,'/ru/account/favorites/');add('favorite-double-click-single-visible-place',await p.locator('a[href*="/place/2-"]').count()>0,{},'outsider','ru',1440,p.url(),await shot(p,'favorites-filled-1440'));await p.reload();add('favorite-reload-preserved',await p.locator('a[href*="/place/2-"]').count()>0,{},'outsider');
phase='private document';p=person.p;await visit(p,'/ru/account/specialists/1/certificates/');await p.locator('[name=document_type]').selectOption('identity');await p.locator('[name=name]').fill('QA13 fictional identity image');await p.locator('[name=file]').setInputFiles('C:/kidsmap/.tmp/module13-20261011-r1/assets/fixture.png');await p.locator('#id_publish').uncheck();const upload=p.locator('form').filter({has:p.locator('[name=action][value=upload]')});await nav(p,upload.locator('button[type=submit]'));const id=Number(await p.locator('[data-document-id]').first().getAttribute('data-document-id'));evidence.documentId=id;add('private-identity-native-upload',id>0,{},'specialist','ru',1440,p.url(),await shot(p,'private-doc-upload-1440'));p=admin.p;await visit(p,'/ru/account/specialists/1/review/');await nav(p,p.locator('[data-document-id="'+id+'"] button[value=document_approve]'));for(const rolePage of [['person',person.p],['guest',guest.p],['network',network.p]]){const r=await rolePage[1].request.get(B+'/ru/specialists/documents/'+id+'/download/');add('identity-document-download-'+rolePage[0],r.status()===(rolePage[0]==='person'?200:404),{http:r.status(),cache:r.headers()['cache-control'],disposition:r.headers()['content-disposition']},rolePage[0]);}await person.p.reload();add('identity-stays-private-after-approval',(await person.p.locator('[data-document-id="'+id+'"]').innerText()).includes('Приватный'),{},'specialist');return{rows,evidence};}catch(e){return{rows,evidence,phase,error:String(e),authorUrl:author.p.url(),personUrl:person.p.url()};}finally{for(const a of[author,admin,guest,person,network])await a.c.close();}}
