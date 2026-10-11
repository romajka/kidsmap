async page => {
  const rows = [], network = [], errors = [];
  page.on('response', response => { if (response.status() >= 400) network.push({url:response.url(),status:response.status()}); });
  page.on('requestfailed', request => network.push({url:request.url(),error:request.failure()?.errorText}));
  page.on('pageerror', error => errors.push(String(error)));
  const browserVersion = page.context().browser().version();
  for (const language of ['ru','az','en']) {
    await page.context().addCookies([{name:'django_language',value:language,domain:'127.0.0.1',path:'/'}]);
    for (const width of [360,390,768,1024,1280,1440]) {
      await page.setViewportSize({width,height:900});
      await page.goto('http://127.0.0.1:8819/admin/catalog/place/1/change/');
      await page.locator('.km-pf-picker-wrap').first().waitFor();
      const snapshot = await page.locator('body').ariaSnapshot();
      const trigger = page.locator('.km-pf-picker-wrap').first().locator('.km-pf-picker-btn');
      const label = await trigger.innerText();
      const closedWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      await trigger.click();
      const popup = page.locator('.km-pf-picker-wrap').first().locator('.km-pf-picker-dropdown');
      await popup.locator('input').waitFor({state:'visible'});
      await popup.locator('input').focus();
      // Two animation frames plus screenshot's animation settlement before measurement.
      await page.waitForFunction(() => getComputedStyle(document.querySelector('.km-pf-picker-dropdown')).minWidth === '320px');
      await page.screenshot({path:`C:/kidsmap/docs/qa/place-qa05-plan-2026-10-10/screenshots/effective-${language}-${width}.png`,animations:'disabled'});
      const metrics = await popup.evaluate(element => {
        const longLabel = element.querySelector('[data-value="QA05_LONG"] .km-pf-picker-item__name');
        const search = element.querySelector('input');
        return {viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
          popup:element.getBoundingClientRect().toJSON(),minWidth:getComputedStyle(element).minWidth,
          triggerWidth:element.parentElement.getBoundingClientRect().width,
          search:search.getBoundingClientRect().toJSON(),searchPlaceholder:search.placeholder,
          htmlLang:document.documentElement.lang,
          longLabel:longLabel ? {text:longLabel.textContent,clientWidth:longLabel.clientWidth,
            scrollWidth:longLabel.scrollWidth,whiteSpace:getComputedStyle(longLabel).whiteSpace} : null};
      });
      rows.push({language,width,label,closedWidth,snapshotContainsCategory:snapshot.includes(label),...metrics});
    }
  }
  const localFailures = network.filter(row => row.url.startsWith('http://127.0.0.1:8819'));
  return {browserVersion,rows,network,errors,environmentValid:localFailures.length===0 && errors.length===0};
}
