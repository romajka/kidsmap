async(page)=>{
 const events=[];page.on('pageerror',e=>events.push(String(e)));page.on('console',m=>{if(m.type()==='error')events.push(m.text())});
 page.on('requestfailed',r=>events.push(r.url()+': '+r.failure()?.errorText));
 page.on('response',r=>{if(r.status()>=400)events.push(r.url()+': HTTP '+r.status())});
 const origin='http://127.0.0.1:8799';
 await page.context().route('**/*',route=>{if(new URL(route.request().url()).origin!==origin)throw Error('External report request');return route.continue()});
 const response=await page.goto(origin+'/completion/report.html');if(response.status()!==200)throw Error('Report unavailable');
 await page.locator('img').evaluateAll(nodes=>nodes.forEach(img=>img.loading='eager'));
 await page.waitForFunction(()=>[...document.images].every(img=>img.complete&&img.naturalWidth>0));
 const checks=[];
 for(const width of [390,1440]){
  await page.setViewportSize({width,height:1000});await page.evaluate(()=>scrollTo(0,0));
  const facts=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,main:document.querySelectorAll('main').length,images:document.images.length,missingAlt:[...document.images].filter(x=>!x.alt).length,records:document.querySelectorAll('.requirement').length}));
  if(facts.scroll>width+1||facts.main!==1||facts.images!==30||facts.missingAlt||facts.records!==120)throw Error(JSON.stringify(facts));
  checks.push({width,...facts,pass:true});
  await page.screenshot({path:'__REPORT_EVIDENCE__/report-'+width+'.png',fullPage:false});
 }
 const input=page.locator('#search');await input.fill('completion-no-such-test');
 if(await page.locator('.requirement:visible').count()!==0)throw Error('Search did not filter');
 await input.fill('');if(await page.locator('.requirement:visible').count()!==120)throw Error('Search did not restore');
 const first=page.locator('.requirement summary').first();await first.focus();await page.keyboard.press('Space');
 if(await page.locator('.requirement[open]').count()!==1)throw Error('Keyboard disclosure failed');
 await page.keyboard.press('Space');if(await page.locator('.requirement[open]').count()!==0)throw Error('Keyboard close failed');
 const links=await page.locator('a[href]').evaluateAll(nodes=>[...new Set(nodes.map(x=>x.href).filter(x=>!x.includes('#')))]);
 for(const url of links){if(new URL(url).origin!==origin)throw Error('External link');const r=await page.request.get(url);if(r.status()!==200)throw Error(url+': '+r.status())}
 if(events.length)throw Error(JSON.stringify(events));
 return {status:'PASS',widths:checks,loadedScreenshots:30,records:120,search:true,keyboardDisclosure:true,linksChecked:links.length,errors:events};
}
