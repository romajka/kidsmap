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

 const L={
  "specialist": 2,
  "event": 2,
  "initial_only": true
},{c,p}=await context('admin');
 for(const [section,field,marker] of [['siteaboutsettings','about_text','ABOUT'],['sitecontactssettings','contacts_text','CONTACT'],['siteemptystatesettings','empty_results_text','EMPTY']]){await visit(p,'/admin/catalog/'+section+'/1/change/');await p.reload();const s=(await state(p)).settings;for(const lang of ['ru','az','en'])add('trimmed-settings-reload-'+field,(await p.locator('[name='+field+'_'+lang+']').inputValue())===s[field+'_'+lang]&&s[field+'_'+lang].startsWith('QA10-'+marker+'-'+lang.toUpperCase()),{},'admin','ru',1440,p.url(),await shot(p,'readback-'+field+'-'+lang));}
 await visit(p,'/admin/catalog/sitevisibilitysettings/1/change/');await p.locator('[name=public_favorites_count_enabled]').check();await p.locator('[name=public_favorites_minimum]').fill('');await p.locator('button[name=_continue]').click();await p.waitForTimeout(150);add('favorites-conditional-error',!(await state(p)).settings.public_favorites_count_enabled&&(await p.locator('.errorlist').count())>0&&await p.locator('[name=public_favorites_count_enabled]').isChecked(),{errors:await p.locator('.errorlist').allTextContents()},'admin','ru',1440,p.url(),await shot(p,'favorite-threshold-error'));
 await p.locator('[name=public_favorites_minimum]').fill('1');await p.locator('button[name=_continue]').click();await p.waitForTimeout(150);add('favorites-error-corrected',(await state(p)).settings.public_favorites_count_enabled&&(await state(p)).settings.public_favorites_minimum===1,{},'admin','ru',1440,p.url(),await shot(p,'favorite-threshold-corrected'));changes.push({label:'public favorites activation error then threshold1',method:'native settings POST',final:(await state(p)).settings.public_favorites_minimum});
 for(const lang of ['ru','az','en'])for(const width of [390,1440]){await p.setViewportSize({width,height:950});await visit(p,F.urls[lang].place);add('public-favorites-on',await p.locator('.favorite-social-proof').count()>0,{text:await p.locator('.favorite-social-proof').allTextContents()},'guest',lang,width,p.url(),await shot(p,'favorite-proof-'+lang+'-'+width));}
 await p.setViewportSize({width:1440,height:950});await saveSettings(p,'sitevisibilitysettings',{public_favorites_count_enabled:false},'favorite-counter-off');
 const old=(await state(p)).settings;await saveSettings(p,'sitebrandingsettings',{home_title_en:''},'empty-en-title');const g=await context('guest','en',390);await visit(g.p,'/en/');const text=await g.p.locator('.home-hero-copy h1').innerText();add('blank-translation-fallback-not-saved',text.length>0&&!text.includes(old.home_title_ru)&&(await state(g.p)).settings.home_title_en==='',{display:text,stored:''},'guest','en',390,g.p.url(),await shot(g.p,'fallback-en-home'));await saveSettings(p,'sitebrandingsettings',{home_title_en:old.home_title_en},'restore-en-title');await g.c.close();
 const owner=await context('owner');for(const [kind,id] of [['specialist',L.specialist],['event',L.event]])for(const enabled of [false,true]){await saveSettings(p,'sitevisibilitysettings',{[kind==='event'?'events_section_enabled':'specialists_section_enabled']:enabled},'lawful-'+kind+'-'+enabled);const status=await visit(owner.p,'/ru/account/places/'+(kind==='event'?'events':'specialists')+'/'+id+'/edit/');add('lawful-owner-flag-'+kind,status===(enabled?200:404),{http:status,enabled},'owner','ru',1440,owner.p.url(),await shot(owner.p,'lawful-owner-'+kind+'-'+enabled));}
 for(const enabled of [false,true]){await saveSettings(p,'sitevisibilitysettings',{organizations_section_enabled:enabled},'org-editor-'+enabled);await visit(p,'/admin/catalog/organization/'+F.organization+'/change/');add('organization-custom-editor-available',await p.locator('button[name=_save_draft]').count()>0&&await p.locator('[name=name_az]').isEnabled(),{enabled,buttons:await p.locator('button[type=submit]').allTextContents()},'admin','ru',1440,p.url(),await shot(p,'org-custom-editor-'+enabled));}
 await visit(p,'/admin/catalog/sitefootersettings/1/change/');await p.locator('[name=footer_email]').fill('invalid');await p.locator('button[name=_continue]').click();await p.waitForTimeout(120);add('invalid-email-rejected',(await p.locator('.errorlist').count())>0&&(await state(p)).settings.footer_email===old.footer_email,{errors:await p.locator('.errorlist').allTextContents()},'admin','ru',1440,p.url(),await shot(p,'footer-email-error'));
 await p.locator('[name=footer_email]').fill(old.footer_email);await p.locator('[name=footer_telegram]').fill('not-a-url');await p.locator('button[name=_continue]').click();await p.waitForTimeout(120);add('invalid-url-rejected',(await p.locator('.errorlist').count())>0&&(await state(p)).settings.footer_telegram===old.footer_telegram,{errors:await p.locator('.errorlist').allTextContents()},'admin','ru',1440,p.url(),await shot(p,'footer-url-error'));
 await visit(p,'/admin/catalog/sitefootersettings/1/change/');await p.locator('[name=footer_email]').fill('unsaved10@example.invalid');await p.route('**/sitefootersettings/1/change/',r=>r.request().method()==='POST'?r.abort():r.continue());await p.locator('button[name=_continue]').click().catch(()=>{});await p.waitForTimeout(150);await p.unroute('**/sitefootersettings/1/change/');add('aborted-settings-post-no-false-save',(await state(p)).settings.footer_email===old.footer_email,{SIMULATED:'browser route.abort before server'},'admin','ru',1440,p.url(),await shot(p,'settings-network-error'));await p.goBack().catch(()=>{});const control=p.locator('[name=footer_email]');add('aborted-settings-input-recovery',await control.count()>0&&(await control.inputValue())==='unsaved10@example.invalid',{method:'browser Back after simulated network abort'},'admin','ru',1440,p.url(),await shot(p,'settings-network-back'));await p.reload();
 await owner.c.close();await c.close();return{rows,changes};
}
