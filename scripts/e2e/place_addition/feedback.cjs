const H=require('./helpers.cjs');
const prefix=language=>language==='az'?'':language+'/';
function feedbackWatch(p,origin){
 const errors=[],unexpected=[],pending=[];let expectedChecks=0;
 p.on('pageerror',error=>errors.push(error.message));
 p.on('response',response=>{if(!response.url().startsWith(origin)||response.status()<400)return;
  pending.push((async()=>{const request=response.request(),data=request.postData()||'',url=new URL(response.url());
   const checkOnly=/name="_km_check_required"\r?\n\r?\n1(?:\r?\n|$)/.test(data)||new URLSearchParams(data).get('_km_check_required')==='1';
   if(response.status()===422&&request.method()==='POST'&&/\/account\/places\/(?:\d+\/)?preview\/$/.test(url.pathname)&&checkOnly){
    try{const payload=await response.json(),r=payload.readiness;
     if(payload.errors&&typeof payload.errors==='object'&&!Array.isArray(payload.errors)&&Object.keys(payload.errors).length&&r&&r.is_ready===false&&Array.isArray(r.items)&&Array.isArray(r.sections)&&Number.isInteger(r.required_count)&&Number.isInteger(r.completed_count)&&r.completed_count>=0&&r.completed_count<=r.required_count){expectedChecks++;return;}
    }catch{}
   }
   unexpected.push({url:response.url(),status:response.status(),method:request.method(),checkOnly});
  })());
 });
 return {errors,async verify(){await Promise.all(pending);H.assert.deepEqual(unexpected,[],'Only contracted incomplete check-only 422 responses are expected');return expectedChecks;}};
}
async function feedback(ctx){
 for(const language of ['az','ru','en'])for(const width of [320,360,390,768,1024,1280,1440]){
  const c=await H.context(ctx.browser,ctx.fixture.origin,width);
  try{const p=await H.login(c,ctx.fixture,'owner',language),w=feedbackWatch(p,ctx.fixture.origin);
   await p.goto(ctx.fixture.origin+`/${prefix(language)}account/places/create/?type=permanent&fresh=1`);
   const description='Əla Bakı! Привет 🙂\nFriendly description';
   await p.locator('[name=name_az]').fill('KidsMap description test');await p.locator('[name=description_az]').fill(description);
   H.assert((await p.locator('[data-pw-field=description_az] [data-km-counter]').innerText()).startsWith(String(Array.from(description).length)+' '));
   H.assert.equal(await p.locator('[data-pw-field=description_az]').getAttribute('data-km-required'),'true');
   H.assert.equal(await p.locator('[data-pw-field=instagram]').getAttribute('data-km-required'),'false');
   H.assert.equal(await p.locator('[data-pw-required=structured_schedule]').isVisible(),true);
   await p.locator('.pc-help-button').click();H.assert(await p.locator('#pc-translation-help').isVisible());await p.keyboard.press('Escape');H.assert(!await p.locator('#pc-translation-help').isVisible());
   await p.locator('[name=description_az]').scrollIntoViewIfNeeded();await H.inspect(p,ctx.out,`feedback-description-${language}-${width}`);
   H.assert.equal(await p.locator('[data-km-phone-slot]:visible').count(),0);await p.locator('[data-km-phone-add]').click();await p.locator('[name=phone2]').fill('+994501234567');await p.locator('[data-km-phone-add]').click();await p.locator('[name=phone3]').fill('+13104564918');H.assert(await p.locator('[data-km-phone-add]').isDisabled());
   await p.locator('[data-km-phone-slot]').first().locator('[data-km-phone-remove]').click();H.assert.equal(await p.locator('[name=phone2]').inputValue(),'');H.assert.equal((await p.locator('[name=phone3]').inputValue()).replace(/[^+0-9]/g,''),'+13104564918');await p.locator('[data-km-phone-add]').click();await p.locator('[name=phone2]').fill('+994551234567');
   await p.locator('[name=whatsapp_mode]').selectOption('separate');await p.locator('[name=whatsapp_number]').fill('+442079460018');
   await p.locator('[data-public-links-add]').click();await p.locator('[data-public-link-key=label]').fill('Telegram');await p.locator('[data-public-link-key=url]').fill('https://t.me/kidsmap_test');await p.locator('[name=whatsapp_mode]').scrollIntoViewIfNeeded();await H.inspect(p,ctx.out,`feedback-contacts-${language}-${width}`);
   H.assert.equal(await p.locator('script[src*="leaflet"]').count(),0);H.assert.equal(await p.locator('.leaflet-tile').count(),0);
   const presets=p.locator('[data-km-schedule-preset]');H.assert.equal(await presets.count(),5);
   for(const code of ['weekdays','all-days','weekday-weekend','always-open','clear']){
    const scheduleBefore=await p.locator('[name=structured_schedule]').inputValue();
    await p.locator(`[data-km-schedule-preset="${code}"]`).click();
    if(code==='clear'){
     const modal=p.locator('.km-modal-backdrop');await modal.waitFor({state:'visible'});H.assert.equal(await p.locator('[name=structured_schedule]').inputValue(),scheduleBefore);
     await modal.locator('.km-btn-modal--secondary').click();await modal.waitFor({state:'detached'});H.assert.equal(await p.locator('[name=structured_schedule]').inputValue(),scheduleBefore);
     await p.locator('[data-km-schedule-preset=clear]').click();await modal.waitFor({state:'visible'});await H.inspect(p,ctx.out,`feedback-schedule-confirm-${language}-${width}`);await modal.locator('.km-btn-modal--danger').click();await modal.waitFor({state:'detached'});
    }
    const days=JSON.parse(await p.locator('[name=structured_schedule]').inputValue());
    H.assert.equal(days.length,7);if(code==='weekdays'){H.assert(days.slice(0,5).every(day=>!day.is_closed&&day.intervals[0].start==='09:00'));H.assert(days.slice(5).every(day=>day.is_closed));}
    if(code==='all-days')H.assert(days.every(day=>!day.is_closed&&day.intervals[0].end==='21:00'));
    if(code==='weekday-weekend')H.assert(days.slice(5).every(day=>day.intervals[0].start==='10:00'));
    if(code==='always-open')H.assert(days.every(day=>!day.is_closed&&day.is_24_hours));
    if(code==='clear')H.assert(days.every(day=>day.is_closed&&!day.is_24_hours&&day.intervals.length===0));
   }
   await p.locator('.km-schedule-editor__presets-panel').scrollIntoViewIfNeeded();await H.inspect(p,ctx.out,`feedback-schedule-${language}-${width}`);
   for(const button of await presets.all()){const rect=await button.boundingBox();H.assert(rect&&rect.height>=43,'Schedule presets remain touch-sized');}
   await p.locator('[data-tariff-add]').click();await H.select(p,'[data-tariff-key=editor_kind]','package');await H.fill(p,'[data-tariff-key=quantity]','8');await H.fill(p,'[data-tariff-key=price]','80');
   const previous=JSON.parse(await p.locator('[name=pricing_plans]').inputValue());await p.locator('[data-price-policy=free_entry_paid_services]').click();
   H.assert.deepEqual(JSON.parse(await p.locator('[name=pricing_plans]').inputValue()),previous);H.assert.equal(await p.locator('[data-tariff-heading]').innerText(),{ru:'Платные услуги',az:'Ödənişli xidmətlər',en:'Paid services'}[language]);
   const advanced=p.locator('.owner-tariff-advanced');await advanced.locator('summary').click();
   H.assert(await advanced.evaluate(el=>{const grid=el.querySelector('.owner-tariff-grid'),s=getComputedStyle(grid),arrow=getComputedStyle(el.querySelector('summary'),'::after');return parseFloat(s.paddingLeft)>=16&&parseFloat(s.paddingRight)>=16&&parseFloat(s.rowGap)>=20&&arrow.content!=='none'&&arrow.display!=='none'&&parseFloat(arrow.width)>=10;}),'Advanced terms have real padding, gaps and a visible chevron');
   await advanced.locator('summary').scrollIntoViewIfNeeded();await H.inspect(p,ctx.out,`feedback-tariff-${language}-${width}`);
   await p.locator('[data-price-policy=free]').click();H.assert(!await p.locator('[data-tariff-heading]').isVisible());await p.locator('[data-price-policy=tariffs]').click();H.assert.deepEqual(JSON.parse(await p.locator('[name=pricing_plans]').inputValue()),previous);
   H.assert.deepEqual(w.errors,[]);const expectedChecks=await w.verify();ctx.record({id:'FEEDBACK_OWNER',role:'owner',lang:language,width,status:'PASS',expectedIncompleteChecks:expectedChecks,assertions:['live description count','recommended help popover and Escape','required vs optional markers','three phone slots and removal without shifting','international WhatsApp','named Telegram link','no silent OSM fallback','five working schedule presets','paid services preserve price payload','visible disclosure chevron and measured advanced spacing','check-only 422 validated against grouped readiness contract']});
  }finally{await c.close();}
 }
 for(const role of ['admin','volunteer'])for(const language of ['az','ru','en'])for(const width of [390,1440]){
  const c=await H.context(ctx.browser,ctx.fixture.origin,width);try{const p=await H.login(c,ctx.fixture,role);await c.addCookies([{name:'django_language',value:language,url:ctx.fixture.origin}]);const w=H.watch(p,ctx.fixture.origin);
   if(role==='admin'){await p.goto(ctx.fixture.origin+'/admin/catalog/place/add/?type=permanent');await p.locator('[data-place-accordion-expand-all]').click();}
   else{await p.goto(ctx.fixture.origin+'/admin/volunteer/add/');await p.locator('[data-editor-expand]').click();}
   await H.fill(p,'#id_description_az','Əla Привет 🙂');H.assert((await p.locator('[data-km-counter]').allTextContents()).some(text=>text.startsWith('12 ')));
   await p.locator('[data-tariff-add]').click();await H.select(p,'[data-tariff-key=editor_kind]','lesson');await H.fill(p,'[data-tariff-key=price]','30');await p.locator('[data-price-policy=free_entry_paid_services]').click();H.assert.equal(await p.locator('[data-tariff-heading]').innerText(),{ru:'Платные услуги',az:'Ödənişli xidmətlər',en:'Paid services'}[language]);
   await p.locator('.owner-tariff-advanced summary').click();await p.locator('.owner-tariff-advanced summary').scrollIntoViewIfNeeded();await H.inspect(p,ctx.out,`feedback-${role}-${language}-${width}`);H.assert.deepEqual(w.errors,[]);ctx.record({id:'FEEDBACK_STAFF',role,lang:language,width,status:'PASS'});
  }finally{await c.close();}
 }
 const item=await require('./create.cjs').create({...ctx,intake:async(p,role,name)=>{await require('./create.cjs').fillPlace(p,role,name);await p.locator('[data-km-phone-add]').click();await p.locator('[name=phone2]').fill('+994551234567');await p.locator('[data-km-phone-add]').click();await p.locator('[name=phone3]').fill('+13104564918');await p.locator('[name=whatsapp_mode]').selectOption('separate');await p.locator('[name=whatsapp_number]').fill('+442079460018');await p.locator('[data-price-policy=free_entry_paid_services]').click();await p.locator('[data-public-links-add]').click();await p.locator('[data-public-link-key=label]').fill('Telegram');await p.locator('[data-public-link-key=url]').fill('https://t.me/kidsmap_test');}},'owner');
 const c=await H.context(ctx.browser,ctx.fixture.origin);try{const p=await H.login(c,ctx.fixture,'owner');await p.goto(item.editUrl);H.assert.equal((await p.locator('[name=phone2]').inputValue()).replace(/[^+0-9]/g,''),'+994551234567');H.assert.equal((await p.locator('[name=phone3]').inputValue()).replace(/[^+0-9]/g,''),'+13104564918');H.assert.equal(await p.locator('[data-km-phone-slot]:visible').count(),2);H.assert.equal(await p.locator('[name=price_mode]').inputValue(),'free_entry_paid_services');H.assert((await p.locator('[data-pw-field=description_az] [data-km-counter]').innerText()).startsWith(String(Array.from(await p.locator('[name=description_az]').inputValue()).length)+' '));
  const popup=c.waitForEvent('page');await p.locator('[data-km-preview]').click();const preview=await popup;await preview.waitForLoadState('networkidle');H.assert.equal(await preview.locator('[data-place-public-link][href="https://t.me/kidsmap_test"]').count(),1);await preview.close();
 }finally{await c.close();}
 await require('./publication.cjs').sendForReview(ctx,item);
 const admin=await H.context(ctx.browser,ctx.fixture.origin);try{const p=await H.login(admin,ctx.fixture,'admin'),id=item.editUrl.match(/places\/(\d+)/)[1];await p.goto(ctx.fixture.origin+`/admin/volunteer/moderation/?place=${id}`);await p.locator('a[href*="/moderation/content/"]').filter({hasText:item.name}).first().click();const hub=p.url(),preview=await p.locator('[data-moderation-full-preview]').getAttribute('href');await p.goto(ctx.fixture.origin+preview);H.assert((await p.locator('body').innerText()).includes('https://t.me/kidsmap_test'));await p.goto(hub);await p.locator('[name=reason]').fill('Три телефона, WhatsApp и платные услуги проверены.');const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.request().isNavigationRequest());await p.locator('button[name=action][value=approve]').click();H.assert((await response).status()<400);
  await p.goto(ctx.fixture.origin+'/ru/catalog/?q='+encodeURIComponent(item.name));const href=await p.locator(`a[href*="/place/${id}-"]`).first().getAttribute('href');await p.goto(new URL(href,ctx.fixture.origin).href);H.assert.equal(await p.locator('[data-place-public-link][href="https://t.me/kidsmap_test"]').count(),1);ctx.record({id:'FEEDBACK_LIFECYCLE',role:'owner/admin',status:'PASS',placeId:id,assertions:['save and reopen all three phones and international WhatsApp','counter reflects restored description','private preview retains Telegram link','full moderation inspection','approval and public catalog/detail']});
 }finally{await admin.close();}
}
module.exports={feedback};
