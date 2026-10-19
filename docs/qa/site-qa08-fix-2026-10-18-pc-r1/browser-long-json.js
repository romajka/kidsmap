async original=>{
 const base='http://127.0.0.1:33580',O='/mnt/c/kidsmap/docs/qa/site-qa08-fix-2026-10-18-pc-r1',url=base+'/admin/catalog/catalogcontentsettings/1/change/',initial=__INITIAL__,fields=['districts_json','metro_stations_json','seo_pages_json'],rows=[],pageerrors=[],local_errors=[],blocked=[];
 const browser=original.context().browser(),contexts={},pages={},stable=x=>Array.isArray(x)?x.map(stable):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,stable(x[k])])):x,eq=(a,b)=>JSON.stringify(stable(a))===JSON.stringify(stable(b)),pick=s=>Object.fromEntries(fields.map(k=>[k,s[k]]));
 for(const role of ['editor','viewer']){
  const c=contexts[role]=await browser.newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));
  const p=pages[role]=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)local_errors.push({path:new URL(r.url()).pathname,status:r.status()});});await p.goto(base+'/qa/site08/login/'+role+'/',{waitUntil:'domcontentloaded'});
 }
 const editor=pages.editor,long='L'.repeat(1024),value={districts_json:[...initial.districts_json,{key:'qa_long',districts:[long]}],metro_stations_json:[...initial.metro_stations_json,long],seo_pages_json:structuredClone(initial.seo_pages_json)};
 for(const lang of ['az','ru','en'])value.seo_pages_json[lang].qa={title:long,nested:{message:'QA «текст» mətn',values:[1,true,null]}};
 const state=async p=>await(await p.request.get(base+'/qa/site08/state/')).json();
 const save=async(v,tag)=>{
  await editor.setViewportSize({width:1440,height:1000});await editor.goto(url,{waitUntil:'domcontentloaded'});const before=await state(editor);for(const key of fields)await editor.locator('[name='+key+']').fill(JSON.stringify(v[key]));
  const [response]=await Promise.all([editor.waitForResponse(r=>r.url()===url&&r.request().method()==='POST'),editor.locator('button[name=_continue]').click()]);await editor.waitForLoadState('domcontentloaded');const after=await state(editor);
  rows.push({id:tag,role:'editor',lang:await editor.locator('html').getAttribute('lang'),width:1440,checks:{native_post302:response.status()===302,exact_json:eq(pick(after),v),one_admin_log:after.admin_log_count===before.admin_log_count+1}});
 };
 await save(value,'save-long');
 for(const role of ['editor','viewer'])for(const lang of ['az','ru','en']){
  const p=pages[role],c=contexts[role],csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
  for(const width of [390,1280,1440]){
   await p.setViewportSize({width,height:1000});const before=await state(p);const response=await p.goto(url,{waitUntil:'domcontentloaded'});await p.locator('#catalogcontentsettings_form').waitFor();
   const geometry=await p.evaluate(()=>{
    const rect=e=>e.getBoundingClientRect(),visible=e=>e.getClientRects().length,main=rect(document.querySelector('.km-place-form-main')),asideElement=document.querySelector('.km-place-form-sidebar'),aside=rect(asideElement),cards=[...document.querySelectorAll('.km-place-form-main > .km-place-section')].filter(visible).map(rect),fields=[...document.querySelectorAll('textarea,.km-place-section .readonly')].filter(visible).map(rect),overlap=(a,b)=>Math.min(a.right,b.right)>Math.max(a.left,b.left)+.5&&Math.min(a.bottom,b.bottom)>Math.max(a.top,b.top)+.5;
    return{viewport:innerWidth,document:document.documentElement.scrollWidth,field_widths:fields.map(f=>f.width),checks:{cards_fit_main:cards.every(c=>c.left>=main.left-.75&&c.right<=main.right+.75),no_action_overlap:!visible(asideElement)||cards.every(c=>!overlap(c,aside)),fields_fit_main:fields.every(f=>f.left>=main.left-.75&&f.right<=main.right+.75),no_horizontal_overflow:document.documentElement.scrollWidth<=innerWidth}};
   });
   const after=await state(p),checks={...geometry.checks,get200:response.status()===200,correct_language:await p.locator('html').getAttribute('lang')===lang,no_write:eq(before,after),correct_controls:await p.locator('textarea').count()===(role==='viewer'?0:3)};
   if(role==='viewer')checks.full_long_value_present=(await p.locator('#catalogcontentsettings_form').innerText()).includes(long);else for(const key of fields)checks['full_'+key]=eq(JSON.parse(await p.locator('[name='+key+']').inputValue()),value[key]);
   const id=role+'-'+lang+'-'+width;await p.screenshot({path:O+'/png/long-'+id+'.png',fullPage:true,animations:'disabled'});rows.push({id,role,lang,width,geometry,checks});
  }
 }
 await save(pick(initial),'restore-short');for(const c of Object.values(contexts))await c.close();return{rows,pageerrors,local_errors,blocked,long_value_length:long.length,scope:'Native long JSON save, actual-source editor/readonly render18cells, native original-short-fixture restoration; no ORM fixture rewrite or injected style/class.'};
}
