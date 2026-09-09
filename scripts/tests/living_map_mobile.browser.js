async page => {
  const base = 'http://127.0.0.1:8773';
  const browser = page.context().browser();
  const errors = [], cases = [];
  const context = await browser.newContext({viewport:{width:390,height:844},reducedMotion:'no-preference'});
  const check = (ok, message) => { if (!ok) throw new Error(message); };
  const instrument = () => {
    const raf = requestAnimationFrame;
    window.__mapFrames = 0;
    window.requestAnimationFrame = callback => {
      if (new Error().stack.includes('living_map_background')) {
        return raf(time => { __mapFrames++; callback(time); });
      }
      return raf(callback);
    };
  };
  try {
    const tab = await context.newPage();
    tab.on('pageerror', error => errors.push(error.message));
    await tab.addInitScript(instrument);
    for (const width of [360,390,430,768,1023]) {
      await tab.setViewportSize({width,height:844});
      for (const path of ['ru/','ru/catalog/','ru/about/']) {
        await tab.goto(base + '/' + path);
        await tab.waitForTimeout(200);
        const canvas = tab.locator('[data-living-map]');
        check(await canvas.evaluate(e => getComputedStyle(e).display === 'none'), `Mobile decoration is visible: ${width} ${path}`);
        check(await tab.evaluate(() => __mapFrames === 0), 'Hidden mobile decoration still schedules frames');
        check(await canvas.evaluate(e => e.width === 1 && e.height === 1), 'Mobile canvas must release its backing store');
        await tab.locator('.site-footer').scrollIntoViewIfNeeded();
        await tab.mouse.click(5,150);
        await tab.waitForTimeout(100);
        check(await tab.evaluate(() => __mapFrames === 0), 'Scroll/click restarts mobile decoration');
        cases.push({width,path});
      }
    }
    await tab.setViewportSize({width:1440,height:1000});
    await tab.goto(base + '/ru/');
    await tab.waitForTimeout(200);
    check(await tab.locator('[data-living-map]').isVisible(), 'Desktop animation must remain visible');
    const running = await tab.evaluate(() => __mapFrames);
    await tab.waitForTimeout(100);
    check(await tab.evaluate(() => __mapFrames) > running, 'Desktop animation does not run');
    await tab.setViewportSize({width:390,height:844});
    await tab.waitForTimeout(150);
    const stopped = await tab.evaluate(() => __mapFrames);
    await tab.waitForTimeout(150);
    check(await tab.evaluate(() => __mapFrames) === stopped, 'Shrinking a desktop viewport must stop animation');
    await tab.locator('#km-burger-open').click();
    check(await tab.locator('#km-mobile-drawer').getAttribute('aria-hidden') === 'false', 'Mobile navigation broke');
    await tab.locator('#km-burger-close').click();
    await tab.waitForTimeout(400);
    await tab.screenshot({path:'output/playwright/living-map/mobile-clean-390.png'});
    await tab.setViewportSize({width:1440,height:1000});
    await tab.waitForTimeout(200);
    check(await tab.evaluate(() => __mapFrames) > stopped, 'Expanding to desktop must restore animation');
    const touch = await browser.newContext({viewport:{width:1180,height:820},hasTouch:true,isMobile:true,reducedMotion:'no-preference'});
    try {
      const tablet = await touch.newPage();
      await tablet.addInitScript(instrument);
      await tablet.goto(base + '/ru/');
      await tablet.touchscreen.tap(5,150);
      await tablet.waitForTimeout(200);
      check(await tablet.locator('[data-living-map]').evaluate(e => getComputedStyle(e).display === 'none'), 'Landscape touch tablet must not show decoration');
      check(await tablet.evaluate(() => __mapFrames === 0), 'Touch tablet still schedules decoration');
    } finally { await touch.close(); }
    check(errors.length === 0, JSON.stringify(errors));
    return {passed:true,mobileCases:cases.length,desktopResume:true,touchTablet:true,errors};
  } finally { await context.close(); }
}
