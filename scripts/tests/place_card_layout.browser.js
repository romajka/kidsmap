// Run on the local homepage with at least three recommended places that have phone buttons.
async (page) => {
  const check = (condition, message) => {
    if (!condition) throw new Error(message);
  };
  const base = new URL(page.url()).origin;
  await page.setViewportSize({width: 1569, height: 950});
  await page.emulateMedia({reducedMotion: 'no-preference'});
  await page.goto(base + '/ru/');
  const rail = page.locator('[data-places-rail]');
  const viewport = rail.locator('[data-rail-viewport]');
  const originals = rail.locator('[data-rail-original]');
  const copies = rail.locator('[data-rail-copy]');

  check(await originals.count() >= 3, 'The fixture needs three recommendations');
  await originals.evaluateAll(items => {
    items.slice(3).forEach(item => item.remove());
    const prices = ['Есть бесплатные и платные варианты', '120 ₼ / месяц', 'От 20 ₼'];
    items.slice(0, 3).forEach((item, index) => {
      item.querySelector('.card-stub-price').textContent = prices[index];
      item.querySelector('.card-rating-row')?.remove();
    });
    const rating = document.createElement('div');
    rating.className = 'card-rating-row';
    rating.textContent = '★ 5,0  1 отзыв';
    items[0].querySelector('.card-action-stack').before(rating);
  });
  await viewport.scrollIntoViewIfNeeded();
  await page.waitForFunction(() => {
    const rail = document.querySelector('[data-places-rail]');
    return rail.matches('.is-static, .is-automatic');
  });
  await page.evaluate(() => document.fonts.ready);

  check(await copies.count() === 0, 'A rail that fits must not repeat cards');
  check(!await rail.locator('[data-rail-next]').isVisible(), 'A rail that fits must hide its next button');
  const cards = await originals.evaluateAll(items => items.map(item => {
    const rect = selector => item.querySelector(selector).getBoundingClientRect();
    const open = rect('.card-go-btn');
    const phone = rect('.card-contact-toggle');
    return {
      controls: [open.width, open.height, phone.width, phone.height],
      actionTop: rect('.card-action-stack').top,
      bottomGap: rect('.place-card').bottom - rect('.card-action-stack').bottom,
    };
  }));
  check(cards.every(card => card.controls.every(size => Math.abs(size - 44) < 0.1)),
    'Price length must not resize either action');
  check(cards.every(card => Math.abs(card.actionTop - cards[0].actionTop) < 1 && card.bottomGap <= 1.1),
    'The price row must stay at the bottom whether or not the card has ratings');

  await page.setViewportSize({width: 768, height: 950});
  await copies.first().waitFor({state: 'attached'});
  check(await copies.locator('a:not([tabindex="-1"])').count() === 0, 'Copies must stay out of tab order');
  await rail.locator('[data-rail-next]').click();
  await page.waitForFunction(() => document.querySelector('[data-rail-viewport]').scrollLeft > 100);
  await page.setViewportSize({width: 1569, height: 950});
  await copies.first().waitFor({state: 'detached'});
  check(!await rail.locator('[data-rail-next]').isVisible(), 'Controls must hide again when the rail fits');
};
