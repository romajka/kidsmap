async original=>{
const base='http://127.0.0.1:33630',O='/mnt/c/kidsmap/docs/qa/site-qa20-fix-2026-10-18-pc-r1',rows=[],pageerrors=[],local_errors=[],blocked=[],console_errors=[];
const models=['sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','catalogcontentsettings','sitegalleryimage'];
const c=await original.context().browser().newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));p.on('console',m=>{if(m.type()==='error')console_errors.push(m.text())});p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)local_errors.push({path:new URL(r.url()).pathname,status:r.status()})});
await p.goto(base+'/qa/site08/login/all_viewer/');const state=async()=>({data:await(await p.request.get(base+'/qa/site08/all-state/')).json(),media:await(await p.request.get(base+'/qa/site08/form-state/')).json()}),before=await state();
for(const role of ['all_viewer','all_editor','gallery_adder','gallery_deleter']){
 await p.goto(base+'/qa/site08/login/'+role+'/');
 for(const lang of ['az','ru','en']){
  const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
  for(const model of ['all_viewer','all_editor'].includes(role)?models:['sitegalleryimage'])for(const width of [360,390,768,1024,1280,1440]){
   await p.setViewportSize({width,height:1000});const add=role==='gallery_adder',response=await p.goto(base+'/admin/catalog/'+model+'/'+(add?'add/':'1/change/'),{waitUntil:'load'});await p.waitForFunction(()=>!document.body.classList.contains('hold-transition'));await p.waitForTimeout(150);
   const geometry=await p.evaluate(()=>{const visible=e=>e.getClientRects().length>0,rect=e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,width:r.width}},root=document.querySelector('#content-main');return{buttons:[...root.querySelectorAll('button[name=_save],button[name=_continue]')].map(e=>({name:e.name,visible:visible(e),disabled:e.disabled,label:e.innerText.trim(),...rect(e)})),action_cards:root.querySelectorAll('.km-place-sidebar-card--actions').length,delete_links:root.querySelectorAll('.deletelink').length,delete_visible:[...root.querySelectorAll('.deletelink')].some(visible),editable_marker:root.classList.contains('km-settings-form-page--editable'),document_width:document.documentElement.scrollWidth,root:rect(root),CSS:[...document.styleSheets].some(s=>s.href?.includes('kidsmap_settings_forms.css'))}});
   const writable=['all_editor','gallery_adder'].includes(role),id=[role,model,lang,width].join('-');let keyboard=true;
   if([360,1440].includes(width)){
    if(writable){await p.locator('button[name=_save]').focus();keyboard=await p.locator('button[name=_save]').evaluate(e=>document.activeElement===e);}
    else {await p.keyboard.press('Tab');keyboard=await p.evaluate(()=>!['_save','_continue'].includes(document.activeElement?.getAttribute('name')));}
   }
   const checks={get200:response.status()===200,language:await p.locator('html').getAttribute('lang')===lang,no_overflow:geometry.document_width<=width,root_bounds:geometry.root.left>=-.75&&geometry.root.right<=width+.75,permission_actions:geometry.buttons.length===(writable?2:0),editable_marker:geometry.editable_marker===writable,action_card:geometry.action_cards===((writable||role==='gallery_deleter')?1:0),delete_preserved:geometry.delete_links===(role==='gallery_deleter'?1:0),allowed_saves_visible:writable?geometry.buttons.every(b=>b.visible&&!b.disabled&&b.label.length>0&&b.left>=-.75&&b.right<=width+.75):true,keyboard,scopedCSS:geometry.CSS};
   if(lang==='ru'&&[360,1440].includes(width))await p.screenshot({path:O+'/png/layout-'+id+'.png',fullPage:true,animations:'disabled'});
   rows.push({id,role,model,lang,width,geometry,checks});
  }
 }
}
const after=await state(),css=await p.request.get(base+'/static/admin/css/pages/kidsmap_settings_forms.css');await c.close();return{rows,pageerrors,local_errors,blocked,console_errors,CSS200:css.status()===200,no_fixture_write:JSON.stringify(before)===JSON.stringify(after),before,after,scope:'Actual applied source; all9consumer view/change permissions and add-only/delete-only states; no candidate/style/transport injection. Existing delete-only mobile visibility recorded without redesign claim.'};
}
