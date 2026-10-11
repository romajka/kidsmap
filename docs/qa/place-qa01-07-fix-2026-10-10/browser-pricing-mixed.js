async (page) => {
  await page.goto('http://127.0.0.1:8840/ru/account/places/2/edit/');
  await page.setViewportSize({width:390,height:900});
  await page.locator('[name=name_az]').fill('KMFIX Yeni təsdiqlənəcək məkan');
  await page.locator('[name=address]').fill('KMFIX New mixed address 18');
  await page.locator('[data-tariff-key=price]').first().fill('18');
  await Promise.all([page.waitForNavigation(),page.locator('[name=form_action][value=save_draft]').click()]);
  await page.goto('http://127.0.0.1:8840/ru/account/places/2/edit/');await page.reload();
  const draft={name:await page.locator('[name=name_az]').inputValue(),address:await page.locator('[name=address]').inputValue(),price:await page.locator('[data-tariff-key=price]').first().inputValue(),live:await page.locator('[data-place-live]').innerText()};
  if(draft.price!=='18.00'||draft.name!=='KMFIX Yeni təsdiqlənəcək məkan'||draft.live.includes('KMFIX Yeni təsdiqlənəcək məkan'))throw new Error('Mixed draft/live separation failed: '+JSON.stringify(draft));
  await page.screenshot({path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/pricing-draft-ru-390.png'});
  await Promise.all([page.waitForNavigation(),page.locator('[data-pc-submit]').click()]);
  return {mixedDraftReload:true,price:draft.price,identityGated:true,submitted:true};
}
