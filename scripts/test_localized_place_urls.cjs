// Only isolated local synthetic forms. Config: {session, addPath, editPath}.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
(async () => {
  const base = process.env.PLACE_URL_BROWSER_ORIGIN || 'http://127.0.0.1:18763';
  assert.equal(new URL(base).hostname, '127.0.0.1');
  const config = JSON.parse(fs.readFileSync(process.env.PLACE_URL_BROWSER_CONFIG));
  const browser = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM_EXECUTABLE || undefined, args: ['--no-sandbox']});
  try {
    const context = await browser.newContext({permissions: ['clipboard-read', 'clipboard-write']});
    await context.addCookies([{name: 'sessionid', value: config.session, domain: '127.0.0.1', path: '/'}]);
    await context.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort());
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(base + config.addPath);
    const block = page.locator('[data-place-localized-urls]');
    await page.waitForFunction(() => { const block = document.querySelector('[data-place-localized-urls]'); return block && document.querySelector('[data-url-status]')?.textContent === block.dataset.labelNew; });
    await page.locator('[data-place-json-prompt-copy]').click();
    const prompt = page.locator('[data-place-json-prompt-input]');
    const original = await prompt.inputValue();
    assert(original.includes('НАЗВАНИЯ НА ТРЁХ ЯЗЫКАХ И АДРЕСА КАРТОЧКИ'));
    assert(original.includes('РАСПИСАНИЕ'));
    assert(original.includes('pricing_plans'));
    await page.locator('[data-place-json-prompt-copy-text]').click();
    assert.equal(await page.evaluate(() => navigator.clipboard.readText()), original);
    await prompt.fill('Changed instruction');
    await page.locator('[data-place-json-prompt-reset]').click();
    assert.equal(await prompt.inputValue(), original);
    await page.keyboard.press('Escape');
    for (const width of [390, 768, 1024, 1280, 1440]) {
      await page.setViewportSize({width, height: 1000});
      await block.scrollIntoViewIfNeeded();
      assert(await block.isVisible());
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `overflow at ${width}`);
    }
    if (config.editPath) {
      await page.goto(base + config.editPath);
      await page.waitForFunction(() => document.querySelector('[data-url-list]')?.children.length === 6);
      const before = await page.locator('[data-url-list] code').allTextContents();
      assert.equal(before.length, 3);
      assert(before.every(url => new URL(url, base).origin === base), 'Preview URLs must use the local request origin');
      await page.locator('[data-url-list] button').first().click();
      assert.equal(await page.evaluate(() => navigator.clipboard.readText()), new URL(before[0], base).href);
      assert.equal(await page.locator('[data-place-localized-urls] input').count(), 0, 'URL preview is read-only');
      // A names-only update must not erase existing pricing; explicit [] can clear it.
      const tariffField = page.locator('#id_pricing_plans');
      const tariffsBefore = await tariffField.inputValue();
      assert(JSON.parse(tariffsBefore).length > 0, 'Edit fixture must contain a tariff');
      await page.locator('[data-place-json-import-open]').click();
      await page.locator('[data-place-json-import-input]').fill(JSON.stringify({
        name_az: 'Synthetic imported place', name_ru: 'Тестовый импорт', name_en: 'Synthetic import',
      }));
      await page.locator('[data-place-json-import-apply]').click();
      await page.getByRole('button', {name: 'Продолжить импорт', exact: true}).click();
      assert.equal(await tariffField.inputValue(), tariffsBefore, 'Partial JSON must preserve existing tariffs');
      // Input may live in an inactive translation tab; use the active AZ name.
      await Promise.all([
        page.waitForResponse(response => response.url().includes('/url-preview/') && response.request().method() === 'POST'),
        page.locator('#id_name_az').fill('Synthetic renamed place'),
      ]);
      assert.deepEqual(await page.locator('[data-url-list] code').allTextContents(), before);
      async function importPricing(data) {
        await page.locator('[data-place-json-import-open]').click();
        await page.locator('[data-place-json-import-input]').fill(JSON.stringify(data));
        await page.locator('[data-place-json-import-apply]').click();
        await page.getByRole('button', {name: 'Продолжить импорт', exact: true}).click();
      }
      await importPricing({pricing_plans: []});
      assert.deepEqual(JSON.parse(await tariffField.inputValue()), [], 'Explicit empty list must still clear pricing');
      await importPricing({price_per_lesson: 25});
      const legacyPlans = JSON.parse(await tariffField.inputValue());
      assert.equal(legacyPlans.length, 1, 'Legacy scalar price must convert to a tariff');
      assert.equal(Number(legacyPlans[0].price), 25);

    }
    assert.deepEqual(errors, []);
    console.log('PASS: localized preview, fixed saved URLs, prompt copy/reset, five widths');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exitCode = 1;});
