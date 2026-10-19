async original=>{
const base='http://127.0.0.1:33630',O='/mnt/c/kidsmap/docs/qa/site-qa20-fix-2026-10-18-pc-r1',rows=[],pageerrors=[],local_errors=[],console_errors=[],blocked=[];
const models=['sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','catalogcontentsettings','sitegalleryimage'];
const c=await original.context().browser().newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});
await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));
const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));p.on('console',m=>{if(m.type()==='error')console_errors.push(m.text())});p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)local_errors.push({path:new URL(r.url()).pathname,status:r.status()})});
await p.goto(base+'/qa/site08/login/all_viewer/');
const state=async()=>({data:await(await p.request.get(base+'/qa/site08/all-state/')).json(),media:await(await p.request.get(base+'/qa/site08/form-state/')).json()});
const before=await state();
for(const role of ['all_viewer','all_editor','gallery_adder','gallery_deleter']){
 await p.goto(base+'/qa/site08/login/'+role+'/');
 for(const lang of ['az','ru','en']){
  const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;
  await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
  for(const model of role==='all_viewer'?models:role==='all_editor'?['catalogcontentsettings']:['sitegalleryimage'])for(const width of [390,1440]){
   await p.setViewportSize({width,height:1000});const add=role==='gallery_adder',path='/admin/catalog/'+model+'/'+(add?'add/':'1/change/');
   const response=await p.goto(base+path,{waitUntil:'load'});await p.waitForFunction(()=>!document.body.classList.contains('hold-transition'));await p.waitForTimeout(150);
   const geometry=await p.evaluate(()=>{const visible=e=>e.getClientRects().length>0;return{buttons:[...document.querySelectorAll('button[name=_save],button[name=_continue]')].map(e=>({name:e.name,visible:visible(e),disabled:e.disabled})),action_cards:document.querySelectorAll('.km-place-sidebar-card--actions').length,delete_links:document.querySelectorAll('.deletelink').length,editable_marker:document.querySelector('#content-main').classList.contains('km-settings-form-page--editable'),document_width:document.documentElement.scrollWidth,viewport:innerWidth}});
   const readonly=['all_viewer','gallery_deleter'].includes(role),id=role+'-'+model+'-'+lang+'-'+width;
   const checks={get200:response.status()===200,language:await p.locator('html').getAttribute('lang')===lang,no_overflow:geometry.document_width<=width,
     permission_actions:readonly?geometry.buttons.length===0:geometry.buttons.length===2,
     editable_marker:geometry.editable_marker===!readonly,
     delete_preserved:geometry.delete_links===(role==='gallery_deleter'?1:0)};
   if(role==='gallery_adder')checks.mobile_add_actions=geometry.buttons.filter(b=>b.visible&&!b.disabled).length===2;
   if(role==='all_viewer')checks.no_empty_action_card=geometry.action_cards===0;
   if(lang==='ru')await p.screenshot({path:O+'/png/'+id+'.png',fullPage:true,animations:'disabled'});
   rows.push({id,role,model,lang,width,geometry,checks});
  }
 }
}
await p.goto(base+'/qa/site08/login/all_viewer/');await p.setViewportSize({width:1440,height:1000});
for(const lang of ['az','ru','en']){
 const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
 await p.goto(base+'/admin/catalog/catalogcontentsettings/1/change/');
 const responsePromise=p.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/admin/catalog/catalogcontentsettings/1/change/');
 await p.locator('button[name=_continue]').click();const response=await responsePromise;
 await p.screenshot({path:O+'/png/viewer-native403-'+lang+'.png',fullPage:true,animations:'disabled'});
 rows.push({id:'native-viewer-'+lang,role:'all_viewer',lang,width:1440,checks:{post403:response.status()===403,no_write:JSON.stringify(before)===JSON.stringify(await state())},native_post:true});
}
const after=await state();await c.close();return{rows,pageerrors,local_errors,console_errors,blocked,no_fixture_write:JSON.stringify(before)===JSON.stringify(after),before,after,scope:'Unmodified actual source baseline; expected SITE20 action failures; no candidate injection or applied GREEN'};
}
