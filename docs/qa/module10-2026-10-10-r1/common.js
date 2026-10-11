const F=__FIXTURES_JSON__,B='http://localhost:8823',ROOT='C:/kidsmap/docs/qa/module10-2026-10-10-r1',ASSET='C:/kidsmap/.tmp/module10-20261010-r1/assets',rows=[],changes=[],diagnostics=[];
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
