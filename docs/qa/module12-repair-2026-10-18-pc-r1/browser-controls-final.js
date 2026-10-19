async page=>{
 const B='http://127.0.0.1:33780',rows=[],errors=[],pageerrors=[];
 await page.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());page.on('pageerror',e=>pageerrors.push(String(e)));
 const state=async()=>await(await page.request.get(B+'/qa/m12/state/')).json();
 try{
  const initial=await state(),id=initial.ids.place;
  for(const role of ['admin','viewer','denied']){
   await page.goto(B+'/qa/m12/login/'+role+'/');
   for(const lang of ['az','ru','en'])for(const width of [390,1440]){
    await page.context().addCookies([{name:'django_language',value:lang,domain:'127.0.0.1',path:'/'}]);await page.setViewportSize({width,height:900});const r=await page.goto(B+'/admin/catalog/siteanalytics/?period=90');const allowed=role!=='denied';
    rows.push({id:'admin-acl-'+role+'-'+lang+'-'+width,role,lang,width,checks:{http:r.status()===(allowed?200:403),report_visibility:(await page.locator('[data-kpi-value]').count()>0)===allowed}});
   }
  }
  for(const role of ['owner','moderator','editor','member','excluded']){
   await page.goto(B+'/qa/m12/login/'+role+'/');
   for(const lang of ['az','ru','en']){
    await page.context().addCookies([{name:'django_language',value:lang,domain:'127.0.0.1',path:'/'}]);const widths=role==='owner'?[360,390,768,1024,1280,1440]:[390,1440];
    for(const width of widths){
     await page.setViewportSize({width,height:900});const r=await page.goto(B+(lang==='az'?'':'/'+lang)+'/account/places/'+id+'/analytics/');const allowed=['owner','moderator'].includes(role);const checks={http:r.status()===(allowed?200:404)};
     if(allowed){const s=await state();const wants=['views','unique_visitors','favorites','contact_actions','directions'].map(k=>String(s.metrics[k]));const values=(await page.locator('.owner-analytics__grid strong').allTextContents()).map(s=>s.trim());checks.aggregate_matches=JSON.stringify(values)===JSON.stringify(wants);checks.no_overflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1);checks.no_private_dimensions=!(await page.locator('.owner-analytics').innerText()).match(/visitor_key_hash|session_key_hash|referrer_domain/);if(lang==='az')checks.az_comparison=(await page.locator('.owner-analytics').innerText()).includes('əvvəlki dövrlə müqayisədə');if(role==='owner'&&[360,1440].includes(width))await page.screenshot({path:'/mnt/c/kidsmap/docs/qa/module12-repair-2026-10-18-pc-r1/png/owner-final-'+lang+'-'+width+'.png',fullPage:true});}
     rows.push({id:'owner-acl-'+role+'-'+lang+'-'+width,role,lang,width,checks});
    }
   }
  }
  await page.goto(B+'/qa/m12/login/admin/');
  for(const lang of ['az','ru','en'])for(const width of [360,390,768,1024,1280,1440]){
   await page.context().addCookies([{name:'django_language',value:lang,domain:'127.0.0.1',path:'/'}]);await page.setViewportSize({width,height:900});await page.goto(B+'/admin/catalog/siteanalytics/?period=30');
   for(const period of [7,30,90,365]){
    const link=page.locator('.km-period-selector [data-period="'+period+'"]');await link.focus();if(period!==7){await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');}
    const focus=await link.evaluate(e=>({focused:document.activeElement===e,visible:e.matches(':focus-visible'),outline:getComputedStyle(e).outlineStyle,width:getComputedStyle(e).outlineWidth,shadow:getComputedStyle(e).boxShadow}));
    await Promise.all([page.waitForURL(u=>u.searchParams.get('period')===String(period)),page.keyboard.press('Enter')]);await page.waitForLoadState('domcontentloaded');
    const values=(await page.locator('[data-kpi-value]').allTextContents()).map(v=>v.trim());rows.push({id:'period-'+lang+'-'+width+'-'+period,role:'admin',lang,width,period,checks:{keyboard_focus:focus.focused&&focus.visible,focus_indicator:focus.outline!=='none'&&parseFloat(focus.width)>0||focus.shadow!=='none',selected_url:new URL(page.url()).searchParams.get('period')===String(period),kpi:JSON.stringify(values)===JSON.stringify([period,period+1,period+2].map(String))},focus});
   }
  }
  const final=await state();rows.push({id:'controls-read-only',checks:{entities_unchanged:initial.sha===final.sha,events_unchanged:initial.events_total===final.events_total,media_unchanged:JSON.stringify(initial.media)===JSON.stringify(final.media)}});
 }catch(e){errors.push(String(e))}return{rows,errors,pageerrors,provider:'Explicitly SIMULATED complete GA snapshot; real local aggregates/ACL and native keyboard controls'};
}
