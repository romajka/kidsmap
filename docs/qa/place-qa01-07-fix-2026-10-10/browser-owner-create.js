async (page) => {
  await page.goto('http://127.0.0.1:8840/ru/account/places/create/?type=permanent&fresh=1');
  await page.setViewportSize({width:390,height:900});
  await page.locator('[name=name_az]').fill('KMFIX Uydurma ictimai məkan');
  await page.locator('[name=description_az]').fill('KMFIX yalnız sınaq üçün uydurma məkan. Uşaqlar və valideynlər üçün açıq oyun, istirahət və təhlükəsiz ünsiyyət sahəsi təqdim edilir.');
  await page.locator('[name=nature]').selectOption('public_space');
  await page.locator('[name=category]').selectOption('EDU');
  await page.locator('[name=subcategory]').selectOption({index:1});
  await page.locator('[name=region]').selectOption('baku');
  await page.locator('[name=district]').selectOption('baku_yasamal');
  await page.locator('[name=address]').fill('KMFIX Uydurma küçə 17');
  await page.locator('[name=age_from]').fill('0');
  await page.locator('[data-tariff-add]').click();
  const tariff=page.locator('[data-tariff-list]');
  const tariffInputs=await tariff.locator('input,select').evaluateAll(xs=>xs.map(x=>({tag:x.tagName,type:x.type,attrs:[...x.attributes].filter(a=>a.name.startsWith('data-')).map(a=>[a.name,a.value])})));
  return {url:page.url(),tariffInputs};
}
