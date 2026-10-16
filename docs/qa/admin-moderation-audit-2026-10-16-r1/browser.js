async page=>{
 const B='http://127.0.0.1:59505',OUT='/home/ramin/kidsmap/output/playwright/admin-moderation-audit-2026-10-16-r1';
 const f=await(await page.request.get(B+'/qa/fixtures/')).json(),rows=[],errors=[],failures=[];
 await page.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
 page.on('pageerror',e=>errors.push(String(e)));page.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)failures.push({status:r.status(),path:new URL(r.url()).pathname});});
 await page.goto(B+'/admin/');
 if(page.url().includes('/login/')){
  await page.getByRole('textbox',{name:'Имя пользователя',exact:true}).fill(f.username);
  await page.getByRole('textbox',{name:'Пароль',exact:true}).fill(f.password);
  await page.getByRole('button',{name:'Войти',exact:true}).click();await page.waitForURL(B+'/admin/');
 }
 for(const lang of ['ru','az','en']){
  await page.context().addCookies([{name:'django_language',value:lang,url:B}]);
  for(const width of [390,768,1024,1280,1440]){
   await page.setViewportSize({width,height:950});
   for(const kind of ['queue','review','place']){
    const path=kind==='queue'?'/admin/catalog_moderation/moderationreview/':kind==='review'?'/admin/catalog/placereview/'+f.reviews[1].head+'/change/':'/admin/catalog_moderation/moderationplace/'+f.pending_place+'/change/';
    const response=await page.goto(B+path);await page.locator('h1').first().waitFor();
    const d=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,rows:document.querySelectorAll('#result_list tbody tr').length,links:[...document.querySelectorAll('a')].filter(n=>/reviews\/place\/target|\/place\//.test(n.getAttribute('href')||'')).map(n=>({text:n.textContent.trim(),href:n.getAttribute('href')}))}));
    rows.push({lang,width,kind,status:response.status(),...d});
    if(width===390||width===1440)await page.screenshot({path:OUT+'/'+lang+'-'+width+'-'+kind+'.png'});
   }
  }
 }
 await page.goto(B+'/admin/catalog_moderation/moderationreview/');
 const first=f.reviews[0];await page.locator('input.action-select[value="'+first.head+'"]').check();
 await page.screenshot({path:OUT+'/bulk-before.png'});
 const button=page.locator('[data-bulk-submit="approve_selected"]');await button.click();
 await page.waitForLoadState('domcontentloaded');
 await page.screenshot({path:OUT+'/bulk-after.png'});
 return{rows,errors,failures,bulk:{submitted:true,head:first.head,url:page.url(),alerts:await page.locator('.messagelist,.alert').allTextContents()},browser:page.context().browser().version()};
}
