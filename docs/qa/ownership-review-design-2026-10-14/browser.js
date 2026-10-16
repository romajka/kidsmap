async (original) => {
 const base=__BASE__,fixtures=__FIXTURES__,folder=__FOLDER__;
 const rows=[],errors=[],network=[],writes=[];
 const check=(id,ok)=>{rows.push({id,status:ok?'PASS':'FAIL'});if(!ok)throw Error(id);};
 const context=await original.context().browser().newContext({viewport:{width:1440,height:1000}});
 await context.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.fulfill({status:200,body:'',contentType:r.request().resourceType()==='stylesheet'?'text/css':'text/plain'}));
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)network.push({url:r.url().split('?')[0],status:r.status()});});
 const inspection=base+'/admin/catalog/placeownershiprequest/'+fixtures.request+'/preview/';
 try {
  await context.addCookies([{name:'django_language',value:'ru',url:base}]);
  await page.goto(base+'/admin/login/?next=/admin/');await page.locator('[name=username]').fill(fixtures.admin_username);await page.locator('[name=password]').fill(__PASSWORD__);
  await Promise.all([page.waitForURL(u=>!u.pathname.includes('login')),page.locator('[type=submit]').click()]);
  page.on('request',r=>{if(r.url().startsWith(base)&&!['GET','HEAD','OPTIONS'].includes(r.method()))writes.push(r.method()+' '+r.url().split('?')[0]);});
  for(const lang of ['ru','az','en'])for(const width of [390,768,1024,1440]){
   const id=lang+'-'+width;
   await context.addCookies([{name:'django_language',value:lang,url:base}]);await page.setViewportSize({width,height:1000});await page.goto(inspection);
   await page.locator('.km-inspection-stats').waitFor();
   if(width>=768&&await page.evaluate(()=>document.body.classList.contains('sidebar-collapse')))await page.locator('[data-widget=pushmenu]').click();
   await page.waitForTimeout(550);
   check(id+'-four-metrics',await page.locator('.km-inspection-stat').count()===4);
   check(id+'-no-overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   check(id+'-icons-resolve',await page.locator('.km-inspection use').evaluateAll(nodes=>nodes.every(n=>document.querySelector(n.getAttribute('href'))?.querySelector('path'))));
   check(id+'-language-filter-default',await page.locator('[data-preview-filter='+lang+']').getAttribute('aria-pressed')==='true');
   const translated={ru:'Сводка карточки',az:'Kartın xülasəsi',en:'Card summary'};
   check(id+'-translated-summary',await page.locator('.km-inspection-stats').getAttribute('aria-label')===translated[lang]);
   check(id+'-real-readiness-value',await page.locator('progress').evaluate(e=>e.value>=0&&e.value<=e.max));
   await page.screenshot({path:folder+'/review-'+lang+'-'+width+'.png'});
   await page.locator('.km-inspection-sections a[href="#preview-photos"]').click();await page.waitForTimeout(550);
   check(id+'-section-focus',await page.locator('#preview-photos').evaluate(e=>document.activeElement===e));
   if(width===1440)check(id+'-section-unobscured',await page.evaluate(()=>document.querySelector('#preview-photos').getBoundingClientRect().top>=document.querySelector('.km-inspection-sections').getBoundingClientRect().bottom));
   await page.locator('[data-preview-filter=all]').click();check(id+'-all-languages-visible',await page.locator('#preview-about [data-preview-language]:visible').count()===6);
  }
  await context.addCookies([{name:'django_language',value:'ru',url:base}]);await page.setViewportSize({width:1440,height:1000});await page.goto(inspection);
  const details=page.locator('[data-preview-details]');await page.locator('[data-preview-expand]').click();check('expand-all',await details.evaluateAll(nodes=>nodes.every(n=>n.open)));
  await page.locator('[data-preview-expand]').click();check('collapse-all',await details.evaluateAll(nodes=>nodes.every(n=>!n.open)));
  const firstPhoto=page.locator('[data-preview-photo]').first();await firstPhoto.click();check('photo-dialog-open',await page.locator('[data-preview-dialog]').evaluate(e=>e.open));
  await page.keyboard.press('ArrowRight');check('photo-next',await page.locator('[data-preview-dialog-count]').innerText()==='2 / 5');await page.keyboard.press('Escape');check('photo-focus-restored',await firstPhoto.evaluate(e=>document.activeElement===e));
  await page.getByRole('link',{name:'Текущее состояние',exact:true}).click();await page.waitForURL(/version=current/);check('current-version-no-diff',await page.locator('.km-inspection-changes').count()===0);
  await page.getByRole('link',{name:'Отправлено на проверку',exact:true}).click();await page.waitForURL(u=>!u.searchParams.has('version'));await page.locator('.km-inspection-changes').waitFor();check('submitted-version-diff',await page.locator('.km-inspection-changes').count()===1);
  check('no-identical-scalar-diffs',await page.locator('.km-inspection-diff-row').evaluateAll(nodes=>nodes.every(e=>{const a=e.querySelector('.km-inspection-diff-before'),b=e.querySelector('.km-inspection-diff-after');return !a||!b||a.querySelector('p').textContent!==b.querySelector('p').textContent;})));
  await page.locator('.km-inspection-changes').evaluate(e=>e.open=true);await page.locator('.km-inspection-changes').scrollIntoViewIfNeeded();await page.screenshot({path:folder+'/review-changes.png'});
  await page.getByRole('link',{name:'Превью на сайте',exact:true}).click();await page.waitForURL(/site-preview/);check('actual-website-preview',await page.locator('.site-preview-bar').isVisible());
  await page.goto(inspection);await page.emulateMedia({reducedMotion:'reduce'});check('reduced-motion',await page.locator('.km-inspection-gallery img').first().evaluate(e=>getComputedStyle(e).transitionDuration==='0s'));
  await page.locator('.km-inspection h1').evaluate(e=>e.textContent='Очень длинное название карточки '.repeat(16));check('long-title-no-overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  check('no-review-writes',writes.length===0);return {phase:'complete',checks:rows.length,rows,errors,network,writes};
 }catch(error){await page.screenshot({path:folder+'/failure.png'});return {phase:'failed',error:String(error),overflow:await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,items:[...document.querySelectorAll('body *')].map(e=>({tag:e.tagName,cls:e.className,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})).filter(e=>e.right>innerWidth+1&&e.width>0).slice(0,20)})),rows,errors,network,writes};}
 finally{await context.close();}
}
