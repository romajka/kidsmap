async (page) => {
  await page.locator('[name=username]').fill(__QA_USER__);
  await page.locator('[name=password]').fill(__QA_PASSWORD__);
  await page.locator('form').filter({has:page.locator('[name=password]')}).locator('button[type=submit]').click();
  await page.waitForURL(/\/account\/places\/3\/edit\//);
  await page.reload();
  const result={realLogin:true,reasonVisible:await page.locator('[data-place-review-note]').isVisible()};
  if(!result.reasonVisible)throw new Error('Persisted reason missing after real login');
  await page.screenshot({path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/rejection-after-login-1440.png'});
  return result;
}
