async original=>{
 const base='http://localhost:8813',c=await original.context().browser().newContext(),p=await c.newPage(),rows=[];await c.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());
 try{
  await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill('moderator@example.invalid');await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.getByRole('button',{name:'Войти',exact:true}).click();
  for(const lang of ['ru','az','en']){
   await c.addCookies([{name:'django_language',value:lang,url:base}]);await p.goto(base+'/admin/catalog/place/3/change/');
   const labels=await p.locator('label[for=id_description_az],label[for=id_description_ru],label[for=id_description_en]').allTextContents();const expected=lang==='en'?'Description':lang==='az'?'Təsvir':'Описание';
   rows.push({id:'admin/description-label/'+lang,status:labels.length===3&&labels.every(t=>t.includes(expected))?'PASS':'FAIL',role:'moderator',lang,labels,htmlLanguage:await p.locator('html').getAttribute('lang')});
   const body=await p.locator('body').innerText();rows.push({id:'admin/feedback-localization/'+lang,status:lang==='ru'||!body.includes('Карта пока не активна')?'PASS':'FAIL',role:'moderator',lang,mapWarningRussian:body.includes('Карта пока не активна')});
   await p.setViewportSize({width:390,height:950});await p.screenshot({path:'C:/kidsmap/docs/qa/module01-2026-10-09-r2/screenshots/localization-admin-'+lang+'-390.png'});
  }
 }finally{await c.close();}
 return {rows};
}

