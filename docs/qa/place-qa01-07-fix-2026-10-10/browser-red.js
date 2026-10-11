async (page) => {
  await page.context().addCookies([{name:'django_language',value:'ru',domain:'127.0.0.1',path:'/'}]);
  await page.goto('http://127.0.0.1:8840/admin/catalog/place/1/change/');
  await page.setViewportSize({width:360,height:900});
  const trigger=page.locator('.km-pf-picker-btn').first();
  await trigger.click();
  const result=await page.evaluate(() => {
    const box=document.querySelector('.km-pf-picker-wrap.is-open .km-pf-picker-dropdown').getBoundingClientRect();
    return {viewport:innerWidth,left:box.left,right:box.right,overflow:box.right>innerWidth};
  });
  await page.screenshot({path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/admin-red-360.png'});
  return result;
}
