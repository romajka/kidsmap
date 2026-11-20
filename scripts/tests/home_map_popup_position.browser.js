// Run with Playwright CLI run-code on a local homepage with Google Maps and an individual place.
async page => {
  const map = page.locator('#home-map');
  const popup = map.locator('.gm-style-iw-c');
  const card = page.locator('.home-explorer-select').first();
  const pin = map.locator('.kidsmap-marker-button.is-selected');
  const results = [];

  async function checkPosition() {
    await popup.waitFor();
    await pin.waitFor();
    await page.waitForFunction(() => {
      const map = document.querySelector('#home-map');
      const popup = map.querySelector('.gm-style-iw-c')?.getBoundingClientRect();
      const pin = map.querySelector('.kidsmap-marker-button.is-selected')?.getBoundingClientRect();
      if (!popup || !pin || !popup.width || !popup.height) return false;
      const bounds = map.getBoundingClientRect();
      return popup.top >= bounds.top && popup.bottom <= bounds.bottom &&
        popup.left >= bounds.left && popup.right <= bounds.right &&
        Math.abs((popup.left + popup.right - pin.left - pin.right) / 2) <= 3 &&
        popup.bottom <= pin.top + 2;
    }, null, {timeout: 5000});
  }

  for (const width of [1440, 375]) {
    for (const reducedMotion of ['no-preference', 'reduce']) {
      await page.setViewportSize({width, height: 900});
      await page.emulateMedia({reducedMotion});
      await page.reload({waitUntil: 'domcontentloaded'});
      await map.scrollIntoViewIfNeeded();
      await map.locator('.kidsmap-marker-button').first().waitFor({state: 'attached'});
      if (width === 375) await page.locator('[data-home-explorer-tab="list"]').click();
      await card.click();
      await checkPosition();
      const pinName = await pin.getAttribute('aria-label');
      await popup.locator('button.gm-ui-hover-effect').click();
      await popup.waitFor({state: 'detached'});
      await map.getByRole('button', {name: pinName, exact: true}).click();
      await checkPosition();
      results.push({width, reducedMotion});
    }
  }
  return results;
}
