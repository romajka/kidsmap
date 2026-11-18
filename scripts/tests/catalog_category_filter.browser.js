// Run on a local catalog page with public places in at least two categories.
async page => {
  await page.setViewportSize({ width: 1280, height: 900 });
  const picker = page.locator('#filters-form #custom-select-category');
  const list = page.locator('#filters-form [data-km-cat-list]').getByRole('radiogroup');
  const trigger = picker.getByRole('button');
  const results = page.locator('.results-count-text');
  const initialCount = await results.innerText();
  const category = list.getByRole('radio').nth(1);
  const code = await category.getAttribute('data-select-value');
  await category.click();
  await page.waitForURL(url => url.searchParams.get('category') === code);
  if (await results.innerText() === initialCount) throw new Error('Category selection did not narrow the results');
  if (await list.getByRole('radio', { checked: true }).getAttribute('data-select-value') !== code) {
    throw new Error('The sidebar does not reflect the filter selection');
  }

  await list.locator('[data-select-value=""]').click();
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
  await picker.locator('[role="option"][data-select-value="' + code + '"]').click();
  await page.waitForURL(url => url.searchParams.get('category') === code);
  if (await results.innerText() === initialCount) throw new Error('The tablet drawer did not filter the results');
  const strip = page.getByRole('tablist').filter({ has: page.locator('[data-select-target="category"]') });
  await strip.locator('[data-select-value=""]').click();
  await page.waitForURL(url => !url.searchParams.has('category'));
  if (await results.innerText() !== initialCount) throw new Error('The tablet category strip did not reset the results');
};
