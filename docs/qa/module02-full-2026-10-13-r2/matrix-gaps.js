async original=>{
 const B='__BASE__',ROOT='__HERE__',c=await original.context().browser().newContext({reducedMotion:'reduce'}),p=await c.newPage(),rows=[],errors=[],network=[];p.setDefaultTimeout(10000);await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.on('pageerror',e=>errors.push(String(e)));p.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)network.push({url:r.url().split('?')[0],status:r.status()});});
 await p.goto(B+'/ru/auth/login/');await p.locator('[name=username]').fill('owner@example.invalid');await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.getByRole('button',{name:'Войти',exact:true}).click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));
 try{
  for(const lang of ['ru','az','en']){await c.addCookies([{name:'django_language',value:lang,url:B}]);for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});for(const scene of ['create-long-open','team-open']){
   const row={id:'owner-'+lang+'-'+width+'-'+scene,role:'owner',lang,width,scene,status:'PASS'};
   try{
    const prefix=lang==='az'?'':'/'+lang;
    if(scene==='create-long-open'){
     const r=await p.goto(B+prefix+'/account/organizations/create/?fresh=1');row.http=r.status();await p.evaluate(()=>{localStorage.clear();sessionStorage.clear();});await p.reload();
     await p.locator('[name=name_az]').fill('QA02 Fictional long organization — creative education and family activities '.repeat(2));
     for(const id of ['translations','contacts','description']){const d=p.locator('#disclosure-'+id);if(await d.getAttribute('open')===null)await d.locator('summary').click();}
     await p.locator('[name=name_en]').fill('QA02 very long fictional English organization '.repeat(4));await p.locator('[name=description_az]').fill('Fictional isolated QA text. '.repeat(18));await p.locator('[name=name_en]').focus();await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');row.keyboard=await p.locator('[name=name_en]').evaluate(e=>e===document.activeElement);row.openDisclosures=await p.locator('[data-org-create-form] details[open]').count();
    }else{
     const r=await p.goto(B+prefix+'/account/organizations/1/');row.http=r.status();await p.locator('a[href="#org-team"]').first().click();await p.locator('#org-team').scrollIntoViewIfNeeded();await p.locator('[data-team-form] [name=role]').focus();await p.keyboard.press('Space');await p.keyboard.press('Escape');row.teamVisible=await p.locator('[data-team-grants]').isVisible();row.nativeAnchor=p.url().endsWith('#org-team');
    }
    row.geometry=await p.evaluate(()=>{const visible=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden';};return{viewport:innerWidth,document:document.documentElement.scrollWidth,clipped:[...document.querySelectorAll('main input:not([type=hidden]),main select,main textarea')].filter(visible).filter(e=>{const r=e.getBoundingClientRect();return r.left< -2||r.right>innerWidth+2;}).map(e=>e.name)};});row.screenshot='screenshots/'+row.id+'-corrected.png';await p.screenshot({path:ROOT+'/'+row.screenshot});
    if(row.http!==200||row.geometry.document>width+2||row.geometry.clipped.length||row.keyboard===false||row.teamVisible===false||row.nativeAnchor===false)row.status='FAIL';
   }catch(e){row.status='NOT RUN';row.error=String(e).slice(0,400);}
   rows.push(row);
  }}}
  return{rows,errors,network,note:'Only36 QA harness gaps rerun. Stable disclosure selectors and native same-document team link; existing assertions unchanged.'};
 }finally{await c.close();}
}
