async page => {
 const out='/home/ramin/kidsmap/output/playwright';
 const ctx=await page.context().browser().newContext({viewport:{width:390,height:844}}),p=await ctx.newPage();p.setDefaultTimeout(8000);
 const check=(v,m)=>{if(!v)throw Error(m)};const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.addInitScript(()=>{let api;Object.defineProperty(window,'KidsMapGoogleMotion',{get:()=>api,set:v=>{api=v;const create=v.create;v.create=m=>{window.__map=m;return create(m)};}})});
 let near=false;
 await p.route('**/static/js/home_map.js?*',async route=>{const response=await route.fetch();await route.fulfill({response,body:`(()=>{const el=document.querySelector('#home-map-data'),base=JSON.parse(el.textContent)[0];el.textContent=JSON.stringify([0,1,2].map(i=>({...base,id:i,url:'/fixture/'+i,name:'Edge '+i,lat:40.4093+${near?'i*.0000001':'0'},lng:49.8671})));})();\n`+await response.text()});});
 try {
  await p.goto('http://127.0.0.1:8773/ru/');await p.locator('#home-map').scrollIntoViewIfNeeded();await p.evaluate(()=>scrollBy(0,-120));await p.waitForFunction(()=>window.__map&&document.querySelector('.kidsmap-marker-button'));await p.waitForTimeout(1000);
  await p.evaluate(()=>__map.moveCamera({center:{lat:40.4093,lng:49.8671},zoom:19}));await p.waitForTimeout(700);await p.locator('.kidsmap-marker-button').last().click();check(await p.locator('.kidsmap-map-chooser li').count()===3,'Missing choice at manual zoom19');
  await p.keyboard.press('Escape');check(!await p.locator('.kidsmap-map-chooser').count(),'Chooser Escape failed');
  near=true;await p.reload();await p.locator('#home-map').scrollIntoViewIfNeeded();await p.evaluate(()=>scrollBy(0,-120));await p.waitForFunction(()=>window.__map&&document.querySelector('.kidsmap-marker-button'));await p.waitForTimeout(1000);
  const zooms=[];
  for(let i=0;i<5;i++){await p.locator('.kidsmap-marker-button').first().click();await p.waitForTimeout(1000);zooms.push(await p.evaluate(()=>__map.getZoom()));if(await p.locator('.kidsmap-map-chooser').count())break;}
  check(zooms[0]<=13&&zooms.every(z=>z<=18),'Native near-point camera overshot cap');check(await p.locator('.kidsmap-map-chooser li').count()===3,'Near points cause endless zoom');
  await p.unroute('**/static/js/home_map.js?*');
  // Force a slow first AJAX response, then select another category.
  await p.setViewportSize({width:1440,height:1000});await p.goto('http://127.0.0.1:8773/ru/catalog/');await p.locator('[data-catalog-map-open]').click();await p.waitForFunction(()=>window.__map);await p.evaluate(()=>{window.__firstMap=__map});
  let requests=0;
  await p.route('**/ru/catalog/?*',async route=>{const response=await route.fetch();if(++requests===1)await new Promise(resolve=>setTimeout(resolve,700));try{await route.fulfill({response})}catch(e){if(!/closed|handled|disposed/i.test(e.message))throw e}});
  const chips=p.locator('.desktop-category-chip[data-select-value]:not([data-select-value=""]):visible');
  const second=await chips.nth(1).getAttribute('data-select-value');await chips.nth(0).click();await p.waitForTimeout(80);await chips.nth(1).click();await p.waitForURL(url=>url.searchParams.get('category')===second);await p.waitForTimeout(1100);
  check(await p.evaluate(value=>JSON.parse(document.querySelector('#catalog-map-data').textContent).every(x=>x.category_code===value),second),'Stale AJAX response replaced latest places');check(await p.evaluate(()=>__map===__firstMap),'Rapid filters recreated map');
  check(errors.length===0,JSON.stringify(errors));return {passed:true,manualZoom19Choice:true,nearZoomSequence:zooms,rapidAjaxRequests:requests,pageErrors:errors};
 }finally{await ctx.close()}
}
