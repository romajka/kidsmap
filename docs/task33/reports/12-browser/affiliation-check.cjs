/* Real Chromium Place-owner affiliation POST flow on disposable QA04 bridge. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
let playwright;
for (const dir of fs.readdirSync(path.join(require('node:os').homedir(), '.npm/_npx'))) {
  const candidate = path.join(require('node:os').homedir(), '.npm/_npx', dir, 'node_modules/playwright');
  if (fs.existsSync(candidate + '/package.json') && JSON.parse(fs.readFileSync(candidate + '/package.json')).version === '1.55.0') { playwright = require(candidate); break; }
}
if (!playwright) throw Error('Cached Playwright 1.55.0 unavailable');
const output = process.argv[2];
if (!output?.startsWith('/tmp/task33-12-')) throw Error('Private stage12 output required');
const origin = 'http://127.0.0.1:8772';
(async () => {
  const browser = await playwright.chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext();
  const page = await context.newPage();
  const result = { checks: [], page_errors: [], screenshots: [] };
  page.on('pageerror', e => result.page_errors.push(e.message));
  try {
    for (const width of [390, 1024]) {
      await page.setViewportSize({ width, height: 900 });
      const response = await page.goto(origin + '/place-owner?lang=en', { waitUntil: 'networkidle' });
      assert.equal(response.status(), 200);
      const section = page.locator('#organization-links');
      assert.equal(await section.count(), 1);
      const scroll = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert(scroll <= 1, `owner places overflow ${width}: ${scroll}`);
      assert.equal(await section.locator('form[action*="detach"]').count(), 1);
      const file = `place-owner-affiliation-en-${width}.png`;
      await page.screenshot({ path: path.join(output, file), fullPage: true });
      result.screenshots.push(file);
      result.checks.push(`place-owner affiliation visible and no overflow at ${width}`);
    }
    await page.setViewportSize({ width: 390, height: 900 });
    await page.goto(origin + '/place-owner?lang=en', { waitUntil: 'networkidle' });
    const join = page.locator('#organization-links form[data-join-form]');
    assert.equal(await join.count(), 1);
    await join.locator('[name=place_id]').selectOption({ label: 'Pending QA place' });
    await join.locator('button[type=submit]').focus();
    const joinResponse = page.waitForResponse(r => r.request().method() === 'POST' && r.url().includes('/join/'));
    await page.keyboard.press('Enter');
    result.join_post_status = (await joinResponse).status();
    await page.locator('#organization-links .org-pending-row').filter({ hasText: 'Pending QA place' }).waitFor({ state: 'visible' });
    result.join_url = page.url();
    result.join_pending_count = await page.locator('#organization-links .org-pending-row').filter({ hasText: 'Pending QA place' }).count();
    assert.equal(result.join_pending_count, 1);
    result.checks.push('join form keyboard POST creates pending request');
    assert.equal((await context.request.get(origin + '/make-stale')).status(), 200);
    await page.goto(origin + '/place-owner?lang=en', { waitUntil: 'networkidle' });
    const stale = page.locator('#organization-links .org-pending-row').filter({ hasText: 'Stale QA place' });
    assert.equal(await stale.count(), 1);
    const staleResponse = page.waitForResponse(r => r.request().method() === 'POST' && r.url().includes('/confirm/'));
    await stale.locator('button[type=submit]').click();
    assert.equal((await staleResponse).status(), 409);
    await page.locator('main.account-page-wrapper h1').waitFor({ state: 'visible' });
    assert.equal(await page.locator('main.account-page-wrapper h1').count(), 1);
    result.checks.push('stale pending join confirmation POST returns 409');
    await page.goto(origin + '/place-owner?lang=en', { waitUntil: 'networkidle' });
    const linked = page.locator('#organization-links .org-pending-row').filter({ hasText: 'Linked QA place' });
    assert.equal(await linked.count(), 1);
    const detachResponse = page.waitForResponse(r => r.request().method() === 'POST' && r.url().includes('/detach/'));
    await linked.locator('button[type=submit]').click();
    assert.equal((await detachResponse).status(), 302);
    await page.locator('#organization-links .org-pending-row').filter({ hasText: 'Linked QA place' }).waitFor({ state: 'detached' });
    assert.equal(await page.locator('#organization-links form[action*="detach"]').count(), 0);
    result.checks.push('place-owner detach POST succeeds and affiliation disappears');
    assert.deepEqual(result.page_errors, []);
    result.status = 'PASS';
    fs.writeFileSync(path.join(output, 'affiliation-results.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
  } catch (e) {
    result.status = 'FAIL'; result.error = e.message;
    fs.writeFileSync(path.join(output, 'affiliation-results.json'), JSON.stringify(result, null, 2));
    throw e;
  } finally { await context.close(); await browser.close(); }
})().catch(e => { console.error(e.message); process.exitCode = 1; });
