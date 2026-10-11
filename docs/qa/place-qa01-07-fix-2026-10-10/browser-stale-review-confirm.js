async (page) => {
  const text=await page.locator('.alert-danger').innerText();
  if(!text.includes('Данные уже изменились'))throw new Error('Stale approval error missing');
  await page.setViewportSize({width:1440,height:900});
  await page.screenshot({animations:'disabled',path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/genuine-review-conflict-1440.png'});
  for(const other of page.context().pages())if(other!==page)await other.close({runBeforeUnload:false});
  return {genuineCompetingApproval:true,staleApprovalRefused:true,error:text};
}
