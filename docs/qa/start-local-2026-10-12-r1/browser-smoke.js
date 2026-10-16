async page => {
  await page.context().unroute('**/*');
  page.removeAllListeners('pageerror'); page.removeAllListeners('response');
  const base='http://127.0.0.1:51665';
  const blocked=[], errors=[], responses=[], pages=[];
  await page.context().route('**/*', route => {
    const url=route.request().url();
    if (url.startsWith(base+'/') || url.startsWith('data:')) return route.continue();
    blocked.push(url.split('/').slice(0,3).join('/')); return route.abort();
  });
  page.on('pageerror', e => errors.push(e.message));
  page.on('response', r => {if(r.url().startsWith(base+'/') && r.status()>=400) responses.push({url:r.url().slice(base.length),status:r.status()});});
  for (const [lang,path,width] of [['az','/',1440],['ru','/ru/',390],['en','/en/',1440],['admin','/admin/login/',1440]]) {
    await page.setViewportSize({width,height:950});
    const response=await page.goto(base+path,{waitUntil:'networkidle'});
    pages.push({lang,path,width,status:response.status(),title:await page.title()});
    await page.screenshot({path:'/home/ramin/kidsmap/docs/qa/start-local-2026-10-12-r1/start-'+lang+'.png',fullPage:false});
  }
  return {browser:page.context().browser().version(),pages,pageerrors:errors,local_errors:responses,blocked_external_origins:[...new Set(blocked)],scope:'START guest/browser availability only; no full module acceptance'};
}
