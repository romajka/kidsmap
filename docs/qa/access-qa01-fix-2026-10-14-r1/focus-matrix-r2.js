async (page) => {
 const rows=[],trails=[],diagnostics={pageerrors:[],console:[],failedRequests:[],localBadResponses:[]};
 page.on('pageerror',e=>diagnostics.pageerrors.push(e.message));
 page.on('console',m=>{if(m.type()==='error')diagnostics.console.push(m.text())});
 page.on('requestfailed',r=>diagnostics.failedRequests.push({url:r.url(),error:r.failure()?.errorText}));
 page.on('response',r=>{if(r.url().startsWith('http://127.0.0.1:57061/')&&r.status()>=400)diagnostics.localBadResponses.push({url:r.url(),status:r.status()})});
 const active=()=>page.evaluate(()=>{const e=document.activeElement,m=document.getElementById('resetPasswordModal');const c=getComputedStyle(e);return {tag:e.tagName,id:e.id,classes:e.className,inModal:m.contains(e),isOpener:e.matches('[data-open-reset-modal]'),outline:c.outline,background:c.backgroundColor,focusVisible:e.matches(':focus-visible')};});
 const record=(lang,width,name,ok,detail)=>rows.push({lang,width,name,status:ok?'PASS':'FAIL',detail});
 for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
  await page.setViewportSize({width,height:900});
  const prefix=lang==='az'?'':lang+'/';await page.goto('http://127.0.0.1:57061/'+prefix+'auth/login/');
  const opener=page.locator('[data-open-reset-modal]'),modal=page.locator('#resetPasswordModal'),input=page.locator('#resetModalEmailInput');
  await opener.focus();await page.keyboard.press('Enter');await input.waitFor({state:'visible'});
  await page.waitForFunction(()=>document.activeElement.id==='resetModalEmailInput');
  record(lang,width,'Enter opens; initial focus',(await active()).id==='resetModalEmailInput');
  const trail=[{key:'opened',...(await active())}];
  for(let i=0;i<5;i++){await page.keyboard.press('Tab');trail.push({key:'Tab',...(await active())});}
  const forward=trail.slice(1).every(e=>e.inModal);record(lang,width,'Tab stays inside',forward,trail);
  await page.screenshot({path:'/home/ramin/kidsmap/docs/qa/access-qa01-fix-2026-10-14-r1/screenshots/'+lang+'-'+width+'-focus-escaped.png'});
  await input.focus();const reverse=[];for(let i=0;i<4;i++){await page.keyboard.press('Shift+Tab');reverse.push({key:'Shift+Tab',...(await active())})}
  record(lang,width,'Shift+Tab stays inside',reverse.every(e=>e.inModal),reverse);
  record(lang,width,'Background inert',await page.evaluate(()=>Array.from(document.body.children).filter(e=>e.id!=='resetPasswordModal'&&!['SCRIPT','STYLE','LINK'].includes(e.tagName)).every(e=>e.inert)));
  await page.keyboard.press('Escape');await page.waitForFunction(()=>!document.getElementById('resetPasswordModal').classList.contains('is-active'));await page.waitForTimeout(300);
  record(lang,width,'Escape closes',await modal.getAttribute('aria-hidden')==='true');record(lang,width,'Escape restores opener',(await active()).isOpener,await active());
  await opener.focus();await page.keyboard.press('Space');await page.waitForTimeout(350);
  const space=await modal.evaluate(e=>e.classList.contains('is-active'));record(lang,width,'Space opens',space);
  if(!space)await opener.click();await page.waitForTimeout(350);
  await page.locator('.km-modal-close').click();await page.waitForTimeout(300);
  record(lang,width,'Close restores opener',(await active()).isOpener,await active());
  await opener.click();await page.waitForTimeout(350);
  const box=await page.locator('.km-modal-dialog').boundingBox();record(lang,width,'Dialog inside viewport',box.x>=0&&box.x+box.width<=width+1&&box.y>=0&&box.y+box.height<=901,box);
  await page.screenshot({path:'/home/ramin/kidsmap/docs/qa/access-qa01-fix-2026-10-14-r1/screenshots/'+lang+'-'+width+'-modal.png'});
  await page.keyboard.press('Escape');await page.waitForTimeout(300);trails.push({lang,width,forward:trail,reverse});
 }
 await page.goto('http://127.0.0.1:57061/ru/auth/login/');
 return {rows,trails,diagnostics,browser:page.context().browser().version(),simulation:'external requests blocked; current approved login focus patch'};
}
