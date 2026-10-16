async (original) => {
  const base=__BASE__, fixtures=__FIXTURES__, folder=__FOLDER__;
  const rows=[], errors=[], network=[], writes=[];let phase='login';
  const context=await original.context().browser().newContext({viewport:{width:1440,height:1000}});
  await context.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.fulfill({status:200,body:'',contentType:r.request().resourceType()==='stylesheet'?'text/css':'text/plain'}));
  const p=await context.newPage();p.setDefaultTimeout(15000);
  p.on('pageerror',e=>errors.push(e.message));
  p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  p.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)network.push({url:r.url().split('?')[0],status:r.status()});});
  p.on('request',r=>{if(phase!=='login'&&r.method()!=='GET')writes.push({path:new URL(r.url()).pathname,method:r.method()});});
  const check=(id,ok,detail)=>{rows.push({id,status:ok?'PASS':'FAIL',detail});if(!ok)throw Error(id);};
  try {
    await context.addCookies([{name:'django_language',value:'ru',url:base}]);
    await p.goto(base+'/admin/login/?next=/admin/');
    await p.locator('[name=username]').fill(fixtures.admin_username);
    await p.locator('[name=password]').fill(__PASSWORD__);
    await Promise.all([p.waitForURL(u=>!u.pathname.includes('login')),p.locator('[type=submit]').click()]);
    phase='entry';await p.goto(base+'/admin/catalog/placeownershiprequest/?status__exact=PENDING');
    check('list-preview-button',await p.getByRole('link',{name:'Превью на сайте',exact:true}).count()===1);
    await p.getByRole('link',{name:'Проверить карточку',exact:true}).click();await p.waitForURL(/\/preview\//);
    await p.locator('.km-inspection-header').waitFor({state:'visible'});
    await p.screenshot({path:folder+'/admin-button-ru-1440.png',animations:'disabled'});
    await p.getByRole('link',{name:'Превью на сайте',exact:true}).click();await p.waitForURL(/\/site-preview\//);
    await p.locator('.detail-title').waitFor({state:'visible'});
    check('real-public-template',await p.locator('#km-site-header').count()===1&&await p.locator('.detail-hero').count()===1);
    check('no-admin-sidebar',await p.locator('.main-sidebar').count()===0);
    check('submitted-text-visible',(await p.locator('.detail-prose').first().innerText()).includes('Отправленное уточнение'));
    check('private-return-keeps-filter',(await p.locator('.site-preview-return').getAttribute('href')).includes('status__exact%3DPENDING'));
    check('noindex',await p.locator('meta[name=robots]').getAttribute('content')==='noindex,nofollow');
    phase='interaction';await p.locator('[data-place-gallery-main] img.place-gallery__image').first().evaluate(img=>img.decode());
    await p.locator('[data-place-gallery-next]').click();
    await p.waitForFunction(()=>document.querySelector('[data-place-gallery-current]').textContent==='2');
    check('real-gallery-next',(await p.locator('[data-place-gallery-current]').innerText())==='2');
    await p.locator('[data-place-gallery-prev]').click();
    await p.waitForFunction(()=>document.querySelector('[data-place-gallery-current]').textContent==='1');
    check('real-gallery-back',(await p.locator('[data-place-gallery-current]').innerText())==='1');
    await p.locator('[data-phone-reveal]:not([data-phone-whatsapp])').first().click();
    await p.locator('.detail-hero .km-phone-number').first().waitFor({state:'visible'});
    check('phone-reveals-locally',await p.locator('.detail-hero a[href^="tel:"]').count()>0);
    await p.locator('.detail-fav-btn').first().click();
    check('favorite-preview-only',await p.locator('.detail-fav-btn').first().getAttribute('aria-pressed')==='true');
    check('preview-feedback-visible',await p.locator('[data-site-preview-feedback]').isVisible());
    const activity=p.getByRole('link',{name:'Рисование и творческое мышление',exact:true});
    check('pending-child-link-is-safe',await activity.getAttribute('href')==='');
    const previewLocation=p.url();await activity.click();
    check('pending-child-does-not-open-public-404',p.url()===previewLocation);
    phase='matrix';
    const titles={ru:'Центр творчества и спорта — полная карточка',az:'Yaradıcılıq və idman mərkəzi',en:'Creative and Sports Centre'};
    for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]) {
      await p.setViewportSize({width,height:1000});
      await p.goto(base+'/admin/catalog/placeownershiprequest/'+fixtures.request+'/site-preview/?lang='+lang);
      await p.locator('.detail-title').waitFor({state:'visible'});
      await p.locator('.place-gallery__image').first().evaluate(image=>image.decode());
      check(lang+'-'+width+'-localized-content',(await p.locator('.detail-title').innerText())===titles[lang]);
      check(lang+'-'+width+'-language-attribute',await p.locator('html').getAttribute('lang')===lang);
      check(lang+'-'+width+'-active-language',await p.locator('.site-preview-bar nav a[aria-current]').innerText()===lang.toUpperCase());
      check(lang+'-'+width+'-no-overflow',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      const layout=await p.evaluate(()=>({scroll:scrollY,toolbar:document.querySelector('.site-preview-bar').getBoundingClientRect().top,header:document.querySelector('#km-site-header').getBoundingClientRect().bottom,margin:getComputedStyle(document.querySelector('.site-preview-bar')).marginTop}));
      check(lang+'-'+width+'-toolbar-not-covered',layout.toolbar>=layout.header,layout);
      check(lang+'-'+width+'-gallery-in-viewport',await p.locator('[data-place-gallery]').evaluate(el=>el.getBoundingClientRect().right<=innerWidth));
      check(lang+'-'+width+'-public-contact-controls',await p.locator('.detail-hero [data-phone-reveal]').count()>0);
      if([390,1440].includes(width))await p.screenshot({path:folder+'/site-'+lang+'-'+width+'.png',animations:'disabled'});
      if(lang==='ru'&&[390,1440].includes(width)){
        await p.locator('.public-offerings').first().scrollIntoViewIfNeeded();
        await p.screenshot({path:folder+'/groups-ru-'+width+'.png',animations:'disabled'});
      }
    }
    phase='return';await p.locator('.site-preview-bar nav a').filter({hasText:'RU'}).click();
    await p.waitForURL(/lang=ru/);check('language-link-stays-preview',p.url().includes('/site-preview/'));
    await p.locator('.site-preview-return').click();await p.waitForURL(/\/preview\//);
    await p.locator('.km-inspection-versions a').nth(1).click();
    await p.getByRole('link',{name:'Превью на сайте',exact:true}).click();await p.waitForURL(/\/site-preview\//);
    await p.locator('.detail-prose').first().waitFor({state:'visible'});
    check('current-version-is-not-submitted',!(await p.locator('.detail-prose').first().innerText()).includes('Отправленное уточнение'));
    check('no-write-requests',writes.length===0,writes);
    return {phase:'complete',browser:original.context().browser().version(),rows,errors,network,writes};
  }catch(error){await p.screenshot({path:folder+'/failure.png'});return {phase,error:String(error),url:p.url(),rows,errors,network,writes};}
  finally {await context.close();}
}
