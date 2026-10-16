async (page) => {
 const base='__BASE__', f=__FIXTURES__, here='__HERE__';const rows=[],errors=[],blocked=[];
 await page.context().route('**/*',r=>r.request().url().startsWith(base)||r.request().url().startsWith('data:')?r.continue():(blocked.push(r.request().url().split('?')[0]),r.abort()));
 page.on('pageerror',e=>errors.push(e.message));
 await page.locator('[name=username]').fill(f.username);await page.locator('[name=password]').fill('__PASSWORD__');await Promise.all([page.waitForNavigation(),page.locator('[type=submit]').click()]);
 await page.setViewportSize({width:390,height:844});await page.goto(base+'/admin/catalog/offeringgroup/'+f.offeringgroup+'/change/');
 return {url:page.url(),tabs:await page.locator('[role=tab],.nav-tabs a').evaluateAll(es=>es.map(e=>({text:e.textContent,id:e.id,href:e.getAttribute('href')}))),badges:await page.locator('.km-status-badge').evaluateAll(es=>es.map(e=>e.textContent)),errors,blocked};
}
