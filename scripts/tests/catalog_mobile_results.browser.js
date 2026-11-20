// Run on a local catalog URL with three active filters and at least one place.
async page => {
  for (const width of [320, 375, 430]) {
    await page.setViewportSize({ width, height: 812 });
    const bar = page.locator('.active-filter-bar');
    const chips = bar.locator('.active-filter-chip');
    if (await chips.count() < 3) throw new Error('The fixture needs at least three filters');
    if ((await bar.boundingBox()).height > 50) throw new Error('Selected filters wrap on a phone');

    await chips.nth(await chips.count() - 2).press('Tab');
    const reset = await bar.locator('.active-filter-reset').boundingBox();
    const chip = await chips.last().boundingBox();
    if (chip.x + chip.width > reset.x + 1) throw new Error('The focused filter is behind Reset');

    const toolbar = page.locator('.results-toolbar');
    if ((await toolbar.boundingBox()).height > 140) throw new Error('The result count is squeezed');
    const card = page.locator('.grid .place-card').first();
    const nextCard = page.locator('.grid .place-card').nth(1);
    if (await nextCard.count()) {
      const first = await card.boundingBox();
      const second = await nextCard.boundingBox();
      if (second.y - first.y - first.height < 12) {
        throw new Error('Adjacent mobile cards must have a visible gap');
      }
    }
    const photo = await card.locator('.card-media-link').boundingBox();
    const title = await card.locator('.card-title').boundingBox();
    if (photo.x + photo.width > title.x || title.y >= photo.y + photo.height) {
      throw new Error('The title must sit beside the thumbnail');
    }
    const save = await card.locator('.like-btn').boundingBox();
    const open = await card.locator('.card-go-btn').boundingBox();
    const label = await card.locator('.card-go-btn > span').first().boundingBox();
    const arrow = await card.locator('.card-go-arrow').boundingBox();
    if (label.x < open.x - 1 || arrow.x + arrow.width > open.x + open.width + 1) {
      throw new Error('The translated Details label and arrow must fit inside the button');
    }
    if (save.y < photo.y + photo.height || Math.abs(save.y - open.y) > 2
        || save.x < open.x + open.width || save.width < 44 || save.height < 44) {
      throw new Error('Favorite must have its own touch target in the bottom action row');
    }
    const price = card.locator('.card-price-pill');
    if (await price.count()) {
      const bounds = await price.boundingBox();
      const separateRow = await price.evaluate(el => el.classList.contains('card-price-pill--long'));
      if (separateRow ? bounds.y + bounds.height > open.y + 1
                      : bounds.x + bounds.width > open.x || bounds.y < open.y - 1) {
        throw new Error('The full price and Details must each have their own space');
      }
    }
    const badge = card.locator('.card-category-overlay');
    if (await badge.count() && (await badge.boundingBox()).y >= title.y) {
      throw new Error('The category should identify the place above its title');
    }
    const offers = card.locator('.card-offer-details');
    if (await offers.count()) {
      const groups = offers.locator('[data-matched-group]').first();
      if (await groups.isVisible()) throw new Error('Matched groups should start collapsed');
      await offers.locator('summary').press('Enter');
      await groups.waitFor({ state: 'visible' });
      await offers.locator('summary').press('Enter');
    }
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) {
      throw new Error('The catalog overflows the viewport');
    }
  }
  const details = page.locator('.grid .place-card .card-go-btn').first();
  const destination = await details.evaluate(link => link.href);
  const catalogUrl = page.url();
  await details.hover();
  await page.mouse.down();
  const stableButton = await details.evaluate(link => {
    const style = getComputedStyle(link);
    return style.backgroundColor !== 'rgba(0, 0, 0, 0)' && style.backgroundImage === 'none'
      && style.transform === 'none' && getComputedStyle(link.closest('.place-card')).transform === 'none';
  });
  await page.mouse.up();
  if (!stableButton) throw new Error('Pressing Details should keep a solid button and a stationary card');
  await page.waitForURL(destination, {waitUntil: 'domcontentloaded'});
  await page.locator('h1').first().waitFor({state: 'visible'});
  await page.goBack({ waitUntil: 'commit' });
  await page.waitForURL(catalogUrl, { waitUntil: 'commit' });

  const bar = page.locator('.active-filter-bar');
  await bar.waitFor({ state: 'visible' });
  const count = await bar.locator('.active-filter-chip').count();
  const lastChip = bar.locator('.active-filter-chip').last();
  const nextUrl = await lastChip.evaluate(link => link.href);
  await lastChip.click();
  await page.waitForURL(nextUrl);
  if (await bar.locator('.active-filter-chip').count() !== count - 1) {
    throw new Error('Removing the last chip should keep the other filters');
  }
  await bar.locator('.active-filter-reset').click();
  await bar.waitFor({ state: 'detached' });
};
