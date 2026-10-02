/* Rendered stage 12 checks against the isolated synthetic Django bridge. */
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
const output = process.argv[2];
if (!output || !output.startsWith('/tmp/task33-12-')) throw Error('Private stage 12 output required');
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext();
  const origin = 'http://127.0.0.1:8772';
  const result = { browser: browser.version(), matrix: [], screenshots: [], console_errors: [], page_errors: [], application_network_failures: [], blocked_external: [] };
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin === origin) return route.continue();
    result.blocked_external.push(url.origin);
    return route.abort();
  });
  const page = await context.newPage();
  page.on('console', message => { if (message.type() === 'error') result.console_errors.push(message.text()); });
  page.on('pageerror', error => result.page_errors.push(error.message));
  page.on('response', response => {
    if (response.url().startsWith(origin + '/static/') && response.status() >= 400) result.application_network_failures.push({ url: response.url().replace(origin, ''), status: response.status() });
  });
  try {
    const cases = await (await context.request.get(origin + '/scenarios')).json();
    result.duplicate_ids = [];
    assert(Array.isArray(cases) && cases.length, 'No synthetic scenarios');
    for (const scenario of cases) for (const lang of ['az', 'ru', 'en']) for (const width of [320, 360, 390, 768, 1024, 1280, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      const response = await page.goto(origin + scenario.path + '?lang=' + lang, { waitUntil: 'networkidle' });
      assert.equal(response.status(), scenario.status || 200, `${scenario.id} ${lang}/${width} HTTP`);
      let overflow = null;
      if (response.status() === 200) {
        assert(await page.locator('main h1, [role="main"] h1, h1').count(), `${scenario.id} ${lang}/${width} heading`);
        const layout = await page.evaluate(() => ({ viewport: innerWidth, scroll: document.documentElement.scrollWidth, duplicate_ids: [...document.querySelectorAll('[id]')].map(node => node.id).filter((id, index, all) => all.indexOf(id) !== index) }));
        if (layout.scroll - layout.viewport > 1) {
          const offenders = await page.evaluate(() => [...document.querySelectorAll('body *')].map(node => ({tag: node.tagName, className: typeof node.className === 'string' ? node.className : '', scrollWidth: node.scrollWidth, left: Math.round(node.getBoundingClientRect().left), right: Math.round(node.getBoundingClientRect().right)})).filter(row => row.right > innerWidth + 1 || row.left < -1).slice(0, 20));
          result.overflow_failure = {scenario: scenario.id, lang, width, delta: layout.scroll - layout.viewport, offenders};
          await page.screenshot({path: path.join(output, `${scenario.id}-${lang}-${width}-overflow.png`), fullPage: true});
        }
        overflow = layout.scroll - layout.viewport;
        if (layout.duplicate_ids.length) result.duplicate_ids.push({scenario: scenario.id, lang, width, ids: layout.duplicate_ids});
        const file = `${scenario.id}-${lang}-${width}.png`;
        await page.screenshot({ path: path.join(output, file), fullPage: true });
        result.screenshots.push(file);
      }
      result.matrix.push({ scenario: scenario.id, lang, width, status: typeof overflow === 'number' && overflow > 1 ? 'FAIL' : 'PASS', overflow: typeof overflow === 'number' ? overflow : null, http: response.status() });
    }
    assert.deepEqual(result.page_errors, [], 'JavaScript page errors');
    assert.deepEqual(result.application_network_failures, [], 'Application network failures');
    result.status = result.matrix.some(row => row.status === 'FAIL') || result.duplicate_ids.length || result.page_errors.length || result.application_network_failures.length ? 'FAIL' : 'PASS';
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify({ status: result.status, matrix: result.matrix.length, screenshots: result.screenshots.length, page_errors: result.page_errors.length, application_network_failures: result.application_network_failures.length }));
  } catch (error) {
    result.status = 'FAIL'; result.error = error.message;
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(result, null, 2));
    throw error;
  } finally {
    await context.close(); await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
