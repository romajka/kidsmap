async (page) => {
 const base='http://127.0.0.1:57061/',rows=[];
 for(const cell of [{lang:'ru',width:390},{lang:'en',width:1440}])for(const kind of ['login','standalone-reset']){
  await page.setViewportSize({width:cell.width,height:900});const path=kind==='login'?'auth/login/':'auth/password-reset/';await page.goto(base+cell.lang+'/'+path);await page.mouse.move(0,0);
  const control=page.locator('form.register-form button[type=submit]');await control.focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');await page.waitForTimeout(220);
  const styles=await control.evaluate(e=>{const c=getComputedStyle(e),b=e.getBoundingClientRect();return {outline:c.outline,outlineOffset:c.outlineOffset,boxShadow:c.boxShadow,background:c.background,fontSize:c.fontSize,padding:c.padding,border:c.border,focusVisible:e.matches(':focus-visible'),box:{width:b.width,height:b.height}}});
  rows.push({...cell,kind,styles});
 }
 await page.goto(base+'ru/auth/login/');return {rows};
}
