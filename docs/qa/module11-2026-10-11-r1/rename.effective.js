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
function add(scenario,ok,detail={},role='guest',lang='ru',width=1440,url='',shot=''){rows.push({scenario,status:ok===null?'NOT RUN':ok?'PASS':'FAIL',role,lang,width,url,shot,...detail});}
function prefix(lang){return lang==='az'?'':('/'+lang);}
async function context(role='guest',lang='ru',width=1440){
 const c=await br.newContext({viewport:{width,height:950}});await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());
 await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);const p=await c.newPage();p.setDefaultTimeout(10000);p.setDefaultNavigationTimeout(25000);
 if(role!=='guest'){await p.goto(B+'/ru/auth/login/');await p.locator('input[name=username]').fill(F.actors[role].email);await p.locator('input[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForTimeout(100);await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);}
 return{c,p};
}
async function shot(p,name){const file='screenshots/'+name+'.png';await p.screenshot({path:ROOT+'/'+file,fullPage:true,animations:'disabled'});return file;}
async function visit(p,path){const r=await p.goto(B+path);await p.waitForTimeout(120);return r?.status()??null;}
async function geometry(p){return p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflow:[...document.querySelectorAll('h1,h2,h3,p,label,button,input,select,textarea,.km-header-inner,.footer-inner')].map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.trim().slice(0,70),r:e.getBoundingClientRect()})).filter(x=>x.r.width&&x.r.left>=0&&x.r.right>innerWidth+2).slice(0,10).map(x=>({...x,r:{left:x.r.left,right:x.r.right,width:x.r.width}}))}));}
async function head(p){return p.evaluate(()=>({title:document.title,h1:[...document.querySelectorAll('h1')].map(e=>e.textContent.trim()),description:document.querySelector('meta[name=description]')?.content,ogTitle:document.querySelector('meta[property="og:title"]')?.content,ogDescription:document.querySelector('meta[property="og:description"]')?.content,ogImage:document.querySelector('meta[property="og:image"]')?.content,twTitle:document.querySelector('meta[name="twitter:title"]')?.content,canonical:document.querySelector('link[rel=canonical]')?.href,robots:document.querySelector('meta[name=robots]')?.content,alternates:[...document.querySelectorAll('link[hreflang]')].map(e=>({lang:e.hreflang,href:e.href})),jsonld:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>{try{return JSON.parse(e.textContent)}catch{return {parseError:true}}}),xss:window.__QA11_XSS__||0}));}

 const admin=await context('admin','ru'),owner=await context('owner','ru'),guest=await context('guest','az'),changes=[];const ap=admin.p,op=owner.p,gp=guest.p;
 async function save(p,loc){await Promise.all([p.waitForNavigation({waitUntil:'load'}),loc.first().click()]);await p.waitForTimeout(120);}
 for(const kind of ['place','organization','program','specialist']){const pub=kind==='program'?F.urls.az.organization:F.urls.az[kind];await visit(gp,pub);let live=(await head(gp)).h1[0];
 for(const n of [3,4]){const value='Uydurma QA11 '+kind+' Rename '+n;const p=kind==='organization'||kind==='program'?op:ap,path=kind==='organization'?'/ru/account/organizations/1/#org-edit':kind==='program'?'/ru/account/organizations/1/programs/1/':'/admin/catalog/'+kind+'/1/change/';
 await visit(p,path);if(kind==='organization'){const edit=p.locator('[data-org-edit-toggle]');if(await edit.isVisible())await edit.click();else if(!await p.locator('[data-org-edit-form] [name=name_az]').isVisible()){const toggles=p.getByRole('button').filter({hasText:/Изменить|Редактировать|Настройки/});if(await toggles.count())await toggles.first().click();}}
 const field=kind==='organization'?p.locator('[data-org-edit-form] [name=name_az]'):p.locator('[name="'+(kind==='specialist'?'name':'name_az')+'"]').first();if(!await field.isVisible()){add(kind+'-rename-UI',null,{reason:'No accessible editor field for actor; no ORM transition',url:p.url()},kind==='organization'||kind==='program'?'owner':'admin','ru',1440,p.url(),await shot(p,'rename-unavailable-'+kind+'-'+n));break;}
 await field.fill(value);if(kind==='program')await p.locator('[name=impact_confirmed]').check();const btn=kind==='organization'?p.locator('[data-org-edit-form] button[name=submit][value="1"]'):kind==='program'?p.locator('button[name=submit]'):p.locator('[name=_continue]');await save(p,btn);const es=await p.locator('.errorlist,[role=alert]').allTextContents(),ss=await shot(p,'rename-'+kind+'-'+n+'-saved');const hasErrors=await p.locator('.errorlist').count();if(hasErrors){add(kind+'-rename-save',false,{errors:es},kind==='organization'||kind==='program'?'owner':'admin','ru',1440,p.url(),ss);break;}
 await p.reload();add(kind+'-rename-reload',(await field.inputValue())===value,{entered:value,errors:es},kind==='organization'||kind==='program'?'owner':'admin','ru',1440,p.url(),ss);
 if(kind!=='specialist'){await visit(gp,pub);const beforeApproval=await head(gp);add(kind+'-candidate-live-preserved',beforeApproval.h1[0]===live,{before:live,after:beforeApproval.h1[0],head:beforeApproval},'guest','az',1440,pub,await shot(gp,'rename-'+kind+'-'+n+'-candidate-live'));
 if(kind==='place'){await visit(ap,'/admin/catalog/place/?id__exact=1');await ap.locator('[name=_selected_action][value="1"]').check();await ap.locator('[data-bulk-submit=mark_published]').click();const dialog=ap.locator('[role=dialog]:visible');if(await dialog.count()){const confirm=dialog.getByRole('button').filter({hasText:/Опубликовать|Подтвердить/});await save(ap,confirm);}else await ap.waitForLoadState('load');}
 else{await visit(ap,'/admin/catalog/'+kind+'/1/change/');const approve=ap.locator('button[name=action][value=approve]');if(!await approve.isVisible()){add(kind+'-approval',null,{reason:'No pending approval button',errors:await ap.locator('.errorlist,.messagelist').allTextContents()},'admin','ru',1440,ap.url(),await shot(ap,'rename-'+kind+'-approval-unavailable'));break;}await save(ap,approve);}
 }
 await visit(gp,pub);const h=await head(gp);const after=await shot(gp,'rename-'+kind+'-'+n+'-live');add(kind+'-approved-stable-canonical',gp.url()===B+pub&&h.canonical===B+pub&&(kind==='program'?(await gp.locator('body').innerText()).includes(value):h.h1[0]===value),{head:h,value,originalURL:pub},'guest','az',1440,gp.url(),after);live=h.h1[0];changes.push({kind,n,value,originalURL:pub,finalURL:gp.url(),head:h});
 for(const lang of ['ru','az','en']){const target=kind==='program'?F.urls[lang].organization:F.urls[lang][kind];const r=await gp.request.get(B+target+'?foreign=qa11',{maxRedirects:0});add(kind+'-rename-query-redirect',r.status()===301,{status:r.status(),location:r.headers().location},'guest',lang,1440,target);await visit(gp,target);add(kind+'-rename-link-resolves',gp.url()===B+target,{canonical:(await head(gp)).canonical},'guest',lang,1440,gp.url());}
 }}await admin.c.close();await owner.c.close();await guest.c.close();return{rows,changes};
}
