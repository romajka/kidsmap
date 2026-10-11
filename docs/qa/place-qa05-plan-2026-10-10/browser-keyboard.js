async driver => {
  const rows = [];
  for (const language of ['ru','az','en']) {
    const page = await driver.context().newPage();
    await page.setViewportSize({width:360,height:900});
    await page.context().addCookies([{name:'django_language',value:language,domain:'127.0.0.1',path:'/'}]);
    await page.goto('http://127.0.0.1:8819/admin/catalog/place/1/change/');
    await page.locator('body').ariaSnapshot();
    const wrap = page.locator('.km-pf-picker-wrap').first();
    const trigger = wrap.locator('.km-pf-picker-btn');
    const popup = wrap.locator('.km-pf-picker-dropdown');
    const search = popup.locator('input');
    const focus = () => page.evaluate(() => ({tag:document.activeElement.tagName,className:document.activeElement.className,
      visible:!!(document.activeElement.offsetWidth || document.activeElement.offsetHeight)}));
    await page.waitForFunction(() => getComputedStyle(document.querySelector('.km-pf-picker-dropdown')).minWidth === '320px');
    await trigger.focus();
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => document.activeElement.closest('.km-pf-picker-search'));
    const opened = await focus();
    await page.keyboard.press('Tab');
    const tab = await focus();
    await page.keyboard.press('Shift+Tab');
    const shiftTab = await focus();
    await page.keyboard.press('Escape');
    const escape = {focus:await focus(),expanded:await trigger.getAttribute('aria-expanded')};
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => document.activeElement.closest('.km-pf-picker-search'));
    await search.fill('QA05');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    const select = {focus:await focus(),expanded:await trigger.getAttribute('aria-expanded'),
      value:await page.locator('select[name="category"]').inputValue()};
    await trigger.click();
    await search.fill('QA05_NO_MATCH_123456');
    await page.keyboard.press('Escape');
    const emptyEscape = {focus:await focus(),expanded:await trigger.getAttribute('aria-expanded')};
    await page.screenshot({path:`C:/kidsmap/docs/qa/place-qa05-plan-2026-10-10/screenshots/keyboard-empty-${language}-360.png`,animations:'disabled'});
    rows.push({language,opened,tab,shiftTab,escape,select,emptyEscape});
    await page.close();
  }
  return {rows,savedToDatabase:false};
}
