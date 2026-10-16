async(page)=>{
 const B='__BASE__',ROOT='__HERE__',rows=[],errors=[],consoleEvents=[],network=[];
 await page.context().route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(['warning','error'].includes(m.type()))consoleEvents.push({type:m.type(),text:m.text().slice(0,300),url:m.location().url});});page.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)network.push({url:r.url().split('?')[0],status:r.status()});});
 const add=(id,ok,detail={})=>rows.push({id,status:ok?'PASS':'FAIL',...detail});const nav=async l=>Promise.all([page.waitForNavigation(),l.click()]);
 await page.goto(B+'/admin/login/?next=/admin/');await page.locator('[name=username]').fill('start_admin');await page.locator('[name=password]').fill('__PASSWORD__');await nav(page.locator('[type=submit]'));
 const language=async lang=>{await page.locator('.km-admin-lang-btn').first().click();await nav(page.locator('#jazzy-languagemenu button[lang="'+lang+'"]:visible'));};
 const fill=async(name,value)=>{const l=page.locator('[name='+name+']');if(!await l.isVisible()){const id=await l.locator('xpath=ancestor::div[contains(@class,"tab-pane")]').getAttribute('id');await page.locator('a[role=tab][href="#'+id+'"]').click();}await l.fill(value);};
 const titles={ru:'Названия',az:'Adlar',en:'Names'},ownership={ru:'Владение',az:'Sahiblik',en:'Ownership'};
 for(const lang of ['ru','az','en','ru']){
  await language(lang);await page.goto(B+'/admin/catalog/organization/4/change/');const actual=await page.locator('html').getAttribute('lang');add('same-session-'+lang+'-'+rows.length,actual===lang&&await page.getByRole('tab',{name:titles[lang],exact:true}).count()===1,{lang,actual});
 }
 const states={add:'/admin/catalog/organization/add/',draft:'/admin/catalog/organization/1/change/',published_candidate:'/admin/catalog/organization/4/change/'};
 for(const lang of ['ru','az','en']){
  await page.setViewportSize({width:1440,height:950});await language(lang);
  for(const width of [360,390,768,1024,1280,1440])for(const [state,path] of Object.entries(states)){
   await page.setViewportSize({width,height:950});await page.goto(B+path);const htmlLang=await page.locator('html').getAttribute('lang'),tabText=await page.getByRole('tab').allTextContents();const body=await page.locator('body').innerText();const g=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth}));
   const foreign=lang==='ru'?['Adlar','Təşkilatlar','Sahiblik']:['Названия','Организации','Владение','Проверка данных','Связанные разделы','Текущие и предложенные данные'];const residual=foreign.filter(x=>body.includes(x));
   const screenshot='screenshots/'+lang+'-'+width+'-'+state+'.png';await page.screenshot({path:ROOT+'/'+screenshot,fullPage:true});add('render-'+lang+'-'+width+'-'+state,htmlLang===lang&&tabText.some(x=>x.trim()===titles[lang])&&residual.length===0&&g.document<=width+1,{lang,width,state,geometry:g,residual,screenshot});
  }
 }
 await page.setViewportSize({width:1440,height:950});await language('en');await page.goto(B+'/admin/catalog/organization/4/change/');await nav(page.locator('button[name=_submit_candidate]'));await page.locator('button[value=approve]').waitFor({state:'visible'});add('native-pending-visible',await page.locator('button[value=approve]').count()===1);
 const pendingShot='screenshots/en-pending.png';await page.screenshot({path:ROOT+'/'+pendingShot,fullPage:true});rows[rows.length-1].screenshot=pendingShot;
 await nav(page.locator('button[value=approve]'));const early=await page.locator('button[value=unpublish]').count();await page.locator('button[value=unpublish]').waitFor({state:'visible'});add('native-published-visible',await page.locator('button[value=unpublish]').count()===1,{earlyCount:early});await page.reload();add('published-reload',await page.locator('button[value=unpublish]').count()===1);
 const website=await page.locator('[name=website]').inputValue();await fill('name_en','QA04 invalid URL retained');await fill('website','not-a-url');await nav(page.locator('button[name=_save_draft]'));add('invalid-url-honest-error',await page.locator('.errorlist').count()>0&&await page.locator('[name=name_en]').inputValue()==='QA04 invalid URL retained');
 const errorShot='screenshots/en-error.png';await page.screenshot({path:ROOT+'/'+errorShot,fullPage:true});rows[rows.length-1].screenshot=errorShot;
 await fill('website',website);await nav(page.locator('button[name=_save_draft]'));await page.reload();add('correct-error-draft-reload',await page.locator('[name=name_en]').inputValue()==='QA04 invalid URL retained');
 for(const lang of ['ru','az','en']){await language(lang);for(const model of ['organization','program','placeownershiprequest']){await page.goto(B+'/admin/catalog/'+model+'/');const label=model==='organization'?(lang==='ru'?'Организации':lang==='az'?'Təşkilatlar':'Organizations'):model==='program'?(lang==='ru'?'Программы':lang==='az'?'Proqramlar':'Programs'):null;add('shared-heading-'+lang+'-'+model,label===null|| (await page.locator('body').innerText()).includes(label),{lang,model});}}
 return{rows,errors,consoleEvents,network};
}
