async (page) => {
 await page.keyboard.press('Escape');await page.waitForTimeout(300);
 await page.evaluate(()=>{
  window.qaFocusTrace=[];window.qaSavedFocus=HTMLElement.prototype.focus;window.qaSavedRaf=window.requestAnimationFrame;window.qaSavedCancel=window.cancelAnimationFrame;
  const state=()=>{const m=document.getElementById('resetPasswordModal'),i=document.getElementById('resetModalEmailInput');return {active:document.activeElement.tagName+'#'+document.activeElement.id,open:m.classList.contains('is-active'),modalVisible:getComputedStyle(m).visibility,inputVisible:getComputedStyle(i).visibility,inputDisabled:i.disabled,inputInert:!!i.closest('[inert]')}};
  HTMLElement.prototype.focus=function(...args){const r=window.qaSavedFocus.apply(this,args);window.qaFocusTrace.push({kind:'focus',target:this.tagName+'#'+this.id,...state()});return r};
  window.requestAnimationFrame=fn=>{const id=window.qaSavedRaf(t=>{window.qaFocusTrace.push({kind:'frame-before',...state()});fn(t);window.qaFocusTrace.push({kind:'frame-after',...state()})});window.qaFocusTrace.push({kind:'queued',id,...state()});return id};
  window.cancelAnimationFrame=id=>{window.qaFocusTrace.push({kind:'cancel',id,...state()});return window.qaSavedCancel(id)};
 });
 const attempts=[];
 for(let i=0;i<12;i++){
  await page.locator('[data-open-reset-modal]').press('Space');await page.waitForTimeout(180);
  const current=await page.evaluate(()=>({active:document.activeElement.tagName+'#'+document.activeElement.id,trace:window.qaFocusTrace}));attempts.push(current);
  if(current.active!=='INPUT#resetModalEmailInput')break;
  await page.keyboard.press('Escape');await page.waitForTimeout(300);await page.evaluate(()=>window.qaFocusTrace=[]);
 }
 await page.evaluate(()=>{HTMLElement.prototype.focus=window.qaSavedFocus;window.requestAnimationFrame=window.qaSavedRaf;window.cancelAnimationFrame=window.qaSavedCancel});
 return {attempts};
}
