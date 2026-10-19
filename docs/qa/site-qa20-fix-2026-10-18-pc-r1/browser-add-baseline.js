async original=>{
const base='http://127.0.0.1:33630',O='/mnt/c/kidsmap/docs/qa/site-qa20-fix-2026-10-18-pc-r1',rows=[],pageerrors=[],phase='red',c=await original.context().browser().newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));await p.goto(base+'/qa/site08/login/gallery_adder/');
const state=async()=>await(await p.request.get(base+'/qa/site08/form-state/')).json(),initial=await state();
for(const button of ['_save','_continue']){
 await p.goto(base+'/admin/catalog/sitegalleryimage/add/',{waitUntil:'load'});await p.locator('#id_title_ru').fill('SITE20 '+phase+' add '+button);await p.locator('#id_image').setInputFiles('/mnt/c/kidsmap/.tmp/site20-pc-fix-r1/assets/valid_'+('long_name_'.repeat(8))+'.png');
 const before=await state(),responses=[],listener=r=>{if(r.url().startsWith(base)&&r.request().isNavigationRequest())responses.push({path:new URL(r.url()).pathname,status:r.status(),method:r.request().method()})};p.on('response',listener);await Promise.all([p.waitForNavigation({waitUntil:'load'}),p.locator('button[name='+button+']').click()]);p.off('response',listener);
 const after=await state(),added=after.gallery.filter(x=>!before.gallery.some(y=>y.pk===x.pk)),last=responses.at(-1);
 await p.screenshot({path:O+'/png/add-'+phase+'-'+button+'.png',fullPage:true,animations:'disabled'});
 rows.push({id:phase+'-add-'+button,button,redirect_chain:responses,added_ids:added.map(x=>x.pk),checks:{native_POST302:responses[0]?.method==='POST'&&responses[0]?.status===302,one_row:added.length===1,exact_caption:added[0]?.title_ru==='SITE20 '+phase+' add '+button,one_log:after.admin_log_count===before.admin_log_count+1,landing200:last?.status===200},known_existing_continue403:button==='_continue'&&last?.status===403});
}
const final=await state();await c.close();return{rows,pageerrors,initial,final,successful_native_posts:2,scope:'Fresh prepatch native add-only desktop baseline. Rows/media are own synthetic additions retained. Continue permission redirect observed independently of SITE20 template patch.'};
}
