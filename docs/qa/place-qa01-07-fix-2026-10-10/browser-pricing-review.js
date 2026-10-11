async (page) => {
  const rows=[];
  for (const language of ['ru','az','en']) {
    await page.context().addCookies([{name:'django_language',value:language,domain:'127.0.0.1',path:'/'}]);
    await page.goto('http://127.0.0.1:8840/admin/volunteer/review/2/');
    for(const width of [390,768,1024,1280,1440]) {
      await page.setViewportSize({width,height:900});
      const approve=await page.locator('[name=action][value=approve]').count();
      if(approve!==1||await page.locator('.alert-warning').count())throw new Error('Unexpected self conflict/readiness failure');
      await page.screenshot({path:`C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/pricing-review-${language}-${width}.png`});
      rows.push({language,width,approvable:true});
    }
  }
  await page.locator('[name=action][value=approve]').click();
  if(await page.locator('.alert-danger').count())throw new Error('Approve returned error');
  return {checks:rows.length,rows,approved:true};
}
