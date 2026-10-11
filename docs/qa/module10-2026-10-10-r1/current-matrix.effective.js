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

 const paths=['/','/about/','/contacts/','/catalog/?q=QA10-NO-MATCH'];
 const publicReads=[];
 for(const lang of ['ru','az','en']){const{c,p}=await context('guest',lang);for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});
 for(const path of paths){const http=await visit(p,prefix(lang)+path),ss=await shot(p,'filled-'+lang+'-'+width+'-'+path.replace(/[^a-z0-9]/gi,'_')),g=await geometry(p),text=await p.locator('body').innerText(),s=(await state(p)).settings;
 add('filled-page-http',http===200,{},'guest',lang,width,p.url(),ss);add('filled-page-no-overflow',g.document<=width+2,{geometry:g},'guest',lang,width,p.url(),ss);
 add('branding-header',await p.locator('.km-brand-title').first().innerText()===s.brand_name,{},'guest',lang,width,p.url(),ss);
 add('footer-updated-email',text.includes(s.footer_email),{},'guest',lang,width,p.url(),ss);add('footer-updated-phone',text.includes(s.footer_phone),{},'guest',lang,width,p.url(),ss);
 if(path==='/'){const copy=await p.locator('.home-hero-copy').innerText();add('hero-saved-title',copy.includes(s['home_title_'+lang]),{},'guest',lang,width,p.url(),ss);add('hero-saved-subtitle',copy.includes(s['home_subtitle_'+lang]),{},'guest',lang,width,p.url(),ss);add('hero-saved-cta',copy.includes(s['home_cta_text_'+lang]),{stored:s['home_cta_text_'+lang],actual:await p.locator('.home-redesign-primary').innerText()},'guest',lang,width,p.url(),ss);add('hero-saved-placeholder',(await p.locator('#home-hero-search-input').getAttribute('placeholder'))===s['home_search_placeholder_'+lang],{stored:s['home_search_placeholder_'+lang],actual:await p.locator('#home-hero-search-input').getAttribute('placeholder')},'guest',lang,width,p.url(),ss);add('hero-saved-search-label',text.includes(s['home_search_label_'+lang]),{},'guest',lang,width,p.url(),ss);add('decor-off',await p.locator('.hero-cloud').count()===0,{},'guest',lang,width,p.url(),ss);
 const imageInfo=await p.evaluate(()=>Array.from(document.querySelectorAll('body,header,footer,.home-hero,.home-hero *')).map(e=>({tag:e.tagName,cls:e.className,bg:getComputedStyle(e).backgroundImage,src:e.getAttribute('src')})).filter(x=>x.bg.includes('url')||x.src));
 const expected=width<768?s.home_hero_mobile_image:s.home_hero_image;add('home-uploaded-background-used',imageInfo.some(x=>(x.bg+' '+x.src).includes(expected)),{expected,imageInfo},'guest',lang,width,p.url(),ss);publicReads.push({lang,width,path,imageInfo});
 }else if(path==='/about/'){const lead=await p.locator('.about-hero-lead').innerText();add('about-saved-text',lead.includes('QA10-ABOUT-'+lang.toUpperCase()),{lead,stored:s['about_text_'+lang]},'guest',lang,width,p.url(),ss);add('footer-about-saved-text',await p.locator('.footer-brand-copy').innerText()===s['about_text_'+lang],{},'guest',lang,width,p.url(),ss);
 }else if(path==='/contacts/'){const main=await p.locator('main').last().innerText();add('contacts-saved-public-text',main.includes('QA10-CONTACT-'+lang.toUpperCase()),{stored:s['contacts_text_'+lang],sample:main.slice(0,380)},'guest',lang,width,p.url(),ss);
 }else{add('empty-saved-text',text.includes('QA10-EMPTY-'+lang.toUpperCase()),{},'guest',lang,width,p.url(),ss);}
 }
 }
 await c.close();}
 for(const lang of ['ru','az','en']){const{c,p}=await context('admin',lang);for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});for(const section of ['sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings']){
 const http=await visit(p,'/admin/catalog/'+section+'/1/change/'),ss=await shot(p,'admin-'+section+'-'+lang+'-'+width),g=await geometry(p);add('admin-render',http===200,{htmlLang:await p.locator('html').getAttribute('lang')},'admin',lang,width,p.url(),ss);add('admin-no-overflow',g.document<=width+2,{geometry:g},'admin',lang,width,p.url(),ss);
 if(section==='sitevisibilitysettings'){const label=await p.locator('label[for=id_events_section_enabled]').innerText(),expected=lang==='ru'?'Показывать «Афишу»':lang==='en'?'Show “Events”':'“Tədbirlər” bölməsini göstər';add('admin-flag-translated-label',label===expected,{label,expected},'admin',lang,width,p.url(),ss);}
 }
 }
 await c.close();}
 return{rows,publicReads};
}
