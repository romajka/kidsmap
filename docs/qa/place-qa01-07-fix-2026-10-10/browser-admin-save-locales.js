async (page) => {
  const rows=[];
  for(const [language,labelPrefix] of [['ru','Описание'],['az','Təsvir'],['en','Description']]) {
    await page.context().addCookies([{name:'django_language',value:language,domain:'127.0.0.1',path:'/'}]);
    await page.goto('http://127.0.0.1:8840/admin/catalog/place/1/change/');await page.reload();
    for(const width of [390,768,1024,1280,1440]) {
      await page.setViewportSize({width,height:900});
      const labels=await page.locator('label[for=id_description_az],label[for=id_description_ru],label[for=id_description_en]').allTextContents();
      if(labels.length!==3||labels.some(x=>!x.includes(labelPrefix)))throw new Error('Description labels incorrect: '+JSON.stringify(labels));
      await page.locator('#id_description_az').scrollIntoViewIfNeeded();
      await page.screenshot({path:`C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/locales-${language}-${width}.png`});
      rows.push({language,width,labels:labels.map(x=>x.trim())});
    }
  }
  const preserved=await page.evaluate(()=>Object.fromEntries(['name_az','address','schedule'].map(name=>[name,document.querySelector('[name='+name+']').value])));
  const sentinel='KMFIX description saved from translated admin. Synthetic content for a controlled local test; other fields must retain their stored values.';
  await page.locator('#id_description_az').fill(sentinel);
  await page.locator('.km-pf-picker-btn').first().click();
  await page.locator('.km-pf-picker-wrap.is-open .km-pf-picker-item[data-value=KMFIX_NEXT]').click();
  const selectedFocus=await page.locator('.km-pf-picker-btn').first().evaluate(el=>el===document.activeElement);
  if(!selectedFocus)throw new Error('Selecting category lost focus');
  await page.locator('.km-pf-picker-btn').nth(1).click();
  await page.locator('.km-pf-picker-wrap.is-open input').fill('KMFIX');
  await page.locator('.km-pf-picker-wrap.is-open .km-pf-picker-item').first().click();
  const subcategory=await page.locator('#id_subcategory').inputValue();
  await Promise.all([page.waitForNavigation(),page.locator('button[name=_continue]').first().click()]);
  await page.reload();
  const after=await page.evaluate(()=>Object.fromEntries(['name_az','address','schedule'].map(name=>[name,document.querySelector('[name='+name+']').value])));
  const result={checks:rows.length,rows,selectedFocus,category:await page.locator('#id_category').inputValue(),subcategory:await page.locator('#id_subcategory').inputValue(),descriptionSaved:await page.locator('#id_description_az').inputValue()===sentinel,otherFieldsPreserved:JSON.stringify(after)===JSON.stringify(preserved)};
  if(result.category!=='KMFIX_NEXT'||result.subcategory!==subcategory||!result.descriptionSaved||!result.otherFieldsPreserved)throw new Error('Admin save/reload failed: '+JSON.stringify(result));
  await page.screenshot({path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/admin-save-reload-en-1440.png'});
  return result;
}
