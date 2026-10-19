async original=>{
const base='http://127.0.0.1:33630',rows=[],pageerrors=[],c=await original.context().browser().newContext({serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));
const models=['sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','catalogcontentsettings','sitegalleryimage'];
await p.goto(base+'/qa/site08/login/all_viewer/');const state=async()=>({data:await(await p.request.get(base+'/qa/site08/all-state/')).json(),media:await(await p.request.get(base+'/qa/site08/form-state/')).json()}),before=await state();
for(const role of ['all_viewer','denied','gallery_adder']){
 await p.goto(base+'/qa/site08/login/'+role+'/');const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;
 for(const model of role==='gallery_adder'?['sitegalleryimage']:models){
  const path='/admin/catalog/'+model+'/1/change/';if(role!=='all_viewer'){const r=await p.request.get(base+path,{maxRedirects:0});rows.push({id:role+'-'+model+'-GET',checks:{forbidden:r.status()===403,no_write:JSON.stringify(before)===JSON.stringify(await state())}});}
  for(const action of ['_save','_continue']){const r=await p.request.post(base+path,{headers:{'X-CSRFToken':csrf},form:{[action]:'1',brand_name:'must-not-persist',title_ru:'must-not-persist'},maxRedirects:0});rows.push({id:role+'-'+model+'-'+action,checks:{forbidden:r.status()===403,no_write:JSON.stringify(before)===JSON.stringify(await state())}});}
 }
}
await p.goto(base+'/qa/site08/login/all_editor/');const noCSRF=await p.request.post(base+'/admin/catalog/sitefootersettings/1/change/',{form:{_save:'1'},maxRedirects:0});rows.push({id:'editor-missingCSRF',checks:{forbidden:noCSRF.status()===403,no_write:JSON.stringify(before)===JSON.stringify(await state())}});
const after=await state();await c.close();return{rows,pageerrors,no_fixture_write:JSON.stringify(before)===JSON.stringify(after),scope:'Explicit negative direct requests, all viewer/denied existing consumers and add-only edit denial; no successful application POST'};
}
