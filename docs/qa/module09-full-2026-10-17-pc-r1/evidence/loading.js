async original=>{
const base='http://127.0.0.1:33380',dir='/mnt/c/kidsmap/.tmp/module09-full-pc-r1/png/',rows=[],context=await original.context().browser().newContext(),p=await context.newPage();
await context.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());p.setDefaultTimeout(7000);await p.goto(base+'/qa/login/author/');
const state=async()=>(await p.request.get(base+'/qa/state/')).json();
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
const prefix=lang==='az'?'':'/'+lang;await p.setViewportSize({width,height:950});
try{
 await p.goto(base+prefix+'/catalog/');const burger=p.locator('#km-burger-open');if(await burger.isVisible()){await burger.focus();await p.keyboard.press('Enter');const opened=await burger.getAttribute('aria-expanded')==='true';await p.screenshot({path:dir+'drawer-'+lang+'-'+width+'.png'});await p.keyboard.press('Escape');rows.push({id:'mobile-drawer-keyboard',status:opened&&await burger.getAttribute('aria-expanded')==='false'?'PASS':'FAIL',lang,width,role:'author'});}const btn=p.locator('form[action$="/place/1/like/"] button');await btn.scrollIntoViewIfNeeded();const before=await state();let release;const gate=new Promise(r=>release=r);
 const pattern='**/place/1/like/';await p.route(pattern,async route=>{await gate;await route.fulfill({status:503,contentType:'application/json',body:'{"ok":false}'});});
 await btn.click();await p.waitForFunction(()=>document.querySelector('form[action$="/place/1/like/"] button').disabled);
 rows.push({id:'favorite-pending-disabled',status:await btn.isDisabled()?'PASS':'FAIL',lang,width,role:'author',classification:'SIMULATED delayed transport',screenshot:'png/loading-'+lang+'-'+width+'.png'});await p.screenshot({path:dir+'loading-'+lang+'-'+width+'.png'});
 release();await p.waitForFunction(()=>!document.querySelector('form[action$="/place/1/like/"] button').disabled);
 rows.push({id:'favorite-503-feedback-recovered-no-write',status:JSON.stringify(before)===JSON.stringify(await state())&&await p.locator('.form-inline-notice,.km-inline-notice,[role=alert]').count()>0?'PASS':'FAIL',lang,width,role:'author',classification:'SIMULATED HTTP503',screenshot:'png/error503-'+lang+'-'+width+'.png'});await p.screenshot({path:dir+'error503-'+lang+'-'+width+'.png'});await p.unroute(pattern);
}catch(e){rows.push({id:'loading-harness',status:'NOT RUN',lang,width,error:String(e).slice(0,400)});}
}
await context.close();return{rows,utc:new Date().toISOString()};}
