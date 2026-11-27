// Run on an event detail page with a poster and at least one loadable gallery photo.
async (page) => {
  await page.emulateMedia({reducedMotion: 'no-preference'});
  const viewer = page.locator('[data-km-lb]');
  const opener = page.locator('[data-km-lb-open="0"]').first();
  const total = await viewer.locator('.km-lb__items > li').count();
  if (total < 2) throw new Error('The fixture needs a poster and a gallery image');

  async function visibleFrame(index) {
    await page.waitForFunction(({index, total}) => {
      const image = document.querySelector('[data-km-lb-img]');
      const counter = document.querySelector('[data-km-lb-count]');
      return counter.textContent === `${index} / ${total}` &&
        image.complete && image.naturalWidth > 0 &&
        getComputedStyle(image).opacity === '1' &&
        image.getAnimations().length === 0;
    }, {index, total});
  }

  await opener.click();
  await visibleFrame(1);
  await viewer.locator('[data-km-lb-next]').click();
  await visibleFrame(2);
  await viewer.locator('[data-km-lb-prev]').click();
  await visibleFrame(1);
  await page.keyboard.press('ArrowRight');
  await visibleFrame(2);
  await page.keyboard.press('ArrowLeft');
  await visibleFrame(1);
  await page.keyboard.press('Escape');
  await viewer.waitFor({state: 'hidden'});
  if (!await opener.evaluate(link => link === document.activeElement)) {
    throw new Error('The viewer should return focus to the photo that opened it');
  }
};
