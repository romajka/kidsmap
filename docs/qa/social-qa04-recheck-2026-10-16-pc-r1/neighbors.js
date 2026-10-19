async (page) => {
  const origin='http://127.0.0.1:33304';
  const rows=[];
  await page.goto(origin+'/qa/login/empty/');
  for(const [lang,prefix] of [['ru','/ru'],['az',''],['en','/en']])for(const width of [390,1440]){
    const pageerrors=[],failed=[];
    const onError=e=>pageerrors.push({message:e.message});
    const onFailed=r=>failed.push({url:r.url(),error:r.failure()?.errorText});
    page.on('pageerror',onError);page.on('requestfailed',onFailed);
    await page.setViewportSize({width,height:844});
    const before=await(await page.request.get(origin+'/qa/state/empty/')).json();
    const response=await page.goto(origin+prefix+'/account/favorites/');
    await page.locator('.account-nav-sidebar').waitFor();
    const facts=await page.evaluate(()=>({
      stylesheets:[...document.styleSheets].map(s=>s.href).filter(Boolean),
      layout:getComputedStyle(document.querySelector('.account-main-layout')).display,
      nav:getComputedStyle(document.querySelector('.account-nav-sidebar')).display,
      active:getComputedStyle(document.querySelector('.account-nav-item.is-active')).textDecorationLine,
      overflow:document.documentElement.scrollWidth>innerWidth+1
    }));
    const after=await(await page.request.get(origin+'/qa/state/empty/')).json();
    const checks={status200:response.status()===200,account_css_loaded:facts.stylesheets.some(s=>s.includes('css/pages/account_profile.css')),
      layout_flex:facts.layout==='flex',nav_flex:facts.nav==='flex',active_undecorated:facts.active==='none',
      no_horizontal_overflow:!facts.overflow,no_notification_write:JSON.stringify(before)===JSON.stringify(after)};
    const png='/mnt/c/kidsmap/.tmp/social04-pc-plan-r1/png/favorites-control-'+lang+'-'+width+'.png';
    await page.screenshot({path:png,fullPage:true});
    page.off('pageerror',onError);page.off('requestfailed',onFailed);
    rows.push({lang,width,checks,facts,pageerrors,request_failed:failed,png});
  }
  return rows;
}
