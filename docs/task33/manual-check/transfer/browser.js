async page => {
 const errors=[],network=[],checks=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('console',e=>{if(e.type()==='error')errors.push(e.text());});
 page.on('requestfailed',r=>network.push({url:r.url(),error:r.failure()?.errorText}));
 page.on('response',r=>{if(r.status()>=400)network.push({url:r.url(),status:r.status()});});
 const base='http://127.0.0.1:8781';
 const assert=(ok,msg)=>{if(!ok)throw Error(msg)};
 await page.setViewportSize({width:1440,height:1000});
 await page.goto(base+'/qa/');await page.waitForLoadState('networkidle');
 const fixtures=await (await page.request.get(base+'/qa/fixtures.json')).json();
 await page.getByRole('button',{name:'Войти: demo_moderator',exact:true}).click();
 await page.goto(base+'/admin/catalog/organization/');await page.waitForLoadState('networkidle');
 const icon=await page.locator('#result_list .km-col-sort-badge svg').first().boundingBox();
 assert(icon.width===14&&icon.height===14,'Sorting icon regression');checks.push('authenticated admin: icon14x14');
 await page.goto(base+'/ru/catalog/');await page.waitForLoadState('networkidle');
 assert((await page.locator('body').innerText()).includes('103'),'Catalog count missing');
 const photos=page.locator('img[src*="/media/"]');
 assert(await photos.count()>=12,'First page does not contain 12 photo elements');
 for(let i=0;i<await photos.count();i++){
  await photos.nth(i).scrollIntoViewIfNeeded();
  await page.waitForFunction(e=>e.complete&&e.naturalWidth>0,await photos.nth(i).elementHandle());
 }
 const images=await page.locator('img').evaluateAll(es=>es.filter(e=>e.src.includes('/media/')&&e.complete&&e.naturalWidth>0).length);
 assert(images>=12,'Catalog photos missing');checks.push({catalog:'103',loadedPhotos:images});
 await page.setViewportSize({width:390,height:844});await page.goto(base+'/admin/catalog/place/');await page.waitForLoadState('networkidle');
 assert(await page.evaluate(()=>document.documentElement.scrollWidth===innerWidth),'Mobile page overflow');
 const height=await page.locator('#result_list tbody tr').first().evaluate(e=>e.getBoundingClientRect().height);assert(height<=120,'Stretched mobile row');checks.push({mobile:390,rowHeight:height});
 await page.goto(base+'/qa/');await page.waitForLoadState('networkidle');
 const hrefs=await page.locator('a[href]').evaluateAll(es=>es.map(e=>e.getAttribute('href')));
 assert(hrefs.some(h=>h.includes(fixtures.links.ru.place_edit)),'Guide uses stale fixture ID');
 assert(!hrefs.some(h=>h.includes('localhost:8780')),'Guide uses old port');checks.push('guide uses current fixture IDs and port');
 assert(!errors.length&&!network.length,JSON.stringify({errors,network}));
 return {status:'PASS',checks,errors,network};
}
