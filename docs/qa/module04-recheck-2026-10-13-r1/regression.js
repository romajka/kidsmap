async original => {
const B='__BASE__',F=__FIXTURE__,browser=original.context().browser(),rows=[];
const c=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.on('dialog',d=>d.accept());
function check(id,ok,data){rows.push({id,status:ok?'PASS':'FAIL',data});}
try {
 await p.goto(B+'/admin/login/?next=/ru/admin/catalog/event/'+F.event+'/change/');await p.locator('[name=username]').fill(F.users.admin);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('[type=submit]').click();await p.waitForURL(u=>u.pathname.includes('/change/'));
 await p.locator('[data-main-photo-clear]').click();
 check('remove-checkbox',await p.locator('[name=photo-clear]').isChecked());check('remove-preview',await p.locator('[data-main-photo-preview]').isHidden());
 check('remove-readiness',await p.locator('[data-progress-missing-list] a[href="#id_photo"]').count() > 0);
 check('remove-disables-publish',await p.locator('#km-publish-btn').isDisabled());
 await p.screenshot({path:'__HERE__/screenshots/regression-click.png',fullPage:true});
 await p.locator('[name=_continue]').last().click();await p.waitForLoadState();
 check('remove-roundtrip',!(await p.locator('[data-main-photo-preview]').getAttribute('data-main-photo-initial-url')));
 await p.locator('#id_photo').setInputFiles('__ASSETS__/photo.png');await p.locator('[name=_continue]').last().click();await p.waitForLoadState();
 check('upload-roundtrip',!!(await p.locator('[data-main-photo-preview]').getAttribute('data-main-photo-initial-url')));
 for(const lang of ['az','en']){
  await p.goto(B+(lang==='az'?'':'/'+lang)+'/account/places/events/'+F.event+'/edit/');
  check('edit-caption-'+lang,!(await p.locator('body').innerText()).includes('Редактирование мероприятия'));
 }
 }catch(e){return{rows,error:String(e),url:p.url()}}finally{await c.close()}
return {rows,failed:rows.filter(r=>r.status==='FAIL').length};
}