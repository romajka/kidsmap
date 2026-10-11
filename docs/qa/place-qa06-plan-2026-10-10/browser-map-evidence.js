async driver => {
  const rows = [];
  for(const language of ['ru','az','en']) {
    await driver.context().addCookies([{name:'django_language',value:language,domain:'127.0.0.1',path:'/'}]);
    const page = await driver.context().newPage();
    await page.setViewportSize({width:390,height:900});
    await page.goto('http://127.0.0.1:8821/admin/catalog/place/1/change/');
    await page.locator('body').ariaSnapshot();
    const alert = page.locator('[data-map-alert]');
    await alert.waitFor({state:'visible'});
    await alert.evaluate(element => window.scrollTo(0,window.scrollY+element.getBoundingClientRect().top-210));
    await page.screenshot({path:`C:/kidsmap/docs/qa/place-qa06-plan-2026-10-10/screenshots/${language}-map-visible.png`,animations:'disabled'});
    rows.push({language,alertRect:await alert.boundingBox(),text:await alert.innerText()});
    await page.close();
  }
  return {rows,note:'Viewport captures keep map warning below sticky mobile navigation.'};
}
