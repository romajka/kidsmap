async (page) => {
  const origin='http://127.0.0.1:33336',rows=[];
  const snap=async()=>await page.locator('[data-review-stars]').evaluate(p=>{
    const s=[...p.querySelectorAll('[role=radio]')],input=p.parentElement.querySelector('[name=rating]');
    return {rating:Number(input.value),checked:s.filter(e=>e.getAttribute('aria-checked')==='true').map(e=>Number(e.dataset.value)),
      tab:s.filter(e=>e.tabIndex===0).map(e=>Number(e.dataset.value)),focus:Number(document.activeElement.dataset.value||0)};
  });
  const agrees=(s,value)=>s.rating===value&&JSON.stringify(s.checked)==='['+value+']'&&JSON.stringify(s.tab)==='['+value+']';
  await page.goto(origin+'/qa/login/author/');
  for(const [lang,prefix] of [['ru','/ru'],['az',''],['en','/en']]){
    for(const width of [390,768,1440]){
      await page.setViewportSize({width,height:844});await page.goto(origin+prefix+'/reviews/');
      const picker=page.locator('[data-review-stars]'),f=page.locator('#site-reviews form.review-form'),checks={};
      checks.initial5=agrees(await snap(),5);
      await picker.locator('[data-value="3"]').click();checks.mouse3=agrees(await snap(),3);
      await picker.locator('[data-value="5"]').hover();checks.hover_keeps3=agrees(await snap(),3);
      await f.locator('[name=author_name]').hover();
      await picker.locator('[data-value="3"]').focus();
      for(const [key,value] of [['ArrowRight',4],['ArrowDown',5],['ArrowRight',1],['ArrowLeft',5],['ArrowUp',4],['Home',1],['End',5]]){
        await page.keyboard.press(key);const s=await snap();checks[key+'-'+value]=agrees(s,value)&&s.focus===value;
      }
      await page.keyboard.press('Tab');checks.tab_exits=await f.locator('[name=author_name]').evaluate(e=>e===document.activeElement);
      await page.keyboard.press('Shift+Tab');checks.shift_tab5=(await snap()).focus===5;
      await picker.locator('[data-value="2"]').click();await f.evaluate(e=>e.reset());
      await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
      checks.reset5=agrees(await snap(),5);
      checks.no_overflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1);
      rows.push({lang,width,checks});
    }
  }
  return rows;
}
