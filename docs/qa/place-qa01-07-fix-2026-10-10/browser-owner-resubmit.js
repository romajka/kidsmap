async (page) => {
  await page.goto('http://127.0.0.1:8840/ru/account/places/3/edit/');
  await page.locator('[name=description_az]').fill('KMFIX düzəldilmiş uydurma məkan. Uşaqlar və valideynlər üçün açıq oyun, istirahət və təhlükəsiz ünsiyyət sahəsi təqdim edilir. Yeni məlumat yoxlanılıb.');
  await Promise.all([page.waitForNavigation(),page.locator('[name=form_action][value=save_draft]').click()]);
  await page.goto('http://127.0.0.1:8840/ru/account/places/3/edit/');
  await page.reload();
  const draftReason=await page.locator('[data-place-review-note]').isVisible();
  if(!draftReason)throw new Error('Draft correction lost saved reason');
  await Promise.all([page.waitForNavigation(),page.locator('[data-pc-submit]').click()]);
  await page.goto('http://127.0.0.1:8840/ru/account/places/3/edit/');await page.reload();
  const result={draftReason,reasonAfterSubmit:await page.locator('[data-place-review-note]').count(),status:await page.locator('[data-pc-lifecycle]').innerText(),district:await page.locator('[name=district]').inputValue()};
  if(result.reasonAfterSubmit||result.status!=='На модерации'||result.district!=='baku_yasamal')throw new Error('Resubmission state failed');
  await page.screenshot({path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/owner-resubmitted-1440.png'});
  return result;
}
