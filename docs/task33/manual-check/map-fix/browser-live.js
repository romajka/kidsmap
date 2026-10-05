async page => {
 await page.context().unrouteAll({behavior:'wait'});
 const requests=[],responses=[],errors=[];
 page.on('request',r=>{if(new URL(r.url()).hostname==='tile.openstreetmap.org')requests.push({url:r.url(),referer:r.headers().referer||null,resource:r.resourceType()});});
 page.on('response',r=>{if(new URL(r.url()).hostname==='tile.openstreetmap.org')responses.push({url:r.url(),status:r.status()});});
 page.on('pageerror',e=>errors.push(String(e)));
 await page.setViewportSize({width:1280,height:900});
 await page.goto('http://127.0.0.1:8780/ru/');
 await page.locator('#home-map').scrollIntoViewIfNeeded();
 await page.waitForFunction(()=>document.querySelectorAll('#home-map .leaflet-tile-loaded').length>0||document.querySelector('[data-home-map-tile-status]'));
 await page.waitForLoadState('networkidle');
 const facts=await page.evaluate(()=>({tiles:document.querySelectorAll('#home-map .leaflet-tile-loaded').length,markers:document.querySelectorAll('#home-map .leaflet-marker-icon').length,status:document.querySelector('[data-home-map-tile-status]')?.textContent||'',scrollWidth:document.documentElement.scrollWidth,width:innerWidth}));
 await page.locator('#home-map-section').screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/map-fixed-live.png'});
 return {requests,responses,errors,facts,scope:'One visible live viewport; no panning, prefetch or provider substitution'};
}
