async (page) => {
  const out = '/mnt/c/kidsmap/docs/task33/final-audit/report-preview';
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const results = [];
  for (const width of [1440, 390]) {
    await page.setViewportSize({width, height: 960});
    await page.goto('http://127.0.0.1:8799/report.html', {waitUntil: 'networkidle'});
    await page.locator('#requirement-search').fill('R19-');
    const filtered = await page.locator('.requirement:not([hidden])').count();
    if (!filtered || filtered >= 306) throw Error('Requirement search did not filter');
    await page.locator('#requirement-search').fill('');
    await page.evaluate(async () => {
      const images = [...document.images];
      for (const img of images) img.loading = 'eager';
      await Promise.all(images.map(img => img.decode()));
    });
    const state = await page.evaluate(() => ({
      viewport: innerWidth, documentWidth: document.documentElement.scrollWidth,
      requirements: document.querySelectorAll('.requirement').length,
      visibleRequirements: document.querySelectorAll('.requirement:not([hidden])').length,
      images: document.images.length,
      brokenImages: [...document.images].filter(x => !x.complete || !x.naturalWidth).length,
      tables: document.querySelectorAll('table').length,
      sectionCount: document.querySelectorAll('main>section').length,
    }));
    if (state.documentWidth > width || state.requirements !== 306 || state.visibleRequirements !== 306 || state.brokenImages) throw Error(JSON.stringify(state));
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({path: `${out}/report-${width}.png`});
    await page.locator('.gallery').scrollIntoViewIfNeeded();
    await page.screenshot({path: `${out}/gallery-${width}.png`});
    results.push({width, filtered, ...state});
  }
  if (errors.length) throw Error(errors.join('\n'));
  const record = {status: 'PASS', reportOnly: true, results, pageErrors: errors, applicationRuntime: 'NOT_PART_OF_THIS_REPORT_RENDER_CHECK'};
  return record;
}
