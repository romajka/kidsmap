const H=require('./helpers.cjs');
const {fillPlace}=require('./create.cjs');const {save}=require('./pricing.cjs');
async function guidance(ctx){
 for(const role of ['admin','owner']){
  const c=await H.context(ctx.browser,ctx.fixture.origin,390);
  try{
   const p=await H.login(c,ctx.fixture,role);p.on('dialog',dialog=>dialog.accept());
   await p.goto(ctx.fixture.origin+(role==='admin'?'/admin/catalog/place/add/?type=permanent':'/ru/account/places/create/?type=permanent&fresh=1'));
   if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   const checked=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/preview/'));
   await p.locator('[data-km-check]').click();const rejected=await checked;H.assert.equal(rejected.status(),422);
   const summary=p.locator('[data-km-errors]');await summary.waitFor({state:'visible'});
   H.assert(await summary.locator('li').count()>0);H.assert(await p.locator('.km-editor-invalid').count()>0);
   H.assert.equal(await summary.evaluate(node=>getComputedStyle(node).animationName),'none','Reduced motion is respected');
   await p.emulateMedia({reducedMotion:'no-preference'});H.assert.equal(await summary.evaluate(node=>getComputedStyle(node).animationName),'km-editor-reveal','Normal motion uses the short reveal animation');await p.emulateMedia({reducedMotion:'reduce'});
   await H.inspect(p,ctx.out,`guidance-empty-${role}`);
   await summary.getByRole('button').filter({hasText:/назван/i}).first().click();
   H.assert.equal(await p.evaluate(()=>document.activeElement?.name),'name_az');
   if(role==='admin'){
    await p.locator('[data-place-accordion-collapse-all]').click();await summary.getByRole('button').filter({hasText:/телефон/i}).first().click();
    H.assert(await p.locator('#id_phone1').isVisible(),'Error navigation reveals its collapsed section');H.assert.equal(await p.evaluate(()=>document.activeElement?.id),'id_phone1');
    await p.locator('[data-place-accordion-expand-all]').click();
   }
   ctx.record({id:'UX_REQUIRED',role,status:'PASS',assertions:['read-only completeness check','422 field errors','red linked fields','click summary focuses actual input','reduced motion','390px error layout fits']});
   const name=`Place guided ${role} ${Date.now()}`;await fillPlace(p,role,name);
   const phone=p.locator('#id_phone1');const valid=await phone.inputValue();await phone.focus();await phone.press('End');
   for(const value of ['abc','Я','Ə','O','++','@','<script>','\n+994551234567']){
    await p.keyboard.insertText(value);H.assert.equal(await phone.inputValue(),valid,`Rejected input preserves digits: ${value}`);
    H.assert(await p.locator('.km-editor-field-error').filter({hasText:/цифр|телефон/i}).first().isVisible());
    ctx.record({id:'UX_PHONE_REJECT',role,status:'PASS',input:value,assertions:['trusted browser insertion rejected','original number retained','visible explanation']});
   }
   await H.fill(p,'#id_phone1','(050) 123-45-67');H.assert.equal(await phone.inputValue(),'(050) 123-45-67');
   await H.select(p,'#id_whatsapp_mode','separate');await H.fill(p,'#id_whatsapp_number','');await p.locator('#id_whatsapp_number').pressSequentially('https://wa.me/13104564918');
   H.assert.equal(await p.locator('#id_whatsapp_number').inputValue(),'https://wa.me/13104564918');await H.select(p,'#id_whatsapp_mode','none');
   ctx.record({id:'UX_WA_LINK',role,status:'PASS',assertions:['valid wa.me URL can be typed one character at a time','optional separate WhatsApp can be hidden without clearing']});
   const title=p.locator('#id_name_az'),limit=Number(await title.getAttribute('maxlength'));
   await title.fill('A'.repeat(limit+1));H.assert.equal((await title.inputValue()).length,limit,'Native maximum clips extra typed character');await title.fill(name);
   const description=p.locator('#id_description_az');
   const text='Ə ə Ş ş İ ı. Привет. Hello 🙂\nİkinci sətir\n'+('ДлинныйТекст'.repeat(250));await description.fill(text);
   H.assert.equal(await description.inputValue(),text);
   const field=description.locator('xpath=ancestor::*[@data-pw-field or @data-pf-field][1]');H.assert((await field.locator('[data-km-counter]').innerText()).startsWith(String(Array.from(text).length)+' '));H.assert.doesNotMatch(await field.locator('[data-km-counter]').innerText(),/строк/);
   await description.scrollIntoViewIfNeeded();await H.inspect(p,ctx.out,`guidance-long-text-${role}`);
   ctx.record({id:'UX_TEXT',role,status:'PASS',assertions:['maximum title boundary','AZ/RU/EN/emoji retained','live character count without misleading line count','long unbroken text stays inside textarea','no horizontal document overflow']});
   const picker=p.locator('[data-place-photos-picker]');await picker.setInputFiles(ctx.fixture.images.slice(0,2).map(path=>H.path.join(ctx.fixtureDir,path)));
   if(role==='owner')await p.waitForFunction(()=>document.querySelector('#id_photo').files.length===1&&document.querySelector('#id_gallery_images').files.length===1&&!document.querySelector('[data-state="queued"],[data-state="preparing"]'));
   await p.locator('[data-km-check]').click();await p.locator('[data-km-check-status][data-state=ready]').waitFor({state:'visible'});
   H.assert(!(await summary.isVisible()));
   ctx.record({id:'UX_READY',role,status:'PASS',assertions:['complete current multipart form passes read-only check','errors clear','ready state is explicit']});
   await H.select(p,'#id_whatsapp_mode','separate');await H.fill(p,'#id_whatsapp_number','12');await H.select(p,'#id_whatsapp_mode','none');
   await p.locator('[data-km-check]').click();await p.locator('[data-pw-field=whatsapp_number] .km-editor-field-error,[data-pf-field=whatsapp_number] .km-editor-field-error').waitFor({state:'visible'});
   await summary.getByRole('button').filter({hasText:'WhatsApp'}).first().click();H.assert.equal(await p.evaluate(()=>document.activeElement?.name),'whatsapp_number');
   await H.fill(p,'#id_whatsapp_number','');H.assert(!(await p.locator('#id_whatsapp_number').isVisible()));
   await p.locator('[data-km-check]').click();await p.locator('[data-km-check-status][data-state=ready]').waitFor({state:'visible'});
   ctx.record({id:'UX_HIDDEN_CONTACT',role,status:'PASS',assertions:['invalid hidden WhatsApp reveals its field','summary focuses that number','correction hides an unused contact again','latest form passes check']});
   await H.fill(p,'[data-tariff-key=price]','-1');
   await p.locator(role==='admin'?'[name=_save_draft]':'[name=form_action][value=save_draft]').first().click();
   await summary.waitFor({state:'visible'});H.assert.equal(await p.locator('[data-tariff-key=price]').getAttribute('aria-invalid'),'true');
   if(role==='admin')H.assert.notEqual(await p.locator('[data-pf-savestate]').first().getAttribute('data-state'),'saving','A client rejection never leaves the admin saving state stuck');
   await H.fill(p,'[data-tariff-key=price]','120');
   await p.locator('[data-price-kind=range]').click();await H.fill(p,'[data-tariff-key=price_min]','100');await H.fill(p,'[data-tariff-key=price_max]','1');
   await p.locator('[data-km-check]').click();await p.locator('.owner-tariff-field--price_max.km-editor-invalid').waitFor({state:'visible'});
   H.assert(!(await summary.innerText()).includes('price_max'),'Technical field key is replaced with its visible label');
   await summary.getByRole('button').first().click();H.assert.equal(await p.evaluate(()=>document.activeElement?.dataset.tariffKey),'price_max');
   await H.fill(p,'[data-tariff-key=price_max]','150');await p.locator('[data-price-kind=exact]').click();await H.fill(p,'[data-tariff-key=price]','120');
   await p.locator('[data-km-check]').click();await p.locator('[data-km-check-status][data-state=ready]').waitFor({state:'visible'});
   ctx.record({id:'UX_PRICE_ERRORS',role,status:'PASS',assertions:['negative amount blocked before save','no stuck saving state','server inverted-range error highlights actual maximum input','summary focuses maximum amount','human field label','correction passes check']});
   const entries=await title.inputValue();
   const filesBefore=await p.locator('form[data-km-editor] input[type=file][name]').evaluateAll(inputs=>inputs.map(input=>({name:input.name,files:[...input.files].map(file=>({name:file.name,size:file.size}))})));
   const opened=c.waitForEvent('page');await p.locator('[data-km-preview]').click();const preview=await opened;
   await preview.waitForLoadState('networkidle');H.assert(preview.url().includes('/preview/'));
   H.assert((await preview.locator('body').innerText()).includes(entries));H.assert(await preview.locator('.site-preview-bar').isVisible());
   H.assert((await preview.locator('img[src^="data:image/"]').evaluateAll(images=>[...new Set(images.map(image=>image.src))])).length>=2,'Both distinct current uploaded images are visible in full preview');
   H.assert(await preview.locator('img[src^="data:image/"]').evaluateAll(images=>images.every(image=>image.complete&&image.naturalWidth>0)),'Preview images actually decode and load');
   H.assert(await preview.evaluate(()=>window.opener===null),'New private preview has no window opener');
   H.assert.equal(await preview.locator('meta[name=robots]').getAttribute('content'),'noindex,nofollow');
   await H.inspect(preview,ctx.out,`guidance-full-preview-${role}`);
   const closing=preview.waitForEvent('close');
   try{await preview.locator('[data-site-preview-close]').click();}catch(error){
    // Firefox can acknowledge window.close before the click command returns.
    if(!preview.isClosed()||!String(error).includes('Target page, context or browser has been closed'))throw error;
   }
   await closing;H.assert(!p.isClosed(),'Returning from preview keeps the original editor open');
   H.assert.equal(await title.inputValue(),entries);H.assert.equal(await description.inputValue(),text);
   H.assert.deepEqual(await p.locator('form[data-km-editor] input[type=file][name]').evaluateAll(inputs=>inputs.map(input=>({name:input.name,files:[...input.files].map(file=>({name:file.name,size:file.size}))}))),filesBefore,'Preview retains both actual form upload fields');
   H.assert.equal(filesBefore.reduce((sum,input)=>sum+input.files.length,0),2);
   ctx.record({id:'UX_PREVIEW',role,status:'PASS',assertions:['actual new tab and private POST URL','full public template with current text','both unsaved photos displayed','noindex','original form and files retained']});
   await save(p,role);H.assert.equal(await p.locator('#id_name_az').inputValue(),name);H.assert.equal(await p.locator('#id_description_az').inputValue(),text);
   await H.fill(p,'#id_name_az',name+' edited');await save(p,role);H.assert.equal(await p.locator('#id_name_az').inputValue(),name+' edited');
   ctx.record({id:'UX_EDIT',role,status:'PASS',assertions:['save same form after preview','reopen retains long text and photos','second real edit saves without stale token']});
   // A failed check has a retry and never discards the current form.
   if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   const route=/(?:\/account\/places\/(?:\d+\/)?preview\/|\/admin\/editor\/places\/(?:\d+\/)?preview\/)/;await c.route(route,r=>r.abort('failed'));
   await p.locator('[data-km-check]').click();await p.locator('[data-km-check-status][data-state=error]').waitFor({state:'visible'});
   H.assert.equal(await p.locator('#id_name_az').inputValue(),name+' edited');H.assert(await p.locator('[data-km-check]').isEnabled());
   await c.unroute(route);await p.locator('[data-km-check]').click();await p.locator('[data-km-check-status][data-state=ready]').waitFor({state:'visible'});
   ctx.record({id:'UX_RETRY',role,status:'PASS',assertions:['check network failure is explained','input retained','button recovers','retry succeeds']});
   let release,seen;const waiting=new Promise(resolve=>seen=resolve),hold=new Promise(resolve=>release=resolve);
   await c.route(route,async intercepted=>{seen();await hold;await intercepted.continue();});
   await p.locator('[data-km-check]').click();await waiting;await H.fill(p,'#id_name_az',name+' race');release();
   await p.locator('[data-km-check-status][data-state=changed]').waitFor({state:'visible'});await c.unroute(route);
   H.assert.equal(await p.locator('[data-km-check-status][data-state=ready]').count(),0,'An old response cannot approve newer input');
   await H.fill(p,'#id_name_az',name+' edited');await p.locator('[data-km-check]').click();await p.locator('[data-km-check-status][data-state=ready]').waitFor({state:'visible'});
   ctx.record({id:'UX_CHECK_RACE',role,status:'PASS',assertions:['editing during an in-flight check invalidates its result','no false ready message','retry checks the latest values']});
  }catch(error){const p=c.pages().at(-1);if(p){await p.screenshot({path:H.path.join(ctx.out,`failure-guidance-${role}.png`),fullPage:true});H.fs.writeFileSync(H.path.join(ctx.out,`failure-guidance-${role}.txt`),await p.locator('body').innerText());}ctx.record({id:'guidance',role,status:'FAIL',error:String(error)});throw error;}finally{await c.close();}
 }
}
module.exports={guidance};
