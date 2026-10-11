async driver => {
  const rows = [], network = [], errors = [], dialogs = [];
  for (const language of ['ru','az','en']) {
    await driver.context().addCookies([{name:'django_language',value:language,domain:'127.0.0.1',path:'/'}]);
    const page = await driver.context().newPage();
    await page.setViewportSize({width:390,height:900});
    page.on('requestfailed', request => network.push({language,url:request.url(),error:request.failure()?.errorText}));
    page.on('response', response => { if(response.status()>=400) network.push({language,url:response.url(),status:response.status()}); });
    page.on('pageerror', error => errors.push({language,error:String(error)}));
    page.on('dialog', async dialog => {
      dialogs.push({language,type:dialog.type()});
      if(dialog.type()==='beforeunload') await dialog.accept(); else await dialog.dismiss();
    });
    await page.goto('http://127.0.0.1:8821/admin/catalog/place/1/change/');
    for (const phase of ['initial','reload']) {
      if(phase==='reload') await page.reload();
      await page.locator('body').ariaSnapshot();
      await page.waitForFunction(() => [...document.styleSheets].some(sheet => sheet.href?.includes('kidsmap_place_form.css')));
      await page.locator('[data-map-alert]').waitFor({state:'visible'});
      const labels = {};
      for(const fieldLanguage of ['az','ru','en']) {
        await page.locator(`#km-pf-langtab-${fieldLanguage}`).click();
        const label = page.locator(`label[for="id_description_${fieldLanguage}"] .km-pf-field__label-text`);
        await label.waitFor({state:'visible'});
        labels[fieldLanguage] = await label.innerText();
        await page.locator('[data-pf-group="names"]').screenshot({
          path:`C:/kidsmap/docs/qa/place-qa06-plan-2026-10-10/screenshots/${language}-${phase}-description-${fieldLanguage}.png`,animations:'disabled'});
      }
      const alert = page.locator('[data-map-alert]');
      const title = await alert.locator('strong').innerText();
      const message = await alert.locator('div > span').innerText();
      await alert.screenshot({path:`C:/kidsmap/docs/qa/place-qa06-plan-2026-10-10/screenshots/${language}-${phase}-map.png`,animations:'disabled'});
      rows.push({language,phase,labels,mapTitle:title,mapMessage:message,
        htmlLanguage:await page.locator('html').getAttribute('lang'),
        viewport:await page.evaluate(()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio})),
        url:page.url()});
    }
    await page.close();
  }
  return {browserVersion:driver.context().browser().version(),rows,network,errors,dialogs,
    localResourceFailures:network.filter(r=>r.url.startsWith('http://127.0.0.1:8821')).length,
    compiledAssets:'frozen copies of current WORKTREE; not rebuilt',databaseSaveRun:false};
}
