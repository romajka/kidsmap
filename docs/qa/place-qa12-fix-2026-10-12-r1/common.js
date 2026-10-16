const F=__FIXTURES__,B='__BASE__',ROOT='__HERE__',SCRATCH='__SCRATCH__',rows=[],errors=[],network=[],consoleEvents=[];
const br=original.context().browser();
function add(id,ok,detail={},role='owner',lang='ru',width=1440){rows.push({id,status:ok===null?'NOT RUN':ok?'PASS':'FAIL',role,lang,width,...detail});}
function prefix(l){return l==='az'?'':'/'+l;}
async function context(role='owner',lang='ru',width=1440){
 const c=await br.newContext({viewport:{width,height:950},reducedMotion:'reduce'});await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(12000);p.on('pageerror',e=>errors.push(String(e)));p.on('console',e=>{if(['error','warning'].includes(e.type()))consoleEvents.push({type:e.type(),text:e.text().slice(0,400),source:e.location().url});});p.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)network.push({url:r.url().slice(B.length).split('?')[0],status:r.status()});});p.on('dialog',d=>d.accept());
 if(role!=='guest'){await p.goto(B+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill(role==='admin'?'__ADMIN_PASSWORD__':'__OWNER_PASSWORD__');await p.getByRole('button',{name:'Войти',exact:true}).click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));}
 await c.addCookies([{name:'django_language',value:lang,url:B}]);return{c,p};
}
async function visit(p,path){await p.bringToFront();const r=await p.goto(path.startsWith('http')?path:B+path);await p.waitForTimeout(200);return r.status();}
async function shot(p,name){const file='screenshots/'+name+'-'+Date.now()+'.png';await p.screenshot({path:ROOT+'/'+file,animations:'disabled'});return file;}
async function saved(p){await p.waitForFunction(()=>document.querySelector('[data-pc-save-status]')?.dataset.state==='saved',{timeout:12000});}
async function navigate(p,l){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),l.click({noWaitAfter:true})]);}
async function geometry(p){return p.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth,overflow:[]}));}
