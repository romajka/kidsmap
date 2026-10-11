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

const network=[],consoleErrors=[];async function db(c){return(await c.request.get(B+'/qa/state/')).json();}
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
 const{c,p}=await context('owner',lang,width),lp=prefix(lang),before=await db(c);
 p.on('pageerror',e=>consoleErrors.push({lang,width,error:String(e)}));p.on('response',r=>{if(r.status()>=400&&new URL(r.url()).hostname==='localhost')network.push({lang,width,status:r.status(),url:r.url()});});
 for(const[state,id]of [['filled',1],['empty',2]]){
  const url=lp+'/account/places/'+id+'/analytics/',st=await visit(p,url),vals=await p.locator('.owner-analytics__grid article strong').allTextContents(),expected=['views','unique_visitors','favorites','contact_actions','directions'].map(k=>String(before.metrics[String(id)][k]));const g=await geometry(p),s=await shot(p,'owner-'+state+'-'+lang+'-'+width);
  add('owner-'+state+'-render',st===200,{http:st,values:vals},'owner',lang,width,p.url(),s);add('owner-'+state+'-db-ui-consistency',JSON.stringify(vals.map(x=>x.trim()))===JSON.stringify(expected),{actual:vals,expected},'owner',lang,width,p.url(),s);add('owner-'+state+'-geometry',g.document<=width+1,{geometry:g},'owner',lang,width,p.url(),s);
  if(state==='filled'){const small=await p.locator('.owner-analytics__grid small').allTextContents();add('owner-delta-language',lang!=='az'||!small.some(x=>x.includes('к прошлому периоду')),{text:small},'owner',lang,width,p.url(),s);}
 }
 await p.keyboard.press('Tab');const focus=await p.evaluate(()=>{const e=document.activeElement,s=getComputedStyle(e);return{tag:e.tagName,text:e.textContent.trim().slice(0,80),outline:s.outlineStyle,width:s.outlineWidth,shadow:s.boxShadow};});add('owner-tab-focus',focus.tag!=='BODY'&&(focus.outline!=='none'||focus.shadow!=='none'),{focus},'owner',lang,width,p.url());await p.keyboard.press('Shift+Tab');await p.keyboard.press('Escape');
 await p.goto('http://localhost:8830'+lp+'/account/places/1/analytics/');const dis=await shot(p,'owner-disabled-'+lang+'-'+width);add('owner-disabled-notice',await p.locator('.owner-analytics__notice').isVisible()&&await p.locator('.owner-analytics__grid').count()===0,{profile:'deliberate guard E103 silenced',SIMULATED:true},'owner',lang,width,p.url(),dis);
 await c.close();
 const ad=await context('admin',lang,width);
 for(const mode of ['disabled','filled','error']){
  const url='/admin/catalog/siteanalytics/?period=90'+(mode==='disabled'?'':'&qa_ga='+mode);const st=await visit(ad.p,url),g=await geometry(ad.p),s=await shot(ad.p,'admin-'+mode+'-'+lang+'-'+width),kpi=(await ad.p.locator('[data-kpi-value]').allTextContents()).map(x=>x.trim()),text=await ad.p.locator('body').innerText();
  add('admin-'+mode+'-render',st===200,{http:st,kpi,SIMULATED:mode!=='disabled'},'admin',lang,width,ad.p.url(),s);add('admin-'+mode+'-geometry',g.document<=width+1,{geometry:g,SIMULATED:mode!=='disabled'},'admin',lang,width,ad.p.url(),s);
  if(mode==='filled'){add('admin-90-range',kpi[0]!=='3650',{actual:kpi,period:90,mapped:'year',SIMULATED:true},'admin',lang,width,ad.p.url(),s);add('admin-chart-table-render',await ad.p.locator('#km-visits-chart').isVisible()&&await ad.p.locator('.km-top-places-table tbody tr').count()===1,{SIMULATED:true,chart:JSON.parse(await ad.p.locator('#km-visits-chart-data').textContent())},'admin',lang,width,ad.p.url(),s);}
  if(mode==='error')add('admin-backend-error-visible',text.includes('SIMULATED report backend unavailable'),{actualKpi:kpi,errorMessageVisible:text.includes('SIMULATED report backend unavailable'),SIMULATED:true},'admin',lang,width,ad.p.url(),s);
 }
 await ad.p.locator('[data-period="7"]').focus();await ad.p.keyboard.press('Enter');await ad.p.waitForLoadState('domcontentloaded');add('period-keyboard-enter',new URL(ad.p.url()).searchParams.get('period')==='7',{},'admin',lang,width,ad.p.url());await ad.p.keyboard.press('Tab');await ad.p.keyboard.press('Shift+Tab');await ad.p.keyboard.press('Escape');await ad.c.close();
 const guest=await context('guest',lang,width);const gb=await db(guest.c),st=await visit(guest.p,F.urls[lang].place),ga=await db(guest.c),s=await shot(guest.p,'public-card-'+lang+'-'+width),g=await geometry(guest.p);add('public-view-delta',ga.metrics['1'].views-gb.metrics['1'].views===1,{delta:ga.metrics['1'].views-gb.metrics['1'].views,before:gb.metrics['1'],after:ga.metrics['1']},'guest',lang,width,guest.p.url(),s);add('public-geometry',g.document<=width+1,{geometry:g},'guest',lang,width,guest.p.url(),s);await guest.c.close();
}
return{rows,consoleErrors,network,coverage:{languages:['ru','az','en'],widths:[360,390,768,1024,1280,1440],native:true,GA:'SIMULATED filled/error; real external NOT RUN'}};
}
