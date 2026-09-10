async page => {
  const base = 'http://127.0.0.1:8773';
  const check = (value, message) => { if (!value) throw new Error(message); };
  const result = {widths: [], scenarios: [], pageErrors: [], failedResources: [], capabilities: null};
  const ctx = await page.context().browser().newContext({viewport: {width:1440,height:1000}});
  const p = await ctx.newPage();
  p.setDefaultTimeout(7000);
  p.on('pageerror', e => result.pageErrors.push(e.message));
  p.on('response', response => { if(response.status() >= 400) { const url=new URL(response.url()); result.failedResources.push({path:url.pathname,status:response.status()}); } });
  await p.addInitScript(() => {
    let api, factory;
    window.__markers=[];
    Object.defineProperty(window,'KidsMapGoogleMotion',{get:()=>api,set:v=>{api=v;const create=v.create;v.create=map=>{window.__map=map;window.__motion=create(map);return window.__motion;};}});
    Object.defineProperty(window,'kidsMapCreateGoogleMarker',{get:()=>factory,set:v=>{factory=options=>{const marker=v(options);if(options.publicVisual)window.__markers.push(marker);return marker;};}});
  });
  async function load(path='/ru/') {
    await p.goto(base+path);
    if(path.includes('catalog')) { await p.locator('[data-catalog-map-open]').click(); await p.locator('[data-catalog-map]').scrollIntoViewIfNeeded(); }
    else await p.locator('#home-map').scrollIntoViewIfNeeded();
    await p.evaluate(()=>scrollBy(0,-130));
    await p.waitForFunction(()=>window.__map && document.querySelector('.kidsmap-marker-button'));
    await p.waitForTimeout(1000);
  }
  async function visibleButton(cluster=true) {
    const label = await p.locator('.kidsmap-marker-button').evaluateAll((es,cluster)=>es.filter(e=>/^\d/.test(e.getAttribute('aria-label'))===cluster).find(e=>{const r=e.getBoundingClientRect();const m=window.__map.getDiv().getBoundingClientRect();return r.x>m.x+2&&r.right<m.right-2&&r.y>Math.max(110,m.y)&&r.bottom<Math.min(innerHeight,m.bottom)-10;})?.getAttribute('aria-label'),cluster);
    return label ? p.locator('.kidsmap-marker-button').filter({has:p.locator('img')}).and(p.locator('[aria-label='+JSON.stringify(label)+']')) : null;
  }
  try {
    await load();
    result.capabilities=await p.evaluate(()=>({rendering:__map.getRenderingType(),fractional:__map.get('isFractionalZoomEnabled'),advanced:__map.getMapCapabilities().isAdvancedMarkersAvailable,places:__markers.filter(m=>m.__kidsMapPlace).length}));
    check(result.capabilities.places===62,'Current local public fixture changed; review baseline');
    check(await p.evaluate(()=>__markers.filter(m=>m.__kidsMapPlace).every(m=>m.getPosition().lat()===m.__kidsMapPlace.lat&&m.getPosition().lng()===m.__kidsMapPlace.lng)),'Real coordinates changed');
    check(await p.locator('.kidsmap-marker-button[aria-hidden="true"]').evaluateAll(es=>es.every(e=>e.tabIndex===-1)),'Offscreen markers remain in keyboard tab order');
    const first=await visibleButton(); const z0=await p.evaluate(()=>__map.getZoom());
    await first.click(); await p.waitForTimeout(1300);
    check(await p.evaluate(z=>__map.getZoom()>z,z0),'Cluster did not zoom');
    let pin=await visibleButton(false);
    if(!pin){ const next=await visibleButton();await next.click();await p.waitForTimeout(1200);pin=await visibleButton(false); }
    check(pin,'No visible category pin after zoom');
    await pin.click();await p.waitForTimeout(300);
    check(await p.locator('.home-map-popup').count()===1,'One card must open');
    check(await p.locator('.kidsmap-marker-button.is-selected').count()===1,'Selection not unique');
    await p.keyboard.press('Escape');
    check(await p.locator('.home-map-popup').count()===0,'Escape does not close home card');
    result.scenarios.push('real mouse cluster → pin → one card → Escape');
    await p.evaluate(()=>__map.moveCamera({center:{lat:40.4093,lng:49.8671},zoom:11}));await p.waitForTimeout(1100);
    const a=await visibleButton();const ar=await a.boundingBox();await p.mouse.click(ar.x+ar.width/2,ar.y+ar.height/2);await p.waitForTimeout(70);
    const b=await visibleButton();if(b){const br=await b.boundingBox();await p.mouse.click(br.x+br.width/2,br.y+br.height/2);}await p.waitForTimeout(1300);
    result.scenarios.push('rapid repeated cluster clicks');
    await p.evaluate(()=>__map.moveCamera({center:{lat:40.4093,lng:49.8671},zoom:11}));await p.waitForTimeout(1100);
    await (await visibleButton()).click();
    const box=await p.locator('#home-map').boundingBox();
    await p.mouse.move(box.x+box.width*.7,box.y+box.height*.7);await p.mouse.down();await p.mouse.move(box.x+box.width*.7+70,box.y+box.height*.7+25,{steps:5});await p.mouse.up();
    await p.waitForTimeout(350);const afterDrag=await p.evaluate(()=>__map.getCenter().toJSON());await p.waitForTimeout(800);
    check(await p.evaluate(c=>Math.abs(__map.getCenter().lat()-c.lat)<1e-6&&Math.abs(__map.getCenter().lng()-c.lng)<1e-6,afterDrag),'Camera resumes after drag');
    result.scenarios.push('manual drag interrupts transition');
    await p.evaluate(()=>__map.moveCamera({center:{lat:40.4093,lng:49.8671},zoom:11}));await p.waitForTimeout(1100);await (await visibleButton()).click();
    await p.locator('#category-dropdown-trigger').click();
    const category=await p.locator('.km-category-option[data-value]:not([data-value=""])').first().getAttribute('data-value');
    await p.locator('.km-category-option[data-value='+JSON.stringify(category)+']').click();await p.waitForTimeout(400);
    const camera=await p.evaluate(()=>({c:__map.getCenter().toJSON(),z:__map.getZoom()}));
    check(await p.evaluate(()=>__markers.filter(m=>m.__kidsMapPlace && m.getMap()).every(m=>m.__kidsMapPlace.category_code===document.querySelector('[name="category"]').value)),'Category filter leaked a place');
    await p.locator('#category-dropdown-trigger').click();await p.locator('.km-category-option[data-value=""]').click();await p.waitForTimeout(400);
    check(await p.evaluate(c=>__map.getZoom()===c.z&&JSON.stringify(__map.getCenter().toJSON())===JSON.stringify(c.c),camera),'Filter reset user camera');
    check(await p.evaluate(()=>__markers.filter(m=>m.__kidsMapPlace).length)===62,'Filter recreates place markers');
    check(await p.evaluate(()=>performance.getEntriesByType('resource').filter(e=>/maps.googleapis.com\/maps\/api\/js\?/.test(e.name)).length)===1,'Duplicate Google API load');
    result.scenarios.push('real category filter during transition; stable markers and viewport; one Maps API request');
    for(const width of [360,390,768,1024,1280,1440]) {
      await p.setViewportSize({width,height:1000});await load();
      check(await p.evaluate(()=>document.querySelectorAll('#home-map div[role="button"][title]').length)===0,'Duplicate marker hit target');
      await (await visibleButton()).click();await p.waitForTimeout(1100);
      pin=await visibleButton(false);
      if(pin){await pin.click();await p.waitForTimeout(250);const r=await p.locator('.gm-style-iw-c').boundingBox();check(r.x>=0&&r.x+r.width<=width+1,'Home card horizontal overflow '+width);await p.keyboard.press('Escape');}
      result.widths.push({width,homeCard:!!pin});
    }
    // Use a browser-only payload override; neither local nor production DB changes.
    let fixtureMode='duplicates';
    await p.route('**/static/js/home_map.js?*',async route=>{
      const response=await route.fetch();const body=await response.text();
      const prefix=`(function(){const el=document.querySelector('#home-map-data');const original=JSON.parse(el.textContent);const count=${fixtureMode==='empty'?0:fixtureMode==='single'?1:fixtureMode==='duplicates'?3:620};const fixture=Array.from({length:count},(_,i)=>({...original[i%original.length],id:'fixture-'+i,name:'Fixture place '+i,search_text:'Fixture place '+i,url:'/fixture/'+i+'/',lat:40.4093+${fixtureMode==='duplicates'?'0':'(i%31)*.003'},lng:49.8671+${fixtureMode==='duplicates'?'0':'Math.floor(i/31)*.003'}}));window.__fixture=fixture;el.textContent=JSON.stringify(fixture);})();\n`;
      await route.fulfill({response,body:prefix+body});
    });
    await p.setViewportSize({width:390,height:844});await load();
    await (await visibleButton()).click();
    check(await p.locator('.kidsmap-map-chooser li button').count()===3,'Coincident places do not offer choice');
    check(await p.evaluate(()=>__map.getZoom())===11,'Coincident places changed zoom');
    await p.locator('.kidsmap-map-chooser li button').nth(1).click();
    check(await p.locator('.home-map-popup').count()===1,'Coincident choice does not open card');
    await p.keyboard.press('Escape');
    await p.evaluate(()=>__map.moveCamera({center:{lat:40.4093,lng:49.8671},zoom:19}));await p.waitForTimeout(800);
    await p.locator('.kidsmap-marker-button').last().click();
    check(await p.locator('.kidsmap-map-chooser li button').count()===3,'Coincident places inaccessible at manual maximum zoom');
    await p.keyboard.press('Escape');
    result.scenarios.push('three coincident coordinates → accessible chooser → single card; choice also at manual zoom19');
    fixtureMode='empty';await p.goto(base+'/ru/');await p.locator('#home-map').scrollIntoViewIfNeeded();await p.waitForTimeout(500);
    check(await p.locator('.kidsmap-marker-button').count()===0,'Empty fixture has markers');check(await p.locator('#home-map iframe').count()===1,'Initial empty payload must preserve existing iframe fallback');
    fixtureMode='single';await load();check(await p.locator('.kidsmap-marker-button').count()===1,'Single fixture not one pin');await (await visibleButton(false)).click();check(await p.locator('.home-map-popup').count()===1,'Single fixture card missing');
    await p.keyboard.press('Escape');
    const onlyCategory=await p.evaluate(()=>__fixture[0].category_code);
    await p.locator('#category-dropdown-trigger').click();
    const other=p.locator('.km-category-option[data-value]:not([data-value=""]):not([data-value='+JSON.stringify(onlyCategory)+'])').first();
    await other.click();await p.waitForTimeout(400);
    check(await p.locator('.kidsmap-marker-button').count()===0,'Empty filter retains a pin');check(await p.locator('#home-map-note').isVisible(),'Empty filter message missing');
    result.scenarios.push('empty initial iframe fallback; single pin/card; filter to empty');
    fixtureMode='large';await p.setViewportSize({width:1440,height:1000});await load();
    check(await p.evaluate(()=>__markers.filter(m=>m.__kidsMapPlace).length)===620,'Expanded fixture missing');
    const start=Date.now();await (await visibleButton()).click();await p.waitForTimeout(1200);
    check(await p.locator('.kidsmap-marker-button').count()>0,'Large dataset left blank');
    result.scenarios.push('620-place browser fixture cluster click ('+(Date.now()-start)+' ms including 1200 ms observation)');
    await p.unroute('**/static/js/home_map.js?*');
    await p.emulateMedia({reducedMotion:'reduce'});await load();
    await (await visibleButton()).focus();await p.keyboard.press('Enter');await p.waitForTimeout(120);
    check(await p.evaluate(()=>__map.getZoom())>11,'Reduced motion keyboard cluster does not advance');
    check(await p.evaluate(()=>[...document.querySelectorAll('.kidsmap-marker-visual')].every(e=>getComputedStyle(e).animationName==='none')),'Reduced motion still animates markers');
    result.scenarios.push('reduced motion + keyboard');
    await p.emulateMedia({reducedMotion:'no-preference'});
    for(const lang of ['','ru/','en/']) {
      await load('/'+lang);check(await p.locator('.kidsmap-marker-button').count()>0,'Language map missing');
    }
    result.scenarios.push('AZ/RU/EN home');
    for(const width of [360,390,1440]) {
      await p.setViewportSize({width,height:1000});await load('/ru/catalog/');
      await (await visibleButton()).click();await p.waitForTimeout(1200);
      pin=await visibleButton(false);
      if(!pin){const next=await visibleButton();if(next){await next.click();await p.waitForTimeout(1100);pin=await visibleButton(false);}}
      check(pin,'No catalog pin after expanding');await pin.click();await p.waitForTimeout(300);
      const card=p.locator(width<768?'[data-map-mobile-sheet]':'[data-map-desktop-card]');
      check(await card.isVisible(),'Catalog card missing');
      const r=await card.boundingBox();check(r.x>=0&&r.x+r.width<=width+1,'Catalog card overflow '+width);
      await card.locator('[data-map-card-close]').click();check(!await card.isVisible(),'Catalog close failed');
      const zoom=await p.evaluate(()=>__map.getZoom());
      await p.locator('[data-catalog-map-close]').click();await p.locator('[data-catalog-map-open]').click();await p.waitForTimeout(350);
      check(await p.evaluate(()=>__map.getZoom())===zoom,'Catalog reopen resets zoom');
      result.scenarios.push('catalog card and reopen '+width);
    }
    await p.setViewportSize({width:1440,height:1000});await load('/ru/catalog/');
    await p.evaluate(()=>{window.__originalMap=__map;window.__originalPins=new Map(__markers.filter(m=>m.__kidsMapPlace).map(m=>[m.__kidsMapPlace.url,m]));});
    await (await visibleButton()).click();
    const categoryChip=p.locator('.desktop-category-chip[data-select-value]:not([data-select-value=""])').first();
    const categoryValue=await categoryChip.getAttribute('data-select-value');await categoryChip.click();
    await p.waitForURL(url=>url.searchParams.get('category')===categoryValue);await p.waitForTimeout(400);
    check(await p.evaluate(()=>__map===__originalMap),'AJAX recreated Google Map');
    check(await p.evaluate(()=>JSON.parse(document.querySelector('#catalog-map-data').textContent).every(place=>__markers.some(m=>m.__kidsMapPlace?.url===place.url&&m===__originalPins.get(place.url)))),'AJAX replaced unchanged markers');
    check(await p.evaluate(()=>performance.getEntriesByType('resource').filter(e=>/maps.googleapis.com\/maps\/api\/js\?/.test(e.name)).length)===1,'AJAX loads Google API twice');
    const cameraAfterFilter=await p.evaluate(()=>({center:__map.getCenter().toJSON(),zoom:__map.getZoom()}));
    await p.locator('.desktop-category-chip[data-select-value=""]').click();await p.waitForURL(url=>!url.searchParams.has('category'));await p.waitForTimeout(300);
    check(await p.evaluate(c=>__map===__originalMap&&__map.getZoom()===c.zoom&&JSON.stringify(__map.getCenter().toJSON())===JSON.stringify(c.center),cameraAfterFilter),'AJAX reset camera on ordinary refresh');
    result.scenarios.push('catalog AJAX during animation: same map, surviving markers, camera and API load');
    check(result.pageErrors.length===0,JSON.stringify(result.pageErrors));
    result.failedResources=[...new Map(result.failedResources.map(x=>[x.path,x])).values()]; return {passed:true,...result};
  } catch(error) { result.failedResources=[...new Map(result.failedResources.map(x=>[x.path,x])).values()]; return {passed:false,failure:error.message,...result}; }
  finally {await ctx.close();}
}
