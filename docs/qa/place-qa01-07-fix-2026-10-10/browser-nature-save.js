async (page) => {
  const rows=[];
  for(const language of ['ru','az','en']) {
    for(const value of ['business','public_space']) {
      await page.goto(`http://127.0.0.1:8840/${language}/account/places/3/edit/`);
      await page.setViewportSize({width:390,height:900});
      await page.locator('[name=nature]').selectOption(value);
      await Promise.all([page.waitForNavigation(),page.locator('[name=form_action][value=save_draft]').click()]);
      await page.goto(`http://127.0.0.1:8840/${language}/account/places/3/edit/`);await page.reload();
      const saved=await page.locator('[name=nature]').inputValue();
      if(saved!==value)throw new Error('Nature enum save/reload failed');
      rows.push({language,value,saved});
      await page.locator('[name=nature]').scrollIntoViewIfNeeded();
      await page.screenshot({path:`C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/nature-${language}-${value}-390.png`});
    }
  }
  return {checks:rows.length,rows};
}
