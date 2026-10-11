async (page) => {
  await page.goto('http://127.0.0.1:8840/az/account/places/2/edit/');
  await page.setViewportSize({width:1440,height:900});
  await page.locator('[data-tariff-key=price]').first().fill('21');
  await Promise.all([page.waitForNavigation(),page.locator('[name=form_action][value=save_draft]').click()]);
  await page.goto('http://127.0.0.1:8840/az/account/places/2/edit/');await page.reload();
  if(await page.locator('[data-tariff-key=price]').first().inputValue()!=='21.00')throw new Error('Price-only reload failed');
  await Promise.all([page.waitForNavigation(),page.locator('[data-pc-submit]').click()]);
  return {language:'az',priceOnly:true,reloadedPrice:'21.00',submitted:true};
}
