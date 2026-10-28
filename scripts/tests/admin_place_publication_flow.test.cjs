const test=require('node:test'),assert=require('node:assert/strict');
const fixturePath=process.env.KIDSMAP_PUBLICATION_LIST_FIXTURE;
test('place list publishes, confirms unpublish, and refreshes actual filtered state', {skip:!fixturePath,timeout:120000},async()=>{
 const H=require('../e2e/place_addition/helpers.cjs');
 const fixture=JSON.parse(H.fs.readFileSync(fixturePath));assert.equal(fixture.synthetic,true);
 const browser=await H.launch(),context=await H.context(browser,fixture.origin);
 try{
  const page=await H.login(context,fixture,'admin'),issues=H.watch(page,fixture.origin);
  await context.addCookies([{name:'django_language',value:'ru',url:fixture.origin}]);
  const row=()=>page.locator('#result_list tbody tr').filter({has:page.locator(`a[href="/admin/catalog/place/${fixture.publication_place_id}/change/"]`)});
  const url=state=>fixture.origin+'/admin/catalog/place/?publication_state='+state;
  await page.goto(url('unpublished'));await row().waitFor();
  assert.match(await row().innerText(),/Не опубликовано/);assert.match(await row().innerText(),/Готово к публикации/);
  const publishResponse=page.waitForResponse(r=>r.url().includes(`/${fixture.publication_place_id}/toggle-publication/`));
  await row().getByRole('button',{name:/^Опубликовать/}).click();
  assert.equal((await publishResponse).status(),200);
  await page.waitForFunction(id=>!document.querySelector(`#result_list a[href="/admin/catalog/place/${id}/change/"]`),fixture.publication_place_id);
  assert.equal((await context.request.get(fixture.origin+fixture.publication_public_url)).status(),200);
  await page.goto(url('published'));await row().waitFor();
  assert.match(await row().innerText(),/Видно на сайте/);
  await row().getByRole('button',{name:/^Снять с публикации/}).click();
  await page.getByRole('button',{name:'Отмена',exact:true}).last().click();
  assert.match(await row().innerText(),/Видно на сайте/);
  await row().getByRole('button',{name:/^Снять с публикации/}).click();
  const unpublishResponse=page.waitForResponse(r=>r.url().includes(`/${fixture.publication_place_id}/toggle-publication/`));
  await page.getByRole('button',{name:'Да, снять',exact:true}).click();
  assert.equal((await unpublishResponse).status(),200);
  await page.waitForFunction(id=>!document.querySelector(`#result_list a[href="/admin/catalog/place/${id}/change/"]`),fixture.publication_place_id);
  assert.equal((await context.request.get(fixture.origin+fixture.publication_public_url)).status(),404);
  let responsiveChecks=0;
  for(const lang of ['ru','az','en']){
   await context.addCookies([{name:'django_language',value:lang,url:fixture.origin}]);
   await page.goto(fixture.origin+'/admin/catalog/place/');await row().waitFor();
   const pending=page.locator('#result_list tbody tr').filter({has:page.locator(`a[href="/admin/catalog/place/${fixture.pending_place_id}/change/"]`)});
   assert.equal(await pending.locator('[data-state="published"]').count(),1);
   assert.equal(await pending.locator('.km-publication-revision').isVisible(),true);
   assert.equal(await pending.locator('[data-publication-action]').getAttribute('data-is-active'),'1');
   for(const width of [1440,1024,768,390]){
    await page.setViewportSize({width,height:1000});
    const button=row().locator('[data-publication-action]');await button.scrollIntoViewIfNeeded();
    assert.equal(await button.isVisible(),true);responsiveChecks++;
   }
   await page.setViewportSize({width:1440,height:1000});
   await page.evaluate(()=>window.scrollTo(0,0));
   await page.screenshot({path:`/tmp/kidsmap-coordinates-20261028/publication-${lang}.png`,fullPage:false});
  }
  assert.deepEqual(issues.errors,[]);assert.deepEqual(issues.requests,[]);
  console.log(JSON.stringify({publish:true,cancelUnpublish:true,unpublish:true,publicVisibility200Then404:true,pendingEditsSeparate:true,responsiveChecks,jsErrors:0,httpErrors:0}));
 }finally{await context.close();await browser.close()}
});
