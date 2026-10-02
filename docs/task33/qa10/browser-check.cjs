/* Real Chromium QA against synthetic, isolated stage 10 Django bridge. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const cache = path.join(require('node:os').homedir(), '.npm/_npx');
let modulePath;
for (const dir of fs.readdirSync(cache)) {
  const candidate = path.join(cache, dir, 'node_modules/playwright');
  if (fs.existsSync(candidate + '/package.json') && JSON.parse(fs.readFileSync(candidate + '/package.json')).version === '1.55.0') { modulePath = candidate; break; }
}
if (!modulePath) throw Error('Cached Playwright 1.55.0 unavailable');
const { chromium } = require(modulePath);
const output = process.argv[2];
if (!output || !output.startsWith('/tmp/task33-10-')) throw Error('Private stage 10 output required');
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext();
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    return url.hostname === '127.0.0.1' && url.port === '8769' ? route.continue() : route.abort();
  });
  const page = await context.newPage();
  const result = { browser: browser.version(), matrix: [], import: [], draft_saves: [], screenshots: [], console_errors: [] };
  page.on('pageerror', error => result.console_errors.push(error.message));
  try {
    const fixture = await (await context.request.get('http://127.0.0.1:8769/fixture')).json();
    const names = { az: ['Sınaq dərsi', 'Qeydiyyat'], ru: ['Пробное занятие', 'Вступительный взнос'], en: ['Trial lesson', 'Registration fee'] };
    if (!process.argv.includes('--import-only')) for (const lang of ['az', 'ru', 'en']) for (const width of [320, 360, 390, 768, 1024, 1280, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      const response = await page.goto(`http://127.0.0.1:8769/detail?lang=${lang}`, { waitUntil: 'networkidle' });
      assert.equal(response.status(), 200, `${lang}/${width} detail status`);
      const rows = page.locator('.detail-plans__row');
      assert.equal(await rows.count(), 1, `${lang}/${width} one group block`);
      const text = await rows.first().innerText();
      assert(text.includes('90') && text.includes('15'), `${lang}/${width} regular and fee`);
      for (const name of names[lang]) assert(text.includes(name), `${lang}/${width} ${name}`);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      assert(overflow <= 1, `${lang}/${width} horizontal overflow ${overflow}`);
      const shot = `public-${lang}-${width}.png`;
      await page.screenshot({ path: path.join(output, shot), fullPage: true });
      result.screenshots.push(shot);
      result.matrix.push({ lang, width, status: 'PASS', overflow });
    }
    for (const lang of ['az', 'ru', 'en']) {
      await page.setViewportSize({ width: 390, height: 900 });
      const response = await page.goto(`http://127.0.0.1:8769/admin?lang=${lang}`, { waitUntil: 'networkidle' });
      assert.equal(response.status(), 200, `${lang} admin status`);
      assert.equal(await page.locator('#id_nested_pricing').count(), 1, `${lang} nested input`);
      await page.locator('[data-place-json-import-open]').click();
      const payload = { schema_version: 1, place_id: fixture.place_id, base_content_version: fixture.base_content_version,
        nested_pricing: { pricing_schema_version: 2, activities: [{ id: fixture.activity_id, groups: [{ id: fixture.group_id, pricing_plans: [
          { product_type: 'membership', price: '90', billing_mode: 'recurring', billing_interval: 'month', billing_interval_count: 1 }
        ] }] }] } };
      await page.locator('[data-place-json-import-input]').fill(JSON.stringify(payload));
      await page.locator('[data-place-json-import-apply]').click();
      const confirm = page.getByText('Продолжить импорт', { exact: true });
      await confirm.waitFor({ state: 'visible', timeout: 5000 });
      await confirm.click();
      const nested = await page.locator('#id_nested_pricing').inputValue();
      if (!nested) throw Error(`${lang} nested UI import empty; message=${await page.locator('[data-place-json-import-message]').innerText()}; dialog=${await page.locator('[data-place-json-import-dialog]').evaluate(node => node.open)}`);
      assert.equal(JSON.parse(nested).pricing_schema_version, 2, `${lang} nested UI import`);
      result.import.push({ lang, status: 'PASS' });
    }
      const saved = await page.evaluate(async () => {
        const form = document.querySelector('input[name="publication_token"]').form;
        const body = new URLSearchParams();
        for (const [key, value] of new FormData(form)) if (typeof value === 'string') body.append(key, value);
        body.set('form_action', 'save_draft'); body.set('_save_draft', '1'); body.set('action', 'admin_save');
        body.delete('_publish_place');
        const response = await fetch(window.location.pathname + window.location.search, { method: 'POST', body });
        const html = await response.text();
        return { status: response.status, errors: [...new DOMParser().parseFromString(html, 'text/html').querySelectorAll('.errorlist')].map(node => node.textContent.trim()) };
      });
      assert.equal(saved.status, 302, `en imported draft save: ${saved.errors.join('; ')}`);
      await page.goto(`http://127.0.0.1:8769/detail?lang=en`, { waitUntil: 'networkidle' });
      const liveText = await page.locator('.detail-plans__row').first().innerText();
      for (const name of names.en) assert(liveText.includes(name), `en imported draft changed approved group content`);
      result.draft_saves.push({ lang: 'en', imported_nested: true, status: 'PASS', approved_group_preserved: true });
    assert.deepEqual(result.console_errors, []);
    result.status = 'PASS';
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify({ status: 'PASS', matrix: result.matrix.length, import: result.import.length, draft_saves: result.draft_saves.length, screenshots: result.screenshots.length }));
  } catch (error) {
    result.status = 'FAIL'; result.error = error.message;
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(result, null, 2));
    throw error;
  } finally {
    await context.close(); await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
