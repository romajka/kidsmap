async (page) => {
 const rows=[],diagnostics={pageerrors:[],localFailures:[],badResponses:[]};
 const base='http://127.0.0.1:57059/',out='/home/ramin/kidsmap/docs/qa/access-qa01-recheck-2026-10-14-r1/screenshots/';
 page.on('pageerror',e=>diagnostics.pageerrors.push(e.message));
 page.on('requestfailed',r=>{if(r.url().includes('/auth/password-reset/'))diagnostics.localFailures.push({path:'password-reset',error:r.failure()?.errorText})});
 page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(base))diagnostics.badResponses.push({path:r.url().includes('/auth/password-reset/')?'password-reset':'other',status:r.status()})});
 const a=()=>page.evaluate(()=>{const e=document.activeElement;return {tag:e.tagName,id:e.id,inModal:document.getElementById('resetPasswordModal')?.contains(e),visible:!!e.getClientRects().length}});
 const record=(lang,name,ok,detail)=>rows.push({lang,width:390,name,status:ok?'PASS':'FAIL',detail});
 try{
  const secret=await (await page.request.get(base+'qa/fixture-password/')).json();
  await page.context().clearCookies();await page.goto(base+'ru/auth/login/');
  await page.locator('#id_username').fill('qa01_ru@example.invalid');await page.locator('#id_password').fill(secret.old);
  await Promise.all([page.waitForNavigation(),page.locator('form.register-form button[type=submit]').click()]);
  record('ru','Old password rejected',page.url().includes('/auth/login/')&&await page.locator('form.register-form .auth-errors').isVisible());
  await page.locator('#id_password').fill(secret.new);await Promise.all([page.waitForURL('**/account/profile/'),page.locator('form.register-form button[type=submit]').click()]);record('ru','New password login succeeds',page.url().endsWith('/account/profile/'));
  for(const lang of ['az','en']){
   await page.context().clearCookies();await page.setViewportSize({width:390,height:900});const prefix=lang==='az'?'':lang+'/';
   await page.goto(base+prefix+'auth/login/');const opener=page.locator('[data-open-reset-modal]'),input=page.locator('#resetModalEmailInput'),submit=page.locator('#resetModalSubmitBtn');
   await opener.click();await page.waitForFunction(()=>document.activeElement.id==='resetModalEmailInput');
   await submit.click();await page.locator('#resetModalFieldError').waitFor({state:'visible'});
   const empty=await page.locator('#resetModalFieldError').innerText();record(lang,'Empty error localized',empty===({ru:'Укажите email или логин.',az:'Email və ya istifadəçi adını daxil edin.',en:'Enter your email or username.'})[lang],empty);
   await input.fill('qa01_'+lang+'@example.invalid');
   await page.route('**/auth/password-reset/',r=>r.abort('failed'));await submit.click();await page.locator('#resetModalAlert').waitFor({state:'visible'});
   const network=await page.locator('#resetModalAlert').innerText();record(lang,'Network error localized',network.includes(({ru:'Ошибка сети.',az:'Şəbəkə xətası.',en:'Network error.'})[lang]),network);record(lang,'Failure preserves identifier / loading reset',await input.inputValue()==='qa01_'+lang+'@example.invalid'&&await submit.isEnabled());
   await page.screenshot({path:out+lang+'-390-network-error.png'});await page.unroute('**/auth/password-reset/');
   await page.route('**/auth/password-reset/',r=>r.fulfill({status:400,contentType:'application/json',body:JSON.stringify({ok:false,message:'SIMULATED validation error'})}));
   await submit.click();await page.waitForFunction(()=>document.getElementById('resetModalAlert').textContent.includes('SIMULATED'));
   record(lang,'AJAX400 stays in form / identifier retained',await input.inputValue()==='qa01_'+lang+'@example.invalid'&&await input.isVisible()&&await submit.isEnabled());await page.unroute('**/auth/password-reset/');
   await page.route('**/auth/password-reset/',async r=>{await new Promise(resolve=>setTimeout(resolve,1000));await r.continue()});
   const response=page.waitForResponse(r=>r.url().endsWith('/auth/password-reset/')&&r.request().method()==='POST');await submit.click();await page.waitForFunction(()=>document.getElementById('resetModalSubmitBtn').disabled);
   record(lang,'Loading disabled / spinner',await submit.isDisabled()&&await page.locator('.km-btn-spinner').isVisible());
   const loadingTrail=[];for(let i=0;i<3;i++){await page.keyboard.press('Tab');loadingTrail.push(await a())}
   record(lang,'Loading focus inside / skip disabled',loadingTrail.every(e=>e.inModal&&e.id!=='resetModalSubmitBtn'),loadingTrail);
   await page.screenshot({path:out+lang+'-390-loading.png'});const posted=await response;record(lang,'Actual reset POST200',(await posted.json()).ok&&posted.status()===200);
   await page.locator('#resetModalSuccessState').waitFor({state:'visible'});await page.unroute('**/auth/password-reset/');
   record(lang,'Success focus is on available control',(await a()).inModal&&(await a()).visible,await a());
   await page.screenshot({path:out+lang+'-390-success.png'});
   await page.locator('#resetModalSuccessState [data-modal-close]').click();await page.waitForTimeout(300);record(lang,'Success close restores opener',await opener.evaluate(e=>document.activeElement===e));
   await opener.click();await page.waitForTimeout(350);record(lang,'Reopen preserves email / shows form',await input.inputValue()==='qa01_'+lang+'@example.invalid'&&await input.isVisible());await page.keyboard.press('Escape');
   const email=await(await page.request.get(base+'qa/reset-link/')).json();const link=email.url;
   record(lang,'Own local email contains reset link',link.startsWith(base)&&link.includes('/reset/'));
   await page.goto(link);await page.locator('[name=new_password1]').fill(secret.new);await page.locator('[name=new_password2]').fill(secret.new);
   await Promise.all([page.waitForURL('**/reset/done/'),page.locator('form button[type=submit]').click()]);record(lang,'Native new password accepted',page.url().endsWith('/reset/done/'));
   await page.goto(link);record(lang,'Consumed reset link refused',await page.locator('[name=new_password1]').count()===0);await page.screenshot({path:out+lang+'-390-replay-denied.png'});
   await page.goto(base+prefix+'auth/login/');await page.locator('#id_username').fill('qa01_'+lang+'@example.invalid');await page.locator('#id_password').fill(secret.old);
   await Promise.all([page.waitForNavigation(),page.locator('form.register-form button[type=submit]').click()]);record(lang,'Old password rejected',page.url().includes('/auth/login/')&&await page.locator('form.register-form .auth-errors').isVisible());
   await page.locator('#id_password').fill(secret.new);await Promise.all([page.waitForURL('**/account/profile/'),page.locator('form.register-form button[type=submit]').click()]);record(lang,'New password login succeeds',page.url().endsWith('/account/profile/'));
  }
  await page.goto(base+'ru/auth/login/');return {rows,diagnostics,simulation:'backend AJAX400 and 1s transport delay SIMULATED; network failure intentional; real reset email/password/replay/login executed'};
 }catch(e){await page.goto(base+'ru/auth/login/').catch(()=>{});return {rows,diagnostics,error:e.message.replace(/http:\/\/[^ ]+\/reset\/[^ ]+/g,'[REDACTED]')};}
}
