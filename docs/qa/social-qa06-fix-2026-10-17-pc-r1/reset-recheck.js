async (page) => {
  const origin='http://127.0.0.1:33337',rows=[],errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const snap=async()=>await page.locator('[data-review-stars]').evaluate(p=>{const s=[...p.querySelectorAll('[role=radio]')],i=p.parentElement.querySelector('[name=rating]');
    return {rating:Number(i.value),defaultValue:Number(i.defaultValue),checked:s.filter(e=>e.getAttribute('aria-checked')==='true').map(e=>Number(e.dataset.value)),
      tab:s.filter(e=>e.tabIndex===0).map(e=>Number(e.dataset.value))};});
  const agrees=(s,n)=>s.rating===n&&JSON.stringify(s.checked)==='['+n+']'&&JSON.stringify(s.tab)==='['+n+']';
  try {
    await page.goto(origin+'/qa/login/author/');
    for(const [lang,prefix] of [['ru','/ru'],['az',''],['en','/en']]){
      for(const width of [390,768,1440]){
        await page.setViewportSize({width,height:844});await page.goto(origin+prefix+'/reviews/');
        const initial=await snap(),f=page.locator('#site-reviews form.review-form');
        await f.locator('[data-value="2"]').click();const chosen=await snap();
        await f.evaluate(e=>e.reset());await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
        const reset=await snap();
        const png='/mnt/c/kidsmap/.tmp/social06-pc-fix-r1/png/reset-final-'+lang+'-'+width+'.png';await page.screenshot({path:png});
        rows.push({id:'reset-'+lang+'-'+width,lang,width,png,checks:{initial5:agrees(initial,5),chosen2:agrees(chosen,2),reset5:agrees(reset,5)},facts:{initial,chosen,reset}});
      }
    }
    return {rows,pageerrors:errors};
  }catch(e){return {rows,pageerrors:errors,fatal:{message:e.message}};}
}
