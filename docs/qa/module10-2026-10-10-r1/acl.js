async original=>{
 __QA10_COMMON__
 const admin=await context('admin'),bytes=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==','base64');
 for(const role of ['guest','owner','outsider','staff']){
  const{c,p}=await context(role);await visit(p,'/ru/auth/login/');const r=await p.goto(B+'/admin/catalog/sitegalleryimage/');const ss=await shot(p,'acl-media-page-'+role);add('media-page-permission-'+role,role==='staff'?r.status()===403:p.url().includes('/admin/login/'),{http:r.status()},role,'ru',1440,p.url(),ss);
  const token=(await c.cookies()).find(x=>x.name==='module10_r1_csrf')?.value;const before=(await state(p)).settings.logo;
  const noCsrf=await p.request.post(B+'/admin/catalog/sitegalleryimage/ajax-upload/',{multipart:{field:'logo',image:{name:'qa10-no-csrf.png',mimeType:'image/png',buffer:bytes}},maxRedirects:0});add('media-no-csrf-'+role,noCsrf.status()===403&&(await state(p)).settings.logo===before,{http:noCsrf.status()},role,'ru',1440,B+'/admin/catalog/sitegalleryimage/ajax-upload/',ss);
  const post=await p.request.post(B+'/admin/catalog/sitegalleryimage/ajax-upload/',{headers:{'X-CSRFToken':token||''},multipart:{field:'logo',image:{name:'qa10-'+role+'.png',mimeType:'image/png',buffer:bytes}},maxRedirects:0});const after=(await state(p)).settings.logo;
  add('media-upload-without-permission-'+role,post.status()!==200&&before===after,{http:post.status(),before,after,method:'negative direct HTTP via native browser context; no ORM mutation'},role,'ru',1440,B+'/admin/catalog/sitegalleryimage/ajax-upload/',ss);
  if(after!==before){const pub=await c.newPage();await visit(pub,'/ru/');const ps=await shot(pub,'acl-public-logo-'+role);add('unauthorized-public-effect-'+role,false,{src:await pub.locator('.km-brand-logo').first().getAttribute('src'),http:post.status()},role,'ru',1440,pub.url(),ps);await pub.close();}
  const del=await p.request.post(B+'/admin/catalog/sitegalleryimage/ajax-delete-main-image/',{headers:{'X-CSRFToken':token||''},form:{field:'logo'},maxRedirects:0});const deleted=(await state(p)).settings.logo;
  add('media-delete-without-permission-'+role,del.status()!==200&&deleted===after,{http:del.status(),before:after,after:deleted,method:'negative direct HTTP via native browser context'},role,'ru',1440,B+'/admin/catalog/sitegalleryimage/ajax-delete-main-image/',ss);
  if(deleted!==before){await visit(admin.p,'/admin/catalog/sitegalleryimage/');const wait=admin.p.waitForResponse(r=>r.url().includes('ajax-upload/')&&r.request().method()==='POST');await admin.p.locator('.km-media-row[data-field=logo] input[type=file]').setInputFiles(ASSET+'/logo.png');await wait;await admin.p.reload();add('admin-native-restore-after-ACL-probe',(await state(admin.p)).settings.logo.includes('logo'),{},'admin','ru',1440,admin.p.url(),await shot(admin.p,'acl-native-restored'));changes.push({label:'ACL probe '+role+' / native admin restore',before,after:deleted,final:(await state(admin.p)).settings.logo});}
  await c.close();
 }
 await admin.c.close();return{rows,changes};
}
