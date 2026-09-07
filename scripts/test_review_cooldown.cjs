// Run only against isolated fixtures with PLACE_REVIEW_COOLDOWN_SECONDS=3.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('fs');
const assert=require('node:assert/strict');
(async()=>{
 const config=JSON.parse(fs.readFileSync(process.env.REVIEW_BROWSER_CONFIG));
 const base=process.env.REVIEW_BROWSER_ORIGIN || 'http://127.0.0.1:18763';
 assert.equal(new URL(base).hostname,'127.0.0.1');
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE || undefined,args:['--no-sandbox']});
 try {
  const context=await browser.newContext({viewport:{width:375,height:900}});
  await context.addCookies([{name:'sessionid',value:config.session,domain:'127.0.0.1',path:'/'}]);
  await context.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());
  const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const url=base+'/ru'+config.place.replace(/^\/(ru|en)\//,'/');
  await page.goto(url);
  const form=page.locator('[data-review-submission]');await form.waitFor();
  await form.locator('.detail-stars__btn').nth(4).click();await form.locator('[name=text]').fill('Да!');
  const action=await form.getAttribute('action');
  const responsePromise=page.waitForResponse(r=>r.request().method()==='POST' && r.url().endsWith(action));
  await form.locator('[type=submit]').click();
  const response=await responsePromise;assert.equal(response.status(),200);
  const payload=await response.json();assert.equal(payload.cooldown.duration_seconds,3);
  const timer=page.locator('[data-review-cooldown]');await timer.waitFor();
  assert.equal(await form.isVisible(),false);
  assert.match(await timer.locator('[data-review-countdown]').innerText(),/^00:0[123]$/);
  await timer.screenshot({path:'/tmp/review-cooldown-mobile.png'});
  await page.reload();await timer.waitFor();assert.equal(await form.isVisible(),false);
  const csrf=await form.locator('[name=csrfmiddlewaretoken]').inputValue();
  const post=()=>page.request.post(base+action,{form:{csrfmiddlewaretoken:csrf,rating:'4',text:'Ещё один хороший отзыв'},headers:{'X-Requested-With':'XMLHttpRequest'}});
  const blocked=await post();assert.equal(blocked.status(),429);assert(Number(blocked.headers()['retry-after'])>0);
  assert.equal((await blocked.json()).code,'review_cooldown');
  // Tampering with wall-clock time must not unlock the form.
  await page.evaluate(()=>{Date.now=()=>8640000000000000;});
  assert.equal(await form.isVisible(),false);
  await form.waitFor();assert.equal(await timer.isVisible(),false);
  const concurrent=await Promise.all([post(),post()]);
  assert.deepEqual(concurrent.map(r=>r.status()).sort(),[200,429]);
  // This tab still had an open form while another request claimed the next slot.
  await form.locator('.detail-stars__btn').nth(3).click();await form.locator('[name=text]').fill('Уютно');
  const stalePromise=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith(action));
  await form.locator('[type=submit]').click();assert.equal((await stalePromise).status(),429);
  await timer.waitFor();assert.equal(await form.locator('[name=text]').inputValue(),'Уютно');
  assert(await page.locator('[data-review-live].flash-warning').isVisible());
  await form.waitFor();assert.equal(await page.locator('[data-review-live]').isVisible(),false);
  const nextPromise=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith(action));
  await form.locator('[type=submit]').click();assert.equal((await nextPromise).status(),200);
  await timer.waitFor();
  assert.deepEqual(errors,[]);
  console.log('PASS cooldown: success, reload, 429/Retry-After, wall-clock tampering, automatic expiry, concurrent 200+429, stale-tab 429 and retained draft, another pending submission, no JS errors');
 } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exit(1)});
