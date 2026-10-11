async (page) => {
  await page.goto('http://127.0.0.1:8840/ru/account/places/1/edit/');
  await page.locator('[name=address]').fill('KMFIX Manual address sentinel');
  await page.locator('[name=district]').selectOption('baku_sabail');
  await page.waitForFunction(()=>document.querySelector('[data-pc-save-status]').dataset.state==='saved'&&document.querySelector('[name=server_draft_id]').value);
  await page.reload();
  await page.waitForFunction(()=>document.querySelector('[name=district]').value==='baku_sabail');
  const local={district:await page.locator('[name=district]').inputValue(),enabled:await page.locator('[name=district]').isEnabled()};
  await page.evaluate(()=>localStorage.clear());await page.reload();
  await page.waitForFunction(()=>document.querySelector('[name=district]').value==='baku_sabail');
  const server={district:await page.locator('[name=district]').inputValue(),enabled:await page.locator('[name=district]').isEnabled(),region:await page.locator('[name=region]').inputValue(),latitude:await page.locator('[name=lat]').inputValue()};
  if(!local.enabled||!server.enabled||server.latitude||server.region!=='baku')throw new Error('Actual local/server restoration failed');
  await page.screenshot({path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/district-server-restore-390.png'});
  return {local,server};
}
