async (page) => {
  await page.goto('http://127.0.0.1:8840/admin/volunteer/review/3/');
  await page.locator('[name=note]').fill('KMFIX Вымышленная причина: уточните описание & адрес.\n<script>window.qaUnexpected=true</script>\n'+ 'Z'.repeat(180));
  await page.locator('[name=action][value=reject]').click();
  if(await page.locator('.alert-danger').count())throw new Error('Review rejected with application error');
  return {rejection_submitted:true,url:page.url()};
}
