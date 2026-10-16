async (page) => {
 const rows=[],base='http://127.0.0.1:57061/',out='/home/ramin/kidsmap/docs/qa/access-qa01-fix-2026-10-14-r1/screenshots/';
 const style=locator=>locator.evaluate(e=>{const c=getComputedStyle(e);return {focusVisible:e.matches(':focus-visible'),boxShadow:c.boxShadow,outline:c.outline,background:c.backgroundColor,color:c.color}});
 const changed=(before,after)=>after.focusVisible&&(before.boxShadow!==after.boxShadow||before.outline!==after.outline||before.background!==after.background||before.color!==after.color);
 for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
  await page.setViewportSize({width,height:900});const prefix=lang==='az'?'':lang+'/';await page.goto(base+prefix+'auth/login/');await page.mouse.move(0,0);
  await page.locator('#id_username').fill('unknown_focus_'+lang+'_'+width+'@example.invalid');await page.locator('[data-open-reset-modal]').press('Enter');await page.waitForFunction(()=>document.activeElement.id==='resetModalEmailInput');
  const submit=page.locator('#resetModalSubmitBtn'),close=page.locator('.km-modal-close'),success=page.locator('.km-modal-success-btn');
  const beforeSubmit=await style(submit),beforeClose=await style(close),beforeSuccess=await style(success);
  await page.keyboard.press('Tab');await page.waitForTimeout(220);const afterSubmit=await style(submit);rows.push({lang,width,name:'Submit keyboard focus visibly changes indicator',status:changed(beforeSubmit,afterSubmit)?'PASS':'FAIL',detail:{before:beforeSubmit,after:afterSubmit}});
  await page.screenshot({path:out+lang+'-'+width+'-submit-visible-focus.png'});
  const response=page.waitForResponse(r=>r.url().endsWith('/auth/password-reset/')&&r.request().method()==='POST');await page.keyboard.press('Enter');await response;await page.waitForFunction(()=>document.activeElement.classList.contains('km-modal-success-btn'));await page.waitForTimeout(220);
  const afterSuccess=await style(success);rows.push({lang,width,name:'Success keyboard focus visibly changes indicator',status:changed(beforeSuccess,afterSuccess)?'PASS':'FAIL',detail:{before:beforeSuccess,after:afterSuccess}});await page.screenshot({path:out+lang+'-'+width+'-success-visible-focus.png'});
  await page.keyboard.press('Tab');await page.waitForTimeout(220);const afterClose=await style(close);rows.push({lang,width,name:'Close keyboard focus visibly changes indicator',status:changed(beforeClose,afterClose)?'PASS':'FAIL',detail:{before:beforeClose,after:afterClose}});await page.screenshot({path:out+lang+'-'+width+'-close-visible-focus.png'});await page.keyboard.press('Escape');
 }
 await page.goto(base+'ru/auth/login/');return {rows,simulation:'No CSS/DOM substitution; real native keyboard and settled computed styles'};
}
