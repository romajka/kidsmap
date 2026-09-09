async (page) => {
  const check = (ok, message) => { if (!ok) throw new Error(message); };
  await page.setViewportSize({width:1440,height:1000});
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.goto('http://127.0.0.1:8773/ru/');
  const canvas = page.locator('[data-living-map]');
  check(await canvas.count() === 1, 'Homepage must have one living map canvas');
  const pixels = () => canvas.evaluate(e => e.toDataURL());
  const first = await pixels();
  await page.waitForTimeout(200);
  check(first !== await pixels(), 'Idle background must animate');
  check(await canvas.evaluate(e => getComputedStyle(e).pointerEvents === 'none' && e.getAttribute('aria-hidden') === 'true' && e.tabIndex < 0), 'Background must be decorative and click-through');
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.waitForTimeout(100);
  const reduced = await pixels();
  await page.waitForTimeout(200);
  check(reduced === await pixels(), 'Reduced motion must produce a static frame');
  await page.mouse.move(80,240);
  await page.waitForTimeout(100);
  check(reduced === await pixels(), 'Reduced motion must ignore pointer motion');
  await page.setViewportSize({width:390,height:844});
  await page.waitForTimeout(100);
  check(await canvas.evaluate(e => e.width <= 780 && e.height <= 1688), 'Canvas backing store must be bounded on mobile');
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Background must not cause horizontal overflow');
  await page.locator('#faq').scrollIntoViewIfNeeded();
  await page.waitForTimeout(100);
  check(reduced !== await pixels(), 'Static background must follow document scroll and resize');
  await page.emulateMedia({reducedMotion:'no-preference'});
  // Observe the active journey in the hero: the FAQ deliberately has long
  // quiet intervals between arrivals, so two nearby frames can match there.
  await page.locator('.home-hero').scrollIntoViewIfNeeded();
  await page.waitForTimeout(100);
  const resumed = await pixels();
  await page.waitForTimeout(200);
  check(resumed !== await pixels(), 'Motion must resume when preference changes');
  return {passed:true, checks:9};
}
