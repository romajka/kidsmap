async page => {
  const check = (ok, message) => { if (!ok) throw new Error(message); };
  const base = 'http://127.0.0.1:8773';
  const errors = [], failedLocal = [], requests = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => { if (response.url().startsWith(base) && response.status() >= 400) failedLocal.push({url:response.url(),status:response.status()}); });
  page.on('request', request => requests.push(request.url()));
  await page.addInitScript(() => {
    const original = window.requestAnimationFrame;
    window.__livingMetrics = {frames:0,durations:[],times:[]};
    window.requestAnimationFrame = callback => {
      const living = new Error().stack.includes('living_map_background.js');
      return original.call(window, living ? time => {
        const before = performance.now();
        callback(time);
        __livingMetrics.frames++;
        __livingMetrics.durations.push(performance.now()-before);
        __livingMetrics.times.push(time);
      } : callback);
    };
  });
  const matrix = [];
  await page.emulateMedia({reducedMotion:'reduce'});
  for (const width of [375,390,768,1024,1280,1440]) {
    await page.setViewportSize({width,height:900});
    for (const locale of ['','ru/','en/']) {
      await page.goto(base+'/'+locale);
      await page.waitForTimeout(200);
      check(await page.locator('[data-living-map]').count()===1, 'Missing canvas '+width+locale);
      check(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth), 'Overflow '+width+locale);
      for (const selector of ['.home-hero','.home-discover','#home-map-section','#how-it-works','#add-place','#faq','.site-footer']) {
        await page.locator(selector).scrollIntoViewIfNeeded();
        await page.waitForTimeout(60);
        check(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth), 'Scroll overflow '+selector+width+locale);
      }
      matrix.push({width,locale:locale||'az',overflow:false});
    }
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.goto(base+'/ru/');
  await page.waitForTimeout(1000);
  await page.evaluate(()=>{ __livingMetrics.frames=0; __livingMetrics.durations=[]; __livingMetrics.times=[]; });
  await page.mouse.move(45,750);
  await page.waitForTimeout(2000);
  const performanceResult=await page.evaluate(()=>{
    const m=__livingMetrics, a=m.durations.toSorted((a,b)=>a-b);
    return {callbacks:m.frames,callbacksPerSecond:1000*(m.times.length-1)/(m.times.at(-1)-m.times[0]),p95ms:a[Math.floor(a.length*.95)],maxMs:a.at(-1)};
  });
  check(performanceResult.p95ms<8, 'Background takes too much of frame budget');
  // Dispatch browser lifecycle signals deterministically (not an OS-tab benchmark).
  await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});
  const paused=await page.evaluate(()=>__livingMetrics.frames);
  await page.waitForTimeout(200);
  check(paused===await page.evaluate(()=>__livingMetrics.frames), 'Hidden document still schedules frames');
  await page.evaluate(()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'));});
  await page.waitForTimeout(200);
  check(paused<await page.evaluate(()=>__livingMetrics.frames), 'Visible document did not resume');
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.waitForTimeout(400);
  const still=await page.evaluate(()=>__livingMetrics.frames);
  await page.waitForTimeout(200);
  check(still===await page.evaluate(()=>__livingMetrics.frames), 'Reduced motion still schedules frames');
  // Same content geometry with enhancement enabled and disabled.
  const geometry=()=>page.locator('main > section,.site-footer,.topbar').evaluateAll(elements=>elements.map(e=>{const r=e.getBoundingClientRect();return {class:e.className,x:r.x,y:r.y+scrollY,w:r.width,h:r.height};}));
  const enhanced=await geometry();
  const nodeCount=await page.locator('*').count();
  await page.locator('[data-living-map]').evaluate(e=>e.style.display='none');
  check(JSON.stringify(enhanced)===JSON.stringify(await geometry()), 'Canvas changes layout');
  await page.locator('[data-living-map]').evaluate(e=>e.style.display='');
  await page.locator('.km-lang-wrapper [data-dropdown-trigger]').click();
  check(await page.locator('.km-lang-wrapper [data-dropdown-trigger]').getAttribute('aria-expanded')==='true','Language dropdown blocked');
  await page.keyboard.press('Escape');
  await page.locator('#district-tree-trigger').click();
  check(await page.locator('#district-tree-dropdown').isVisible(),'Region selector blocked');
  await page.locator('#district-tree-trigger').click();
  await page.locator('#category-dropdown-trigger').click();
  check(await page.locator('#category-dropdown-menu').isVisible(),'Category selector blocked');
  await page.locator('#category-dropdown-trigger').click();
  const age=page.locator('[data-age-value="6"]');
  if (await age.count()) await age.click();
  await page.locator('.home-faq-item').nth(1).locator('summary').click();
  check(await page.locator('.home-faq-item').nth(1).getAttribute('open')!==null,'FAQ blocked');
  await page.locator('.home-redesign-primary').focus();
  check(await page.locator('.home-redesign-primary').evaluate(e=>document.activeElement===e),'Keyboard focus blocked');
  await page.setViewportSize({width:390,height:844});
  await page.locator('#km-burger-open').click();
  check(await page.locator('#km-mobile-drawer').getAttribute('aria-hidden')==='false','Mobile menu blocked');
  await page.locator('#km-burger-close').click();
  await page.screenshot({path:'output/playwright/living-map/mobile-controls.png'});
  check(errors.length===0,'Runtime errors: '+errors.join(';'));
  check(failedLocal.length===0,'Local network failures: '+JSON.stringify(failedLocal));
  return {passed:true,matrix,performanceResult,nodeCount,runtimeErrors:errors,failedLocal,backgroundAssets:[...new Set(requests.filter(url=>url.includes('living_map')))]};
}
