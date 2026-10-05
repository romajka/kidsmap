async page => {
 await page.context().unrouteAll({behavior:'wait'});
 let mode='403';const rows=[],errors=[],network=[],consoleErrors=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('console',m=>{if(m.type()==='error')consoleErrors.push({mode,text:m.text(),url:m.location().url});});
 page.on('requestfailed',r=>network.push({mode,url:r.url(),error:r.failure()?.errorText}));
 await page.context().route('https://tile.openstreetmap.org/**',async route=>{
  if(mode==='offline')return route.abort('internetdisconnected');
  return route.fulfill({status:mode==='403'?403:200,contentType:'image/png',headers:{'Access-Control-Allow-Origin':'*'},body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64')});
 });
 const labels={ru:'Фон карты временно недоступен.',az:'Xəritənin fonu müvəqqəti əlçatan deyil.',en:'The map background is temporarily unavailable.'};
 for(mode of ['403','offline','ok'])for(const lang of ['az','ru','en'])for(const width of [320,1280]){
  await page.setViewportSize({width,height:900});
  await page.goto('http://127.0.0.1:8780/'+(lang==='az'?'':lang+'/'));
  await page.locator('#home-map').scrollIntoViewIfNeeded();
  if(mode==='ok')await page.locator('#home-map .leaflet-tile-loaded').first().waitFor();
  else await page.locator('[data-home-map-tile-status]').waitFor();
  await page.waitForLoadState('networkidle');
  const facts=await page.evaluate(()=>{
   const map=document.querySelector('#home-map'),status=document.querySelector('[data-home-map-tile-status]');
   const r=map.getBoundingClientRect(),s=status?.getBoundingClientRect();
   return {tiles:map.querySelectorAll('.leaflet-tile-loaded').length,markers:map.querySelectorAll('.leaflet-marker-icon').length,
    status:status?.textContent||'',role:status?.getAttribute('role'),link:status?.querySelector('a')?.getAttribute('href'),
    mapFits:r.left>=-1&&r.right<=innerWidth+1,statusFits:!s||(s.left>=-1&&s.right<=innerWidth+1)};
  });
  const expectedCatalog=lang==='az'?'/catalog/':'/'+lang+'/catalog/';
  const pass=facts.markers>0&&facts.mapFits&&facts.statusFits&&(mode==='ok'?facts.tiles>0&&!facts.status:facts.tiles===0&&facts.status.startsWith(labels[lang])&&facts.role==='status'&&facts.link===expectedCatalog);
  rows.push({mode,lang,width,facts,pass});
  if(lang==='ru'&&mode!=='ok')await page.locator('#home-map-section').screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/map-'+mode+'-'+width+'.png'});
 }
 // The surviving business markers still open actual place cards after failure.
 mode='403';await page.setViewportSize({width:1280,height:900});await page.goto('http://127.0.0.1:8780/ru/');
 await page.locator('#home-map').scrollIntoViewIfNeeded();await page.locator('[data-home-map-tile-status]').waitFor();
 await page.locator('#home-map .leaflet-marker-icon:not(.kidsmap-map-cluster)').first().click();
 await page.locator('.leaflet-popup').waitFor();
 const popup=await page.locator('.leaflet-popup').innerText();
 const expectedErrors=consoleErrors.filter(e=>e.url.startsWith('https://tile.openstreetmap.org/')&&e.mode!=='ok');
 const unexpectedErrors=consoleErrors.filter(e=>!expectedErrors.includes(e));
 const unexpectedNetwork=network.filter(e=>!e.url.startsWith('https://tile.openstreetmap.org/')||
   !((e.mode==='offline'&&['net::ERR_INTERNET_DISCONNECTED','net::ERR_ABORTED'].includes(e.error))||
     (e.mode==='403'&&e.error==='net::ERR_ABORTED')));
 await page.context().unrouteAll({behavior:'wait'});
 return {rows,popup,errors,expectedTransportErrors:expectedErrors,unexpectedErrors,network,unexpectedNetwork,
   status:rows.every(r=>r.pass)&&popup.length>0&&!errors.length&&!unexpectedErrors.length&&!unexpectedNetwork.length?'PASS':'REVIEW_REQUIRED'};
}
