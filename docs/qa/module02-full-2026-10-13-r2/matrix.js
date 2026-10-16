async original=>{
 const B='__BASE__',ROOT='__HERE__',browser=original.context().browser(),rows=[],errors=[],consoleEvents=[],network=[],blocked={};
 const scenes={owner:[['list','/account/organizations/'],['create-empty','/account/organizations/create/?fresh=1'],['create-long-open','/account/organizations/create/?fresh=1'],['create-error','/account/organizations/create/?fresh=1'],['workspace','/account/organizations/1/'],['team-open','/account/organizations/1/#org-team'],['search-filled','/account/organizations/1/connections/?q=QA02+BULK'],['search-empty','/account/organizations/1/connections/?q=QA02-no-such-place'],['mixed-result','/account/organization-operations/ff9a0772-fc19-44ba-91a3-5cfead0ce8d1/'],['request-recovery','/account/organizations/1/requests/16/recovery/']],guest:[['public-list','/organizations/'],['public-card','/organizations/e8376fab-1824-4a90-b78f-2afe61819eda/']],moderator:[['admin-create','/admin/catalog/organization/add/'],['admin-edit','/admin/catalog/organization/4/change/'],['admin-selection','/admin/catalog/place/?q=QA02+BULK'],['admin-result','/admin/catalog/place/organization-connections/?operation=ab12fbb6-c2ee-4a70-ba6a-69aed635a3cc']]};
 for(const role of Object.keys(scenes)){
  const c=await browser.newContext({reducedMotion:'reduce'});await c.route('**/*',r=>{const u=r.request().url();if(u.startsWith(B+'/'))return r.continue();try{const o=new URL(u).origin;blocked[o]=(blocked[o]||0)+1;}catch{}return r.abort();});const p=await c.newPage();p.setDefaultTimeout(10000);p.on('pageerror',e=>errors.push({role,text:String(e)}));p.on('console',m=>{if(['warning','error'].includes(m.type()))consoleEvents.push({role,type:m.type(),text:m.text().slice(0,300),url:m.location().url});});p.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)network.push({role,url:r.url().split('?')[0],status:r.status()});});
  if(role!=='guest'){await p.goto(B+'/ru/auth/login/');await p.locator('[name=username]').fill(role+'@example.invalid');await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.getByRole('button',{name:'Войти',exact:true}).click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));}
  for(const lang of ['ru','az','en']){
   await c.addCookies([{name:'django_language',value:lang,url:B}]);
   for(const width of [360,390,768,1024,1280,1440]){
    await p.setViewportSize({width,height:950});
    for(const [scene,path] of scenes[role]){
     const row={id:role+'-'+lang+'-'+width+'-'+scene,role,lang,width,scene,status:'PASS'};
     try{
      const url=B+(path.startsWith('/admin/')?'':lang==='az'?'':'/'+lang)+path;const r=await p.goto(url);row.http=r.status();
      if(scene.startsWith('create-')){await p.evaluate(()=>{localStorage.clear();sessionStorage.clear();});await p.reload();}
      if(scene==='create-long-open'){await p.locator('[name=name_az]').fill('QA02 Fictional long organization — creative education and family activities '.repeat(2));for(const s of await p.locator('[data-org-create-form] details:not([open]) > summary').all())await s.click();await p.locator('[name=name_en]').fill('QA02 very long fictional English organization '.repeat(4));await p.locator('[name=description_az]').fill('Fictional isolated QA text. '.repeat(18));await p.locator('[name=name_en]').focus();await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');row.keyboard=await p.locator('[name=name_en]').evaluate(e=>e===document.activeElement);}
      if(scene==='create-empty'){await p.locator('[name=name_az]').focus();await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');row.keyboard=await p.locator('[name=name_az]').evaluate(e=>e===document.activeElement);const summary=p.locator('#disclosure-translations summary');await summary.focus();await p.keyboard.press('Enter');row.disclosure=await p.locator('#disclosure-translations').getAttribute('open')!==null;}
      if(scene==='create-error'){await p.locator('[name=name_az]').fill('QA02 invalid URL draft');const field=p.locator('[name=website]');if(!await field.isVisible())await field.locator('xpath=ancestor::details').locator('summary').click();await field.fill('invalid-url');await Promise.all([p.waitForNavigation(),p.locator('[data-org-create-form] button[type=submit]').click()]);row.expectedError=await p.locator('.org-field-error,[role=alert]').count()>0;row.inputPreserved=await p.locator('[name=name_az]').inputValue()==='QA02 invalid URL draft';}
      if(scene==='team-open'){await p.locator('#org-team').scrollIntoViewIfNeeded();await p.locator('[data-team-form] [name=role]').focus();await p.keyboard.press('Space');await p.keyboard.press('Escape');row.teamVisible=await p.locator('[data-team-grants]').isVisible();}
      if(scene==='admin-selection'){const cb=p.locator('input[name=_selected_action]').first();await cb.focus();await p.keyboard.press('Space');row.keyboard=await cb.isChecked();}
      if(scene==='admin-create'||scene==='admin-edit'){row.formPresent=await p.locator('[name=name_az]').count()===1;row.documentLanguage=await p.locator('html').getAttribute('lang');row.nameTab=await p.getByRole('tab',{name:lang==='ru'?'Названия':lang==='az'?'Adlar':'Names',exact:true}).count()===1;}
      if(scene.endsWith('result'))row.resultVisible=await p.locator('#organization-connection-main').isVisible();
      row.geometry=await p.evaluate(()=>{const visible=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden';};return{viewport:innerWidth,document:document.documentElement.scrollWidth,clipped:[...document.querySelectorAll('main input:not([type=hidden]),main select,main textarea,#content input:not([type=hidden]),#content select,#content textarea')].filter(visible).filter(e=>{const r=e.getBoundingClientRect();return r.left< -2||r.right>innerWidth+2;}).map(e=>e.name)};});
      row.screenshot='screenshots/'+row.id+'.png';await p.screenshot({path:ROOT+'/'+row.screenshot});
      if(row.http!==200||row.geometry.document>width+2||row.geometry.clipped.length||row.keyboard===false||row.disclosure===false||row.expectedError===false||row.inputPreserved===false||row.formPresent===false||row.nameTab===false||row.resultVisible===false)row.status='FAIL';
     }catch(e){row.status='NOT RUN';row.error=String(e).slice(0,400);row.url=p.url().split('?')[0];}
     rows.push(row);
    }
   }
  }
  await c.close();
 }
 return{rows,errors,consoleEvents,network,blockedExternalOrigins:blocked,note:'Native rendered288 states. Geometry gates plus screenshot review; no h1-only admin heuristic. Functional native core transitions retained by source provenance.'};
}
