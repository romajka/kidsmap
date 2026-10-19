async original=>{
const base='http://127.0.0.1:33380',dir='/mnt/c/kidsmap/.tmp/module09-full-pc-r1/png/',cases=__EXTRA_CASES__,rows=[],browser=original.context().browser(),pageerrors=[],http=[];
for(const item of cases){
 const c=await browser.newContext();await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(7000);const prefix=item.lang==='az'?'':'/'+item.lang;const inbox=base+prefix+'/account/notifications/';
 const add=(id,ok,width,details={})=>rows.push({id,status:ok?'PASS':'FAIL',kind:item.kind,lang:item.lang,width,role:'recipient',...details});
 try{
  await p.goto(base+prefix+'/auth/login/');await p.locator('[name=username]').fill(item.email);await p.locator('[name=password]').fill('<fictional-local-password>');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));
  const tabs=[];for(const width of [360,390,768,1024,1280,1440]){const tab=await c.newPage();tab.on('pageerror',e=>pageerrors.push(String(e)));await tab.setViewportSize({width,height:950});await tab.goto(inbox);tabs.push({tab,width});}
  await p.goto(inbox);await p.locator('form[action$="/notifications/'+item.notice_id+'/accept/"] button').click();await p.waitForLoadState('domcontentloaded');add('valid-invitation-native-accept',p.url()===inbox&&await p.locator('form[action$="/notifications/'+item.notice_id+'/accept/"]').count()===0,1280);
  for(const {tab,width}of tabs){
   const wait=tab.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/accept/'));await tab.locator('form[action$="/notifications/'+item.notice_id+'/accept/"] button').click();const response=await wait;await tab.waitForLoadState('domcontentloaded');http.push({kind:item.kind,lang:item.lang,width,http:response.status(),expected:403});
   const checks={denied403:response.status()===403,feedback:await tab.locator('.account-notifications__error[role=alert]').isVisible(),noAccept:await tab.locator('form[action$="/notifications/'+item.notice_id+'/accept/"]').count()===0,fit:await tab.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)};
   add('stale-invitation-rendered-feedback',Object.values(checks).every(Boolean),width,{checks,screenshot:'png/stale-'+item.key+'-'+width+'.png'});await tab.screenshot({path:dir+'stale-'+item.key+'-'+width+'.png'});
   await tab.keyboard.press('Tab');await tab.keyboard.press('Shift+Tab');await tab.keyboard.press('Escape');await tab.close();
  }
 }catch(e){rows.push({id:'extra-invite-harness',status:'NOT RUN',kind:item.kind,lang:item.lang,error:String(e).slice(0,450)});}
 await c.close();
}
return{rows,pageerrors,http,utc:new Date().toISOString()};}
