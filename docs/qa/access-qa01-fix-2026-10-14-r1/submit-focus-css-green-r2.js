async (page) => {
 const rows=[],base='http://127.0.0.1:57061/',out='/home/ramin/kidsmap/docs/qa/access-qa01-fix-2026-10-14-r1/screenshots/';
 const errors=[],badResponses=[];const onError=e=>errors.push(String(e));const onResponse=r=>{if(r.url().startsWith(base)&&r.status()>=400)badResponses.push({url:r.url(),status:r.status()});};
 page.on('pageerror',onError);page.on('response',onResponse);
 const style=locator=>locator.evaluate(e=>{const c=getComputedStyle(e);return {focusVisible:e.matches(':focus-visible'),boxShadow:c.boxShadow,outline:c.outline,background:c.backgroundColor,color:c.color}});
 const changed=(before,after)=>after.focusVisible&&(before.boxShadow!==after.boxShadow||before.outline!==after.outline||before.background!==after.background||before.color!==after.color);
 const check=(lang,width,name,ok,detail)=>rows.push({lang,width,name,status:ok?'PASS':'FAIL',detail});
 try {
 for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
  await page.setViewportSize({width,height:900});const prefix=lang==='az'?'':lang+'/';await page.goto(base+prefix+'auth/login/');await page.mouse.move(0,0);
  const opener=page.locator('[data-open-reset-modal]'),submit=page.locator('#resetModalSubmitBtn');await opener.press('Enter');await page.waitForFunction(()=>document.activeElement.id==='resetModalEmailInput');await page.waitForTimeout(220);
  const before=await style(submit),beforeBox=await submit.boundingBox();await page.keyboard.press('Tab');await page.waitForTimeout(220);const after=await style(submit),box=await submit.boundingBox();
  check(lang,width,'Submit keyboard focus visibly changes indicator',changed(before,after),{before,after});
  const ring=await submit.evaluate(e=>{const c=getComputedStyle(e);return {width:c.outlineWidth,style:c.outlineStyle,color:c.outlineColor,offset:c.outlineOffset,brand:getComputedStyle(document.documentElement).getPropertyValue('--brand-turf').trim(),parentOverflow:getComputedStyle(e.parentElement).overflow}});
  check(lang,width,'Scoped ring is visible and within viewport',ring.width==='3px'&&ring.style==='solid'&&ring.color==='rgb(19, 111, 56)'&&ring.offset==='3px'&&box.x>=6&&box.y>=6&&box.x+box.width+6<=width&&box.y+box.height+6<=900,{ring,box});
  check(lang,width,'Scoped ring preserves button geometry',Math.abs(box.width-beforeBox.width)<.25&&Math.abs(box.height-beforeBox.height)<.25,{before:beforeBox,after:box});
  await page.screenshot({path:out+lang+'-'+width+'-submit-visible-focus-green.png'});
  await page.keyboard.press('Escape');await page.waitForFunction(()=>document.activeElement.matches('[data-open-reset-modal]'));
  check(lang,width,'Escape returns opener after CSS change',await opener.evaluate(e=>document.activeElement===e&&!e.closest('[inert]')),{});
  await page.reload();await page.mouse.move(0,0);await opener.press('Enter');await page.waitForFunction(()=>document.activeElement.id==='resetModalEmailInput');await page.waitForTimeout(220);const beforeReload=await style(submit);await page.keyboard.press('Tab');await page.waitForTimeout(220);
  check(lang,width,'Reload retains visible submit indicator',changed(beforeReload,await style(submit)),{});await page.keyboard.press('Escape');
 }
 await page.goto(base+'ru/auth/login/');
 } catch(e) {return {rows,error:String(e),pageErrors:errors,localBadResponses:badResponses};} finally {page.off('pageerror',onError);page.off('response',onResponse);}
 return {rows,pageErrors:errors,localBadResponses:badResponses,simulation:'NONE: actual native keyboard, application CSS and reload; no request/DOM/style substitution'};
}
