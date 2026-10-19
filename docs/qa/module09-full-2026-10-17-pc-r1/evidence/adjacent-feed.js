async original=>{
const base='http://127.0.0.1:33380',dir='/mnt/c/kidsmap/.tmp/module09-full-pc-r1/png/',rows=[],context=await original.context().browser().newContext(),p=await context.newPage();
await context.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());
p.setDefaultTimeout(7000);const pageerrors=[],consoleErrors=[],network=[];p.on('pageerror',e=>pageerrors.push(String(e)));p.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});p.on('response',r=>{if(r.status()>=400)network.push({url:r.url(),http:r.status()});});
const add=(id,ok,lang,width,details={})=>rows.push({id,status:ok?'PASS':'FAIL',lang,width,role:'guest',...details});
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
const prefix=lang==='az'?'':'/'+lang;await p.setViewportSize({width,height:950});
try{
 const protectedUrl=base+prefix+'/account/notifications/';const rr=await p.request.get(protectedUrl,{maxRedirects:0});const location=rr.headers().location;const r=await p.goto(protectedUrl);await p.screenshot({path:dir+'anonymous-login-'+lang+'-'+width+'.png'});
 add('anonymous-notifications-login-recovery',r.status()===200&&!p.url().includes('/accounts/login/'),lang,width,{url:protectedUrl,initialHttp:rr.status(),location,finalHttp:r.status(),finalUrl:p.url(),screenshot:'png/anonymous-login-'+lang+'-'+width+'.png'});
 const actual=await p.goto(base+prefix+'/auth/login/');add('actual-login-route-reachable',actual.status()===200&&await p.locator('[name=username]').isVisible(),lang,width);
 await p.goto(base+prefix+'/place-reviews/');const first=await p.locator('.place-reviews-list .review-text').allTextContents();
 await p.locator('.pagination a.page-item[href="?page=2"]').press('Enter');await p.waitForLoadState('domcontentloaded');const second=await p.locator('.place-reviews-list .review-text').allTextContents();
 add('feed-page2-native',new URL(p.url()).searchParams.get('page')==='2'&&JSON.stringify(first)!==JSON.stringify(second),lang,width);
 const reloaded=await p.reload();add('feed-page2-reload',reloaded.status()===200&&new URL(p.url()).searchParams.get('page')==='2'&&JSON.stringify(second)===JSON.stringify(await p.locator('.place-reviews-list .review-text').allTextContents()),lang,width);
 await p.locator('.pagination').scrollIntoViewIfNeeded();await p.screenshot({path:dir+'feed-page2-'+lang+'-'+width+'.png'});
 await p.locator('select[name=sort]').selectOption('likes');await p.locator('.place-reviews-toolbar-wrap button[type=submit]').click();await p.waitForLoadState('domcontentloaded');
 add('feed-sort-native',new URL(p.url()).searchParams.get('sort')==='likes'&&await p.locator('select[name=sort]').inputValue()==='likes',lang,width);
 await p.reload();add('feed-sort-reload',new URL(p.url()).searchParams.get('sort')==='likes'&&await p.locator('select[name=sort]').inputValue()==='likes',lang,width);
 add('feed-no-overflow',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),lang,width);
}catch(e){rows.push({id:'adjacent-feed-harness',status:'NOT RUN',lang,width,error:String(e).slice(0,400)});}
}
await context.close();return{rows,pageerrors,consoleErrors,network,utc:new Date().toISOString()};}
