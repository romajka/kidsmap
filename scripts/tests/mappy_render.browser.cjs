const assert = require('node:assert/strict');
const path = require('node:path');
const {test} = require('node:test');
const {chromium} = require('playwright');

test('a visible Mappy renders once per frame, including after scrolling back', async () => {
  const browser = await chromium.launch({
    channel: process.env.CHROME_CHANNEL || undefined,
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  try {
    const page = await browser.newPage();
    let releaseModel;
    const modelGate = new Promise(resolve => { releaseModel = resolve; });
    await page.route('https://mappy.invalid/**', async route => {
      const file = new URL(route.request().url()).pathname;
      if (file === '/') return route.fulfill({contentType:'text/html', body:`
        <body style="min-height:300vh"><div data-mappy3d style="width:120px;height:140px"></div>
        <script src="/js/mappy3d_boot.js" data-module="/3d/mappy3d.js" data-model="/3d/mappy.glb"></script>`});
      if (file === '/3d/mappy.glb') await modelGate;
      return route.fulfill({path:path.join(__dirname, '../../static', file)});
    });
    await page.addInitScript(() => {
      window.frameCounts = [];
      const request = window.requestAnimationFrame.bind(window);
      let lastTime, seen;
      window.requestAnimationFrame = callback => request(time => {
        if (time !== lastTime) {
          seen = new Map();
          lastTime = time;
          window.frameCounts.push(0);
        }
        const count = (seen.get(callback) || 0) + 1;
        seen.set(callback, count);
        const last = window.frameCounts.length - 1;
        window.frameCounts[last] = Math.max(window.frameCounts[last], count);
        callback(time);
      });
    });
    const modelRequested = page.waitForRequest('**/mappy.glb');
    await page.goto('https://mappy.invalid/', {waitUntil:'domcontentloaded'});
    await modelRequested;
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    releaseModel();
    await page.waitForFunction(() => document.querySelector('[data-mappy3d]').mappy?.ready);

    async function checkFrames() {
      await page.evaluate(() => { window.frameCounts.length = 0; });
      await page.waitForFunction(() => window.frameCounts.length >= 6, null, {polling:25});
      const counts = await page.evaluate(() => window.frameCounts.slice(1));
      assert.ok(counts.every(count => count === 1), `callbacks per frame: ${counts}`);
    }
    await checkFrames();
    await page.evaluate(() => scrollTo(0, innerHeight * 2));
    await page.waitForFunction(() => document.querySelector('[data-mappy3d]').getBoundingClientRect().bottom < 0);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await page.evaluate(() => scrollTo(0, 0));
    await checkFrames();
  } finally {
    await browser.close();
  }
});
