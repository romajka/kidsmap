async original=>{
const F={
  "synthetic_only": true,
  "settings_id": 1,
  "paths": {
    "place": "/place/1-uydurma-m10-mekan/",
    "draft": "/place/2-keyfiyyetli-usaq-derneyi/",
    "archived": "/place/3-keyfiyyetli-usaq-derneyi-2/",
    "specialist": "/specialists/fictional-m10-specialist/",
    "event": "/event/1-uydurma-m10-tedbir/",
    "organization": "/organizations/c7e52794-2a0f-4687-86eb-ee89a5e92b43/",
    "activity": "/activities/1/",
    "owner_events": "/account/places/events/1/edit/",
    "owner_specialists": "/account/places/specialists/1/edit/",
    "owner_organizations": "/account/organizations/1/"
  },
  "ids": {
    "place": 1,
    "specialist": 1,
    "event": 1,
    "organization": 1
  },
  "counts": {
    "places": 3,
    "specialists": 1,
    "events": 1,
    "organizations": 1
  }
},base='http://127.0.0.1:33460',O='/mnt/c/kidsmap/docs/qa/module10-full-2026-10-18-pc-r1',rows=[],writes=[],consoleErrors=[],pageerrors=[],http=[],failed=[],blocked=[],browser=original.context().browser();
async function make(role){const c=await browser.newContext({viewport:{width:1440,height:950},serviceWorkers:'block'});await c.route('**/*',r=>{if(new URL(r.request().url()).hostname==='127.0.0.1')return r.continue();blocked.push(new URL(r.request().url()).hostname);return r.abort();});const p=await c.newPage();p.setDefaultTimeout(8000);p.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});p.on('pageerror',e=>pageerrors.push(String(e)));p.on('response',r=>{if(r.status()>=400)http.push({path:new URL(r.url()).pathname,status:r.status()});});p.on('requestfailed',r=>failed.push({local:new URL(r.url()).hostname==='127.0.0.1',path:new URL(r.url()).pathname,error:r.failure()?.errorText}));await p.goto(base+'/qa/m10-login/'+role+'/');return{c,p};}
const a=await make('admin'),g=await make('guest'),owner=await make('owner'),initial=(await(await a.p.request.get(base+'/qa/m10-state/')).json());
const kinds=[{kind:'organizations',list:'/organizations/',direct:F.paths.organization,owner:F.paths.owner_organizations,model:'organization',id:F.ids.organization,off:404,ownerOff:200},{kind:'specialists',list:'/specialists/',direct:F.paths.specialist,owner:F.paths.owner_specialists,model:'specialist',id:F.ids.specialist,off:404,ownerOff:404},{kind:'events',list:'/events/',direct:F.paths.event,owner:F.paths.owner_events,model:'event',id:F.ids.event,off:410,ownerOff:404}];
for(const k of kinds)for(const enabled of [false,true]){
 const adminPath='/admin/catalog/sitevisibilitysettings/1/change/';await a.p.goto(base+adminPath);await a.p.locator('[name='+k.kind+'_section_enabled]').setChecked(enabled);const wait=a.p.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname===adminPath);await a.p.locator('button[name=_continue]').click();const saved=await wait;await a.p.reload();writes.push({kind:k.kind,enabled,nativeSave:saved.status()});const state=(await(await a.p.request.get(base+'/qa/m10-state/')).json());
 for(const lang of ['az','ru','en'])for(const width of [360,390,768,1024,1280,1440]){
  const prefix=lang==='az'?'':'/'+lang;await g.p.setViewportSize({width,height:950});await g.p.goto(base+prefix+'/');const links=await g.p.locator('#km-site-header a[href="'+prefix+k.list+'"]').count(),homeOverflow=await g.p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);const r=await g.p.goto(base+prefix+k.list);const direct=await g.p.request.get(base+prefix+k.direct);const own=await owner.p.request.get(base+prefix+k.owner),admin=await a.p.request.get(base+'/admin/catalog/'+k.model+'/'+k.id+'/change/');const api=await g.p.request.get(base+prefix+'/api/catalog/map/?q=M10'),suggestions=await g.p.request.get(base+prefix+'/api/catalog/suggestions/?q=M10');
  const checks={save302:saved.status()===302,featureReadback:state.features[k.kind]===enabled,independent:Object.entries(state.features).every(([name,value])=>name===k.kind||value===true),navHiddenShown:enabled?links>0:links===0,noHomeOverflow:!homeOverflow,listContract:r.status()===(enabled?200:k.off),directContract:direct.status()===(enabled?200:k.off),ownerContract:own.status()===(enabled?200:k.ownerOff),adminEditingAvailable:admin.status()===200,recordsPreserved:JSON.stringify(state.counts)===JSON.stringify(initial.counts),mapApi200:api.status()===200,suggestions200:suggestions.status()===200};rows.push({id:'feature-toggle',kind:k.kind,enabled,lang,width,checks,statuses:{list:r.status(),direct:direct.status(),owner:own.status(),admin:admin.status(),map:api.status(),suggestions:suggestions.status()},featureState:state.features});
  if(width===390||width===1440)await g.p.screenshot({path:O+'/png/flag-'+k.kind+'-'+enabled+'-'+lang+'-'+width+'.png',fullPage:true,animations:'disabled'});
 }
}
const finalState=(await(await a.p.request.get(base+'/qa/m10-state/')).json());await a.c.close();await g.c.close();await owner.c.close();return{rows,writes,initial,finalState,consoleErrors,pageerrors,http,failed,blocked,expectedErrors:'OFF public events410/specialists-organizations404; captured native DEBUG=true error pages, not production error styling'};
}
