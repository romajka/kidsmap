// Requires a synthetic fixture config: {session, place, specialist}; no production targets.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs');
const assert = require('node:assert/strict');
(async()=>{
 const config=JSON.parse(fs.readFileSync(process.env.REVIEW_BROWSER_CONFIG));
 const browser=await chromium.launch({headless:true, executablePath:process.env.CHROMIUM_EXECUTABLE || undefined,args:['--no-sandbox']});
 const base=process.env.REVIEW_BROWSER_ORIGIN || 'http://127.0.0.1:18763';
 assert.equal(new URL(base).hostname, '127.0.0.1', 'Use isolated local fixtures only');
 const context=await browser.newContext();
 await context.addCookies([{name:'sessionid',value:config.session,domain:'127.0.0.1',path:'/'}]);
 await context.route('**/*',route=>route.request().url().startsWith(base+'/')?route.continue():route.abort());
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const placePath=config.place.replace(/^\/(ru|en)\//,'/');
 async function load(lang='ru',path=placePath){ await page.goto(base+(lang==='az'?'':'/'+lang)+path); await page.locator('[data-review-submission]').waitFor(); }
 async function fill(){
 const form=page.locator('[data-review-submission]');
 if(await form.locator('.detail-stars__btn').count()) await form.locator('.detail-stars__btn').nth(4).click();
 else if(await form.locator('.review-star').count()) await form.locator('.review-star').nth(4).click();
 else await form.locator('.km-star-btn').nth(4).click();
 await form.locator('[name="text"]').fill('This is a helpful synthetic review for moderation.');
 }
 // Regression: sufficient text alone must never announce that submission is ready.
 const missingRating = {
  ru: 'Выберите оценку звёздами, чтобы отправить отзыв.',
  az: 'Rəyi göndərmək üçün ulduzlarla qiymət verin.',
  en: 'Choose a star rating to submit your review.'
 };
 const ratingWarning = {
  ru: 'Чтобы отправить отзыв, выберите оценку от 1 до 5 звёзд.',
  az: 'Rəyi göndərmək üçün 1-dən 5-ə qədər ulduz seçərək qiymət verin.',
  en: 'To submit your review, choose a rating from 1 to 5 stars.'
 };
 for (const lang of Object.keys(missingRating)) {
  await page.setViewportSize({width:375,height:900});
  await load(lang);
  const form = page.locator('[data-review-form]');
  const text = form.locator('[name="text"]');
  const button = form.locator('[data-review-submit]');
  const hint = form.locator('[data-review-length-hint]');
  assert(await button.isDisabled());
  assert.equal(await form.locator('[name="is_anonymous"]').count(),0);
  await text.fill('testtesttesttesttesttesttesttest');
  assert.equal(await button.isDisabled(),false,'Allow clicking submit to explain the missing rating');
  let requests=0;
  const countPost=request=>{if(request.method()==='POST')requests++;};
  page.on('request',countPost);
  await button.click();
  await page.locator('[data-review-live].flash-warning').waitFor();
  assert.equal(await page.locator('[data-review-live] [data-review-message]').innerText(),ratingWarning[lang]);
  await page.screenshot({path:'/tmp/review-rating-warning-'+lang+'.png'});
  assert.equal(await page.locator('[data-review-live]').getAttribute('role'),'alert');
  assert.equal(await form.locator('.detail-stars__row').getAttribute('aria-invalid'),'true');
  assert(await form.locator('.detail-stars__btn').first().evaluate(el=>document.activeElement===el));
  assert.equal(requests,0,'Missing rating must not send a request');
  assert.equal(await text.inputValue(),'testtesttesttesttesttesttesttest');
  page.off('request',countPost);
  assert.equal(await hint.innerText(), missingRating[lang]);
  assert.equal(await hint.evaluate(el=>el.classList.contains('is-ready')), false);
  assert.equal(await button.getAttribute('aria-describedby'), await hint.getAttribute('id'));
  for(let rating=1; rating<=5; rating++) {
   await form.locator('.detail-stars__btn').nth(rating-1).click();
   assert.equal(await form.locator('[name="rating"]').inputValue(), String(rating));
   assert.equal(await button.isDisabled(), false);
   assert.equal(await page.locator('[data-review-live]').isVisible(),false);
  }
  await text.fill('   '); assert(await button.isDisabled());
  await text.fill('x'.repeat(2)); assert(await button.isDisabled());
  await text.fill('x'.repeat(3)); assert.equal(await button.isDisabled(),false);
  await text.fill('x'.repeat(1000)); assert.equal(await button.isDisabled(),false);
  await form.locator('[data-review-chip]').first().click();
  assert.equal((await text.inputValue()).length,1000);
  await form.locator('.detail-stars__btn').nth(4).focus();
  await page.keyboard.press('ArrowLeft');
  assert.equal(await form.locator('[name="rating"]').inputValue(),'4');
  assert.equal(await form.locator('.detail-stars__btn').nth(3).getAttribute('aria-checked'),'true');
  console.log('PASS composer validation and keyboard',lang);
 }
 // Retrying must preserve button markup and current validity, including edits in flight.
 await load(); await fill();
 {
  const form=page.locator('[data-review-form]');
  const button=form.locator('[data-review-submit]');
  const action=await form.getAttribute('action');
  let release;
  let routed;
  const arrived=new Promise(resolve=>{routed=resolve;});
  const pending=new Promise(resolve=>{release=resolve;});
  await page.route('**'+action,async route=>{
   routed(); await pending;
   await route.fulfill({status:500,contentType:'text/plain',body:'Synthetic server error'});
  });
  await button.click(); await arrived;
  await form.locator('[name="text"]').fill('');
  assert(await button.isDisabled());
  release();
  await page.locator('[data-review-live].flash-error').waitFor();
  await page.waitForFunction(()=>!document.querySelector('[data-review-form]').hasAttribute('aria-busy'));
  assert(await button.isDisabled(), 'Empty form must remain disabled after the request fails');
  assert.equal(await button.locator('svg').count(),1,'Retry must preserve the submit icon');
  await page.unroute('**'+action);
  console.log('PASS pending request edits and button restoration');
 }
 const headings={ru:'Спасибо! Отзыв отправлен на модерацию',az:'Təşəkkür edirik! Rəyiniz yoxlanışa göndərildi',en:'Thank you! Your review was submitted for moderation.'};
 for(const [lang,heading] of Object.entries(headings)){
  for(const width of [375,768,1024,1440]){
   await page.setViewportSize({width,height:900});await load(lang);await fill();
   let count=0;const countRequest=req=>{if(req.method()==='POST'&&req.url().includes('review'))count++;};page.on('request',countRequest);
   const url=page.url();
   await page.locator('[data-review-submit]').click();
   await page.locator('[data-review-submission]').evaluate(form=>{form.requestSubmit();form.requestSubmit();});
   await page.locator('[data-review-live].flash-success').waitFor();
   assert.equal(await page.locator('[data-review-live] [data-review-title]').innerText(),heading);
   assert.equal(await page.locator('[data-review-submission]').isVisible(),false);
   assert.equal(count,1);assert.equal(page.url(),url);page.off('request',countRequest);
   const box=await page.locator('[data-review-live]').boundingBox();assert(box.x>=0 && box.x+box.width<=width+1);
   await page.screenshot({path:`/tmp/review-${lang}-${width}.png`,fullPage:false});
   console.log('PASS',lang,width,'success, duplicate lock, viewport');
  }
 }
 for(const path of ['/reviews/', config.specialist.replace(/^\/(ru|en)\//,'/')]) {
  await load('ru',path);await fill();
  await page.locator('[data-review-submission]').evaluate(form=>form.requestSubmit());
  await page.locator('[data-review-live].flash-success').waitFor();
  assert.equal(await page.locator('[data-review-submission]').isVisible(),false);
  console.log('PASS additional review form',path);
 }
 for(const kind of ['validation','network','server','malformed','csrf','timeout']){
  await load();await fill();const form=page.locator('[data-review-submission]');
  const action=await form.getAttribute('action');
  if(kind==='validation') await form.locator('[name="rating"]').evaluate(el=>el.value='9');
  if(kind==='csrf') await form.locator('[name="csrfmiddlewaretoken"]').evaluate(el=>{el.value='expired-token';});
  if(kind==='malformed') await page.route('**'+action,route=>route.fulfill({status:200,contentType:'text/html',body:'Unexpected login page'}));
  let timeoutRoute;
  if(kind==='timeout') {
   await page.clock.install();
   await page.route('**'+action,route=>{timeoutRoute=route;});
  }
  if(kind==='network') await page.route('**'+action,route=>route.abort('failed'));
  if(kind==='server') await page.route('**'+action,route=>route.fulfill({status:500,contentType:'text/html',body:'Server error'}));
  await form.evaluate(f=>f.requestSubmit());
  if(kind==='timeout') await page.clock.fastForward(30001);
  await page.locator(kind==='validation'?'[data-review-live].flash-warning':'[data-review-live].flash-error').waitFor();
  if(timeoutRoute) await timeoutRoute.abort().catch(()=>{});
  assert(await form.isVisible());assert((await form.locator('[name="text"]').inputValue()).includes('synthetic'));
  assert.equal(await page.locator('[data-review-live].flash-success').count(),0);
  await page.unroute('**'+action);
  if(kind==='validation') await form.locator('.detail-stars__btn').nth(4).click();
  if(kind!=='csrf' && kind!=='timeout') {
   await form.locator('[type="submit"]').click();
   await page.locator('[data-review-live].flash-success').waitFor();
  }
  console.log('PASS',kind,'error, input retained, retry where applicable');
 }
 assert.deepEqual(errors,[]);console.log('PASS no JavaScript exceptions');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
