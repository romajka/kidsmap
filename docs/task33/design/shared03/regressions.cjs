/* Reproducible real-browser prototype acceptance. No Django, DB or external API. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
let pwPath = process.env.STAGE03_PLAYWRIGHT_MODULE;
if (!pwPath) {
  try { pwPath = require.resolve('playwright'); }
  catch {
    const cache = path.join(require('node:os').homedir(), '.npm/_npx');
    if (fs.existsSync(cache)) for (const dir of fs.readdirSync(cache)) {
      const candidate = path.join(cache, dir, 'node_modules/playwright');
      if (fs.existsSync(candidate + '/package.json') && JSON.parse(fs.readFileSync(candidate + '/package.json')).version === '1.55.0') { pwPath = candidate; break; }
    }
  }
}
if (!pwPath) throw new Error('Playwright is unavailable. Set STAGE03_PLAYWRIGHT_MODULE to an existing Playwright library.');
const { chromium } = require(pwPath);

(async()=>{const browser=await chromium.launch();const page=await browser.newPage();const assert=require('node:assert/strict');const results=[];const base='http://127.0.0.1:8763/docs/task33/design/';async function check(name,fn){try{await fn();results.push({name,status:'PASS'});}catch(e){results.push({name,status:'FAIL',error:e.message});}}
await check('new proposal is unpublished/unowned',async()=>{await page.goto(base+'admin/review.html?lang=en&state=new');assert(!(await page.locator('.axes').textContent()).includes('Published'));assert(!(await page.locator('.axes').textContent()).includes('Owner assigned'));});
await check('garden match does not open unrelated map marker',async()=>{await page.goto(base+'public/catalog.html?lang=en');await page.locator('#search').fill('Quiet garden');await page.locator('#catalog-map').click();assert(await page.locator('#venue').isDisabled());});
await check('org name does not return unrelated garden',async()=>{await page.goto(base+'public/catalog.html?lang=en');await page.locator('#search').fill('Discovery network');assert(await page.locator('[data-place="park"]').isHidden());});
await check('month survives reload beyond initial fixture months',async()=>{await page.goto(base+'public/events.html?lang=en&month=2026-11');await page.locator('#next-month').click();await page.reload();assert.equal(new URL(page.url()).searchParams.get('month'),'2026-12');});
await check('shared venue shows independent filtered business cards',async()=>{await page.goto(base+'public/catalog.html?lang=en');await page.locator('#catalog-map').click();await page.locator('#venue').click();assert.equal(await page.locator('[data-venue-place]:visible').count(),2);await page.locator('#activity-filter').selectOption('robotics');await page.locator('#venue').click();assert.equal(await page.locator('[data-venue-place]:visible').count(),1);});
await browser.close();fs.writeFileSync(path.join(__dirname,'regression-results.json'),JSON.stringify({generated_at:new Date().toISOString(),status:results.every(r=>r.status==='PASS')?'PASS':'FAIL',checks:results},null,2)+'\n');console.log(JSON.stringify(results,null,2));process.exitCode=results.some(r=>r.status==='FAIL')?1:0;})();
