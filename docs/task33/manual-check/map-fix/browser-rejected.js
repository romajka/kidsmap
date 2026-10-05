async page => {
 const requests=[];
 await page.context().route('**/*.tile.openstreetmap.org/**',async route=>{
  requests.push({url:route.request().url(),referer:route.request().headers().referer||null});
  await route.fulfill({status:403,contentType:'image/png',headers:{'Access-Control-Allow-Origin':'*'},body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64')});
 });
 await page.context().route('https://tile.openstreetmap.org/**',async route=>{
  requests.push({url:route.request().url(),referer:route.request().headers().referer||null});
  await route.fulfill({status:403,contentType:'image/png',headers:{'Access-Control-Allow-Origin':'*'},body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64')});
 });
 await page.setViewportSize({width:1280,height:900});
 await page.goto('http://127.0.0.1:8780/ru/');
 await page.locator('#home-map').scrollIntoViewIfNeeded();
 await page.waitForFunction(()=>document.querySelector('#home-map.leaflet-container'));
 await page.waitForLoadState('networkidle');
 const result=await page.evaluate(()=>({failedTilesVisible:document.querySelectorAll('#home-map .leaflet-tile-loaded').length,
    fallback:document.querySelector('[data-home-map-tile-status]')?.textContent||'',markers:document.querySelectorAll('#home-map .leaflet-marker-icon').length}));
 return {requests,result,pass:requests.length>0&&result.failedTilesVisible===0&&!!result.fallback&&result.markers>0};
}
