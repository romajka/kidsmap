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

 const contrasts=[];
 for(const lang of ['ru','az','en']){const{c,p}=await context('guest',lang);for(const width of [360,390,768,1024,1280,1440]){
  await p.setViewportSize({width,height:950});await visit(p,prefix(lang)+'/catalog/?q=QA10&category=EDU');const lb=p.locator('.km-lang-btn'),next=lang==='ru'?'az':lang==='az'?'en':'ru';let option;
  if(await lb.isVisible()){await lb.focus();await p.keyboard.press('Space');await p.waitForTimeout(80);add('language-menu-space',await lb.getAttribute('aria-expanded')==='true',{},'guest',lang,width,p.url(),await shot(p,'language-open-'+lang+'-'+width));await p.keyboard.press('Escape');add('language-menu-escape',await lb.getAttribute('aria-expanded')==='false'&&await lb.evaluate(e=>document.activeElement===e),{},'guest',lang,width,p.url());await lb.press('Enter');option=p.locator('.km-lang-option[hreflang='+next+']');}
  else{await p.locator('#km-burger-open').press('Enter');option=p.locator('.km-drawer-lang-btn[hreflang='+next+']');await option.scrollIntoViewIfNeeded();await shot(p,'language-open-'+lang+'-'+width);}
  const href=await option.getAttribute('href');const navigation=p.waitForURL(u=>u.pathname===prefix(next)+'/catalog/',{waitUntil:'load'});await option.click();await navigation;const u=new URL(p.url());add('native-language-retains-page-params',u.pathname===prefix(next)+'/catalog/'&&u.searchParams.get('q')==='QA10'&&u.searchParams.get('category')==='EDU'&&await p.locator('html').getAttribute('lang')===next,{href,url:p.url()},'guest',lang,width,p.url(),await shot(p,'language-switched-'+lang+'-'+width));
  await visit(p,prefix(lang)+'/faq/');const burger=p.locator('#km-burger-open');
  if(await burger.isVisible()){await burger.focus();await p.keyboard.press('Enter');await p.waitForTimeout(120);const drawer=p.locator('#km-mobile-drawer');add('mobile-menu-enter',await drawer.getAttribute('aria-hidden')==='false',{},'guest',lang,width,p.url(),await shot(p,'mobile-menu-'+lang+'-'+width));let trapped=true;for(let i=0;i<30;i++){await p.keyboard.press('Tab');trapped=trapped&&await p.evaluate(()=>!!document.activeElement.closest('#km-mobile-drawer'));}await p.keyboard.press('Shift+Tab');trapped=trapped&&await p.evaluate(()=>!!document.activeElement.closest('#km-mobile-drawer'));add('mobile-menu-tab-trap',trapped,{},'guest',lang,width,p.url());await p.keyboard.press('Escape');add('mobile-menu-escape-focus',await drawer.getAttribute('aria-hidden')==='true'&&await burger.evaluate(e=>document.activeElement===e),{},'guest',lang,width,p.url());
  }else{const about=p.locator('.km-nav-desktop [data-dropdown-trigger]');await about.focus();await about.press('Space');add('desktop-about-space',await about.getAttribute('aria-expanded')==='true',{},'guest',lang,width,p.url(),await shot(p,'desktop-menu-'+lang+'-'+width));await p.keyboard.press('Escape');add('desktop-about-escape',await about.getAttribute('aria-expanded')==='false'&&await about.evaluate(e=>document.activeElement===e),{},'guest',lang,width,p.url());}
  const faq=p.locator('details summary');if(await faq.count()){await faq.first().focus();await faq.first().press('Space');add('faq-keyboard-space',await faq.first().evaluate(e=>e.parentElement.open),{},'guest',lang,width,p.url(),await shot(p,'faq-open-'+lang+'-'+width));await faq.first().press('Enter');add('faq-keyboard-enter',!await faq.first().evaluate(e=>e.parentElement.open),{},'guest',lang,width,p.url());}else add('faq-details-contract',null,{reason:'FAQ uses another implemented widget; checked separately'},'guest',lang,width,p.url());
  await p.locator('footer').scrollIntoViewIfNeeded();await p.waitForTimeout(150);add('footer-native-visible',await p.locator('footer').isVisible(),{},'guest',lang,width,p.url(),await shot(p,'footer-'+lang+'-'+width));
  const rgb=await p.locator('.footer-contact-val').first().evaluate(e=>({fg:getComputedStyle(e).color,bg:getComputedStyle(e.closest('footer')).backgroundColor,font:getComputedStyle(e).fontSize}));contrasts.push({lang,width,...rgb});
  const btt=p.locator('.km-back-to-top');if(await btt.isVisible()){const g=await btt.boundingBox();add('fixed-back-to-top-in-viewport',g.x>=0&&g.x+g.width<=width+2&&g.y>=0&&g.y+g.height<=950,{box:g},'guest',lang,width,p.url());await btt.focus();await btt.press('Enter');await p.waitForFunction(()=>scrollY<50,null,{timeout:3000}).catch(()=>{});add('back-to-top-enter',await p.evaluate(()=>scrollY)<50,{},'guest',lang,width,p.url());}
  await visit(p,prefix(lang)+'/contacts/');await p.evaluate(()=>document.documentElement.style.zoom='2');await p.waitForTimeout(120);const zg=await geometry(p);add('200-percent-zoom-no-document-overflow',zg.document<=width+2,{geometry:zg,method:'Chromium CSS zoom 2; not device/browser chrome zoom'},'guest',lang,width,p.url(),await shot(p,'zoom-contacts-'+lang+'-'+width));await p.evaluate(()=>document.documentElement.style.zoom='');
  const local=p.locator('a[href="'+prefix(lang)+'/catalog/"]').last();await local.focus();await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');const focused=await local.evaluate(e=>document.activeElement===e),style=await local.evaluate(e=>({outline:getComputedStyle(e).outlineStyle,width:getComputedStyle(e).outlineWidth,shadow:getComputedStyle(e).boxShadow}));add('keyboard-tab-shift-focus',focused,{style},'guest',lang,width,p.url(),await shot(p,'focus-'+lang+'-'+width));
 }
 await c.close();}
 // Same WORKTREE, separate QA10 DEBUG=False process; generic error body is runtime evidence, not DEBUG traceback.
 const {c,p}=await context('guest');for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});const r=await p.goto('http://localhost:8824'+prefix(lang)+'/qa10-no-such-page/');const g=await geometry(p),text=await p.locator('body').innerText();const ss=await shot(p,'404-debug-false-'+lang+'-'+width);add('404-debug-false-status',r.status()===404,{text,htmlLang:await p.locator('html').getAttribute('lang'),geometry:g},'guest',lang,width,p.url(),ss);add('404-debug-false-no-overflow',g.document<=width+2,{geometry:g},'guest',lang,width,p.url(),ss);add('404-recovery-link',await p.locator('a').count()>0,{text},'guest',lang,width,p.url(),ss);}
 await c.close();return{rows,contrasts};
}
