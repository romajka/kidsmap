async original=>{
const base='http://127.0.0.1:33480',O='/mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1',fixture='/mnt/c/kidsmap/.tmp/site01-pc-fix-r1/fixture.png',rows=[],pageerrors=[],local_errors=[],blocked=[],console_errors=[],browser=original.context().browser();
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
async function context(role) {
 const c=await browser.newContext({viewport:{width:1440,height:950},serviceWorkers:'block'});
 await c.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='127.0.0.1')return r.continue();blocked.push(u.hostname);return r.abort();});
 const p=await c.newPage();p.setDefaultTimeout(12000);
 p.on('pageerror',e=>pageerrors.push({role,message:String(e)}));p.on('console',m=>{if(m.type()==='error')console_errors.push({role,message:m.text()});});
 p.on('response',r=>{const u=new URL(r.url());if(u.hostname==='127.0.0.1'&&r.status()>=400&&![400,403].includes(r.status()))local_errors.push({role,path:u.pathname,status:r.status()});});
 await p.goto(base+'/qa/site01/login/'+role+'/');return {c,p};
}
async function state(p){return(await p.request.get(base+'/qa/site01/state/')).json();}
async function publicLogo(p){await p.goto(base+'/');return p.locator('#km-site-header .km-brand-logo').getAttribute('src');}
async function post(p,c,kind,data,csrf=true) {
 const token=(await c.cookies()).find(x=>x.name==='csrftoken')?.value;
 return p.request.post(base+'/admin/catalog/sitegalleryimage/'+(kind==='upload'?'ajax-upload/':'ajax-delete-main-image/'),{headers:csrf?{'X-CSRFToken':token}:{},...data,maxRedirects:0});
}
for(const role of ['none','viewer','gallery_change','settings_view','gallery_add','proxyonly','volunteer']) {
 const {c,p}=await context(role);const src=await publicLogo(p);const before=await state(p);
 const file={name:'denied.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=','base64')};
 const upload=await post(p,c,'upload',{multipart:{field:'logo',image:file}});const middle=await state(p);
 const del=await post(p,c,'delete',{form:{field:'logo'}});const after=await state(p);const finalsrc=await publicLogo(p);
 rows.push({id:'negative-main',role,upload:upload.status(),delete:del.status(),before,after,publicBefore:src,publicAfter:finalsrc,checks:{upload403:upload.status()===403,delete403:del.status()===403,noDBFileMutation:same(before,middle)&&same(before,after),noPublicCacheChange:src===finalsrc}});await c.close();
}
for(const role of ['guest','nonstaff','inactive']) {
 const {c,p}=await context(role),before=await state(p);
 const r=await post(p,c,'delete',{form:{field:'logo'}});const after=await state(p);
 rows.push({id:'outer-admin-denial',role,status:r.status(),checks:{loginRedirect:r.status()===302&&r.headers().location.includes('/admin/login/'),noMutation:same(before,after)}});await c.close();
}
for(const role of ['content','super']) {
 const {c,p}=await context(role);await p.goto(base+'/admin/catalog/sitegalleryimage/');
 const noCSRF=await post(p,c,'delete',{form:{field:'logo'}},false);
 rows.push({id:'csrf',role,status:noCSRF.status(),checks:{csrf403:noCSRF.status()===403}});
 for(const lang of ['az','ru','en']) {
  const token=(await c.cookies()).find(x=>x.name==='csrftoken')?.value;
  await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':token},form:{language:lang,next:'/admin/'},maxRedirects:0});
  await p.setViewportSize({width:lang==='ru'?390:1440,height:950});
  await p.goto(base+'/admin/catalog/sitegalleryimage/');const before=await state(p);
  const uploaded=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/ajax-upload/'));
  await p.locator('.km-media-row[data-field=logo] input[type=file]').setInputFiles(fixture);
  const ur=await uploaded,ub=await ur.json();await p.waitForFunction(()=>!document.querySelector('.km-media-row[data-field=logo] .km-media-upload-btn')?.disabled);
  const middle=await state(p),src=await publicLogo(p);
  rows.push({id:'native-logo-upload',role,lang,status:ur.status(),before,after:middle,checks:{success:ur.status()===200&&ub.success,dbChanged:middle.logo!==before.logo,filePresent:!!middle.files[middle.logo],publicReadback:src.endsWith(ub.file.url)}});
  await p.screenshot({path:O+'/png/public-upload-'+role+'-'+lang+'.png',animations:'disabled'});
  await p.goto(base+'/admin/catalog/sitegalleryimage/');await p.locator('.km-media-row[data-field=logo] .km-media-delete-btn').click();
  const dialog=p.locator('[role=alertdialog],[role=dialog]').filter({has:p.locator('.km-modal__title')}).first();await dialog.waitFor({state:'visible'});
  await p.waitForTimeout(80);await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');
  const trapped=await dialog.evaluate(d=>d.contains(document.activeElement));
  await p.screenshot({path:O+'/png/delete-dialog-'+role+'-'+lang+'.png',animations:'disabled'});
  const deleted=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/ajax-delete-main-image/'));
  await dialog.locator('.km-btn-modal--danger').click();const dr=await deleted;await p.waitForLoadState('domcontentloaded');
  // Serialize the application's automatic reload before navigating to public readback.
  await p.waitForTimeout(500);await p.goto(base+'/admin/catalog/sitegalleryimage/');
  const final=await state(p),fallback=await publicLogo(p);
  rows.push({id:'native-logo-delete',role,lang,status:dr.status(),after:final,fallback,checks:{success:dr.status()===200,dbCleared:final.logo==='',fileRemoved:!(middle.logo in final.files),publicFallback:!fallback.includes('/media/'),focusTrapped:trapped}});
  await p.screenshot({path:O+'/png/public-fallback-'+role+'-'+lang+'.png',animations:'disabled'});
 }
 // Leave an uploaded legitimate logo for final public and denied-state readback.
 await p.goto(base+'/admin/catalog/sitegalleryimage/');const done=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/ajax-upload/'));
 await p.locator('.km-media-row[data-field=logo] input[type=file]').setInputFiles(fixture);await done;await c.close();
}
for(const role of ['addviewer','content','super']) {
 const {c,p}=await context(role);await p.goto(base+'/admin/catalog/sitegalleryimage/');const before=await state(p);
 const grid=p.locator('.km-gallery-grid').first(),cards=await grid.locator('.km-gallery-card').count();
 const uploaded=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/ajax-upload/'));
 await grid.locator('input[type=file]').setInputFiles(fixture);const response=await uploaded,body=await response.json();
 await p.waitForFunction(n=>document.querySelector('.km-gallery-grid').querySelectorAll('.km-gallery-card:not(.km-gallery-card-uploading)').length===n+1,cards);
 const newest=grid.locator('.km-gallery-card:not(.km-gallery-card-uploading)').last(),links=await newest.locator('a').count(),after=await state(p);
 rows.push({id:'native-gallery-upload',role,status:response.status(),links,returnedURLs:{edit:body.edit_url,delete:body.delete_url},before,after,checks:{success:response.status()===200&&body.success,countIncrement:after.gallery_count===before.gallery_count+1,mainUnchanged:before.logo===after.logo,correctReturnedURLs:role==='addviewer'?body.edit_url===null&&body.delete_url===null:!!body.edit_url&&!!body.delete_url,correctDynamicLinks:links===(role==='addviewer'?0:2)}});
 await p.screenshot({path:O+'/png/gallery-upload-'+role+'.png',animations:'disabled'});await c.close();
}
return{rows,pageerrors,local_errors,console_errors,blocked,scope:'Synthetic auth helper only; native input uploads and delete dialog clicks, real CSRF/admin ACL/storage/public readbacks'};
}
