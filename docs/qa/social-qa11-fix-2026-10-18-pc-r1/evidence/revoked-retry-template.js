async original=>{
const F=__FIXTURES__,base='http://127.0.0.1:33422',O='/mnt/c/kidsmap/docs/qa/social-qa11-fix-2026-10-18-pc-r1',c=await original.context().browser().newContext({viewport:{width:390,height:950},serviceWorkers:'block'}),p=await c.newPage(),rows=[],consoleErrors=[],pageerrors=[],http=[],failed=[],blocked=[];
await c.route('**/*',r=>{if(new URL(r.request().url()).hostname==='127.0.0.1')return r.continue();blocked.push(new URL(r.request().url()).hostname);return r.abort();});p.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});p.on('pageerror',e=>pageerrors.push(String(e)));p.on('response',r=>{if(r.status()>=400)http.push({path:new URL(r.url()).pathname,status:r.status()});});p.on('requestfailed',r=>failed.push({path:new URL(r.url()).pathname,error:r.failure()?.errorText}));
await p.goto(base+'/qa/social11-login/author/');
for(const lang of ['az','ru','en']){
 const prefix=lang==='az'?'':'/'+lang,path=prefix+'/account/notifications/'+F.revoked.notice_id+'/accept/';await p.goto(base+prefix+'/account/notifications/');const csrf=await p.locator('input[name=csrfmiddlewaretoken]').first().inputValue(),responsePromise=p.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===path);
 await p.evaluate(({path,token})=>{const f=document.createElement('form');f.action=path;f.method='POST';const e=document.createElement('input');e.name='csrfmiddlewaretoken';e.value=token;f.append(e);document.body.append(f);f.submit();},{path,token:csrf});
 const response=await responsePromise;let early;
 try{early=await p.evaluate(()=>({url:location.pathname,readyState:document.readyState,main:document.querySelectorAll('main').length,alert:!!document.querySelector('.account-notifications__error[role=alert]')}));}catch(e){early={navigationContextChange:String(e).slice(0,160)};}
 await p.waitForURL(u=>u.pathname===path,{waitUntil:'domcontentloaded'});await p.locator('.account-notifications__error[role=alert]').waitFor({state:'visible'});
 const first=p.locator('#main-content button').first();await first.focus();const focused=await first.evaluate(e=>document.activeElement===e);await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');
 const checks={status403:response.status()===403,singleMain:await p.getByRole('main').count()===1,noNested:await p.locator('main main').count()===0,alert:await p.locator('.account-notifications__error[role=alert]').isVisible(),idPreserved:await p.locator('div.account-main-content#main-content').count()===1,keyboard:focused&&await first.evaluate(e=>document.activeElement===e),noOverflow:await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)};
 rows.push({id:'revoked403',lang,checks,earlySnapshot:early,committedURL:new URL(p.url()).pathname,transport:'QA-crafted stale native form; real backend POST/CSRF/ACL response',synchronization:'wait for target URL DOMContentLoaded and visible alert before identical assertions'});await p.screenshot({path:O+'/png/subset-retry-'+lang+'-403.png',fullPage:true,animations:'disabled'});
}
await c.close();return{rows,consoleErrors,pageerrors,http,failed,blocked};
}
