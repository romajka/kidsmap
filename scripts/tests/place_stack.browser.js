// Playwright CLI run-code on a place detail with one or several real photos.
async page => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  // The gallery reads reduced-motion preferences when it mounts.
  await page.reload({ waitUntil: 'networkidle' });
  const gallery = page.getByRole('region', { name: /Галерея фотографий|Fotoqalereya|Photo gallery/i });
  const photos = gallery.locator('img');
  await gallery.waitFor({ timeout: 5000 });
  const labels = await photos.evaluateAll(images => images.map(image => image.alt.trim()));
  if (!labels.length || labels.some(label => !label)) throw new Error('Every photo needs an alt');
  const buttons = gallery.getByRole('button');
  if (labels.length === 1) {
    if (await buttons.count()) throw new Error('A single photo has navigation controls');
    return;
  }
  const current = gallery.locator('[aria-live="polite"]');
  async function expectPosition(index) {
    await current.getByText(String(index), { exact: true }).waitFor({ timeout: 2000 });
  }
  await gallery.focus();
  await page.keyboard.press('ArrowRight');
  await expectPosition(2);
  await page.keyboard.press('ArrowLeft');
  await expectPosition(1);

  const photo = gallery.getByRole('img').first();
  await photo.scrollIntoViewIfNeeded();
  const bounds = await photo.boundingBox();
  const session = await page.context().newCDPSession(page);
  try {
    const y = bounds.y + bounds.height / 2;
    const start = bounds.x + bounds.width * .8;
    const end = bounds.x + bounds.width * .2;
    await session.send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 1 });
    await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: start, y }] });
    for (let n = 1; n <= 6; n++) {
      await session.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: start + (end - start) * n / 6, y }] });
    }
    await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await expectPosition(2);
  } finally {
    await session.detach();
  }
};
