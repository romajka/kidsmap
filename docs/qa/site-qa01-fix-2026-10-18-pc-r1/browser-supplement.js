async original=>{
const base='http://127.0.0.1:33480',O='/mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1',rows=[],pageerrors=[],local_errors=[],blocked=[],browser=original.context().browser();
for(const role of ['none','viewer','addviewer','content']) {
 const c=await browser.newContext({viewport:{width:390,height:950},serviceWorkers:'block'});
 await c.route('**/*',r=>{if(new URL(r.request().url()).hostname==='127.0.0.1')return r.continue();blocked.push(new URL(r.request().url()).hostname);return r.abort();});
 const p=await c.newPage();p.setDefaultTimeout(10000);p.on('pageerror',e=>pageerrors.push(String(e)));
 await p.goto(base+'/qa/site01/login/'+role+'/');
 const state=async()=> (await p.request.get(base+'/qa/site01/state/')).json();
 const before=await state();const csrf=(await c.cookies()).find(x=>x.name==='csrftoken')?.value;
 if(['none','viewer'].includes(role)) {
  const upload=await p.request.post(base+'/admin/catalog/sitegalleryimage/ajax-upload/',{headers:{'X-CSRFToken':csrf},multipart:{placement:'home_hero',image:{name:'denied-gallery.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=','base64')}}});
  rows.push({id:'gallery-direct-denial',role,status:upload.status(),checks:{status403:upload.status()===403,noDBFilesMutation:JSON.stringify(await state())===JSON.stringify(before)}});
 }
 if(role==='none') {
  for(const prefix of ['','/ru','/en']) {
   const r=await p.request.get(base+prefix+'/admin/catalog/sitegalleryimage/',{maxRedirects:0});
   rows.push({id:'localized-denial',prefix,status:r.status(),checks:{status403:r.status()===403}});
  }
  for(const suffix of ['','ajax-upload/','ajax-delete-main-image/']) {
   const path='/admin/catalog/sitegalleryimage/'+suffix;
   const r=suffix?await p.request.post(base+'/az'+path,{headers:{'X-CSRFToken':csrf},form:{field:'logo'},maxRedirects:0}):await p.request.get(base+'/az'+path,{maxRedirects:0});
   rows.push({id:'legacy-az-redirect',path,status:r.status(),location:r.headers().location,checks:{redirect301:r.status()===301,canonicalTarget:r.headers().location===path,noMutation:JSON.stringify(await state())===JSON.stringify(before)}});
  }
 } else {
  await p.goto(base+'/admin/catalog/sitegalleryimage/');
  const grid=p.locator('.km-gallery-grid').first();await grid.scrollIntoViewIfNeeded();
  await p.screenshot({path:O+'/png/gallery-controls-'+role+'-390.png',animations:'disabled'});
  if(role==='viewer') {
   await p.goto(base+'/admin/catalog/sitegalleryimage/');let forbiddenFocus=false;
   for(let i=0;i<12;i++){await p.keyboard.press('Tab');forbiddenFocus ||= await p.evaluate(()=>!!document.activeElement.closest('.km-media-upload-btn,.km-media-delete-btn,.km-gallery-add,.km-gallery-card-actions a'));}
   rows.push({id:'readonly-keyboard',role,checks:{noMutationFocus:!forbiddenFocus,noMutation:JSON.stringify(await state())===JSON.stringify(before)}});
  }
  if(role==='content') {
   await p.goto(base+'/admin/catalog/sitegalleryimage/');const trigger=p.locator('.km-media-row[data-field=logo] .km-media-delete-btn');
   await trigger.focus();await p.keyboard.press('Enter');const dialog=p.locator('[role=alertdialog],[role=dialog]').filter({has:p.locator('.km-modal__title')}).first();await dialog.waitFor({state:'visible'});await p.waitForTimeout(80);await p.keyboard.press('Escape');await dialog.waitFor({state:'hidden'});
   const focusRestored=await trigger.evaluate(e=>e===document.activeElement);
   rows.push({id:'keyboard-cancel-delete',role,checks:{focusRestored,noMutation:JSON.stringify(await state())===JSON.stringify(before)}});
  }
 }
 await c.close();
}
return {rows,pageerrors,local_errors,blocked};
}
