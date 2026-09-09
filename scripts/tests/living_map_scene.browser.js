async page => {
 const check=(ok,msg)=>{if(!ok)throw new Error(msg);};
 await page.setViewportSize({width:1440,height:1000});
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.goto('http://127.0.0.1:8773/ru/');
 await page.waitForTimeout(500);
 check(await page.evaluate(()=>!!window.KidsMapLivingScene),'Journey renderer must be loaded on homepage');
 const canvas=page.locator('[data-living-map]');
 await page.locator('.home-hero-visual').evaluate(e=>{e.style.position='relative';e.style.overflow='hidden';});
 await page.evaluate(()=>window.dispatchEvent(new Event('resize')));await page.waitForTimeout(150);
 const before=await canvas.evaluate(e=>e.toDataURL());
 // An absolutely positioned slide image outside its clipping parent must not
 // reserve background space outside the actual gallery viewport.
 await page.locator('.home-hero-visual').evaluate(e=>{
  const img=document.createElement('img');img.dataset.sceneClipFixture='';img.alt='';
  img.style.cssText='position:absolute;left:-800px;top:0;width:650px;height:520px';
  e.append(img);window.dispatchEvent(new Event('resize'));
 });
 await page.waitForTimeout(150);
 check(before===await canvas.evaluate(e=>e.toDataURL()),'Clipped slideshow images incorrectly erase the surrounding map');
 await page.locator('[data-scene-clip-fixture]').evaluate(e=>e.remove());
 await page.evaluate(()=>window.dispatchEvent(new Event('resize')));
 return {passed:true,checks:2};
}
