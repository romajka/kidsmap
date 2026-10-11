async (page) => {
  await page.goto('http://127.0.0.1:8840/en/account/places/2/edit/');
  await page.setViewportSize({width:390,height:900});
  await page.locator('[name=name_az]').fill('KMFIX İkinci təsdiqlənəcək məkan');
  await page.locator('[name=address]').fill('KMFIX Second mixed address 24');
  await page.locator('[data-tariff-key=price]').first().fill('24');
  await Promise.all([page.waitForNavigation(),page.locator('[name=form_action][value=save_draft]').click()]);
  await page.goto('http://127.0.0.1:8840/en/account/places/2/edit/');await page.reload();
  if(await page.locator('[data-tariff-key=price]').first().inputValue()!=='24.00')throw new Error('Second mixed reload failed');
  const live=await page.locator('[data-place-live]').innerText();
  if(live.includes('KMFIX İkinci'))throw new Error('Second identity leaked before approval');
  await Promise.all([page.waitForNavigation(),page.locator('[data-pc-submit]').click()]);
  return {language:'en',secondMixed:true,reloadedPrice:'24.00',identityGated:true,submitted:true};
}
