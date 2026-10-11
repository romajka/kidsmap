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

const{c,p}=await context('admin');const guest=await context('guest'),actions=[];async function state(){return(await c.request.get(B+'/qa/state/')).json();}
async function action(name,fn){const before=await state(),result=await fn(),after=await state();actions.push({name,before,after,result});return{before,after,result};}
async function bulk(name){await visit(p,'/admin/catalog/place/?id__exact=1');await p.locator('[name=_selected_action][value="1"]').check();const b=p.locator('[data-bulk-submit="'+name+'"]');if(await b.count()){if(!await b.isVisible()){await p.locator('#km-bulk-bar details summary').click();}await b.click();}else{await p.locator('select[name=action]').first().selectOption(name);await p.locator('button[name=index]').first().click();}await p.waitForTimeout(350);return{url:p.url(),messages:await p.locator('.messagelist,.alert').allTextContents()};}
for(let n=1;n<=2;n++){
 const names={az:'Uydurma QA12 dəyişiklik '+n+' '+('uzun məkan adı '.repeat(8)),ru:'Вымышленное QA12 переименование '+n+' '+('длинное название '.repeat(7)),en:'Fictional QA12 rename '+n+' '+('long place name '.repeat(8))};
 const save=await action('rename-candidate-'+n,async()=>{await visit(p,'/admin/catalog/place/1/change/');for(const lang of ['az','ru','en']){await p.locator('[data-pf-langtab="'+lang+'"]').first().click();await p.locator('[name="name_'+lang+'"]').fill(names[lang]);}const[r]=await Promise.all([p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/place/1/change/')),p.locator('[name=_continue]').first().click()]);await p.waitForLoadState('domcontentloaded');return{http:r.status(),errors:await p.locator('.errorlist,.errornote,[data-pf-error-summary]').allTextContents(),candidateAZ:await p.locator('[name=name_az]').inputValue()};});
 const live=save.after.places.find(x=>x.id===1);add('rename-candidate-saved-'+n,save.result.http===302,{result:save.result,before:save.before.places.find(x=>x.id===1),liveAfter:live},'admin');await shot(p,'rename-candidate-'+n+'-admin-1440');
 if(save.result.http!==302){add('rename-approval-'+n,null,{reason:'Native admin validation blocks candidate',errors:save.result.errors},'admin');continue;}
 const approved=await action('rename-approve-'+n,()=>bulk('mark_published'));const al=approved.after.places.find(x=>x.id===1);add('rename-approved-'+n,al.name_az===names.az&&al.status==='published',{result:approved.result,live:al,expected:names},'admin');
 const old=await action('old-url-after-rename-'+n,()=>visit(guest.p,F.urls.ru.place));add('rename-old-url-view-'+n,old.result===200&&old.after.metrics['1'].views-old.before.metrics['1'].views===1,{delta:old.after.metrics['1'].views-old.before.metrics['1'].views,result:old.result,url:guest.p.url(),URLPolicy:'stable localized slug'},'guest');
 const redirect=await action('old-slug-redirect-'+n,()=>visit(guest.p,'/ru/place/1-obsolete-synthetic-name/'));add('redirect-one-entity-'+n,redirect.result===200&&redirect.after.metrics['1'].views-redirect.before.metrics['1'].views===1,{delta:redirect.after.metrics['1'].views-redirect.before.metrics['1'].views,result:redirect.result,finalURL:guest.p.url()},'guest');
 await guest.p.reload();await shot(guest.p,'public-renamed-'+n+'-ru-1440');
}
const owner=await context('owner');for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){await owner.p.setViewportSize({width,height:950});await owner.c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);await visit(owner.p,prefix(lang)+'/account/places/1/analytics/');const g=await geometry(owner.p),s=await shot(owner.p,'owner-long-'+lang+'-'+width);add('owner-long-title',g.document<=width+1,{geometry:g,h1:await owner.p.locator('h1').textContent()},'owner',lang,width,owner.p.url(),s);}
const hidden=await action('hide-native',()=>bulk('mark_inactive'));add('hide-history-preserved',hidden.before.event_count===hidden.after.event_count&&hidden.after.places.find(x=>x.id===1).is_active===false,{before:hidden.before.metrics['1'],after:hidden.after.metrics['1'],result:hidden.result},'admin');const st=await visit(guest.p,F.urls.ru.place);add('hidden-public-unavailable',st===404,{http:st},'guest');await shot(guest.p,'hidden-public-ru-1440');
const restored=await action('restore-publish-native',()=>bulk('mark_published'));add('restore-history-preserved',restored.before.event_count===restored.after.event_count&&restored.after.places.find(x=>x.id===1).is_active===true,{before:restored.before.metrics['1'],after:restored.after.metrics['1'],result:restored.result},'admin');
for(const q of [guest,owner,{c}])await q.c.close();return{rows,actions,limitations:['Place has hide/draft/soft-delete actions, no archive action; Event cancellation and actual Organization archive tracked different subject scope NOT RUN']};
}
