async original => {
 const B='__BASE__',F=__FIXTURE__,browser=original.context().browser(),rows=[],errors=[],network=[];
 const c=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
 const p=await c.newPage();p.on('dialog',d=>d.accept());p.setDefaultTimeout(10000);p.on('pageerror',e=>errors.push(String(e)));p.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)network.push({url:r.url().split('?')[0],status:r.status()})});
 try {
 await p.goto(B+'/admin/login/');await p.locator('[name=username]').fill(F.users.admin);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/login/'));
 await p.goto(B+'/ru/admin/catalog/event/'+F.event+'/change/');
 rows.push({id:'EVENT-QA-01',labels:await p.locator('label[for=id_owner],label[for=id_related_place]').allTextContents()});
 await p.screenshot({path:'__HERE__/screenshots/admin-before-ru-1440.png',fullPage:true});
 const before=await p.locator('[name=photo-clear]').isChecked();
 await p.locator('[data-main-photo-clear]').click();
 rows.push({id:'EVENT-QA-02',before,afterClick:await p.locator('[name=photo-clear]').isChecked(),previewHidden:await p.locator('[data-main-photo-preview]').isHidden(),missing:await p.locator('[data-progress-missing-list]').textContent()});
 await p.screenshot({path:'__HERE__/screenshots/admin-clear-click-ru-1440.png',fullPage:true});
 await p.locator('[name=_continue]').last().click();await p.waitForLoadState();
 rows.push({id:'EVENT-QA-02-roundtrip',photoAfterSave:await p.locator('[data-main-photo-preview]').getAttribute('data-main-photo-initial-url')});
 await p.screenshot({path:'__HERE__/screenshots/admin-clear-save-ru-1440.png',fullPage:true});
 // Independent owner browser context, no administrative session reuse.
 const oc=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});await oc.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const op=await oc.newPage();op.setDefaultTimeout(10000);
 await op.goto(B+'/ru/auth/login/');await op.locator('[name=username]').fill('owner@example.invalid');await op.locator('[name=password]').fill('__LOCAL_PASSWORD__');await op.getByRole('button',{name:'Войти',exact:true}).click();await op.waitForURL(u=>!u.pathname.includes('/auth/login/'));
 for(const lang of ['az','en']){
 await op.goto(B+(lang==='az'?'':'/'+lang)+'/account/places/events/'+F.event+'/edit/');
 rows.push({id:'EVENT-QA-03',lang,russianLabels:await op.locator('.org-status,[aria-label="Шаги формы мероприятия"],[aria-label="Вперёд"],label').allTextContents(),help:await op.locator('form > p.helptext').allTextContents()});
 await op.screenshot({path:'__HERE__/screenshots/owner-'+lang+'-390.png',fullPage:true});
 }
 await oc.close();
 }catch(e){return {rows,error:String(e),url:p.url(),errors,network}}
 finally{await c.close()}
 return {rows,errors,network};
}