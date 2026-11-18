// Run on a local catalog page with public places in at least two categories.
async page => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const picker = page.locator('#filters-form #custom-select-category');
  const strip = page.getByRole('tablist').filter({ has: page.locator('[data-select-target="category"]') });
  const trigger = picker.getByRole('button');
  const results = page.locator('.results-count-text');
  const initialCount = await results.innerText();
  await strip.waitFor({ state: 'visible' });
  await trigger.click();
  const option = picker.locator('[role="option"][data-select-value]:not([data-select-value=""])').first();
  const code = await option.getAttribute('data-select-value');
  await option.click();
  await page.waitForURL(url => url.searchParams.get('category') === code);
  if (await results.innerText() === initialCount) throw new Error('Category selection did not narrow the results');
  if (await strip.getByRole('tab', { selected: true }).getAttribute('data-select-value') !== code) {
    throw new Error('The category strip does not reflect the filter selection');
  }

  await strip.locator('[data-select-value=""]').click();
  await page.waitForURL(url => !url.searchParams.has('category'));
  if (await picker.locator('select').inputValue() !== '' || await results.innerText() !== initialCount) {
    throw new Error('Choosing all categories did not restore the unfiltered catalog');
  }

  await page.setViewportSize({ width: 768, height: 900 });
  await page.locator('.mobile-catalog-search [data-filters-open]').click();
  const drawer = await page.getByRole('dialog').boundingBox();
  if (!drawer || drawer.x !== 0 || Math.abs(drawer.y + drawer.height - 900) > 1) {
    throw new Error('The tablet filter panel is not anchored to the viewport');
  }
  await page.locator('#filters-form .km-btn-apply').waitFor({ state: 'visible' });
  await trigger.click();
  await option.click();
  await page.waitForURL(url => url.searchParams.get('category') === code);
  if (await results.innerText() === initialCount) throw new Error('The tablet drawer did not filter the results');
};
