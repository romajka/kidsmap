async page => {
 const context=await page.context().browser().newContext({viewport:{width:1920,height:1080},reducedMotion:'no-preference'});
 const errors=[],matrix=[];
 try {
  const tab=await context.newPage();
  tab.on('pageerror',e=>errors.push(e.message));
  await tab.addInitScript(()=>{
   let scene;
   Object.defineProperty(window,'KidsMapLivingScene',{
    get:()=>scene,
    set(value){
     const create=value.createVertical;
     value.createVertical=options=>{window.__footerRoutes=create(options);return __footerRoutes;};
     scene=value;
    }
   });
  });
  // Narrow/touch layouts are covered by living_map_mobile.browser.js.
  for(const width of [1024,1440,1920,2560]){
   await tab.setViewportSize({width,height:1080});
   await tab.goto('http://127.0.0.1:8773/ru/about/');
   await tab.locator('.site-footer').scrollIntoViewIfNeeded();
   await tab.waitForTimeout(400);
   const result=await tab.evaluate(()=>{
    const footer=document.querySelector('.site-footer').getBoundingClientRect();
    return {width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,
     ends:__footerRoutes.map(r=>r.points.at(-1).y),footerEnd:footer.bottom+scrollY-12,
     maxJump:Math.max(...__footerRoutes.map(r=>{
      const p=r.points.filter(p=>p.y>r.bottom-500);
      const angles=p.slice(1).map((b,i)=>Math.atan2(b.y-p[i].y,Math.abs(b.x-p[i].x)));
      return Math.max(...angles.slice(1).map((a,i)=>Math.abs(a-angles[i])));
     }))};
   });
   if(result.overflow||result.maxJump>=.12||result.ends.some(y=>Math.abs(y-result.footerEnd)>1))throw new Error(JSON.stringify(result));
   const canvas=tab.locator('[data-living-map]');
   const before=await canvas.evaluate(e=>e.toDataURL());
   await tab.waitForTimeout(150);
   if(before===await canvas.evaluate(e=>e.toDataURL()))throw new Error('Footer does not animate at '+width);
   await tab.screenshot({path:'output/playwright/living-map/footer-smooth-'+width+'.png'});
   matrix.push(result);
  }
  await tab.emulateMedia({reducedMotion:'reduce'});
  await tab.waitForTimeout(150);
  const before=await tab.locator('[data-living-map]').evaluate(e=>e.toDataURL());
  await tab.waitForTimeout(150);
  if(before!==await tab.locator('[data-living-map]').evaluate(e=>e.toDataURL()))throw new Error('Reduced footer must remain static');
  if(errors.length)throw new Error(JSON.stringify(errors));
  return {passed:true,matrix,errors};
 } finally { await context.close(); }
}
