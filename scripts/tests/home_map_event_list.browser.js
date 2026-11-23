// Run with Playwright CLI run-code on a homepage with at least 12 upcoming map events.
async page => {
  const section = page.locator('#home-map-section');
  const map = section.locator('#home-map');
  const list = section.locator('.km-evlist');
  const rows = list.locator('[data-km-evlist]');
  const places = section.locator('[data-home-map-list]');
  const results = [];

  await page.emulateMedia({ reducedMotion: 'reduce' });
  for (const width of [1440, 1024, 768, 390]) {
    await page.setViewportSize({ width, height: 900 });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await map.scrollIntoViewIfNeeded();
    const engine = await page.waitForFunction(() => document.querySelector('#home-map')?.__kmEventLayer?.engine);
    await section.locator('.km-mode--events').click();
    if (width < 768) await section.locator('[data-home-explorer-tab="list"]').click();
    await rows.first().waitFor();
    const rowCount = await rows.count();
    if (rowCount < 12) throw new Error('The homepage fixture needs at least 12 upcoming map events');

    const bounds = await list.evaluate(element => ({
      listBottom: element.getBoundingClientRect().bottom,
      panelBottom: element.parentElement.getBoundingClientRect().bottom,
      height: element.clientHeight,
      contentHeight: element.scrollHeight,
    }));
    if (bounds.listBottom > bounds.panelBottom + 1 || bounds.contentHeight <= bounds.height) {
      throw new Error(`Events must scroll inside the map list at ${width}px: ${JSON.stringify(bounds)}`);
    }

    await rows.first().hover();
    const pagePosition = await page.evaluate(() => window.scrollY);
    await page.mouse.wheel(0, 240);
    await page.waitForFunction(() => document.querySelector('.km-evlist').scrollTop > 0);
    if (await page.evaluate(() => window.scrollY) !== pagePosition) {
      throw new Error(`Wheel scrolling over the event list moved the page at ${width}px`);
    }
    await rows.last().focus();
    const lastRowVisible = await rows.last().evaluate(row => {
      const item = row.getBoundingClientRect();
      const scrollport = row.closest('.km-evlist').getBoundingClientRect();
      return item.top >= scrollport.top - 1 && item.bottom <= scrollport.bottom + 1;
    });
    if (!lastRowVisible) throw new Error(`Keyboard focus could not reach the last event at ${width}px`);

    await section.locator('.km-mode--places').click();
    await list.waitFor({ state: 'hidden' });
    await places.locator('button').first().waitFor();
    await section.locator('.km-mode--all').click();
    await places.locator('button').first().waitFor();
    results.push({ width, engine: await engine.jsonValue(), rowCount, listHeight: bounds.height });
  }
  return results;
}
