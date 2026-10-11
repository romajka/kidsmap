async (page) => {
  const rows=[];
  for(const [language,title,message] of [
    ['ru','Карта пока не активна','Геокодирование не настроено.'],
    ['az','Xəritə hazırda əlçatan deyil','Geokodlaşdırma qurulmayıb.'],
    ['en','Map currently unavailable','Geocoding is not configured.']]) {
    await page.context().addCookies([{name:'django_language',value:language,domain:'127.0.0.1',path:'/'}]);
    await page.goto('http://127.0.0.1:8840/admin/catalog/place/1/change/');await page.reload();
    const text=await page.locator('body').innerText();
    if(!text.includes(title)||!text.includes(message))throw new Error('Localized unavailable-map copy absent: '+language);
    await page.locator('.km-pf-picker-btn').first().click();await page.locator('#id_name_az').click();
    const outsideFocus=await page.locator('#id_name_az').evaluate(el=>document.activeElement===el);
    if(!outsideFocus||await page.locator('.km-pf-picker-wrap.is-open').count())throw new Error('Outside click stole focus');
    rows.push({language,mapTitle:title,mapMessage:true,outsideFocus});
  }
  return {rows};
}
