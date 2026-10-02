/* Validate account-scoped browser fallback and offline state on isolated loopback. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const cache = path.join(require('node:os').homedir(), '.npm/_npx');
let modulePath;
for (const dir of fs.readdirSync(cache)) {
  const candidate = path.join(cache, dir, 'node_modules/playwright');
  if (fs.existsSync(candidate + '/package.json') && JSON.parse(fs.readFileSync(candidate + '/package.json')).version === '1.55.0') {
    modulePath = candidate;
    break;
  }
}
if (!modulePath) throw Error('Cached Playwright 1.55.0 unavailable');
const { chromium } = require(modulePath);

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext();
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    return url.hostname === '127.0.0.1' && url.port === '8768' ? route.continue() : route.abort();
  });
  try {
    const page = await context.newPage();
    for (const lang of ['az', 'ru', 'en']) {
      await page.goto(`http://127.0.0.1:8768/owner?lang=${lang}`, { waitUntil: 'networkidle' });
      const online = await page.evaluate(() => {
        const form = document.querySelector('[data-permanent-place-form]');
        const field = form.querySelector('[name="description_az"]');
        field.value = 'Browser fallback probe';
        field.dispatchEvent(new Event('input', { bubbles: true }));
        return { account: form.dataset.accountId, object: form.dataset.draftKey,
          keys: Object.keys(localStorage), status: form.querySelector('[data-pw-draft-status]')?.textContent };
      });
      assert(online.account && online.object);
      const key = `kidsmap:permanent:v1:${online.account}:${online.object}`;
      assert(online.keys.includes(key), `${lang} account/object key missing`);
      assert(online.status, `${lang} browser-only status missing`);
      await context.setOffline(true);
      const offline = await page.evaluate(() => {
        const form = document.querySelector('[data-permanent-place-form]');
        const field = form.querySelector('[name="description_az"]');
        field.value = 'Offline recovery probe';
        field.dispatchEvent(new Event('input', { bubbles: true }));
        return { status: form.querySelector('[data-pw-draft-status]')?.textContent,
          value: JSON.parse(localStorage.getItem(`kidsmap:permanent:v1:${form.dataset.accountId}:${form.dataset.draftKey}`)).data.description_az };
      });
      assert.equal(offline.value, 'Offline recovery probe');
      assert(offline.status && offline.status !== online.status, `${lang} offline status not distinct`);
      await context.setOffline(false);
    }
    console.log(JSON.stringify({ languages: 3, account_scoped_key: 'PASS', browser_only_status: 'PASS', offline_recovery: 'PASS' }));
  } finally {
    await context.close();
    await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
