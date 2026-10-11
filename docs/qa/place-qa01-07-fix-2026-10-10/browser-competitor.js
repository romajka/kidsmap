async (page) => {
  await page.goto('http://127.0.0.1:8840/admin/catalog/place/2/change/');
  await page.locator('#id_name_az').fill('KMFIX Real authorized competitor');
  await Promise.all([page.waitForNavigation(),page.locator('button[name=_continue]').first().click()]);
  await page.goto('http://127.0.0.1:8840/admin/volunteer/review/2/');
  const result={genuineOtherActorChange:true,approveCount:await page.locator('[name=action][value=approve]').count(),conflictVisible:await page.locator('.alert-warning').count()>0};
  if(result.approveCount!==0||!result.conflictVisible)throw new Error('Real competing identity change did not block stale approval');
  await page.setViewportSize({width:1440,height:900});
  await page.screenshot({path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/genuine-review-conflict-1440.png'});
  return result;
}
