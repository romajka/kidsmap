async original=>{
 const F={
  "actors": {
    "owner": {
      "id": 1,
      "username": "qa11_owner",
      "email": "owner11@example.invalid"
    },
    "staff": {
      "id": 2,
      "username": "qa11_staff",
      "email": "staff11@example.invalid"
    },
    "admin": {
      "id": 3,
      "username": "qa11_admin",
      "email": "admin11@example.invalid"
    },
    "outsider": {
      "id": 4,
      "username": "qa11_outsider",
      "email": "outsider11@example.invalid"
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
  "organization_public_id": "7b78e253-9a64-4772-a308-7e59ae9a390b",
  "urls": {
    "ru": {
      "place": "/ru/place/1-vymyshlennoe-qa11-live/",
      "specialist": "/ru/specialists/fictional-qa11-specialist/",
      "event": "/ru/event/1-uydurma-qa11-tedbir/",
      "organization": "/ru/organizations/7b78e253-9a64-4772-a308-7e59ae9a390b/",
      "activity": "/ru/activities/1/",
      "program": "/ru/account/organizations/1/programs/1/",
      "landing": "/ru/catalog/qa11-strong/",
      "extras": {
        "pending": "/ru/place/6-vymyshlennoe-qa11-pending/",
        "rejected": "/ru/place/7-vymyshlennoe-qa11-rejected/",
        "fallback": "/ru/place/8-vymyshlennoe-qa11-fallback/",
        "long": "/ru/place/9-vymyshlennoe-qa11-long-dlinnyitekst-dlinnyitekst-dlinnyiteks/",
        "escaping": "/ru/place/10-vymyshlennoe-qa11-escaping-scriptscriptwindow__qa11_xss__1sc/"
      }
    },
    "az": {
      "place": "/place/1-uydurma-qa11-live/",
      "specialist": "/specialists/fictional-qa11-specialist/",
      "event": "/event/1-uydurma-qa11-tedbir/",
      "organization": "/organizations/7b78e253-9a64-4772-a308-7e59ae9a390b/",
      "activity": "/activities/1/",
      "program": "/account/organizations/1/programs/1/",
      "landing": "/catalog/qa11-strong/",
      "extras": {
        "pending": "/place/6-uydurma-qa11-pending/",
        "rejected": "/place/7-uydurma-qa11-rejected/",
        "fallback": "/place/8-uydurma-qa11-fallback/",
        "long": "/place/9-uydurma-qa11-long-uzunmetn-uzunmetn-uzunmetn-uzunmetn-uzunme/",
        "escaping": "/place/10-uydurma-qa11-escaping-scriptscriptwindow__qa11_xss__1script/"
      }
    },
    "en": {
      "place": "/en/place/1-fictional-qa11-live/",
      "specialist": "/en/specialists/fictional-qa11-specialist/",
      "event": "/en/event/1-uydurma-qa11-tedbir/",
      "organization": "/en/organizations/7b78e253-9a64-4772-a308-7e59ae9a390b/",
      "activity": "/en/activities/1/",
      "program": "/en/account/organizations/1/programs/1/",
      "landing": "/en/catalog/qa11-strong/",
      "extras": {
        "pending": "/en/place/6-fictional-qa11-pending/",
        "rejected": "/en/place/7-fictional-qa11-rejected/",
        "fallback": "/en/place/8-uydurma-qa11-fallback/",
        "long": "/en/place/9-fictional-qa11-long-longtext-longtext-longtext-longtext-long/",
        "escaping": "/en/place/10-fictional-qa11-escaping-scriptscriptwindow__qa11_xss__1scrip/"
      }
    }
  },
  "settings": 1,
  "synthetic_only": true,
  "program": 1,
  "activity": 1,
  "extra_places": {
    "pending": 6,
    "rejected": 7,
    "fallback": 8,
    "long": 9,
    "escaping": 10
  }
},B='http://localhost:8827',ROOT='C:/kidsmap/docs/qa/module11-2026-10-11-r1',rows=[];
const br=original.context().browser();
function add(scenario,ok,detail={},role='guest',lang='ru',width=1440,url='',shot=''){const d={...detail};if('status' in d){d.responseStatus=d.status;delete d.status;}rows.push({...d,scenario,status:ok===null?'NOT RUN':ok?'PASS':'FAIL',role,lang,width,url,shot});}
function prefix(lang){return lang==='az'?'':('/'+lang);}
async function context(role='guest',lang='ru',width=1440){
 const c=await br.newContext({viewport:{width,height:950}});await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());
 await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);const p=await c.newPage();p.setDefaultTimeout(10000);p.setDefaultNavigationTimeout(25000);p.on('dialog',async d=>{await d.accept();});
 if(role!=='guest'){await p.goto(B+'/ru/auth/login/');await p.locator('input[name=username]').fill(F.actors[role].email);await p.locator('input[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForTimeout(100);await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);}
 return{c,p};
}
async function shot(p,name){const file='screenshots/'+name+'.png';await p.screenshot({path:ROOT+'/'+file,fullPage:true,animations:'disabled'});return file;}
async function visit(p,path){const r=await p.goto(B+path);await p.waitForTimeout(120);return r?.status()??null;}
async function geometry(p){return p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflow:[...document.querySelectorAll('h1,h2,h3,p,label,button,input,select,textarea,.km-header-inner,.footer-inner')].map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.trim().slice(0,70),r:e.getBoundingClientRect()})).filter(x=>x.r.width&&x.r.left>=0&&x.r.right>innerWidth+2).slice(0,10).map(x=>({...x,r:{left:x.r.left,right:x.r.right,width:x.r.width}}))}));}
async function head(p){return p.evaluate(()=>({title:document.title,h1:[...document.querySelectorAll('h1')].map(e=>e.textContent.trim()),description:document.querySelector('meta[name=description]')?.content,ogTitle:document.querySelector('meta[property="og:title"]')?.content,ogDescription:document.querySelector('meta[property="og:description"]')?.content,ogImage:document.querySelector('meta[property="og:image"]')?.content,twTitle:document.querySelector('meta[name="twitter:title"]')?.content,canonical:document.querySelector('link[rel=canonical]')?.href,robots:document.querySelector('meta[name=robots]')?.content,alternates:[...document.querySelectorAll('link[hreflang]')].map(e=>({lang:e.hreflang,href:e.href})),jsonld:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>{try{return JSON.parse(e.textContent)}catch{return {parseError:true}}}),xss:window.__QA11_XSS__||0}));}

 const o=await context('owner'),p=o.p,second=await o.c.newPage();second.on('dialog',d=>d.accept());second.setDefaultTimeout(10000);const gctx=await context('guest','az'),g=gctx.p,admin=await context('admin');await visit(g,F.urls.az.organization);const live=(await head(g)).h1[0];await visit(p,'/ru/account/organizations/1/');await visit(second,'/ru/account/organizations/1/');const form=p.locator('[data-org-edit-form]');await form.locator('[name=name_az]').fill('Uydurma QA11 conflict accepted');await p.waitForTimeout(1300);await Promise.all([p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/save/')),form.locator('button[name=submit]').click()]);await p.waitForLoadState('load');const stale=second.locator('[data-org-edit-form]'),value='Uydurma QA11 stale text retained';await stale.locator('[name=name_az]').fill(value);await second.waitForTimeout(100);const rr=await Promise.all([second.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/save/')),stale.locator('button[name=submit]').click()]);await second.waitForLoadState('load');const errors=await second.locator('[data-org-error-summary]').allTextContents();add('two-tab-stale-conflict-input-retained',rr[0].status()===409&&(await second.locator('[data-org-edit-form] [name=name_az]').inputValue())===value&&errors.length>0,{responseStatus:rr[0].status(),errors,value},'owner','ru',1440,second.url(),await shot(second,'two-tabs-conflict-error'));await visit(g,F.urls.az.organization);add('conflict-public-live-canonical-unchanged',(await head(g)).h1[0]===live&&(await head(g)).canonical===B+F.urls.az.organization,{live,head:await head(g)},'guest','az',1440,g.url());
 // Abort before the server; autosave remains available and is independently read back.
 await visit(second,'/ru/account/organizations/1/');const net=second.locator('[data-org-edit-form]'),networkValue='Uydurma QA11 network input';await net.locator('[name=name_az]').fill(networkValue);await second.waitForTimeout(1400);const action=await net.getAttribute('action');await second.route('**'+action,r=>r.request().method()==='POST'?r.abort('failed'):r.continue());await net.locator('button[name=submit]').click();await second.waitForTimeout(500);await shot(second,'network-abort-before-server');await second.unroute('**'+action);await second.goBack().catch(()=>null);await second.waitForTimeout(200);const retained=second.locator('[data-org-edit-form] [name=name_az]');add('SIMULATED-network-abort-input-after-back',await retained.count()>0&&(await retained.inputValue())===networkValue,{classification:'SIMULATED local POST transport aborted before server; autosave allowed',networkValue},'owner','ru',1440,second.url(),await shot(second,'network-input-after-back'));await visit(g,F.urls.az.organization);add('SIMULATED-network-abort-live-unchanged',(await head(g)).h1[0]===live,{head:await head(g)},'guest','az',1440,g.url());
 await visit(admin.p,'/admin/catalog/organization/1/change/');const approve=admin.p.locator('button[name=action][value=approve]');if(await approve.isVisible()){await Promise.all([admin.p.waitForResponse(r=>r.request().method()==='POST'),approve.click()]);await admin.p.waitForLoadState('load');add('post-negative-native-approved',true,{},'admin','ru',1440,admin.p.url());}else add('post-negative-native-approved',null,{reason:'Remaining autosave draft is not pending; live untouched'},'admin','ru',1440,admin.p.url());await o.c.close();await gctx.c.close();await admin.c.close();return {rows};
}
