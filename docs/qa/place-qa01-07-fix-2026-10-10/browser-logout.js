async (page) => {
  await page.goto('http://127.0.0.1:8840/ru/account/places/3/edit/');
  await page.setViewportSize({width:1440,height:900});
  await page.locator('#account-menu-trigger').click();
  await page.locator('.km-logout-form button').click();
  await page.goto('http://127.0.0.1:8840/ru/account/places/3/edit/');
  const result={redirectedToLogin:page.url().includes('/auth/login/'),noteVisible:await page.locator('[data-place-review-note]').count()};
  if(!result.redirectedToLogin||result.noteVisible)throw new Error('Guest ACL failed after logout');
  return result;
}
