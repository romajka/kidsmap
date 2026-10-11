async (page) => {
  await page.goto('http://127.0.0.1:8840/ru/account/places/2/edit/');
  const stale=await page.context().newPage();
  await stale.goto('http://127.0.0.1:8840/ru/account/places/2/edit/');
  await page.locator('[name=name_az]').fill('KMFIX Current concurrent candidate');
  await page.locator('[data-tariff-key=price]').first().fill('27');
  await Promise.all([page.waitForNavigation(),page.locator('[name=form_action][value=save_draft]').click()]);
  await page.goto('http://127.0.0.1:8840/ru/account/places/2/edit/');
  await Promise.all([page.waitForNavigation(),page.locator('[data-pc-submit]').click()]);
  await stale.locator('[name=name_az]').fill('KMFIX Stale input must remain');
  await stale.locator('[name=form_action][value=save_draft]').click();
  await stale.waitForFunction(()=>document.querySelector('[data-pc-save-status]').dataset.state==='conflict'||document.querySelector('[data-pc-errors]').textContent.includes('Publication source/schema conflict'));
  const result={controlledConflict:true,staleInputPreserved:await stale.locator('[name=name_az]').inputValue()==='KMFIX Stale input must remain'};
  if(!result.staleInputPreserved)throw new Error('Stale editor lost input');
  await stale.setViewportSize({width:390,height:900});
  await stale.screenshot({path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/stale-conflict-390.png'});
  await stale.close();
  return result;
}
