/* Rendered localization/focus sweep on disposable Place-owner bridge. */
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
if (!output?.startsWith('/tmp/task33-12-')) throw Error('Private output required');
(async () => {
  const browser = await playwright.chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext();
  const page = await context.newPage();
  const data = { status: 'RUNNING', cases: [], page_errors: [] };
  page.on('pageerror', e => data.page_errors.push(e.message));
  try {
    for (const lang of ['az','ru','en']) for (const width of [390,1024]) {
      await page.setViewportSize({width,height:900});
      const response = await page.goto('http://127.0.0.1:8772/place-owner?lang='+lang,{waitUntil:'networkidle'});
      const section = page.locator('#organization-links');
      const heading = (await section.locator('h2').textContent()).trim();
      const expected = {az:'Təşkilat əlaqələri',ru:'Связи с организациями',en:'Organization links'}[lang];
      assert.equal(response.status(),200); assert.equal(heading,expected);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth-innerWidth);
      assert(overflow<=1);
      const button = section.locator('form[action*=detach] button').first();
      assert.equal(await button.count(),0); // detached in prior POST flow
      const confirm = section.locator('form[action*=confirm] button').first();
      await confirm.focus();
      const focused = await confirm.evaluate(el => document.activeElement===el);
      assert(focused);
      data.cases.push({lang,width,status:200,heading,overflow,focus:focused});
    }
    assert.deepEqual(data.page_errors,[]);
    data.status='PASS';
    fs.writeFileSync(path.join(output,'affiliation-locales.json'),JSON.stringify(data,null,2));
    console.log(JSON.stringify(data));
  } catch(e) { data.status='FAIL'; data.error=e.message; fs.writeFileSync(path.join(output,'affiliation-locales.json'),JSON.stringify(data,null,2)); throw e; }
  finally { await context.close(); await browser.close(); }
})().catch(e => { console.error(e.message); process.exitCode=1; });
