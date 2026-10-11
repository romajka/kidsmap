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
async function visit(p,path){const r=await p.goto(B+path);await p.waitForTimeout(120);return r.status();}
async function geometry(p){return p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflow:[...document.querySelectorAll('h1,h2,h3,p,label,button,input,select,textarea,.km-header-inner,.footer-inner')].map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.trim().slice(0,70),r:e.getBoundingClientRect()})).filter(x=>x.r.width&&x.r.left>=0&&x.r.right>innerWidth+2).slice(0,10).map(x=>({...x,r:{left:x.r.left,right:x.r.right,width:x.r.width}}))}));}
async function head(p){return p.evaluate(()=>({title:document.title,h1:[...document.querySelectorAll('h1')].map(e=>e.textContent.trim()),description:document.querySelector('meta[name=description]')?.content,ogTitle:document.querySelector('meta[property="og:title"]')?.content,ogDescription:document.querySelector('meta[property="og:description"]')?.content,ogImage:document.querySelector('meta[property="og:image"]')?.content,twTitle:document.querySelector('meta[name="twitter:title"]')?.content,canonical:document.querySelector('link[rel=canonical]')?.href,robots:document.querySelector('meta[name=robots]')?.content,alternates:[...document.querySelectorAll('link[hreflang]')].map(e=>({lang:e.hreflang,href:e.href})),jsonld:[...document.querySelectorAll('script[type="application/ld+json"]')].map(e=>{try{return JSON.parse(e.textContent)}catch{return {parseError:true}}}),xss:window.__QA11_XSS__||0}));}

 for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){const {c,p}=await context('guest',lang,width);await p.bringToFront();const consoleErrors=[],pageErrors=[],external=[];p.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});p.on('pageerror',e=>pageErrors.push(e.message));p.on('requestfailed',r=>external.push({url:r.url(),error:r.failure()?.errorText}));await visit(p,F.urls[lang].place);await p.waitForTimeout(500);
 const mobile=await p.locator('#km-burger-open').isVisible(),trigger=mobile?'#km-burger-open':'.km-lang-btn';let reached=false;const focusTrail=[];
 for(let n=0;n<30;n++){await p.keyboard.press('Tab');const f=await p.evaluate(()=>{const e=document.activeElement,s=getComputedStyle(e),r=e.getBoundingClientRect();return{tag:e.tagName,id:e.id,cls:e.className,label:e.getAttribute('aria-label'),outline:s.outline,shadow:s.boxShadow,x:r.x,y:r.y,w:r.width,h:r.height,visible:!!e.getClientRects().length}});focusTrail.push(f);if(await p.locator(trigger).evaluate(e=>e===document.activeElement)){reached=true;break;}}
 add('Tab-reaches-language-navigation',reached,{focusTrail},'guest',lang,width,p.url());if(!reached){await c.close();continue;}
 const fs=await shot(p,'focus-'+lang+'-'+width);const last=focusTrail.at(-1);add('visible-keyboard-focus',last.visible&&(last.outline&&!last.outline.startsWith('none')||last.shadow&&last.shadow!=='none'),{focus:last},'guest',lang,width,p.url(),fs);
 await p.keyboard.press('Space');await p.waitForTimeout(450);const open=mobile?(await p.locator('#km-mobile-drawer').getAttribute('aria-hidden'))==='false':await p.locator('.km-dropdown-lang').isVisible();const os=await shot(p,'menu-open-'+lang+'-'+width);add('Space-opens-menu',open,{},'guest',lang,width,p.url(),os);
 const trail=[];for(const key of ['Tab','Tab','Shift+Tab']){await p.keyboard.press(key);trail.push(await p.evaluate(()=>{const e=document.activeElement;return {key:e.tagName,id:e.id,text:e.textContent.trim().slice(0,50),inModal:!!e.closest('#km-mobile-drawer'),visible:!!e.getClientRects().length}}));}
 add('menu-Tab-ShiftTab',trail.every(x=>x.visible)&&(!mobile||trail.every(x=>x.inModal)),{trail},'guest',lang,width,p.url(),os);
 await p.keyboard.press('Escape');await p.waitForTimeout(450);add('Escape-closes-restores-focus',mobile?(await p.locator('#km-mobile-drawer').getAttribute('aria-hidden'))==='true':!await p.locator('.km-dropdown-lang').isVisible(),{focus:await p.evaluate(()=>({id:document.activeElement.id,cls:document.activeElement.className}))},'guest',lang,width,p.url(),fs);
 await p.locator(trigger).press('Enter');await p.waitForTimeout(400);const target=lang==='en'?'az':lang==='az'?'ru':'en',href=B+F.urls[target].place;const option=mobile?p.locator('.km-drawer-lang-btn').filter({has:p.locator('span.km-lang-opt-code')}).first():p.locator('.km-lang-option');
 const selector=mobile?'.km-drawer-lang-btn[href="'+href+'"]':'.km-lang-option[href="'+href+'"]';await Promise.all([p.waitForURL(href,{waitUntil:'load'}),p.locator(selector).click()]);await p.waitForTimeout(250);const switched=(await p.locator('html').getAttribute('lang'))===target&&p.url()===href;await p.reload();const ss=await shot(p,'language-after-reload-'+lang+'-'+width);add('native-language-switch-reload',switched&&p.url()===href,{target,head:await head(p)},'guest',lang,width,p.url(),ss);
 await p.locator('footer').scrollIntoViewIfNeeded();await p.waitForTimeout(650);const footer=await p.locator('footer').evaluate(e=>({opacity:getComputedStyle(e).opacity,visibility:getComputedStyle(e).visibility,r:e.getBoundingClientRect().toJSON(),text:e.innerText.slice(0,80)}));const bs=await shot(p,'footer-scrolled-'+lang+'-'+width);add('rendered-footer-after-scroll',footer.opacity!=='0'&&footer.visibility==='visible'&&footer.r.height>0,{footer},'guest',lang,width,p.url(),bs);
 add('browser-console-local-runtime',pageErrors.length===0&&!consoleErrors.some(x=>!x.includes('ERR_FAILED')),{pageErrors,consoleErrors,external},'guest',lang,width,p.url(),bs);if(external.length)add('console-external-route-abort',null,{classification:'SIMULATED transport; external integration NOT RUN',external},'guest',lang,width,p.url(),bs);
 await c.close();}return{rows};
}
