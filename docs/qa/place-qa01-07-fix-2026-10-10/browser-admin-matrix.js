async (page) => {
  const rows=[];
  for (const language of ['ru','az','en']) {
    await page.context().addCookies([{name:'django_language',value:language,domain:'127.0.0.1',path:'/'}]);
    await page.goto('http://127.0.0.1:8840/admin/catalog/place/1/change/');
    for (const width of [360,390,768,1024,1280,1440]) {
      await page.setViewportSize({width,height:900});
      const trigger=page.locator('.km-pf-picker-btn').first();await trigger.click();
      const popup=page.locator('.km-pf-picker-wrap.is-open .km-pf-picker-dropdown');
      await popup.locator('input').fill('KMFIX');
      const geometry=await popup.evaluate(el=> {
        const rect=el.getBoundingClientRect(),input=el.querySelector('input'),label=el.querySelector('.km-pf-picker-item__name');
        const item=label.getBoundingClientRect(),style=getComputedStyle(label);
        return {left:rect.left,right:rect.right,viewport:innerWidth,inputRight:input.getBoundingClientRect().right,
          text:label.textContent,whiteSpace:style.whiteSpace,textOverflow:style.textOverflow,labelHeight:item.height,
          fullLabel:label.scrollWidth<=label.clientWidth+1};
      });
      if(geometry.left<0 || geometry.right>width+1 || geometry.inputRight>geometry.right || !geometry.fullLabel || geometry.whiteSpace!=='normal')throw new Error('Popup overflow/truncation: '+JSON.stringify(geometry));
      await page.screenshot({animations:'disabled',path:`C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/admin-${language}-${width}.png`});
      await popup.locator('input').fill('no-such-synthetic-category');await page.keyboard.press('Escape');
      const emptyEscape=await trigger.evaluate(el=>document.activeElement===el && el.getAttribute('aria-expanded')==='false');
      if(!emptyEscape)throw new Error('Empty search Escape focus failed');
      await trigger.click();await page.keyboard.press('Tab');await page.keyboard.press('Escape');
      const optionEscape=await trigger.evaluate(el=>document.activeElement===el && el.getAttribute('aria-expanded')==='false');
      if(!optionEscape)throw new Error('Option Escape focus failed');
      rows.push({language,width,...geometry,emptyEscape,optionEscape});
    }
  }
  return {checks:rows.length,rows};
}
