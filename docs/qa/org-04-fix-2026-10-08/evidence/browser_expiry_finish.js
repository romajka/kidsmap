async p=>{
const rows=[],errors=[];p.on('pageerror',e=>errors.push(String(e)));
const nav=p.waitForNavigation({waitUntil:'load'});const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/detach-preview/'));
await p.locator('[name=consent]').check();await p.locator('[data-confirm-form] button[type=submit]').click();const res=await response;await nav;
rows.push({id:'expired-native-submit',status:res.status()===409&&await p.locator('[data-confirm-form]').count()===0?'PASS':'FAIL',statusCode:res.status()});
await p.locator('main').screenshot({path:'output/playwright/org04-fix-20261008/expired-ru-1440.png'});
await p.goto('http://localhost:8788/ru/account/organizations/43/branches/81/detach-preview/');rows.push({id:'expired-link-preserved',status:await p.locator('tr[data-result=detached]').count()===1?'PASS':'FAIL'});
return{rows,errors};}
