async page => {
 const check=(ok,message)=>{if(!ok)throw new Error(message);};
 const base='http://127.0.0.1:8773/ru/';
 const browser=page.context().browser();
 const results={};
 for (const fallback of ['no-canvas','throwing-canvas','no-js']) {
   const context=await browser.newContext({javaScriptEnabled:fallback!=='no-js'});
   if(fallback!=='no-js') await context.addInitScript(mode=>{
     const get=HTMLCanvasElement.prototype.getContext;
     HTMLCanvasElement.prototype.getContext=function(...args){
       if(this.hasAttribute('data-living-map')) {if(mode==='throwing-canvas')throw new Error('Canvas unavailable');return null;}
       return get.apply(this,args);
     };
   },fallback);
   const tab=await context.newPage();const errors=[];tab.on('pageerror',e=>errors.push(e.message));
   await tab.goto(base);
   check(await tab.locator('h1').isVisible(),fallback+' hides page');
   await tab.locator('.home-redesign-secondary').first().click();
   check(tab.url().includes('/catalog/'),fallback+' blocks normal links');
   check(errors.length===0,fallback+' runtime error');
   results[fallback]=true;await context.close();
 }
 const touch=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:3,isMobile:true,hasTouch:true,reducedMotion:'reduce'});
 const mobile=await touch.newPage();await mobile.goto(base);await mobile.waitForTimeout(400);
 const canvas=mobile.locator('[data-living-map]');
 check(await canvas.evaluate(e=>e.width===1&&e.height===1&&getComputedStyle(e).display==='none'),'Touch decoration must remain disabled');
 const before=await canvas.evaluate(e=>e.toDataURL());
 await mobile.touchscreen.tap(5,150);await mobile.waitForTimeout(150);
 check(before===await canvas.evaluate(e=>e.toDataURL()),'Touch/reduced motion changes decorative background');
 await mobile.locator('#km-burger-open').tap();
 check(await mobile.locator('#km-mobile-drawer').getAttribute('aria-hidden')==='false','Touch navigation intercepted');
 results.touchAndDpr=true;await touch.close();
 // Compare renderer cadence on the same page with and without the enhancement.
 await page.setViewportSize({width:1440,height:1000});
 await page.emulateMedia({reducedMotion:'no-preference'});
 const sample=()=>page.evaluate(()=>new Promise(resolve=>{
   let start=0,count=0;
   function tick(t){if(!start)start=t;count++;if(t-start>=2000)resolve(1000*(count-1)/(t-start));else requestAnimationFrame(tick);}
   requestAnimationFrame(tick);
 }));
 await page.goto(base);await page.waitForTimeout(500);
 results.enhancedFps=await sample();
 await page.route('**/js/living_map_background.js',route=>route.fulfill({contentType:'application/javascript',body:''}));
 await page.goto(base);await page.waitForTimeout(500);
 results.baselineFps=await sample();
 await page.unroute('**/js/living_map_background.js');
 await page.goto(base);
 return {passed:true,...results};
}
