async original => {
 const base='http://127.0.0.1:33580',O='/mnt/c/kidsmap/docs/qa/site-qa08-fix-2026-10-18-pc-r1',url=base+'/admin/catalog/catalogcontentsettings/1/change/';
 const expectedLabels={"az": "Kataloqda yenilər", "ru": "Контент каталога", "en": "New in catalog"};
 const fields=['districts_json','metro_stations_json','seo_pages_json'],rows=[],pageerrors=[],local_errors=[],console_errors=[],blocked=[];const browser=original.context().browser();
 const state=async p=>await(await p.request.get(base+'/qa/site08/state/')).json();
 const pick=s=>Object.fromEntries(fields.map(k=>[k,s[k]]));const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 for(const role of ['editor']){
  const c=await browser.newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});
  await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():(blocked.push(new URL(r.request().url()).hostname),r.abort()));
  const p=await c.newPage();p.on('pageerror',e=>pageerrors.push(String(e)));p.on('console',m=>{if(m.type()==='error')console_errors.push(m.text());});p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)local_errors.push({path:new URL(r.url()).pathname,status:r.status()});});
  await p.goto(base+'/qa/site08/login/'+role+'/',{waitUntil:'domcontentloaded'});
  for(const lang of ['az','ru','en'])for(const width of [360,390]){await p.setViewportSize({width,height:1000});
   const csrf=(await c.cookies()).find(x=>x.name==='csrftoken').value;
   await p.request.post(base+'/i18n/setlang/',{headers:{'X-CSRFToken':csrf},form:{language:lang,next:'/admin/'},maxRedirects:0});
   const info=await(await p.request.get(base+'/qa/site08/info/')).json();
   await p.goto(url,{waitUntil:'domcontentloaded'});await p.locator('#id_districts_json').waitFor();
   let serial=0;
   const values=(s,tag)=>{
    const v=structuredClone(pick(s));v.districts_json.push({key:'qa_'+role+'_'+lang+'_'+(++serial),districts:['QА «mətn» '+tag]});
    v.metro_stations_json.push('QA '+role+' '+lang+' '+tag+' Əə ё " /');
    v.seo_pages_json[lang].qa.title='QA '+tag+' «текст» mətn " / '+serial;
    return v;
   };
   const fill=async v=>{for(const key of fields)await p.locator('[name='+key+']').fill(JSON.stringify(v[key],null,2));};
   const submit=async name=>{
    const [response]=await Promise.all([p.waitForResponse(r=>r.url()===url&&r.request().method()==='POST'),p.locator('button[name='+name+']').click()]);
    await p.waitForLoadState('domcontentloaded');return response.status();
   };
   const valid=async(tag,button)=>{
    const before=await state(p),v=values(before,tag);await fill(v);const status=await submit(button);const after=await state(p);
    const checks={admin_language:await p.locator('html').getAttribute('lang')===lang,post302:status===302,exact_json_roundtrip:eq(pick(after),v),one_admin_log:after.admin_log_count===before.admin_log_count+1,localized_log:after.last_log_repr===expectedLabels[lang]};
    if(button==='_continue'){
     await p.locator('#id_districts_json').waitFor();await p.reload({waitUntil:'domcontentloaded'});
     for(const key of fields)checks['reload_'+key]=eq(JSON.parse(await p.locator('[name='+key+']').inputValue()),v[key]);
    }else checks.exits_editor=new URL(p.url()).pathname!=='/admin/catalog/catalogcontentsettings/1/change/';
    const id=role+'-'+lang+'-'+width+'-'+tag;await p.screenshot({path:O+'/png/json-flow-'+id+'.png',animations:'disabled'});rows.push({id,role,lang,width,action:button,checks});
   };
   await valid('valid-initial','_continue');
   for(const field of fields){
    const before=await state(p),draft=values(before,'draft-'+field);await fill(draft);const malformed='{"broken":';await p.locator('[name='+field+']').fill(malformed);
    const status=await submit('_continue');await p.locator('.errorlist').first().waitFor();const after=await state(p);
    const checks={post200:status===200,no_db_or_log_write:eq(before,after),malformed_draft_retained:await p.locator('[name='+field+']').inputValue()===malformed,visible_error:await p.locator('.errorlist').first().isVisible(),visible_summary:await p.locator('[role=alert]').first().isVisible()};
    for(const key of fields.filter(k=>k!==field))checks['other_draft_'+key]=eq(JSON.parse(await p.locator('[name='+key+']').inputValue()),draft[key]);
    const id=role+'-'+lang+'-invalid-'+field;await p.screenshot({path:O+'/png/json-flow-'+id+'.png',animations:'disabled'});
    rows.push({id,role,lang,width,field,active_element:await p.evaluate(()=>({tag:document.activeElement.tagName,role:document.activeElement.getAttribute('role')})),checks});
    await valid('retry-'+field,'_continue');
   }
   await valid('save-exit','_save');
  }
  await c.close();
 }
 return{rows,pageerrors,local_errors,console_errors,blocked,scope:'Actual native mobile textarea edits/button submits/reload/readback; every malformed field tested then native valid retry, both save actions, two authorized actors and3languages. No API submission in these rows.'};
}
