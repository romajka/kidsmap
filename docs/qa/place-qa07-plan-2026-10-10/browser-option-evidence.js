async page => {
  const rows = [];
  for (const language of ['ru','az','en']) {
    const tab = await page.context().newPage();
    await tab.setViewportSize({width:390,height:900});
    await tab.goto(`http://127.0.0.1:8823/${language}/account/places/1/edit/`, {waitUntil:'networkidle'});
    const field = tab.locator('[data-pw-field="nature"]');
    const select = field.locator('select[name="nature"]');
    await field.scrollIntoViewIfNeeded();
    await select.focus();
    await select.press('ArrowDown');
    const value = await select.inputValue();
    if (value !== 'public_space') throw new Error(`Unexpected enum selection ${value}`);
    const screenshot = `${language}-390-public-space-keyboard.png`;
    await field.screenshot({path:`C:/kidsmap/docs/qa/place-qa07-plan-2026-10-10/screenshots/${screenshot}`});
    rows.push({language,value,label:await select.locator('option:checked').innerText(),
      aria:await select.ariaSnapshot(),screenshot});
    await tab.close();
  }
  return {rows,interaction:'native select keyboard ArrowDown',explicitFormSave:false};
}
