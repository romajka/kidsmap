/* Real layout regression. Uses the existing isolated-browser fixture contract. */
const H = require('./helpers.cjs');
const widths = [390, 768, 1024, 1280, 1440];
async function geometry(page, count) {
  await page.waitForFunction(() => {
    const img = document.querySelector('.swiper-slide-active .place-gallery__image');
    return img && img.complete && img.naturalWidth > 0;
  });
  const result = await page.evaluate(() => {
    const main = document.querySelector('[data-place-gallery-main]');
    const slide = main.querySelector('.swiper-slide-active');
    const image = slide.querySelector('.place-gallery__image');
    return {
      viewport: innerWidth,
      main: main.getBoundingClientRect().width,
      slide: slide.getBoundingClientRect().width,
      image: image.getBoundingClientRect().width,
      imageHeight: image.getBoundingClientRect().height,
      naturalWidth: image.naturalWidth,
      count: main.querySelectorAll('.swiper-slide').length,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    };
  });
  H.assert.equal(result.count, count);
  H.assert(result.main > 100 && result.main <= result.viewport, JSON.stringify(result));
  H.assert(Math.abs(result.slide - result.main) < 2, JSON.stringify(result));
  H.assert(Math.abs(result.image - result.main) < 2 && result.imageHeight > 50, JSON.stringify(result));
  H.assert(result.overflow <= 1, JSON.stringify(result));
  return result;
}
async function gallery(ctx) {
  for (const lang of ['az', 'ru', 'en']) {
    for (const count of [1, 5]) {
      const fixture = ctx.fixture.fixtures[count === 1 ? 'gallery_one' : 'gallery_five'];
      H.assert(fixture, 'Explicit one/five-photo fictional fixtures required');
      const context = await H.context(ctx.browser, ctx.fixture.origin, 390);
      try {
        const page = await context.newPage();
        const watched = H.watch(page, ctx.fixture.origin);
        const url = ctx.fixture.origin + fixture.urls[lang];
        for (const width of widths) {
          await page.setViewportSize({width, height: 1000});
          await page.goto(url);
          const measured = await geometry(page, count);
          if (count === 5) {
            await page.locator('[data-place-gallery-next]').click();
            await page.waitForFunction(() => document.querySelector('[data-place-gallery-current]').textContent === '2');
            await geometry(page, count);
            await page.locator('[data-place-gallery-thumb]').last().click();
            await page.waitForFunction(() => document.querySelector('[data-place-gallery-current]').textContent === '5');
            await geometry(page, count);
            await page.locator('[data-place-gallery-prev]').click();
            await page.waitForFunction(() => document.querySelector('[data-place-gallery-current]').textContent === '4');
            await page.locator('[data-place-gallery-thumb]').first().press('Enter');
            await page.waitForFunction(() => document.querySelector('[data-place-gallery-current]').textContent === '1');
          }
          ctx.record({lang, count, phase: 'reload', ...measured, status: 'PASS'});
          if (width === 390 || width === 768) await page.screenshot({path: H.path.join(ctx.out, `gallery-${lang}-${count}-${width}.png`)});
        }
        // Same initialized gallery must shrink and grow without a page reload.
        for (const width of [...widths].reverse()) {
          await page.setViewportSize({width, height: 1000});
          await page.waitForFunction(() => Math.abs(document.querySelector('.swiper-slide-active').getBoundingClientRect().width - document.querySelector('[data-place-gallery-main]').getBoundingClientRect().width) < 2);
          ctx.record({lang, count, phase: 'resize', ...await geometry(page, count), status: 'PASS'});
        }
        H.assert.deepEqual(watched.errors, []);
        H.assert.deepEqual(watched.requests, []);
      } finally { await context.close(); }
    }
  }
}
module.exports = {gallery};
if (require.main === module) (async () => {
  const fixture = JSON.parse(H.fs.readFileSync(process.argv[2], 'utf8'));
  H.assert.equal(fixture.synthetic, true);
  const out = process.argv[3]; H.fs.mkdirSync(out, {recursive: true});
  const browser = await H.launch(); const states = [];
  try { await gallery({browser, fixture, out, record: x => states.push(x)}); }
  finally { await browser.close(); H.fs.writeFileSync(H.path.join(out, 'gallery-matrix.json'), JSON.stringify(states, null, 2)); }
  console.log(JSON.stringify({states: states.length, status: 'PASS'}));
})().catch(error => { console.error(error); process.exitCode = 1; });
