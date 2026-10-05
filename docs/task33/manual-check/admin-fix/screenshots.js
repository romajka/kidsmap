async page => {
 await page.goto('http://127.0.0.1:8780/admin/catalog/organization/');
 await page.locator('.km-admin-header__lang-btn').click();
 await page.locator('form.km-admin-lang-switch-form:has(input[name="language"][value="ru"]) button').first().click();
 const files=[];
 for(const [model,width] of [['organization',1440],['organization',390],['program',1440],['place',390],['staffaccessuser',390],['seoissue',320]]){
  await page.setViewportSize({width,height:1000});
  await page.goto(`http://127.0.0.1:8780/admin/catalog/${model}/`);await page.waitForLoadState('networkidle');
  const name=`admin-repaired-${model}-${width}.png`;
  await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/'+name});files.push(name);
 }
 return {files};
}
