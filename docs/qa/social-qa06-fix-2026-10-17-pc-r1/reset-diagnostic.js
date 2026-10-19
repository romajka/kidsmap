async (page) => {
  await page.goto('http://127.0.0.1:33337/qa/login/author/');
  await page.goto('http://127.0.0.1:33337/ru/reviews/');
  const form=page.locator('#site-reviews form.review-form');
  const read=async()=>await form.evaluate(f=>{const i=f.querySelector('[name=rating]');return {value:i.value,defaultValue:i.defaultValue,attribute:i.getAttribute('value'),
    checked:[...f.querySelectorAll('[aria-checked=true]')].map(e=>e.dataset.value)};});
  const initial=await read();
  await form.locator('[data-value="2"]').click();const chosen=await read();
  await form.evaluate(f=>f.reset());await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  return {initial,chosen,afterReset:await read(),application_changes:0};
}
