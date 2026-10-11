async original=>{
 const B='http://localhost:8820',D='C:/kidsmap/docs/qa/module07-2026-10-10-r1/screenshots/',rows=[];
 for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
  const pre=lang==='az'?'/':'/'+lang+'/',c=await original.context().browser().newContext({viewport:{width,height:950}}),p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'anonymous',lang,width,...x});
  await p.goto(B+pre+'auth/login/',{waitUntil:'domcontentloaded'});const open=p.locator('[data-open-reset-modal]');await open.click();await p.waitForTimeout(500);const focus=[];
  for(let i=0;i<8;i++){await p.keyboard.press('Tab');focus.push(await p.evaluate(()=>({tag:document.activeElement.tagName,inModal:!!document.activeElement.closest('#resetPasswordModal'),text:document.activeElement.textContent?.trim().slice(0,90)})));}
  const trapFile='reset-focus-trap-'+lang+'-'+width+'.png';await p.screenshot({path:D+trapFile});add('reset-modal-focus-trap',focus.every(x=>x.inModal),{focus,screenshot:trapFile});
  await p.keyboard.press('Escape');await p.waitForTimeout(1000);const state=await p.locator('#resetPasswordModal').evaluate(e=>({active:e.classList.contains('is-active'),hidden:e.getAttribute('aria-hidden'),opacity:getComputedStyle(e).opacity,visibility:getComputedStyle(e).visibility}));add('reset-modal-Escape-settled',!state.active&&state.hidden==='true',{state});add('reset-modal-focus-return',await open.evaluate(e=>e===document.activeElement),{active:await p.evaluate(()=>({tag:document.activeElement.tagName,id:document.activeElement.id,text:document.activeElement.textContent?.trim().slice(0,100)}))});
  await open.click();await p.locator('#resetModalEmailInput').fill('owner07@example.invalid');await p.route('**/auth/password-reset/',r=>r.abort());await p.locator('#resetModalSubmitBtn').click();await p.waitForTimeout(550);add('reset-network-error-input-preserved',(await p.locator('#resetModalEmailInput').inputValue())==='owner07@example.invalid'&&!(await p.locator('#resetModalSubmitBtn').isDisabled()),{classification:'SIMULATED localhost AJAX abort',screenshot:'reset-network-error-'+lang+'-'+width+'.png'});await p.screenshot({path:D+'reset-network-error-'+lang+'-'+width+'.png'});await c.close();
 }
 return{rows};
}
