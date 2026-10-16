async page=>{
const B='http://127.0.0.1:40257',P='http://localhost:40257',O='/home/ramin/kidsmap/output/playwright/admin-moderation-fix-2026-10-16-r1',f=await(await page.request.get(B+'/admin/qa/fixtures/')).json(),rows=[],errors=[],http=[];
page.on('pageerror',e=>errors.push(String(e)));page.on('response',r=>{if((r.url().startsWith(B+'/')||r.url().startsWith(P+'/'))&&r.status()>=400)http.push({status:r.status(),path:new URL(r.url()).pathname});});
const writerContext=await page.context().browser().newContext({viewport:{width:390,height:950}});await writerContext.route('**/*',r=>r.request().url().startsWith(B+'/')||r.request().url().startsWith(P+'/')?r.continue():r.abort());const writer=await writerContext.newPage();
try{
 await page.goto(B+'/admin/');if(page.url().includes('/login/')){await page.locator('[name=username]').fill(f.username);await page.locator('[name=password]').fill(f.password);await Promise.all([page.waitForURL(B+'/admin/',{waitUntil:'domcontentloaded'}),page.getByRole('button',{name:'Войти',exact:true}).click()]);}
 await writer.goto(P+'/ru/auth/login/');await writer.locator('[name=username]').fill('fictional_author_3');await writer.locator('[name=password]').fill(f.password);await Promise.all([writer.waitForURL(u=>!u.pathname.includes('/auth/login/'),{waitUntil:'domcontentloaded'}),writer.locator('form.register-form--login button[type=submit]').click()]);
 await writer.goto(P+'/ru/reviews/place/target/'+f.place+'/');await writer.locator('#review-rating').selectOption('4');await writer.locator('#review-text').fill('Вымышленная правка для проверки интерфейса. '+('ОченьДлинноеСлово'.repeat(9))+' Детали должны оставаться читаемыми.');await Promise.all([writer.waitForNavigation({waitUntil:'domcontentloaded'}),writer.locator('form[data-review-edit] button').click()]);
 for(const lang of ['ru','az','en']){
  await page.context().addCookies([{name:'django_language',value:lang,url:B}]);
  for(const width of [390,768,1024,1280,1440]){
   await page.setViewportSize({width,height:950});
   for(const kind of ['queue','workflow','place-preview']){
    const path=kind==='queue'?'/admin/catalog_moderation/moderationreview/':kind==='workflow'?'/admin/catalog/placereview/'+f.reviews[3].head+'/workflow/':'/admin/catalog/place/'+f.pending_place+'/site-preview/?lang='+lang;
    const r=await page.goto(B+path);await page.locator('h1').first().waitFor();
    const d=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,language:document.documentElement.lang,buttons:[...document.querySelectorAll('main[data-review-workflow] button')].filter(n=>n.getBoundingClientRect().height>0).map(n=>({text:n.textContent.trim(),height:n.getBoundingClientRect().height})),candidate:!!document.querySelector('[data-candidate-id]')}));
    let keyboard=null;
    if(kind==='workflow'){
     const text=page.locator('#review-reason');await text.focus();await page.keyboard.press('Tab');keyboard=await page.evaluate(()=>document.activeElement?.tagName==='BUTTON');await page.keyboard.press('Shift+Tab');keyboard=keyboard&&await text.evaluate(n=>n===document.activeElement);
    }
    rows.push({lang,width,kind,http:r.status(),same_admin_host:page.url().startsWith(B+'/admin/'),...d,keyboard,status:r.status()===200&&d.scrollWidth<=width+1&&(kind!=='workflow'||(d.candidate&&keyboard&&d.buttons.every(b=>b.height>=43)))?'PASS':'FAIL'});
    if(width===390||width===1440)await page.screenshot({path:O+'/matrix-'+lang+'-'+width+'-'+kind+'.png'});
   }
  }
 }
 await page.context().addCookies([{name:'django_language',value:'ru',url:B}]);await page.setViewportSize({width:1440,height:950});await page.goto(B+'/admin/catalog/placereview/'+f.reviews[3].head+'/workflow/');const post=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/approve/'));await page.locator('form[action$="/approve/"] button').click();const approved=(await post).status()===302;await page.waitForLoadState('domcontentloaded');
 const state=await(await page.request.get(B+'/admin/qa/state/')).json();return{complete:true,rows,errors,http,cleanup_approved:approved,final_state:state};
}catch(e){return{complete:false,error:String(e),rows,errors,http};}finally{await writerContext.close();}
}
