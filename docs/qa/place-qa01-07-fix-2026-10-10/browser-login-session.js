async (page) => {
  await page.locator('[name=username]').fill(__QA_USER__);
  await page.locator('[name=password]').fill(__QA_PASSWORD__);
  await Promise.all([page.waitForNavigation(),page.locator('form').filter({has:page.locator('[name=password]')}).locator('button[type=submit]').click()]);
  if(await page.locator('#account-menu-trigger').count()!==1)throw new Error('Real owner login failed');
  return {realLogin:true};
}
