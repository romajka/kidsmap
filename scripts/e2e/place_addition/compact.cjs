const H=require('./helpers.cjs');
const {save}=require('./pricing.cjs');
const canonical=value=>value.replace(/[^+\d]/g,'');

async function legacyCurrency(ctx,role){
 const c=await H.context(ctx.browser,ctx.fixture.origin);
 try{const p=await H.login(c,ctx.fixture,role);
  for(const currency of ['USD','EUR']){
   const f=ctx.fixture.editor_fixtures[role][currency];
   await p.goto(ctx.fixture.origin+(role==='admin'?`/admin/catalog/place/${f.id}/change/`:`/ru/account/places/${f.id}/edit/`));await p.waitForLoadState('networkidle');
   if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   H.assert.equal(await p.locator('select[data-tariff-key=currency]').count(),0);
   H.assert.equal(await p.locator('[data-money-currency]').first().innerText(),currency);
   const startingCountry=await p.locator('#id_phone_country').inputValue();H.assert(['US','AZ'].includes(startingCountry),'Owned fixture retains its original US context or a prior explicit AZ edit');
   const before=JSON.parse(await p.locator('[name=pricing_plans]').inputValue());
   await H.fill(p,'#id_phone1','050 123 45 67');H.assert.equal(await p.locator('#id_phone_country').inputValue(),'AZ','Trusted local entry resets hidden input context');
   await save(p,role);
   H.assert.equal(canonical(await p.locator('#id_phone1').inputValue()),'+994501234567');
   H.assert.equal(canonical(await p.locator('#id_whatsapp_number').inputValue()),'+905321234567');
   H.assert.deepEqual(JSON.parse(await p.locator('[name=pricing_plans]').inputValue()),before,'Contact edit preserves every saved tariff value and ID');
   ctx.record({id:'COMPACT_FX',role,status:'PASS',currency,placeId:f.id,startingCountry,assertions:['foreign currency visible at amount','no currency dropdown','local AZ phone with hidden input context','international WhatsApp retained','full tariff object unchanged after real save']});
  }
 }finally{await c.close();}
}
async function publicPhones(ctx,place,whatsapp,calling=true){
 const c=await H.context(ctx.browser,ctx.fixture.origin);
 try{const p=await c.newPage();H.assert.equal((await p.goto(place.publicUrl)).status(),200);
  const token=(await c.cookies()).find(cookie=>cookie.name==='csrftoken');H.assert(token,'Actual public CSRF cookie');
  const r=await c.request.post(ctx.fixture.origin+`/api/places/${place.id}/phones/`,{headers:{'X-CSRFToken':token.value},data:{}});H.assert.equal(r.status(),200);
  const contacts=await r.json();H.assert.equal(contacts.whatsapp,whatsapp?'https://wa.me/13104564918':'');
  if(calling)H.assert(contacts.phones.some(phone=>phone.number==='+994501234567'),'Public calling phone remains AZ');
  else H.assert.deepEqual(contacts.phones,[],'WhatsApp-only place has no invented calling number');
  return contacts;
 }finally{await c.close();}
}
async function updatePublished(ctx,item,phone,mode){
 const c=await H.context(ctx.browser,ctx.fixture.origin);
 try{const p=await H.login(c,ctx.fixture,item.role);await p.goto(item.editUrl);await p.waitForLoadState('networkidle');
  if(item.role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
  await H.fill(p,'#id_phone1',phone);await H.select(p,'#id_whatsapp_mode',mode);await save(p,item.role);
 }finally{await c.close();}
}
async function approveExisting(ctx,item){
 const c=await H.context(ctx.browser,ctx.fixture.origin);
 try{const p=await H.login(c,ctx.fixture,'admin');const id=item.editUrl.match(/\/(\d+)\/(?:edit|change)\//)[1];
  await p.goto(ctx.fixture.origin+`/admin/catalog/place/${id}/change/`);await p.locator('[data-place-accordion-expand-all]').click();
  const loaded=p.waitForEvent('domcontentloaded');await p.locator('[name=_continue]').first().click();await loaded;await p.waitForLoadState('networkidle');
  H.assert(!(await p.locator('body').innerText()).includes('Проверьте подсвеченные поля формы.'));
  H.assert.equal((await p.goto(ctx.fixture.origin+`/admin/volunteer/review/${id}/`)).status(),200);
  const approve=p.locator('[name=action][value=approve]');H.assert(await approve.isEnabled(),'Existing published-place revision is ready for staff approval');
  await Promise.all([p.waitForURL(url=>url.pathname==='/admin/volunteer/review/'),approve.click()]);
 }finally{await c.close();}
}
async function compact(ctx){
 for(const role of (ctx.roles || ['admin','owner'])){
  const item=await require('./create.cjs').create({...ctx,intake:async(p,actualRole,name)=>{
   if(actualRole==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   const openAge=p.locator(actualRole==='admin'?'#id_age_open_ended':'[data-pc-open-age]');
   // Age choices now live beside the range. Check the visible, operable
   // control rather than requiring the former feature-disclosure markup.
   await H.reveal(openAge);
   const ageControl=actualRole==='admin'?openAge:openAge.locator('xpath=ancestor::label[1]');
   H.assert(await ageControl.isVisible(),'The age choice is visible in the age section');
   const wasChecked=await openAge.isChecked();await ageControl.click();H.assert.equal(await openAge.isChecked(),!wasChecked);
   await ageControl.click();H.assert.equal(await openAge.isChecked(),wasChecked);
   if(actualRole==='admin'){
    const settings=p.locator('[data-compact-settings]');H.assert.equal(await settings.getAttribute('open'),null);
    await settings.locator('summary').click();H.assert(await p.locator('#id_status').isVisible());
    await settings.locator('summary').click();
   }
   await require('./create.cjs').fillPlace(p,actualRole,name);
   H.assert.equal(await p.locator('#id_phone_country').getAttribute('type'),'hidden');
   H.assert.equal(await p.locator('[name=price_mode]').count(),1);
   H.assert.equal(await p.locator('[data-price-policy]').count(),4);
   H.assert.equal(await p.locator('#id_whatsapp_mode').inputValue(),'none','New place does not presume WhatsApp');
   H.assert.equal(await p.locator('select[data-tariff-key=currency]').count(),0);
   H.assert.equal(await p.locator('[data-money-currency]').first().innerText(),'₼');
   await H.fill(p,'#id_phone1','(050) 123-45-67');
   await H.select(p,'#id_whatsapp_mode','separate');await H.fill(p,'#id_whatsapp_number','+1 (310) 456-4918');
  }},role);
  const c=await H.context(ctx.browser,ctx.fixture.origin);
  try{const p=await H.login(c,ctx.fixture,role);await p.goto(item.editUrl);await p.waitForLoadState('networkidle');
   H.assert.equal(canonical(await p.locator('#id_phone1').inputValue()),'+994501234567');H.assert.equal(canonical(await p.locator('#id_whatsapp_number').inputValue()),'+13104564918');
   if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   for(const mode of ['same','none','separate']){
    await H.select(p,'#id_whatsapp_mode',mode);await save(p,role);
    H.assert.equal(await p.locator('#id_whatsapp_mode').inputValue(),mode);
    H.assert.equal(canonical(await p.locator('#id_whatsapp_number').inputValue()),'+13104564918');
    if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   }
   const name=await p.locator('#id_name_az').inputValue();await H.fill(p,'#id_phone1','12');
   const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(role==='owner'?'/save-photos/':'/change/'));
   await p.locator(role==='admin'?'[name=_save_draft]':'[name=form_action][value=save_draft]').first().click();const r=await response;H.assert([200,422].includes(r.status()));
   const errors=p.locator(role==='admin'?'[data-pf-field=phone1] .km-editor-field-error':'[data-pc-errors]');await errors.filter({hasText:/./}).first().waitFor({state:'visible'});
   H.assert(!(await errors.allInnerTexts()).join(' ').toLowerCase().includes('выберите страну'),'Validation does not refer to a removed country chooser');
   if(role==='owner'){H.assert.equal(await p.locator('#id_phone1').getAttribute('aria-invalid'),'true');await errors.getByRole('button').filter({hasText:'Телефон'}).first().click();H.assert.equal(await p.evaluate(()=>document.activeElement?.id),'id_phone1');}
   H.assert.equal(await p.locator('#id_name_az').inputValue(),name);await H.fill(p,'#id_phone1','+994 50 123 45 67');await save(p,role);
   await H.inspect(p,ctx.out,`compact-saved-${role}`);
   ctx.record({id:'COMPACT_CONTACT',role,status:'PASS',assertions:['hidden country','AZN currency suffix','one price mode control','explicit initial WhatsApp choice','AZ local phone and US WhatsApp saved','all WhatsApp modes preserve numbers','invalid phone rejected and corrected without loss']});
  }catch(error){const p=c.pages().at(-1);if(p){await p.screenshot({path:H.path.join(ctx.out,`failure-compact-${role}.png`),fullPage:true});H.fs.writeFileSync(H.path.join(ctx.out,`failure-compact-${role}.txt`),await p.locator('body').innerText());}ctx.record({id:'COMPACT_CONTACT',role,status:'FAIL',error:String(error)});throw error;}finally{await c.close();}
  if(role==='owner')await require('./publication.cjs').sendForReview(ctx,item);
  const place=await require('./publication.cjs').publish(ctx,item);await publicPhones(ctx,place,true);
  ctx.record({id:'COMPACT_PUBLIC',role,status:'PASS',placeId:place.id,assertions:['actual publication','public calling number and WhatsApp stay distinct','real protected contact endpoint and CSRF']});
  await updatePublished(ctx,item,'','separate');
  if(role==='owner'){await publicPhones(ctx,place,true);await require('./publication.cjs').sendForReview(ctx,item);}
  await approveExisting(ctx,item);await publicPhones(ctx,place,true,false);
  ctx.record({id:'COMPACT_WHATSAPP_ONLY',role,status:'PASS',placeId:place.id,assertions:['same published place supports only international WhatsApp','owner approved contact remains public until review','approved update removes calling number without inventing one']});
  await updatePublished(ctx,item,'+994 50 123 45 67','none');
  if(role==='owner'){await publicPhones(ctx,place,true,false);await require('./publication.cjs').sendForReview(ctx,item);}
  await approveExisting(ctx,item);await publicPhones(ctx,place,false);
  ctx.record({id:'COMPACT_NO_WHATSAPP',role,status:'PASS',placeId:place.id,assertions:['explicit no-WhatsApp choice survives publication','public phone retained','no WhatsApp fallback after approved update']});
  await legacyCurrency(ctx,role);
 }
}
module.exports={compact};
