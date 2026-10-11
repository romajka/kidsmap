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
},B='http://localhost:8823',ROOT='C:/kidsmap/docs/qa/module10-2026-10-10-r1',ASSET='C:/kidsmap/.tmp/module10-20261010-r1/assets',rows=[],changes=[],diagnostics=[];
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
async function shot(p,name){const file='screenshots/'+name+'.png';await p.screenshot({path:ROOT+'/'+file,fullPage:true,animations:'disabled'});return file;}
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

 const admin=await context('admin'),bytes=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==','base64');
 for(const role of ['guest','owner','outsider','staff']){
  const{c,p}=await context(role);await visit(p,'/ru/auth/login/');const r=await p.goto(B+'/admin/catalog/sitegalleryimage/');const ss=await shot(p,'acl-media-page-'+role);add('media-page-permission-'+role,role==='staff'?r.status()===403:p.url().includes('/admin/login/'),{http:r.status()},role,'ru',1440,p.url(),ss);
  const token=(await c.cookies()).find(x=>x.name==='module10_r1_csrf')?.value;const before=(await state(p)).settings.logo;
  const noCsrf=await p.request.post(B+'/admin/catalog/sitegalleryimage/ajax-upload/',{multipart:{field:'logo',image:{name:'qa10-no-csrf.png',mimeType:'image/png',buffer:bytes}},maxRedirects:0});add('media-no-csrf-'+role,noCsrf.status()===403&&(await state(p)).settings.logo===before,{http:noCsrf.status()},role,'ru',1440,B+'/admin/catalog/sitegalleryimage/ajax-upload/',ss);
  const post=await p.request.post(B+'/admin/catalog/sitegalleryimage/ajax-upload/',{headers:{'X-CSRFToken':token||''},multipart:{field:'logo',image:{name:'qa10-'+role+'.png',mimeType:'image/png',buffer:bytes}},maxRedirects:0});const after=(await state(p)).settings.logo;
  add('media-upload-without-permission-'+role,post.status()!==200&&before===after,{http:post.status(),before,after,method:'negative direct HTTP via native browser context; no ORM mutation'},role,'ru',1440,B+'/admin/catalog/sitegalleryimage/ajax-upload/',ss);
  if(after!==before){const pub=await c.newPage();await visit(pub,'/ru/');const ps=await shot(pub,'acl-public-logo-'+role);add('unauthorized-public-effect-'+role,false,{src:await pub.locator('.km-brand-logo').first().getAttribute('src'),http:post.status()},role,'ru',1440,pub.url(),ps);await pub.close();}
  const del=await p.request.post(B+'/admin/catalog/sitegalleryimage/ajax-delete-main-image/',{headers:{'X-CSRFToken':token||''},form:{field:'logo'},maxRedirects:0});const deleted=(await state(p)).settings.logo;
  add('media-delete-without-permission-'+role,del.status()!==200&&deleted===after,{http:del.status(),before:after,after:deleted,method:'negative direct HTTP via native browser context'},role,'ru',1440,B+'/admin/catalog/sitegalleryimage/ajax-delete-main-image/',ss);
  if(deleted!==before){await visit(admin.p,'/admin/catalog/sitegalleryimage/');const wait=admin.p.waitForResponse(r=>r.url().includes('ajax-upload/')&&r.request().method()==='POST');await admin.p.locator('.km-media-row[data-field=logo] input[type=file]').setInputFiles(ASSET+'/logo.png');await wait;await admin.p.reload();add('admin-native-restore-after-ACL-probe',(await state(admin.p)).settings.logo.includes('logo'),{},'admin','ru',1440,admin.p.url(),await shot(admin.p,'acl-native-restored'));changes.push({label:'ACL probe '+role+' / native admin restore',before,after:deleted,final:(await state(admin.p)).settings.logo});}
  await c.close();
 }
 await admin.c.close();return{rows,changes};
}
