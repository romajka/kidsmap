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

 for(const lang of ['ru','az','en']){const{c,p}=await context('admin',lang);for(const width of [360,390,768,1024,1280,1440]){
 await p.setViewportSize({width,height:950});await visit(p,'/admin/catalog/sitegalleryimage/');const row=p.locator('.km-media-row[data-field=logo]');await row.scrollIntoViewIfNeeded();const before=(await state(p)).settings.logo;
 let release;const gate=new Promise(r=>release=r);await p.route('**/ajax-upload/',async r=>{await gate;await r.abort();});
 await row.locator('input[type=file]').setInputFiles(ASSET+'/replacement.png');await p.waitForTimeout(150);const loading=await row.innerText(),ss=await shot(p,'upload-loading-'+lang+'-'+width);add('upload-loading-disabled',await row.locator('.km-media-upload-btn').isDisabled(),{loading,SIMULATED:'network gated before server'},'admin',lang,width,p.url(),ss);release();await p.waitForTimeout(250);await p.unroute('**/ajax-upload/');
 const unchanged=(await state(p)).settings.logo===before,error=(await p.locator('.km-toast-container').innerText().catch(()=>''));add('upload-network-error-preserves-file',unchanged&&!await row.locator('.km-media-upload-btn').isDisabled()&&error.length>0,{error,SIMULATED:'route.abort no server mutation'},'admin',lang,width,p.url(),await shot(p,'upload-error-'+lang+'-'+width));
 add('upload-loading-language',lang==='ru'||!loading.includes('Загрузка'),{loading},'admin',lang,width,p.url(),ss);
 await row.locator('.km-media-delete-btn').click();await p.waitForTimeout(100);const modal=p.locator('[role=alertdialog],[role=dialog]').filter({has:p.locator('.km-modal__title')}).first();const title=await modal.locator('.km-modal__title').innerText();const ms=await shot(p,'delete-modal-'+lang+'-'+width);add('delete-dialog-language',lang==='ru'||!title.includes('Удалить'),{title},'admin',lang,width,p.url(),ms);
 let trap=true;for(let i=0;i<8;i++){await p.keyboard.press('Tab');trap=trap&&await modal.evaluate(e=>e.contains(document.activeElement));}await p.keyboard.press('Shift+Tab');trap=trap&&await modal.evaluate(e=>e.contains(document.activeElement));add('delete-dialog-keyboard-trap',trap,{},'admin',lang,width,p.url(),ms);await p.keyboard.press('Escape');await p.waitForTimeout(100);add('delete-dialog-escape-preserves-file',!await modal.isVisible()&&(await state(p)).settings.logo===before,{},'admin',lang,width,p.url(),ms);
 }
 await c.close();}
 const {c,p}=await context('admin','ru',390);await visit(p,'/admin/catalog/sitegalleryimage/');const row=p.locator('.km-media-row[data-field=logo]'),before=(await state(p)).settings.logo,wait=p.waitForResponse(r=>r.url().includes('ajax-upload/')&&r.request().method()==='POST');
 await row.locator('input[type=file]').setInputFiles({name:'qa10-bad.png',mimeType:'image/png',buffer:Buffer.from('Synthetic invalid PNG; not an image')});const res=await wait,j=await res.json();await p.waitForTimeout(150);const after=(await state(p)).settings.logo;await p.reload();const saved=row.locator('img');const broken=await saved.evaluate(e=>e.complete&&e.naturalWidth===0);const bs=await shot(p,'invalid-file-saved-admin-mobile');add('invalid-file-rejected',!j.success&&after===before,{http:res.status(),success:j.success,before,after,broken},'admin','ru',390,p.url(),bs);
 const publicP=await c.newPage();await visit(publicP,'/ru/');add('invalid-file-keeps-public-logo',!await publicP.locator('.km-brand-logo').first().evaluate(e=>e.complete&&e.naturalWidth===0),{broken:await publicP.locator('.km-brand-logo').first().evaluate(e=>e.complete&&e.naturalWidth===0)},'guest','ru',390,publicP.url(),await shot(publicP,'invalid-file-public-mobile'));
 // Restore through native upload, then exercise actual delete + replacement and public reload.
 let wr=p.waitForResponse(r=>r.url().includes('ajax-upload/')&&r.request().method()==='POST');await row.locator('input[type=file]').setInputFiles(ASSET+'/logo.png');await wr;await p.reload();await row.locator('.km-media-delete-btn').click();const dialog=p.locator('[role=alertdialog],[role=dialog]').filter({has:p.locator('.km-modal__title')}).first();const buttons=await dialog.locator('button').allTextContents();diagnostics.push({deleteButtons:buttons});await dialog.locator('button').filter({hasText:/^Удалить$/}).click();await p.waitForTimeout(250);add('native-image-delete',!(await state(p)).settings.logo,{},'admin','ru',390,p.url(),await shot(p,'logo-deleted'));await publicP.reload();add('public-logo-fallback-after-delete',(await publicP.locator('.km-brand-logo').first().getAttribute('src')).startsWith('/static/'),{},'guest','ru',390,publicP.url(),await shot(publicP,'logo-deleted-public'));
 await p.reload();wr=p.waitForResponse(r=>r.url().includes('ajax-upload/')&&r.request().method()==='POST');await row.locator('input[type=file]').setInputFiles(ASSET+'/logo.png');await wr;await p.reload();await publicP.reload();add('logo-replacement-reload',await publicP.locator('.km-brand-logo').first().evaluate(e=>e.complete&&e.naturalWidth>0),{},'guest','ru',390,publicP.url(),await shot(publicP,'logo-restored-public'));
 changes.push({label:'logo invalid / restore / native delete / native restore',method:'native file chooser and confirm modal',before,final:(await state(p)).settings.logo});
 await c.close();return{rows,changes,diagnostics};
}
