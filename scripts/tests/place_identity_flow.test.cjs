const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const fixturePath=process.env.KIDSMAP_IDENTITY_FIXTURE;
const output=fixturePath?require('node:path').dirname(fixturePath):'';
test('registry exports both versions and editor prevents duplicate creation',{skip:!fixturePath,timeout:180000},async()=>{
 const H=require('../e2e/place_addition/helpers.cjs'),fixture=JSON.parse(fs.readFileSync(fixturePath));assert.equal(fixture.synthetic,true);
 const browser=await H.launch(),context=await H.context(browser,fixture.origin);
 try{
  const page=await H.login(context,fixture,'admin'),issues=H.watch(page,fixture.origin);
  const registry=fixture.origin+'/admin/catalog/place/duplicate-registry/';
  const compare=fixture.origin+`/admin/catalog/place/${fixture.place_id}/compare-versions/`;
  let checks=0;
  for(const lang of ['ru','az','en']){
   await context.addCookies([{name:'django_language',value:lang,url:fixture.origin}]);
   await page.goto(compare);
   const body=await page.locator('body').innerText();
   assert.match(body,/QA Stored Avenue 10/);assert.match(body,/QA Saved Avenue 20/);
   assert.equal(await page.locator('.km-identity-changed').count()>0,true);
   for(const width of [390,768,1024,1280,1440]){
    await page.setViewportSize({width,height:1000});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,`${lang}/${width} page overflow`);
    await page.locator('.km-identity-table-wrap').focus();
    assert.equal(await page.locator('.km-identity-table-wrap').evaluate(e=>e===document.activeElement),true);checks++;
   }
   await page.screenshot({path:`${output}/compare-${lang}.png`,fullPage:false});
   await page.goto(registry);
   await page.locator('input[name=phone]').fill('+994509999990');await page.locator('.km-identity-search button').click();
   await page.locator('[data-identity-record]').first().waitFor({state:'visible'});
   assert.equal(await page.locator('[data-identity-record]').count(),12);
  }
  await context.addCookies([{name:'django_language',value:'ru',url:fixture.origin}]);
  await page.goto(registry);
  const downloadPromise=page.waitForEvent('download');await page.locator('[data-identity-export]').click();
  const download=await downloadPromise,exported=JSON.parse(fs.readFileSync(await download.path()));
  const record=exported.records.find(r=>r.id===fixture.place_id);
  assert.deepEqual(record.versions.map(v=>v.source),['stored','candidate']);
  assert.equal(exported.export_scope,'duplicate_registry');assert.equal(exported.coverage.global_absence_proven,false);
  assert.equal(exported.records.some(r=>r.draft_id===fixture.own_draft_id),true);
  assert.equal(JSON.stringify(exported).includes('OTHER_PRIVATE_MARKER'),false);
  const first=await context.request.get(fixture.origin+'/admin/catalog/place/duplicate-candidates/?phone=%2B994509999990&page_size=8');
  const result=await first.json();assert.equal(result.total,12);assert.equal(result.results.length,8);assert.equal(result.has_next,true);
  const second=await context.request.get(fixture.origin+'/admin/catalog/place/duplicate-candidates/'+result.next_url);
  assert.equal((await second.json()).results.length,4);
  const site=await context.request.get(fixture.origin+'/admin/catalog/place/duplicate-candidates/?website=https%3A%2F%2Fdedup.example.invalid');
  assert((await site.json()).results.some(r=>r.evidence.some(e=>e.matched_fields.includes('public_links'))));
  await page.goto(fixture.origin+'/admin/catalog/place/add/?type=permanent');
  await H.fill(page,'#id_name_az','Yeni Bilik Evi');await H.select(page,'#id_category','EDU');
  await H.fill(page,'#id_address','QA Saved Avenue 20');await page.locator('#id_address').blur();
  await page.locator('[data-place-duplicate-alert]').waitFor({state:'visible'});
  await page.waitForFunction(()=>document.querySelector('[data-place-duplicate-alert] a[href*="compare-versions"]'));
  const post=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/admin/catalog/place/add/');
  await page.locator('button[name="_save_draft"]:visible').first().click();
  assert.equal((await post).status(),200);
  assert.match(await page.locator('body').innerText(),/Возможный дубль/);
  const after=await (await context.request.get(registry+'?format=json')).json();
  assert.equal(after.records.filter(r=>r.id!==null).length,exported.records.filter(r=>r.id!==null).length);
  await page.screenshot({path:`${output}/duplicate-blocked.png`,fullPage:false});
  assert.deepEqual(issues.errors,[]);assert.deepEqual(issues.requests,[]);
  console.log(JSON.stringify({responsiveChecks:checks,bothVersions:true,fullExport:true,privateScope:true,pagination:true,duplicatePostRejected:true,jsErrors:0,httpErrors:0}));
 }finally{await context.close();await browser.close()}
});
