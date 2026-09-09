async page => {
  const base = 'http://127.0.0.1:8773';
  const check = (ok, message) => { if (!ok) throw new Error(message); };
  const context = await page.context().browser().newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  const errors = [], matrix = [], existingOverflow = [];
  try {
    const tab = await context.newPage();
    tab.on('pageerror', error => errors.push(error.message));
    await tab.addInitScript(() => {
      let scene;
      Object.defineProperty(window, 'KidsMapLivingScene', {
        get: () => scene,
        set(value) {
          const create = value.createVertical;
          value.createVertical = options => {
            window.__verticalRoutes = create(options);
            return window.__verticalRoutes;
          };
          scene = value;
        },
      });
    });
    const routes = ['', 'catalog/', 'catalog/new/', 'about/', 'faq/', 'contacts/',
      'reviews/', 'place-reviews/', 'add-place/', 'privacy/', 'terms/',
      'review-rules/', 'listing-rules/', 'events/', 'specialists/',
      'place/15-brush-and-clay-atelier/'];
    for (const lang of ['', 'ru/', 'en/']) {
      for (const path of routes) {
        const response = await tab.goto(base + '/' + lang + path);
        check(response.status() === 200, `Public page ${lang}${path}: ${response.status()}`);
        await tab.waitForFunction(() => window.__verticalRoutes?.length === 2);
        check(await tab.locator('[data-living-map]').count() === 1, 'Duplicate or missing Canvas');
        check(await tab.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Overflow: ' + lang + path);
        const geometry = await tab.evaluate(() => ({
          end: __verticalRoutes[0].points.at(-1).y,
          footer: document.querySelector('.site-footer').getBoundingClientRect().bottom + scrollY - 12,
          pointer: getComputedStyle(document.querySelector('[data-living-map]')).pointerEvents,
        }));
        check(Math.abs(geometry.end - geometry.footer) < 2, 'Route must reach footer: ' + path);
        check(geometry.pointer === 'none', 'Canvas intercepts controls');
        matrix.push(lang + path);
      }
    }
    for (const width of [390, 768, 1280]) {
      await tab.setViewportSize({width,height:900});
      for (const path of ['catalog/', 'about/', 'faq/', 'privacy/', 'place/15-brush-and-clay-atelier/']) {
        await tab.goto(base + '/ru/' + path);
        if (width >= 1024) await tab.waitForFunction(() => window.__verticalRoutes?.length === 2);
        else check(await tab.locator('[data-living-map]').evaluate(e => getComputedStyle(e).display === 'none'), 'Narrow page shows decoration');
        await tab.locator('.site-footer').scrollIntoViewIfNeeded();
        await tab.waitForTimeout(100);
        const overflow = await tab.evaluate(() => {
          const canvas = document.querySelector('[data-living-map]');
          const withCanvas = document.documentElement.scrollWidth;
          canvas.style.display = 'none';
          const withoutCanvas = document.documentElement.scrollWidth;
          canvas.style.display = '';
          return {withCanvas,withoutCanvas,width:innerWidth};
        });
        check(overflow.withCanvas <= Math.max(overflow.width, overflow.withoutCanvas), `Canvas adds overflow: ${width} ${path}`);
        if (overflow.withoutCanvas > width) existingOverflow.push({width,path,...overflow});
        if (width >= 1024) check(await tab.evaluate(() => __verticalRoutes.every(r => r.points.every(p => p.x >= 0 && p.x <= innerWidth))), 'Trail outside viewport');
      }
    }
    await tab.goto(base + '/ru/auth/login/');
    check(await tab.locator('[data-living-map]').count() === 0, 'Login must not load decoration');
    check(await tab.evaluate(() => !window.KidsMapLivingScene), 'Login downloads scene script');
    await tab.setViewportSize({width:1440,height:1000});
    await tab.goto(base + '/ru/faq/');
    const faq = tab.locator('main summary').first();
    if (await faq.count()) {
      await faq.click();
      check(await faq.evaluate(e => e.parentElement.open), 'FAQ stopped opening');
    }
    await tab.goto(base + '/ru/about/');
    await tab.locator('main a[href="/ru/catalog/"]').first().click();
    check(tab.url() === base + '/ru/catalog/', 'Catalog navigation failed');
    check(errors.length === 0, JSON.stringify(errors));
    return {passed:true,publicLanguagePages:matrix.length,responsivePages:15,errors,existingOverflow};
  } finally { await context.close(); }
}
