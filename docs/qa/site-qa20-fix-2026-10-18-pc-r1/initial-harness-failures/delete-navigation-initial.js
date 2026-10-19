async original=>{
const base='http://127.0.0.1:33630',O='/mnt/c/kidsmap/docs/qa/site-qa20-fix-2026-10-18-pc-r1',rows=[],pageerrors=[],c=await original.context().browser().newContext({serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));await p.goto(base+'/qa/site08/login/gallery_deleter/');
const state=async()=>await(await p.request.get(base+'/qa/site08/form-state/')).json(),before=await state();
for(const lang of ['az','ru','en']){
 const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
 for(const width of [360,1440]){
  await p.setViewportSize({width,height:1000});await p.goto(base+'/admin/catalog/sitegalleryimage/1/change/',{waitUntil:'load'});const link=p.locator('.deletelink'),visible=await link.isVisible();let keyboard=true,response;
  if(visible){await link.focus();keyboard=await link.evaluate(e=>document.activeElement===e);const next=p.waitForNavigation({waitUntil:'load'});await p.keyboard.press('Enter');response=await next;}
  else response=await p.goto(base+'/admin/catalog/sitegalleryimage/1/delete/',{waitUntil:'load'});
  if(lang==='ru')await p.screenshot({path:O+'/png/delete-confirm-'+width+'.png',animations:'disabled'});
  rows.push({id:lang+'-'+width,lang,width,existing_mobile_delete_hidden:!visible,checks:{delete_confirmation200:response.status()===200,correct_route:new URL(p.url()).pathname==='/admin/catalog/sitegalleryimage/1/delete/',language:await p.locator('html').getAttribute('lang')===lang,keyboard_if_visible:keyboard,no_write:JSON.stringify(before)===JSON.stringify(await state())}});
 }
}
const after=await state();await c.close();return{rows,pageerrors,no_fixture_write:JSON.stringify(before)===JSON.stringify(after),scope:'Existing permitted delete confirmation only; no deletion POST. Desktop keyboard link exercised, pre-existing hidden mobile link visibility explicitly recorded.'};
}
