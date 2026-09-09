async page => {
  const context = await page.context().browser().newContext({viewport:{width:1440,height:1000},reducedMotion:'no-preference'});
  const check = (ok, message) => { if (!ok) throw new Error(message); };
  try {
    const tab = await context.newPage();
    await tab.addInitScript(() => {
      const raf = window.requestAnimationFrame, arc = CanvasRenderingContext2D.prototype.arc;
      let queued, time = 1000, circles = 0;
      window.requestAnimationFrame = callback => {
        if (new Error().stack.includes('living_map_background.js')) { queued = callback; return -1; }
        return raf(callback);
      };
      CanvasRenderingContext2D.prototype.arc = function(x,y,...args) {
        if (this.canvas.hasAttribute('data-living-map') && x === 25 && y === 280) circles++;
        return arc.call(this,x,y,...args);
      };
      window.__advanceMap = (steps = 1) => {
        for (let i = 0; i < steps; i++) { circles = 0; queued(time += 50); }
        return circles;
      };
    });
    await tab.goto('http://127.0.0.1:8773/ru/about/');
    await tab.evaluate(() => __advanceMap());
    await tab.mouse.click(25,280);
    check(await tab.evaluate(() => __advanceMap()) === 2, 'Click must create a visible double ripple');
    for (let i = 0; i < 10; i++) await tab.mouse.click(25,280);
    check(await tab.evaluate(() => __advanceMap()) === 8, 'Click effects must be bounded to four ripples');
    check(await tab.evaluate(() => __advanceMap(25)) === 0, 'Ripples must expire');
    await tab.emulateMedia({reducedMotion:'reduce'});
    // The media query change event resets the scene asynchronously.
    await tab.waitForTimeout(200);
    await tab.mouse.click(25,280);
    check(await tab.evaluate(() => __advanceMap()) === 0, 'Reduced motion must suppress click effects');
    const before = await tab.locator('[data-living-map]').evaluate(e => e.toDataURL());
    await tab.evaluate(() => __advanceMap(10));
    check(before === await tab.locator('[data-living-map]').evaluate(e => e.toDataURL()), 'Reduced scene changes over time');
    return {passed:true,checks:5};
  } finally { await context.close(); }
}
