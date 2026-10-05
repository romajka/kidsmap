async page => {
 const errors=[], failures=[], badResponses=[], checks=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 page.on('requestfailed',r=>failures.push({url:r.url(),error:r.failure()?.errorText}));
 page.on('response',r=>{if(r.status()>=400)badResponses.push({url:r.url(),status:r.status()});});
 const base='http://127.0.0.1:8780';
 const assert=(condition,message)=>{if(!condition)throw Error(message);};
 const inspectImages=async()=>{
   const images=page.locator('.place-card img');
   for(let i=0;i<await images.count();i++){
     const im=images.nth(i);await im.scrollIntoViewIfNeeded();
     await im.evaluate(el=>el.decode());
   }
   return await images.count();
 };
 await page.setViewportSize({width:1440,height:1000});
 for(const lang of ['ru','az','en']){
   const response=await page.goto(`${base}/${lang}/catalog/`);
   await page.waitForLoadState('networkidle');
   assert(response.status()===200,lang+' catalog HTTP');
   const count=await page.locator('.results-count-text').innerText();
   assert(count.includes('103'),lang+' public count: '+count);
   const mapCount=await page.locator('#catalog-map-data').evaluate(el=>JSON.parse(el.textContent).length);
   assert(mapCount===103,lang+' map count: '+mapCount);
   const images=await inspectImages();assert(images>0,lang+' photos missing');
   checks.push({case:lang+' catalogue',count,images,mapCount});
   if(lang==='ru'){
     await page.locator('.results-count').scrollIntoViewIfNeeded();
     await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/demo100-catalog.png'});
   }
 }
 await page.goto(`${base}/ru/catalog/?category=SPRT`);
 await page.waitForLoadState('networkidle');
 const sportCount=await page.locator('.results-count-text').innerText();
 assert(sportCount.includes('13'),'Sports count: '+sportCount);
 checks.push({case:'sports filter',count:sportCount,images:await inspectImages()});
 const detail=await page.locator('.place-card a').first().getAttribute('href');
 await page.goto(base+detail);await page.waitForLoadState('networkidle');
 assert((await page.locator('h1').innerText()).includes('Демо'),'Demo detail heading');
 const media=page.locator('main img[src*="/media/"]');
 for(let i=0;i<await media.count();i++)await media.nth(i).evaluate(async el=>{
   el.loading='eager';
   await Promise.race([el.decode(),new Promise((_,reject)=>setTimeout(()=>reject(Error('Image decode timeout: '+el.src)),10000))]);
 });
 assert(await media.count()>0,'Detail photos missing');
 checks.push({case:'detail',url:detail,images:await media.count()});
 await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/demo100-detail.png'});
 await page.setViewportSize({width:390,height:844});
 await page.goto(`${base}/ru/catalog/?page=2`);await page.waitForLoadState('networkidle');
 assert(await page.locator('.place-card').count()>0,'Second page empty');
 const mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
 assert(mobile.scrollWidth<=mobile.width,'Mobile overflow');
 checks.push({case:'mobile page 2',...mobile,images:await inspectImages()});
 await page.locator('.results-count').scrollIntoViewIfNeeded();
 await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/demo100-mobile.png'});
 assert(!errors.length&&!failures.length&&!badResponses.length,JSON.stringify({errors,failures,badResponses}));
 return {status:'PASS',checks,errors,failures,badResponses};
}
