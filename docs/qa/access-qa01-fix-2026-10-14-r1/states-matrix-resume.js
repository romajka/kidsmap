async (page) => {
 const base='http://127.0.0.1:57061/',out='/home/ramin/kidsmap/docs/qa/access-qa01-fix-2026-10-14-r1/screenshots/';
 const rows=[],diagnostics={pageerrors:[],console:[],failedRequests:[],badResponses:[]};
 page.on('pageerror',e=>diagnostics.pageerrors.push(e.message));
 page.on('console',m=>{if(['error','warning'].includes(m.type()))diagnostics.console.push({type:m.type(),text:m.text()})});
 page.on('requestfailed',r=>diagnostics.failedRequests.push({url:r.url(),error:r.failure()?.errorText}));
 page.on('response',r=>{if(r.status()>=400)diagnostics.badResponses.push({url:r.url(),status:r.status()})});
 const active=()=>page.evaluate(()=>{const e=document.activeElement,c=getComputedStyle(e);return {id:e.id,tag:e.tagName,classes:e.className,inModal:document.getElementById('resetPasswordModal').contains(e),opener:e.matches('[data-open-reset-modal]'),focusVisible:e.matches(':focus-visible'),boxShadow:c.boxShadow,outline:c.outline,borderColor:c.borderColor,background:c.backgroundColor};});
 const record=(lang,width,name,ok,detail)=>rows.push({lang,width,name,status:ok?'PASS':'FAIL',detail});
 try{
  for(const lang of ['az','en'])for(const width of [360,390,768,1024,1280,1440]){
   if(lang==='az' && width!==1440)continue;
   await page.setViewportSize({width,height:900});const prefix=lang==='az'?'':lang+'/';await page.goto(base+prefix+'auth/login/');
   const opener=page.locator('[data-open-reset-modal]'),input=page.locator('#resetModalEmailInput'),submit=page.locator('#resetModalSubmitBtn'),modal=page.locator('#resetPasswordModal');
   const identifier='matrix_'+lang+'_'+width+'@example.invalid';await page.locator('#id_username').fill(identifier);
   let reached=false;for(let i=0;i<20;i++){if((await active()).opener){reached=true;break}await page.keyboard.press('Tab')}
   record(lang,width,'Native Tab reaches opener',reached);
   const inertBefore=await page.evaluate(()=>Array.from(document.body.children).filter(e=>e.id!=='resetPasswordModal'&&!['SCRIPT','STYLE','LINK'].includes(e.tagName)).map(e=>e.getAttribute('inert')));
   await page.keyboard.press('Space');await input.waitFor({state:'visible'});await page.waitForFunction(()=>document.activeElement.id==='resetModalEmailInput');
   record(lang,width,'Space initial focus / prefill',(await active()).id==='resetModalEmailInput'&&await input.inputValue()===identifier);
   record(lang,width,'Visible keyboard input focus',(await active()).focusVisible&&(await active()).boxShadow!=='none',await active());
   await input.fill('');await submit.click();await page.locator('#resetModalFieldError').waitFor({state:'visible'});
   const empty=await page.locator('#resetModalFieldError').innerText();record(lang,width,'Empty localized error / focus',(await active()).id==='resetModalEmailInput'&&empty===({ru:'Укажите email или логин.',az:'Email və ya istifadəçi adını daxil edin.',en:'Enter your email or username.'})[lang],empty);
   await page.screenshot({path:out+lang+'-'+width+'-empty-error.png'});await input.fill(identifier);
   await page.route('**/auth/password-reset/',r=>r.abort('failed'));await submit.click();await page.locator('#resetModalAlert').waitFor({state:'visible'});
   const network=await page.locator('#resetModalAlert').innerText();record(lang,width,'Network error localized / input retained',network.includes(({ru:'Ошибка сети.',az:'Şəbəkə xətası.',en:'Network error.'})[lang])&&await input.inputValue()===identifier&&await submit.isEnabled()&&(await active()).inModal,network);
   await page.screenshot({path:out+lang+'-'+width+'-network-error.png'});await page.unroute('**/auth/password-reset/');
   await page.route('**/auth/password-reset/',r=>r.fulfill({status:400,contentType:'application/json',body:JSON.stringify({ok:false,message:'SIMULATED validation error'})}));
   await submit.click();await page.waitForFunction(()=>document.getElementById('resetModalAlert').textContent.includes('SIMULATED'));
   record(lang,width,'AJAX400 retains enabled form and identifier',await input.inputValue()===identifier&&await submit.isEnabled()&&await input.isVisible()&&(await active()).inModal);
   await page.unroute('**/auth/password-reset/');
   let release;await page.route('**/auth/password-reset/',async r=>{await new Promise(resolve=>release=resolve);await r.continue()});
   const response=page.waitForResponse(r=>r.url().endsWith('/auth/password-reset/')&&r.request().method()==='POST');await submit.click();await page.waitForFunction(()=>document.getElementById('resetModalSubmitBtn').disabled);
   record(lang,width,'Loading disabled / spinner / available focus',await submit.isDisabled()&&await page.locator('.km-btn-spinner').isVisible()&&(await active()).id==='resetModalEmailInput',await active());
   const loadingTrail=[];for(let i=0;i<5;i++){await page.keyboard.press(i===4?'Shift+Tab':'Tab');loadingTrail.push(await active())}
   record(lang,width,'Loading Tab skips disabled submit',loadingTrail.every(e=>e.inModal&&e.id!=='resetModalSubmitBtn'),loadingTrail);
   await page.screenshot({path:out+lang+'-'+width+'-loading.png'});while(!release)await new Promise(r=>setTimeout(r,20));release();const posted=await response;
   record(lang,width,'Real reset endpoint accepts filled identifier',posted.status()===200&&(await posted.json()).ok);
   await page.locator('#resetModalSuccessState').waitFor({state:'visible'});await page.unroute('**/auth/password-reset/');
   record(lang,width,'Success focuses visible action',(await active()).classes.includes('km-modal-success-btn')&&(await active()).inModal,await active());
   const label=await modal.getAttribute('aria-labelledby');record(lang,width,'Success dialog has visible localized name',label==='resetModalSuccessTitle'&&await page.locator('#'+label).isVisible());
   const successTrail=[];for(let i=0;i<5;i++){await page.keyboard.press(i===4?'Shift+Tab':'Tab');successTrail.push(await active())}
   record(lang,width,'Success Tab excludes hidden form',successTrail.every(e=>e.inModal&&(e.classes.includes('km-modal-close')||e.classes.includes('km-modal-success-btn'))),successTrail);
   await page.screenshot({path:out+lang+'-'+width+'-success.png'});
   if(!(await active()).classes.includes('km-modal-success-btn'))await page.keyboard.press('Tab');await page.keyboard.press('Enter');await page.waitForTimeout(280);
   const inertAfter=await page.evaluate(()=>Array.from(document.body.children).filter(e=>e.id!=='resetPasswordModal'&&!['SCRIPT','STYLE','LINK'].includes(e.tagName)).map(e=>e.getAttribute('inert')));
   record(lang,width,'Success keyboard close restores opener and background',(await active()).opener&&JSON.stringify(inertBefore)===JSON.stringify(inertAfter)&&await modal.evaluate(e=>e.inert));
   await page.keyboard.press('Space');await input.waitFor({state:'visible'});await page.waitForFunction(()=>document.activeElement.id==='resetModalEmailInput');record(lang,width,'Reopen preserves identifier / resets form label',await input.inputValue()===identifier&&await modal.getAttribute('aria-labelledby')==='resetModalTitle'&&await input.isVisible()&&await page.locator('#resetModalAlert').isHidden());
   await page.keyboard.press('Shift+Tab');const closeFocus=await active();record(lang,width,'Close receives visible keyboard focus',closeFocus.classes.includes('km-modal-close')&&closeFocus.focusVisible,closeFocus);
   await page.screenshot({path:out+lang+'-'+width+'-close-focus.png'});await page.keyboard.press('Space');await page.waitForTimeout(280);
   record(lang,width,'Close button Space restores opener',(await active()).opener);
   await page.keyboard.press('Enter');await input.waitFor({state:'visible'});await page.locator('.km-modal-backdrop').click({position:{x:5,y:5}});await page.waitForTimeout(280);record(lang,width,'Backdrop close restores opener',(await active()).opener);
   await page.keyboard.press('Enter');await page.keyboard.press('Escape');await page.waitForTimeout(150);record(lang,width,'Rapid close has no delayed focus',(await active()).opener&&await modal.getAttribute('aria-hidden')==='true');
  }
  await page.goto(base+'ru/auth/login/');return {rows,diagnostics,simulation:'network abort/AJAX400/held transport SIMULATED; real filled reset POST; app DOM/text unchanged'};
 }catch(e){await page.unroute('**/auth/password-reset/').catch(()=>{});return {rows,diagnostics,error:e.message};}
}
