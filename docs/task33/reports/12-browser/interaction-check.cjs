/* Real Chromium interaction checks against disposable stage 12 bridge. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
let playwright;
for (const dir of fs.readdirSync(path.join(require('node:os').homedir(), '.npm/_npx'))) {
  const candidate = path.join(require('node:os').homedir(), '.npm/_npx', dir, 'node_modules/playwright');
  if (fs.existsSync(candidate + '/package.json') && JSON.parse(fs.readFileSync(candidate + '/package.json')).version === '1.55.0') { playwright = require(candidate); break; }
}
if (!playwright) throw Error('Cached Playwright unavailable');
const output = process.argv[2];
if (!output?.startsWith('/tmp/task33-12-')) throw Error('Private stage12 output required');
const origin = 'http://127.0.0.1:8772';
(async () => {
  const browser = await playwright.chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext();
  const page = await context.newPage();
  const result = { checks: [], page_errors: [] };
  page.on('pageerror', e => result.page_errors.push(e.message));
  try {
    await page.goto(origin + '/zero?lang=en', { waitUntil: 'networkidle' });
    assert.equal(await page.locator('[data-empty-organizations]').count(), 1);
    assert.equal(await page.locator('[data-empty-standalone]').count(), 1);
    result.checks.push('zero-org and standalone empty states');
    const add = page.locator('.org-hero a.account-btn-action');
    assert.match(await add.getAttribute('href'), /\/account\/.*(create|add)|\/owner\/.*(create|add)/i);
    result.checks.push('Add place direct form link');
    await page.locator('[data-org-create-form] [name=name_az]').fill('Browser QA local draft');
    await page.waitForTimeout(100);
    result.create_status = await page.locator('[data-create-status]').textContent();
    result.create_storage = await page.evaluate(() => Object.entries(sessionStorage).filter(([key]) => key.startsWith('kidsmap:org:create:')).map(([, value]) => JSON.parse(value).name_az));
    assert.equal(result.create_status, 'Draft saved in this browser');
    assert.deepEqual(result.create_storage, ['Browser QA local draft']);
    result.checks.push('create draft persists in session storage');
    result.create_error = result.page_errors.find(x => /value|undefined/.test(x)) || null;
    await page.goto(origin + '/org-empty?lang=en', { waitUntil: 'networkidle' });
    assert.equal(await page.locator('[data-empty-branches]').count(), 1);
    result.checks.push('empty branch state');
    await page.locator('.org-tabs a[href="#org-about"]').focus();
    await page.keyboard.press('Enter');
    assert.equal(new URL(page.url()).hash, '#org-about');
    result.checks.push('keyboard tab navigation');
    await page.route('**/api/**', route => route.abort());
    await page.locator('[data-org-edit-form] [name=name_az]').fill('Browser QA failed draft');
    await page.waitForTimeout(1100);
    result.save_failure_status = await page.locator('[data-draft-status]').textContent();
    result.checks.push('draft save failure visible');
    await page.goto(origin + '/org-network?lang=en', { waitUntil: 'networkidle' });
    const ownerBranches = await page.locator('#org-branches article.org-row').count();
    assert(ownerBranches >= 2);
    await page.goto(origin + '/manager-selected?lang=en', { waitUntil: 'networkidle' });
    const managerBranches = await page.locator('#org-branches article.org-row').count();
    assert.equal(managerBranches, 1);
    assert.equal(await page.locator('[data-team-form]').count(), 0);
    assert.equal(await page.locator('#org-branches form[action*=detach]').count(), 0);
    result.checks.push('manager selected branch only; owner controls absent');
    result.branch_counts = { owner: ownerBranches, manager: managerBranches };
    const forbidden = await page.goto(origin + '/manager-forbidden?lang=en');
    assert.equal(forbidden.status(), 404);
    result.checks.push('manager direct URL denied');
    result.status = result.create_error ? 'FAIL' : 'PASS';
    fs.writeFileSync(path.join(output, 'interaction-results.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
  } catch (e) {
    result.status = 'FAIL'; result.error = e.message;
    fs.writeFileSync(path.join(output, 'interaction-results.json'), JSON.stringify(result, null, 2));
    throw e;
  } finally { await context.close(); await browser.close(); }
})().catch(e => { console.error(e.message); process.exitCode = 1; });
