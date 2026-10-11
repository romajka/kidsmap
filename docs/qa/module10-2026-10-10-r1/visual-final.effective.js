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

 const{c,p}=await context('admin');await visit(p,'/admin/catalog/organization/2/change/');await p.getByText('Названия',{exact:true}).click();const organizationControls=await p.locator('[name^=name_], [name=_save_draft]').evaluateAll(es=>es.map(e=>({name:e.name,tag:e.tagName,visible:!!(e.offsetWidth||e.offsetHeight),closest:e.closest('fieldset')?.className,html:e.outerHTML.slice(0,420)})));
 await visit(p,'/admin/catalog/sitegalleryimage/');await p.setViewportSize({width:390,height:950});await p.locator('.km-media-row[data-field=logo] .km-media-delete-btn').click();await p.waitForTimeout(450);const focusables=await p.locator('.km-modal').evaluate(e=>({outer:e.outerHTML.slice(0,5000),active:document.activeElement.outerHTML.slice(0,300),scripts:Array.from(document.scripts).map(x=>x.src).filter(Boolean)}));await p.screenshot({path:ROOT+'/screenshots/modal-final-viewport.png'});await p.keyboard.press('Tab');const focusAfter=await p.evaluate(()=>document.activeElement.outerHTML.slice(0,400));await p.keyboard.press('Escape');await p.waitForTimeout(450);await c.close();
 const contrast=[];function ratio(a,b){function lum(c){const v=c.match(/[\d.]+/g).slice(0,3).map(Number).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4});return v[0]*.2126+v[1]*.7152+v[2]*.0722}const x=lum(a),y=lum(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05)}
 for(const lang of ['ru','az','en']){const{c,p}=await context('guest',lang);for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});await visit(p,prefix(lang)+'/contacts/');const styles=await p.locator('h1').evaluate(e=>{let a=e;const ancestors=[];while(a){const s=getComputedStyle(a);ancestors.push({tag:a.tagName,fg:s.color,bg:s.backgroundColor,image:s.backgroundImage,opacity:s.opacity});a=a.parentElement}return{fg:getComputedStyle(e).color,size:getComputedStyle(e).fontSize,weight:getComputedStyle(e).fontWeight,ancestors}});const bg=styles.ancestors.find(s=>s.bg!=='rgba(0, 0, 0, 0)');const r=bg&&bg.image==='none'?ratio(styles.fg,bg.bg):null;contrast.push({lang,width,...styles,ratio:r});add('contacts-h1-solid-contrast',r===null?null:r>=3,{ratio:r,reason:r===null?'background needs pixel composition':null},'guest',lang,width,p.url());if([390,1440].includes(width)){await p.screenshot({path:ROOT+'/screenshots/contacts-viewport-'+lang+'-'+width+'.png'});await visit(p,prefix(lang)+'/about/');await p.screenshot({path:ROOT+'/screenshots/about-viewport-'+lang+'-'+width+'.png'});await visit(p,prefix(lang)+'/');await p.screenshot({path:ROOT+'/screenshots/home-viewport-'+lang+'-'+width+'.png'});}}
 await c.close();}return{rows,organizationControls,focusables,focusAfter,contrast};
}
