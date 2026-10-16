async(page)=>{
 const B='__BASE__',ROOT='__HERE__',rows=[],errors=[],consoleEvents=[],network=[];
 await page.context().route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(['warning','error'].includes(m.type()))consoleEvents.push({type:m.type(),text:m.text(),url:m.location().url});});page.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)network.push({url:r.url().split('?')[0],status:r.status()});});
 const add=(id,ok,detail={})=>rows.push({id,status:ok?'PASS':'FAIL',...detail});const nav=async l=>Promise.all([page.waitForNavigation(),l.click()]);
 await page.goto(B+'/admin/login/?next=/admin/');await page.locator('[name=username]').fill('start_admin');await page.locator('[name=password]').fill('__PASSWORD__');await nav(page.locator('[type=submit]'));
 const tab=async(name,value)=>{const l=page.locator('[name='+name+']');if(!await l.isVisible()){const id=await l.locator('xpath=ancestor::div[contains(@class,"tab-pane")]').getAttribute('id');await page.locator('a[href="#'+id+'"]:not([data-toggle=collapse])').first().click();}await l.fill(value);};
 const language=async lang=>{await page.locator('.km-admin-lang-btn').first().click();await nav(page.locator('#jazzy-languagemenu button[lang="'+lang+'"]:visible'));};
 const ids={};
 for(const lang of ['ru','az','en']){
  await language(lang);await page.setViewportSize({width:1440,height:950});await page.goto(B+'/admin/catalog/organization/add/');await tab('name_az','QA04 Native '+lang);await tab('name_ru','QA04 сеть '+lang);await tab('name_en','QA04 Native '+lang+' EN');await tab('description_az','Fictional organization for isolated language acceptance.');
  await nav(page.locator('button[name=_save_draft]'));const id=Number(page.url().match(/organization\/(\d+)\/change/)[1]);ids[lang]=id;add('native-draft-'+lang,id>0,{lang,id});await page.reload();add('reload-draft-'+lang,await page.locator('[name=name_en]').inputValue()==='QA04 Native '+lang+' EN',{lang});
  await tab('name_en','QA04 Native '+lang+' pending');await nav(page.locator('button[name=_submit_candidate]'));add('pending-'+lang,await page.locator('button[value=approve]').count()===1,{lang});
  const before='screenshots/'+lang+'-pending.png';await page.screenshot({path:ROOT+'/'+before,fullPage:true});
  await nav(page.locator('button[value=approve]'));add('published-'+lang,await page.locator('button[value=unpublish]').count()===1,{lang});
  await tab('name_en','QA04 candidate '+lang);await nav(page.locator('button[name=_save_draft]'));await page.reload();add('candidate-reload-'+lang,await page.locator('[name=name_en]').inputValue()==='QA04 candidate '+lang,{lang});
  for(const width of [360,390,768,1024,1280,1440]){
   await page.setViewportSize({width,height:950});await page.goto(B+'/admin/catalog/organization/'+id+'/change/');await page.waitForTimeout(200);
   const text=await page.locator('body').innerText();const missing=['Названия','Организации','Владение','Проверка данных','Связанные разделы','Текущие и предложенные данные'].filter(x=>text.includes(x));
   const g=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth}));const screenshot='screenshots/'+lang+'-'+width+'-edit.png';await page.screenshot({path:ROOT+'/'+screenshot,fullPage:true});add('render-edit-'+lang+'-'+width,(lang==='ru'||missing.length===0)&&g.document<=width+1,{lang,width,missing,geometry:g,screenshot});
   await page.goto(B+'/admin/catalog/organization/add/');const tx=await page.locator('body').innerText();add('render-add-'+lang+'-'+width,lang==='ru'||!tx.includes('Названия'),{lang,width});
  }
 }
 for(const lang of ['ru','az','en','ru']){await language(lang);await page.goto(B+'/admin/catalog/organization/'+ids.en+'/change/');const label=lang==='ru'?'Названия':lang==='az'?'Adlar':'Names';add('same-session-switch-'+lang,await page.getByRole('tab',{name:label,exact:true}).count()===1,{lang});}
 return{rows,errors,consoleEvents,network,ids,note:'native admin language dropdown transitions'};
}
