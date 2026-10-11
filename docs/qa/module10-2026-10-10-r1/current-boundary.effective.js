async original=>{
 const F={
  "actors": {
    "owner": {
      "id": 1,
      "username": "qa10_owner",
      "email": "owner10@example.invalid"
    },
    "staff": {
      "id": 2,
      "username": "qa10_staff",
      "email": "staff10@example.invalid"
    },
    "admin": {
      "id": 3,
      "username": "qa10_admin",
      "email": "admin10@example.invalid"
    },
    "outsider": {
      "id": 4,
      "username": "qa10_outsider",
      "email": "outsider10@example.invalid"
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
  "organization_public_id": "6911adc9-9ea0-4fc9-8112-e06ce2db1238",
  "urls": {
    "ru": {
      "place": "/ru/place/1-vymyshlennoe-qa10-live/",
      "specialist": "/ru/specialists/fictional-qa10-specialist/",
      "event": "/ru/event/1-uydurma-qa10-tedbir/",
      "organization": "/ru/organizations/6911adc9-9ea0-4fc9-8112-e06ce2db1238/"
    },
    "az": {
      "place": "/place/1-uydurma-qa10-live/",
      "specialist": "/specialists/fictional-qa10-specialist/",
      "event": "/event/1-uydurma-qa10-tedbir/",
      "organization": "/organizations/6911adc9-9ea0-4fc9-8112-e06ce2db1238/"
    },
    "en": {
      "place": "/en/place/1-fictional-qa10-live/",
      "specialist": "/en/specialists/fictional-qa10-specialist/",
      "event": "/en/event/1-uydurma-qa10-tedbir/",
      "organization": "/en/organizations/6911adc9-9ea0-4fc9-8112-e06ce2db1238/"
    }
  },
  "settings": 1,
  "synthetic_only": true
},B='http://localhost:8825',ROOT='C:/kidsmap/docs/qa/module10-2026-10-10-r1',ASSET='C:/kidsmap/.tmp/module10-20261010-r1/assets',rows=[],changes=[],diagnostics=[];
const br=original.context().browser();
function add(scenario,ok,detail={},role='guest',lang='ru',width=1440,url='',shot=''){rows.push({scenario,status:ok===null?'NOT RUN':ok?'PASS':'FAIL',role,lang,width,url,shot,...detail});}
function prefix(lang){return lang==='az'?'':('/'+lang);}
async function context(role='guest',lang='ru',width=1440){
 const c=await br.newContext({viewport:{width,height:950}});await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());
 await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);const p=await c.newPage();p.setDefaultTimeout(8000);p.setDefaultNavigationTimeout(15000);
 if(role!=='guest'){await p.goto(B+'/ru/auth/login/');await p.locator('input[name=username]').fill(F.actors[role].email);await p.locator('input[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForTimeout(180);await c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);}
 return{c,p};
}
async function state(p){return(await p.request.get(B+'/qa/state/')).json();}
async function shot(p,name){const file='screenshots/current-'+name+'.png';await p.screenshot({path:ROOT+'/'+file,fullPage:true,animations:'disabled'});return file;}
async function visit(p,path){const r=await p.goto(B+path);await p.waitForTimeout(100);return r.status();}
async function geometry(p){return p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflow:Array.from(document.querySelectorAll('h1,h2,h3,p,label,button,input,select,textarea,.km-header-inner,.footer-inner,.km-media-row')).map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.trim().slice(0,70),r:e.getBoundingClientRect()})).filter(x=>x.r.width&&x.r.left>=0&&x.r.right>innerWidth+2).slice(0,12).map(x=>({...x,r:{left:x.r.left,right:x.r.right,width:x.r.width}}))}));}
async function saveSettings(p,section,values,label){
 await visit(p,'/admin/catalog/'+section+'/1/change/');const before=(await state(p)).settings;
 for(const [field,value] of Object.entries(values)){const control=p.locator('[name="'+field+'"]');if(typeof value==='boolean')await control.setChecked(value);else await control.fill(String(value));}
 await p.locator('button[name=_continue]').click();await p.waitForTimeout(180);
 const after=(await state(p)).settings;const file=await shot(p,'settings-'+label);add('native-save-'+label,Object.entries(values).every(([k,v])=>after[k]===(typeof v==='string'?v.trim():v)),{values,stored:Object.fromEntries(Object.keys(values).map(k=>[k,after[k]])),errors:await p.locator('.errorlist').allTextContents()},'admin','ru',1440,p.url(),file);
 changes.push({label,section,method:'native admin form POST',before:Object.fromEntries(Object.keys(values).map(k=>[k,before[k]])),after:Object.fromEntries(Object.keys(values).map(k=>[k,after[k]]))});
 await p.reload();for(const [field,value] of Object.entries(values)){const control=p.locator('[name="'+field+'"]');add('native-reload-'+label+'-'+field,typeof value==='boolean'?(await control.isChecked())===value:(await control.inputValue())===String(value).trim(),{},'admin','ru',1440,p.url(),file);}
 return after;
}

 const X={
  "temporary": 6,
  "urls": {
    "ru": "/ru/place/6-vymyshlennoe-qa10-temporary/",
    "az": "/place/6-uydurma-qa10-temporary/",
    "en": "/en/place/6-fictional-qa10-temporary/"
  }
},{c,p}=await context('admin');
 await saveSettings(p,'sitevisibilitysettings',{organizations_section_enabled:false},'current-org-off');await visit(p,'/admin/catalog/organization/2/change/');await p.getByText('Названия',{exact:true}).click();await p.waitForTimeout(450);await p.locator('[name=name_az]').fill('Uydurma QA10 admin: CURRENT OFF candidate');await p.locator('[name=_save_draft]').click();await p.reload();await p.getByText('Названия',{exact:true}).click();await p.waitForTimeout(450);add('current-org-hidden-native-save-reload',await p.locator('[name=name_az]').inputValue()==='Uydurma QA10 admin: CURRENT OFF candidate',{id:2},'admin','ru',1440,p.url(),await shot(p,'current-org-hidden-after'));await saveSettings(p,'sitevisibilitysettings',{organizations_section_enabled:true},'current-org-on');
 const staff=await context('staff');const sr=await visit(staff.p,'/admin/catalog/sitegalleryimage/');add('current-staff-media-page-denied',sr===403,{http:sr,note:'No additional security mutation; prior upload/delete evidence plus unchanged handlers.'},'staff','ru',1440,staff.p.url(),await shot(staff.p,'current-staff-media'));await staff.c.close();
 await saveSettings(p,'sitevisibilitysettings',{events_section_enabled:false},'current-events-off');
 for(const lang of ['ru','az','en']){const{c,p}=await context('guest',lang);for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});for(const [kind,path] of [['list',prefix(lang)+'/events/'],['detail',F.urls[lang].event]]){const http=await visit(p,path),text=(await p.locator('body').innerText()).trim();add('current-disabled-event-readable-'+kind,text.length>0,{http,bodyLength:text.length},'guest',lang,width,p.url(),await shot(p,'current-event-off-'+kind+'-'+lang+'-'+width));}const http=await visit(p,X.urls[lang]);add('current-temporary-direct-hidden',http===404,{http},'guest',lang,width,p.url(),await shot(p,'current-temporary-off-'+lang+'-'+width));const r=await p.goto('http://localhost:8826'+prefix(lang)+'/qa10-no-such-page/');const links=await p.locator('a').count();add('current-404-localized-recovery',r.status()===404&&links>0,{http:r.status(),text:await p.locator('body').innerText(),links},'guest',lang,width,p.url(),await shot(p,'current-404-'+lang+'-'+width));}await c.close();}
 await saveSettings(p,'sitevisibilitysettings',{events_section_enabled:true},'current-events-on');await visit(p,'/admin/catalog/sitegalleryimage/');await p.setViewportSize({width:390,height:950});const row=p.locator('.km-media-row[data-field=logo]'),before=(await state(p)).settings.logo;let wr=p.waitForResponse(r=>r.url().includes('ajax-upload/')&&r.request().method()==='POST');await row.locator('input[type=file]').setInputFiles({name:'qa10-current-bad.png',mimeType:'image/png',buffer:Buffer.from('Synthetic invalid PNG; not an image')});const res=await wr,j=await res.json();await p.reload();const after=(await state(p)).settings.logo;add('current-invalid-image-rejected',!j.success&&after===before,{http:res.status(),success:j.success,before,after},'admin','ru',390,p.url(),await shot(p,'current-invalid-image-admin'));
 const pub=await c.newPage();await visit(pub,'/ru/');add('current-invalid-image-public-logo-preserved',await pub.locator('.km-brand-logo').first().evaluate(e=>e.complete&&e.naturalWidth>0),{},'guest','ru',390,pub.url(),await shot(pub,'current-invalid-image-public'));wr=p.waitForResponse(r=>r.url().includes('ajax-upload/')&&r.request().method()==='POST');await row.locator('input[type=file]').setInputFiles(ASSET+'/logo.png');await wr;await p.reload();await pub.reload();add('current-logo-native-restored',await pub.locator('.km-brand-logo').first().evaluate(e=>e.complete&&e.naturalWidth>0),{},'guest','ru',390,pub.url(),await shot(pub,'current-logo-restored'));changes.push({label:'current malformed logo then native restore',method:'native chooser',before,after,final:(await state(p)).settings.logo});await c.close();return{rows,changes};
}
