async (page) => {
  const item = __ITEM__;
  const origin = 'http://127.0.0.1:33304';
  const errors=[], consoleErrors=[], failed=[], responses=[];
  const onError=e=>errors.push({message:e.message});
  const onConsole=m=>{if(m.type()==='error')consoleErrors.push(m.text());};
  const onFailed=r=>failed.push({url:r.url(),error:r.failure()?.errorText});
  const onResponse=r=>{if(r.status()>=400)responses.push({url:r.url(),status:r.status()});};
  page.on('pageerror',onError);page.on('console',onConsole);page.on('requestfailed',onFailed);page.on('response',onResponse);
  await page.setViewportSize({width:item.width,height:844});
  await page.goto(origin+'/qa/login/'+item.state+'/');
  const before = await (await page.request.get(origin+'/qa/state/'+item.state+'/')).json();
  const response = await page.goto(origin+item.url);
  await page.locator('#main-content h1').waitFor();
  const facts = await page.evaluate(() => {
    const root=document.querySelector('.account-page-wrapper');
    const layout=root.querySelector('.account-main-layout');
    const nav=root.querySelector('.account-nav-sidebar');
    const active=nav.querySelector('[aria-current="page"]');
    const list=root.querySelector('.org-list');
    const rows=[...root.querySelectorAll('.org-row')];
    const buttons=[...root.querySelectorAll('button')];
    const styles=e=>e?{display:getComputedStyle(e).display,color:getComputedStyle(e).color,
      background:getComputedStyle(e).backgroundColor,border:getComputedStyle(e).borderTopWidth,
      textDecoration:getComputedStyle(e).textDecorationLine,listStyle:getComputedStyle(e).listStyleType,
      minHeight:getComputedStyle(e).minHeight,height:e.getBoundingClientRect().height}:null;
    return {layout:styles(layout),nav:styles(nav),active:styles(active),list:styles(list),row:styles(rows[0]),
      buttons:buttons.map(styles),rows:rows.length,readButtons:root.querySelectorAll('form[action$="/read/"]').length,
      accepts:root.querySelectorAll('form[action$="/accept/"]').length,rejects:root.querySelectorAll('form[action$="/reject/"]').length,
      activeCurrent:active?.classList.contains('is-active'),navLabel:nav.getAttribute('aria-label'),
      unnamedButtons:buttons.filter(b=>!b.textContent.trim()).length,
      csrfForms:[...root.querySelectorAll('form')].every(f=>f.method.toLowerCase()==='post'&&Boolean(f.querySelector('[name="csrfmiddlewaretoken"]'))),
      heading:root.querySelector('h1').textContent.trim(),
      overflow:document.documentElement.scrollWidth>innerWidth+1,
      stylesheets:[...document.styleSheets].map(s=>s.href).filter(Boolean),
      fonts:{symbols:document.fonts.check('20px "Material Symbols Rounded"'),nunito:document.fonts.check('16px Nunito')}};
  });
  const active=page.locator('.account-nav-sidebar [aria-current="page"]');
  await active.focus();await page.keyboard.press('Tab');
  const keyboard=await page.evaluate(()=>({tag:document.activeElement.tagName,
    insideNav:Boolean(document.activeElement.closest('.account-nav-sidebar')),
    outline:getComputedStyle(document.activeElement).outlineStyle}));
  const after = await (await page.request.get(origin+'/qa/state/'+item.state+'/')).json();
  const controls={status200:response.status()===200,correct_url:page.url()===origin+item.url,
    expected_rows:facts.rows===before.rows,read_state:facts.readButtons===before.unread,
    current_invite_actions:facts.accepts===before.accept&&facts.rejects===before.reject,
    active_nav:facts.activeCurrent===true&&Boolean(facts.navLabel),named_buttons:facts.unnamedButtons===0,
    csrf_post_forms:facts.csrfForms,no_business_write:JSON.stringify(before)===JSON.stringify(after),
    keyboard_nav:keyboard.tag==='A'&&keyboard.insideNav,heading_localized:facts.heading===item.heading};
  const style_checks={account_css_loaded:facts.stylesheets.some(s=>s.includes('/css/pages/account_profile.css')),
    layout_flex:facts.layout.display==='flex',nav_flex:facts.nav.display==='flex',
    active_link_undecorated:facts.active.textDecoration==='none'};
  if(before.rows)Object.assign(style_checks,{list_no_bullets:facts.list.listStyle==='none',
    row_has_card_border:parseFloat(facts.row.border)>=1,
    actions_min44:facts.buttons.every(b=>b.height>=44)});
  const png='/mnt/c/kidsmap/.tmp/social04-pc-plan-r1/png/inbox-'+item.state+'-'+item.lang+'-'+item.width+'.png';
  await page.screenshot({path:png,fullPage:true});
  page.off('pageerror',onError);page.off('console',onConsole);page.off('requestfailed',onFailed);page.off('response',onResponse);
  return {item,status:response.status(),controls,style_checks,facts,keyboard,before,after,
    pageerrors:errors,console_errors:consoleErrors,request_failed:failed,http_failures:responses,png};
}
