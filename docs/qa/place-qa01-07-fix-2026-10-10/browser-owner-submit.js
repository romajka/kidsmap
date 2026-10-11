async (page) => {
  await page.locator('[name=age_to]').fill('12');
  await page.locator('[data-tariff-key=editor_kind]').first().selectOption('admission');
  await page.locator('[data-tariff-key=price]').first().fill('5');
  await page.locator('[name=schedule_mode]').selectOption('always_open');
  await page.locator('[data-pc-submit]').click();
  await page.waitForURL(/\/account\/places\/$/);
  await page.goto('http://127.0.0.1:8840/ru/account/places/3/edit/');
  await page.reload();
  const result=await page.evaluate(()=>({url:location.href,placeId:Number(document.querySelector('[data-permanent-place-form]').dataset.targetId),status:document.querySelector('[data-pc-lifecycle]').textContent.trim(),district:document.querySelector('[name=district]').value,latitude:document.querySelector('[name=lat]').value,address:document.querySelector('[name=address]').value}));
  if(result.status!=='На модерации')throw new Error('Submission not pending: '+JSON.stringify(result));
  await page.screenshot({path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/owner-submitted-390.png'});
  return result;
}
