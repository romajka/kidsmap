async original=>{
const base='http://127.0.0.1:33630',rows=[],pageerrors=[],c=await original.context().browser().newContext({serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));let adminPOSTs=0;p.on('request',r=>{if(r.method()==='POST'&&new URL(r.url()).pathname.startsWith('/admin/'))adminPOSTs++;});
for(const role of ['all_viewer','all_editor','gallery_adder']){
 await p.goto(base+'/qa/site08/login/'+role+'/');
 for(const lang of ['az','ru','en']){
  const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
  for(const width of [360,1440]){
   await p.setViewportSize({width,height:1000});await p.goto(base+'/admin/catalog/'+(role==='gallery_adder'?'sitegalleryimage/add/':'catalogcontentsettings/1/change/'),{waitUntil:'load'});
   const targets=await p.locator('a[href],button,input,select,textarea,[tabindex]').evaluateAll(es=>es.filter(e=>e.tabIndex>=0&&!e.disabled&&e.getClientRects().length).length);
   await p.locator('h1').last().click();const names=[];
   for(let i=0;i<targets+2;i++){await p.keyboard.press('Tab');const a=await p.evaluate(()=>({in_form:!!document.activeElement?.closest('#content-main form'),name:document.activeElement?.getAttribute('name')}));if(a.in_form&&a.name)names.push(a.name);if(names.includes('_continue')&&names.includes('_save'))break;}
   const writable=role!=='all_viewer';rows.push({id:[role,lang,width].join('-'),role,lang,width,tabbed_action_names:names.filter(n=>n==='_save'||n==='_continue'),checks:{save_tab_reachable:writable?names.includes('_save'):!names.includes('_save'),continue_tab_reachable:writable?names.includes('_continue'):!names.includes('_continue'),no_positive_POST:adminPOSTs===0,language:await p.locator('html').getAttribute('lang')===lang}});
  }
 }
}
await c.close();return{rows,pageerrors,scope:'Actual native Tab navigation to permitted Save actions and no unavailable view-only action targets. Enter persistence is exercised separately in browser-saves/add.'};
}
