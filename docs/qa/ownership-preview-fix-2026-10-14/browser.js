async (original) => {
  const base=__BASE__, fixtures=__FIXTURES__, folder=__FOLDER__;
  const rows=[], errors=[], network=[]; let phase='login';
  const context=await original.context().browser().newContext({viewport:{width:1440,height:1000}});
  await context.route('**/*', r=>r.request().url().startsWith(base)?r.continue():r.fulfill({status:200,body:'',contentType:r.request().resourceType()==='stylesheet'?'text/css':'text/plain'}));
  const p=await context.newPage();p.setDefaultTimeout(15000);
  p.on('pageerror',e=>errors.push(e.message));
  p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)network.push({url:r.url().split('?')[0],status:r.status()});});
  function check(id, ok, detail) { rows.push({id,status:ok?'PASS':'FAIL',detail});if(!ok)throw Error(id); }
  async function language(lang) {await context.addCookies([{name:'django_language',value:lang,url:base}]);}
  try {
    await language('ru');await p.goto(base+'/admin/login/?next=/admin/');
    await p.locator('[name=username]').fill(fixtures.admin_username);
    await p.locator('[name=password]').fill(__PASSWORD__);
    await Promise.all([p.waitForURL(u=>!u.pathname.includes('login')),p.locator('[type=submit]').click()]);
    phase='list-entry';await p.goto(base+'/admin/catalog/placeownershiprequest/?status__exact=PENDING');
    const review=p.getByRole('link',{name:'Проверить карточку',exact:true});
    check('list-protected-preview-link',await review.count()===1);
    await review.click();await p.waitForURL(/\/preview\//);
    check('list-opens-preview',(await p.locator('#km-inspection').count())===1);
    check('return-keeps-filter',(await p.locator('.km-inspection-back').first().getAttribute('href')).includes('status__exact=PENDING'));
    check('submitted-description-visible',(await p.locator('#preview-about').innerText()).includes('Отправленное уточнение'));
    await p.screenshot({path:folder+'/overview-ru-1440.png'});
    phase='content';await p.locator('[data-preview-expand]').click();
    check('all-tariff-details-expand',await p.locator('[data-preview-details]:not([open])').count()===0);
    for(const text of ['+994502223344','+994503334455','Группа 6–10 лет','Неактивный тариф','Преподаватель фикстуры','09:00–18:00']) {
      check('complete-'+text,(await p.locator('#km-inspection').innerText()).includes(text));
    }
    check('all-photos-render',await p.locator('[data-preview-photo]').count()===5);
    await p.locator('a[href="#preview-photos"]').click();
    await p.locator('#preview-photos img').first().waitFor({state:'visible'});
    check('all-thumbnails-loaded',await p.locator('#preview-photos img').evaluateAll(async images=>{
      await Promise.all(images.map(img=>img.decode()));return images.every(img=>img.naturalWidth===1200);
    }));
    await p.screenshot({path:folder+'/photos-ru-1440.png'});
    phase='gallery';const opener=p.locator('[data-preview-photo]').first();await opener.click();
    const dialog=p.locator('[data-preview-dialog]');
    check('gallery-opens',await dialog.isVisible());
    check('gallery-image-loaded',await p.locator('[data-preview-dialog-image]').evaluate(async img=>{if(!img.complete)await new Promise(r=>img.addEventListener('load',r,{once:true}));return img.naturalWidth===1200;}));
    await p.keyboard.press('ArrowRight');check('gallery-keyboard-next',(await p.locator('[data-preview-dialog-count]').innerText())==='2 / 5');
    for(let i=0;i<8;i++){await p.keyboard.press('Tab');check('gallery-focus-trapped-'+i,await dialog.evaluate(d=>d.contains(document.activeElement)));}
    await p.screenshot({path:folder+'/gallery-ru-1440.png'});
    await p.keyboard.press('Escape');check('gallery-escape-closes',!(await dialog.isVisible()));
    check('gallery-restores-focus',await opener.evaluate(e=>e===document.activeElement));
    phase='version';await p.locator('.km-inspection-versions a').nth(1).click();
    check('current-does-not-show-candidate',!(await p.locator('#preview-about').innerText()).includes('Отправленное уточнение'));
    check('current-cannot-approve-other-version',await p.locator('.km-inspection-actions a[href*="/approve/"]').count()===0);
    await p.locator('.km-inspection-versions a').first().click();
    check('submitted-restored',(await p.locator('#preview-about').innerText()).includes('Отправленное уточнение'));
    phase='request-form';await p.getByRole('link',{name:'Открыть заявку',exact:true}).click();
    await p.waitForURL(/\/change\//);
    check('request-summary-visible',(await p.locator('.form-group.field-place_completion_summary').innerText()).includes('Пространство для творчества и спорта'));
    await p.getByRole('link',{name:'Проверить карточку',exact:true}).click();
    await p.waitForURL(/\/preview\//);await p.locator('#km-inspection').waitFor({state:'visible'});
    check('request-returns-to-inspection',await p.locator('#km-inspection').count()===1);
    phase='decision';check('publication-action-correct',await p.getByRole('link',{name:'Одобрить и опубликовать',exact:true}).count()===1);
    await p.getByRole('link',{name:'Одобрить и опубликовать',exact:true}).click();
    await p.waitForURL(/\/approve\//);
    await p.locator('.km-inspection-confirm-actions [type=submit]').waitFor({state:'visible'});
    check('decision-requires-confirmation',await p.locator('.km-inspection-confirm-actions [type=submit]').count()===1);
    await p.getByRole('link',{name:'Отмена',exact:true}).click();
    await p.waitForURL(/\/preview\//);
    await p.locator('#km-inspection').waitFor({state:'visible'});
    check('cancel-returns-to-inspection',await p.locator('#km-inspection').count()===1);
    phase='responsive';
    const headings={ru:'О карточке',az:'Kart haqqında',en:'About the card'};
    for(const lang of ['ru','az','en']) for(const width of [360,390,768,1024,1280,1440]) {
      await language(lang);await p.setViewportSize({width,height:1000});
      await p.goto(base+'/admin/catalog/placeownershiprequest/'+fixtures.request+'/preview/');
      check(lang+'-'+width+'-localized-heading',await p.getByRole('heading',{name:headings[lang],exact:true}).count()===1);
      if(lang!=='ru')check(lang+'-'+width+'-localized-field-labels',!(await p.locator('#km-inspection dt').allTextContents()).some(label=>/[А-Яа-яЁё]/.test(label)));
      check(lang+'-'+width+'-current-language',await p.locator('[data-preview-filter="'+lang+'"]').getAttribute('aria-pressed')==='true');
      check(lang+'-'+width+'-no-document-overflow',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      await p.locator('[data-preview-filter=all]').click();
      check(lang+'-'+width+'-all-translations',await p.locator('[data-preview-language][hidden]').count()===0);
      await p.locator('[data-preview-filter="'+lang+'"]').click();
      check(lang+'-'+width+'-language-filter',await p.locator('[data-preview-language]:not([hidden])').evaluateAll(els=>els.every(e=>e.getAttribute('data-preview-language')===document.documentElement.lang.split('-')[0])));
      if([390,1440].includes(width))await p.screenshot({path:folder+'/overview-'+lang+'-'+width+'.png'});
      for(const target of ['#preview-schedule','#preview-prices','#preview-offers','#preview-request']) {
        await p.locator('.km-inspection-sections a[href="'+target+'"]').click();
        const box=await p.locator(target+' h2').first().boundingBox();
        check(lang+'-'+width+'-'+target+'-reachable',box.y>=0&&box.y<1000,box);
        if(lang==='ru'&&[390,1440].includes(width)&&['#preview-prices','#preview-offers'].includes(target))await p.screenshot({path:folder+'/'+target.slice(9)+'-ru-'+width+'.png'});
      }
      if(lang==='ru'&&width===390){await p.locator('.km-inspection-sections a[href="#preview-photos"]').click();await p.locator('[data-preview-photo]').first().click();await p.locator('[data-preview-dialog-image]').evaluate(img=>img.decode());await p.screenshot({path:folder+'/gallery-ru-390.png'});await p.keyboard.press('Escape');}
    }
    return {phase:'complete',browser:original.context().browser().version(),rows,errors,network};
  } catch(e) {await p.screenshot({path:folder+'/failure.png'});return {phase,url:p.url(),error:String(e),rows,errors,network};}
  finally {await context.close();}
}
