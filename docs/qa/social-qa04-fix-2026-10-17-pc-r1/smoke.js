async (page) => {
  const origin='http://127.0.0.1:33314',rows=[],cases=__CASES__;
  for(const key of ['role-owner','role-staff']){
    for(const [lang,prefix] of [['ru','/ru'],['az',''],['en','/en']])for(const width of [390,1440]){
      const errors=[],onError=e=>errors.push({message:e.message});page.on('pageerror',onError);
      await page.setViewportSize({width,height:844});await page.goto(origin+'/qa/login/'+key+'/');
      const r=await page.goto(origin+prefix+'/account/notifications/');await page.evaluate(()=>document.fonts.ready);
      const facts=await page.evaluate(()=>({css:[...document.styleSheets].map(s=>s.href).filter(Boolean),
        layout:getComputedStyle(document.querySelector('.account-main-layout')).display,
        badge:document.querySelectorAll('.account-notifications__unread').length,
        actions:[...document.querySelectorAll('.account-main-content button')].map(b=>b.getBoundingClientRect().height),
        overflow:document.documentElement.scrollWidth>innerWidth+1}));
      const checks={status200:r.status()===200,styled_layout:facts.layout==='flex',
        scoped_css_loaded:facts.css.some(s=>s.includes('/account_notifications.css')),unread_visible:facts.badge===1,
        actions_min44:facts.actions.length>0&&facts.actions.every(h=>h>=44),no_overflow:!facts.overflow};
      const png='/mnt/c/kidsmap/.tmp/social04-pc-fix-r1/png/role-'+key+'-'+lang+'-'+width+'.png';
      await page.screenshot({path:png,fullPage:true});page.off('pageerror',onError);
      rows.push({key,lang,width,checks,facts,pageerrors:errors,png});
    }
  }
  const owner=cases.find(c=>c.key==='role-owner');
  for(const [surface,path] of [['favorites','/account/favorites/'],['profile','/account/profile/'],
    ['organization','/account/organizations/'+owner.org_id+'/']]){
    for(const [lang,prefix] of [['ru','/ru'],['az',''],['en','/en']])for(const width of [390,1440]){
      const errors=[],failed=[],onError=e=>errors.push({message:e.message});
      const onFailed=r=>failed.push({url:r.url(),error:r.failure()?.errorText});
      page.on('pageerror',onError);page.on('requestfailed',onFailed);
      await page.setViewportSize({width,height:844});await page.goto(origin+'/qa/login/role-owner/');
      const before=await(await page.request.get(origin+'/qa/state/role-owner/')).json();
      const r=await page.goto(origin+prefix+path);await page.evaluate(()=>document.fonts.ready);
      const facts=await page.evaluate(()=>({css:[...document.styleSheets].map(s=>s.href).filter(Boolean),
        overflow:document.documentElement.scrollWidth>innerWidth+1,heading:document.querySelector('h1')?.textContent.trim()}));
      const after=await(await page.request.get(origin+'/qa/state/role-owner/')).json();
      const checks={status200:r.status()===200,no_inbox_css:facts.css.every(s=>!s.includes('/account_notifications.css')),
        heading_present:Boolean(facts.heading),no_notification_write:JSON.stringify(before)===JSON.stringify(after)};
      const png='/mnt/c/kidsmap/.tmp/social04-pc-fix-r1/png/shared-'+surface+'-'+lang+'-'+width+'.png';
      await page.screenshot({path:png,fullPage:true});
      page.off('pageerror',onError);page.off('requestfailed',onFailed);
      rows.push({surface,lang,width,checks,facts,pageerrors:errors,request_failed:failed,png});
    }
  }
  return rows;
}
