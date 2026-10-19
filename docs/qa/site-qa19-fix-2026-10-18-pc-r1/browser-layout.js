async original=>{
 const base='http://127.0.0.1:33540',O='/mnt/c/kidsmap/docs/qa/site-qa19-fix-2026-10-18-pc-r1',url=base+'/admin/catalog/catalogcontentsettings/1/change/',initial=__INITIAL__;
 const c=await original.context().browser().newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const p=await c.newPage(),rows=[],pageerrors=[];p.on('pageerror',e=>pageerrors.push(String(e)));
 await p.goto(base+'/qa/site19/login/super/');await p.goto(url,{waitUntil:'domcontentloaded'});
 for(const key of ['districts_json','metro_stations_json','seo_pages_json'])await p.locator('[name='+key+']').fill(JSON.stringify(initial[key]));
 const [saved]=await Promise.all([p.waitForResponse(r=>r.url()===url&&r.request().method()==='POST'),p.locator('button[name=_continue]').click()]);await p.waitForLoadState('domcontentloaded');
 const restored=await(await p.request.get(base+'/qa/site19/state/')).json();const restore_checks={native_post302:saved.status()===302,original_synthetic_JSON_restored:['districts_json','metro_stations_json','seo_pages_json'].every(k=>JSON.stringify(restored[k])===JSON.stringify(initial[k]))};
 for(const lang of ['az','ru','en']){
  const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
  for(const width of [1280,1440]){
   await p.setViewportSize({width,height:1000});await p.goto(url,{waitUntil:'domcontentloaded'});await p.locator('#id_districts_json').waitFor();
   const g=await p.evaluate(()=>{
    const rect=e=>{const r=e.getBoundingClientRect();return{left:r.left,right:r.right,top:r.top+scrollY,bottom:r.bottom+scrollY,width:r.width,height:r.height};};
    const main=rect(document.querySelector('.km-place-form-main')),aside=rect(document.querySelector('.km-place-form-sidebar')),card=rect(document.querySelector('.km-place-section')),field=rect(document.querySelector('#id_districts_json'));
    const chain=[];let e=document.querySelector('.km-place-form-layout');for(let i=0;e&&i<6;i++,e=e.parentElement){const s=getComputedStyle(e);chain.push({tag:e.tagName,id:e.id,class:e.className,width:rect(e).width,display:s.display,grid_columns:s.gridTemplateColumns,position:s.position});}
    return{viewport:innerWidth,document:document.documentElement.scrollWidth,main,aside,card,field,main_aside_overlap:Math.min(main.right,aside.right)>Math.max(main.left,aside.left)&&Math.min(main.bottom,aside.bottom)>Math.max(main.top,aside.top),card_aside_overlap:Math.min(card.right,aside.right)>Math.max(card.left,aside.left)&&Math.min(card.bottom,aside.bottom)>Math.max(card.top,aside.top),chain};
   });
   const id='desktop-layout-'+lang+'-'+width;await p.screenshot({path:O+'/png/'+id+'.png',fullPage:true,animations:'disabled'});
   rows.push({id,role:'super',lang,width,geometry:g,checks:{main_not_covered_by_actions:!g.main_aside_overlap},classification:'Separate unchanged shared-shell layout diagnostic; negative checks remain failures, not accepted SITE19 layout closure.'});
  }
 }
 await c.close();return{rows,pageerrors,restore_checks,scope:'Native restore of original short synthetic JSON then actual desktop GET/rectangles/PNG; no app/CSS changes, no long-brand fixture.'};
}
