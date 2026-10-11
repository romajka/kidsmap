async (page) => {
  await page.goto('http://127.0.0.1:8840/admin/volunteer/review/2/');
  if(await page.locator('[name=action][value=approve]').count()!==1||await page.locator('.alert-warning').count())throw new Error('Revision is not approvable');
  await page.locator('[name=action][value=approve]').click();
  return {approved:true};
}
