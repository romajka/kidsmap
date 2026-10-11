async page => {
  const origin = 'http://127.0.0.1:8823';
  const dir = 'C:/kidsmap/docs/qa/place-qa07-plan-2026-10-10/screenshots';
  const rows = [], errors = [], consoleErrors = [], blocked = new Set(), localFailures = [];
  const context = page.context();
  context.on('requestfailed', request => {
    if (request.url().startsWith(origin)) localFailures.push({url:request.url(),failure:request.failure()});
    else blocked.add(new URL(request.url()).origin);
  });
  for (const language of ['ru','az','en']) {
    for (const width of [390,768,1024,1280,1440]) {
      const tab = await context.newPage();
      tab.on('pageerror', error => errors.push(String(error)));
      tab.on('console', message => {
        if (message.type() === 'error') consoleErrors.push({language,width,text:message.text(),url:message.location().url});
      });
      tab.on('response', response => {
        if (response.url().startsWith(origin) && response.status() >= 400)
          localFailures.push({url:response.url(),status:response.status()});
      });
      await tab.setViewportSize({width,height:900});
      await tab.goto(`${origin}/${language}/account/places/1/edit/`, {waitUntil:'networkidle'});
      for (const phase of ['initial','reload']) {
        if (phase === 'reload') await tab.reload({waitUntil:'networkidle'});
        const field = tab.locator('[data-pw-field="nature"]');
        const select = field.locator('select[name="nature"]');
        await select.waitFor({state:'visible'});
        await field.scrollIntoViewIfNeeded();
        const options = await select.locator('option').evaluateAll(items => items.map(item => ({value:item.value,text:item.textContent.trim()})));
        const htmlLanguage = await tab.locator('html').getAttribute('lang');
        const geometry = await tab.evaluate(() => ({
          viewport: {width:innerWidth,height:innerHeight,dpr:devicePixelRatio},
          horizontalOverflow:document.documentElement.scrollWidth > innerWidth
        }));
        const screenshot = `${language}-${width}-${phase}-nature.png`;
        await field.screenshot({path:`${dir}/${screenshot}`});
        rows.push({language,width,phase,url:tab.url(),htmlLanguage,options,
          selected:await select.inputValue(),label:await field.locator('label').innerText(),
          aria:await select.ariaSnapshot(),geometry,screenshot});
      }
      await tab.close();
    }
  }
  return {browserVersion:context.browser().version(),rows,errors,consoleErrors,
    localFailures,blockedOrigins:Array.from(blocked),formSubmitted:false,compilationPerformed:false};
}
