async (page) => {
  const item = __ITEM__;
  const origin = 'http://127.0.0.1:33314';
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
  await page.evaluate(()=>document.fonts.ready);
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
      flexDirection:getComputedStyle(layout).flexDirection,
      badges:root.querySelectorAll('.account-notifications__unread').length,
      styledUnreadRows:root.querySelectorAll('.account-notifications__item.is-unread').length,
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
  if(!facts.buttons.length)delete style_checks.actions_min44;
  Object.assign(style_checks,{
    inbox_css_loaded:facts.stylesheets.some(s=>s.includes('/css/pages/account_notifications.css')),
    responsive_direction:facts.flexDirection===(item.width<=860?'column':'row'),
    no_horizontal_overflow:!facts.overflow,
    unread_state_text:facts.badges===before.unread&&facts.styledUnreadRows===before.unread
  });
  const contrast=await page.evaluate(()=>{
    const parse=s=>{const n=s.match(/[\d.]+/g).map(Number);return [n[0]/255,n[1]/255,n[2]/255,n.length>3?n[3]:1];};
    const over=(a,b)=>a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3]));
    const bg=el=>{const chain=[];for(let p=el;p;p=p.parentElement)chain.push(p);let b=[1,1,1];
      for(const p of chain.reverse())b=over(parse(getComputedStyle(p).backgroundColor),b);return b;};
    const lum=a=>a.map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
    const ratio=(a,b)=>(Math.max(lum(a),lum(b))+.05)/(Math.min(lum(a),lum(b))+.05);
    const elements=[...document.querySelectorAll('.account-notifications__title,.account-notifications__intro,.account-notifications__meta strong,.account-notifications__meta time,.account-notifications__unread,.account-notifications__action,.account-notifications__empty')];
    return elements.map(e=>{const b=bg(e);return {tag:e.tagName,class:e.className,ratio:ratio(over(parse(getComputedStyle(e).color),b),b)};});
  });
  style_checks.text_contrast=contrast.every(c=>c.ratio>=4.5);
  const focus=[];
  const buttons=page.locator('.account-main-content button');
  if(await buttons.count()){
    await page.locator('.account-nav-sidebar a').last().focus();
    for(let i=0;i<await buttons.count();i++){
      await page.keyboard.press('Tab');
      const result=await buttons.nth(i).evaluate(e=>{
        const s=getComputedStyle(e),r=e.getBoundingClientRect();
        const x=Math.min(innerWidth-2,Math.max(2,r.x+r.width/2)),y=Math.min(innerHeight-2,Math.max(75,r.y+r.height/2));
        return {focused:document.activeElement===e,outline:s.outlineStyle,outlineWidth:parseFloat(s.outlineWidth),
          hit:e===document.elementFromPoint(x,y)||e.contains(document.elementFromPoint(x,y)),height:r.height};
      });focus.push(result);
    }
    await page.keyboard.press('Shift+Tab');
    style_checks.shift_tab=await buttons.nth(Math.max(0,await buttons.count()-2)).evaluate(e=>document.activeElement===e);
    // For one button, Shift+Tab returns to the navigation rather than a second button.
    if(await buttons.count()===1)style_checks.shift_tab=await page.locator('.account-nav-sidebar a').last().evaluate(e=>document.activeElement===e);
    style_checks.actions_keyboard_focus_hit=focus.every(f=>f.focused&&f.outline!=='none'&&f.outlineWidth>=2&&f.hit&&f.height>=44);
  }
  const png='/mnt/c/kidsmap/.tmp/social04-pc-fix-r1/png/inbox-'+item.state+'-'+item.lang+'-'+item.width+'.png';
  await page.screenshot({path:png,fullPage:true});
  page.off('pageerror',onError);page.off('console',onConsole);page.off('requestfailed',onFailed);page.off('response',onResponse);
  return {item,status:response.status(),controls,style_checks,facts,keyboard,before,after,
    contrast,focus,pageerrors:errors,console_errors:consoleErrors,request_failed:failed,http_failures:responses,png};
}
