async (page) => {
  await page.goto('http://127.0.0.1:8840/admin/volunteer/review/2/');
  const competitor=await page.context().newPage();
  await competitor.goto('http://127.0.0.1:8840/admin/catalog/place/2/change/');
  await competitor.locator('#id_name_az').fill('KMFIX Competitor approved live');
  await Promise.all([competitor.waitForNavigation(),competitor.locator('button[name=_continue]').first().click()]);
  await competitor.goto('http://127.0.0.1:8840/admin/volunteer/review/2/');
  await competitor.locator('[name=action][value=approve]').click();
  await page.locator('[name=action][value=approve]').click();
  const text=await page.locator('.alert-danger').innerText();
  if(!text.includes('Данные уже изменились'))throw new Error('Stale review did not reject after real competing approval: '+text);
  await page.setViewportSize({width:1440,height:900});
  await page.screenshot({animations:'disabled',path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/genuine-review-conflict-1440.png'});
  await competitor.close({runBeforeUnload:false});
  return {genuineOtherActorChangeAndApproval:true,staleApprovalRefused:true,error:text};
}
