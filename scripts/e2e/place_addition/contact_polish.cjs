/* Synthetic localhost acceptance for contacts, responsive edges and staff dialogs. */
const H=require('./helpers.cjs'),crypto=require('node:crypto');
const fixture=JSON.parse(H.fs.readFileSync(process.argv[2],'utf8'));
const out=H.path.resolve(process.argv[3]||'.tmp/place-contact-polish-20261025/browser');
H.fs.mkdirSync(out,{recursive:true});
const results=[];
function record(row){results.push(row);H.fs.writeFileSync(H.path.join(out,'results.json'),JSON.stringify({synthetic:true,externalMaps:'NOT RUN: all off-origin requests blocked; no API key',sources:fixture.sources,results},null,2));console.log(row.status,row.id,row.role||'',row.lang||'',row.width||'');}
function sourceGuard(){H.assert(fixture.synthetic&&fixture.database==='qa_stage04');for(const [name,digest]of Object.entries(fixture.sources))H.assert.equal(crypto.createHash('sha256').update(H.fs.readFileSync(name)).digest('hex'),digest,`Frozen source ${name}`);}
const prefix=lang=>lang==='az'?'':lang+'/';
async function checked(name,meta,p,fn){try{record({id:name,...meta,status:'PASS',...await fn()});}catch(error){await p.screenshot({path:H.path.join(out,`FAIL-${name}-${meta.role}-${meta.lang}-${meta.width}.png`)}).catch(()=>{});record({id:name,...meta,status:'FAIL',error:String(error),url:p.url()});}}
function watch(page){const errors=[],assets=[],native=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.url().startsWith(fixture.origin)&&r.status()>=400&&['script','stylesheet','image','font'].includes(r.request().resourceType()))assets.push({url:r.url(),status:r.status()});});page.on('dialog',async d=>{if(d.type()==='beforeunload')await d.accept();else{native.push({type:d.type(),message:d.message()});await d.dismiss();}});return{errors,assets,native};}
async function fresh(page,role,lang){await page.goto(fixture.origin+(role==='owner'?`/${prefix(lang)}account/places/create/?type=permanent&fresh=1`:role==='admin'?'/admin/catalog/place/add/?type=permanent':'/admin/volunteer/add/'));await page.waitForSelector('[data-km-phone-list],#id_phone1');if(role==='owner')await page.waitForFunction(()=>!!window.KidsMapOwnerWorkflow);else await page.waitForFunction(()=>!!document.querySelector('#place_form,[data-volunteer-admin-form]')?.kmDraftSave);}
async function expand(page,role){const button=page.locator(role==='admin'?'[data-place-accordion-expand-all]':'[data-editor-expand]');if(await button.count())await button.click();}
async function contactControls(page,meta){
  const phone=page.locator('#id_phone1'),group=page.locator(meta.role==='owner'?'[data-km-phone-list]':'[data-km-phone-editor]');await H.reveal(phone);await phone.fill('+994501234567');
  if(await group.count()){
  const add=group.locator('[data-km-phone-add]');await add.focus();await add.press('Enter');
  H.assert.equal(await page.evaluate(()=>document.activeElement?.name),'phone2','Keyboard add focuses second phone');await page.locator('#id_phone2').fill('+994502345678');
  await add.click();await page.locator('#id_phone3').fill('+994503456789');H.assert(!await add.isVisible()||await add.isDisabled(),'At most three phone fields');
  await page.locator('#id_phone2').locator('xpath=ancestor::*[@data-km-phone-slot or @data-km-phone-row][1]').locator('[data-km-phone-remove]').click();
  H.assert.equal(await page.locator('#id_phone3').inputValue(),'+994503456789','Removing phone2 preserves phone3');H.assert.equal(await phone.inputValue(),'+994501234567');
  await add.click();H.assert.equal(await page.locator('#id_phone2').inputValue(),'');await page.locator('#id_phone2').fill('+994504567890');
  }else{for(const [name,value]of [['phone2','+994504567890'],['phone3','+994503456789']])await H.fill(page,'#id_'+name,value);H.assert.equal(await page.locator('#id_phone3').inputValue(),'+994503456789');}
  await H.select(page,'#id_whatsapp_mode','separate');await H.fill(page,'#id_whatsapp_number','+905321234567');
  await H.select(page,'#id_whatsapp_mode','none');H.assert.equal(await page.locator('#id_whatsapp_number').inputValue(),'+905321234567');await H.select(page,'#id_whatsapp_mode','separate');H.assert(await page.locator('#id_whatsapp_number').isVisible());
  const website=page.locator('#id_website');await H.reveal(website);await website.fill('https://example.invalid/contact-polish');
  const details=website.locator('xpath=ancestor::details[1]');
  if(await details.count()){await details.locator(':scope > summary').click();H.assert(!await website.isVisible());await details.locator(':scope > summary').focus();await details.locator(':scope > summary').press('Enter');H.assert(await website.isVisible());}
  else H.assert(await website.isVisible(),'Owner social fields are intentionally always visible');
  H.assert.equal(await website.inputValue(),'https://example.invalid/contact-polish');
  let whatsappMetrics=null;if(meta.role==='admin'&&meta.width>=1024){whatsappMetrics=await page.evaluate(()=>{const box=id=>{const r=document.getElementById(id).getBoundingClientRect();return{x:r.x,y:r.y,bottom:r.bottom,width:r.width};};const mode=document.getElementById('id_whatsapp_mode'),visibleMode=mode.closest('.km-pf-field')?.getBoundingClientRect();return{phone:box('id_phone1'),lastPhone:box('id_phone3'),number:box('id_whatsapp_number'),mode:visibleMode?{x:visibleMode.x,y:visibleMode.y,bottom:visibleMode.bottom,width:visibleMode.width}:box('id_whatsapp_mode')};});H.assert(whatsappMetrics.number.x>whatsappMetrics.phone.x+100,'Separate WhatsApp stays in right column');H.assert(Math.abs(whatsappMetrics.number.x-whatsappMetrics.mode.x)<4,'WhatsApp number aligned below mode');H.assert(whatsappMetrics.number.y<whatsappMetrics.lastPhone.bottom,'WhatsApp does not wait for entire three-phone column');}
  let disclosureMetrics=null;const socials=page.locator('.km-pf-contact-socials');if(await socials.count()){disclosureMetrics=await socials.evaluate(el=>{const b=el.getBoundingClientRect(),p=el.parentElement.getBoundingClientRect(),s=el.querySelector('summary').getBoundingClientRect();return{width:b.width,parentWidth:p.width,summaryHeight:s.height};});H.assert(Math.abs(disclosureMetrics.width-disclosureMetrics.parentWidth)<2,'Admin socials span full contact grid');H.assert(disclosureMetrics.summaryHeight>=44,'Social disclosure tap area');}
  await H.inspect(page,out,`contacts-filled-${meta.role}-${meta.lang}-${meta.width}`);
  return{socialDisclosure:!!await details.count(),disclosureMetrics,whatsappMetrics,phoneControls:await group.count()?'dynamic max3':'volunteer three native fields',assertions:[...(await group.count()?['keyboard add focuses new phone','max three phones','remove preserves other values']:['three native volunteer phone fields retain values']),'international WhatsApp preserved across modes','social value retention; keyboard disclosure when present']};
}
async function realSocialError(page,meta){
  const website=page.locator('#id_website');await H.reveal(website);await website.fill('http://');
  const details=website.locator('xpath=ancestor::details[1]');if(await details.count())await details.locator(':scope > summary').click();
  const check=page.locator('[data-km-check]');await H.reveal(check);await check.click();
  await page.waitForFunction(()=>document.querySelector('#id_website')?.getAttribute('aria-invalid')==='true');
  H.assert(await website.isVisible(),'Actual invalid website is revealed');H.assert.equal(await website.inputValue(),'http://','Invalid value is retained for correction');
  await H.inspect(page,out,`contacts-errors-${meta.lang}-${meta.width}`);await website.fill('https://example.invalid/contact-polish');
  return{assertions:['real validation request, no injected UI','actual social error is visible; ancestor disclosure opens if present','invalid user input preserved']};
}
async function scheduleModal(page,meta){
  const regular=page.locator('#id_schedule_mode');if(await regular.count())await H.select(page,'#id_schedule_mode','regular');
  const preset=page.locator('[data-km-schedule-preset=weekdays]').first(),clear=page.locator('[data-km-schedule-preset=clear]').first();await H.reveal(preset);await preset.click();
  const value=()=>page.locator('[name=structured_schedule]').inputValue();const before=await value();H.assert(before.includes('09:00'),'Actual preset populated schedule');
  for(const close of ['cancel','escape']){
    await clear.click();const modal=page.locator('.km-modal:visible');await modal.waitFor();
    H.assert(await modal.evaluate(el=>{const r=el.getBoundingClientRect();return [0.2,0.5,0.8].every(x=>[0.2,0.5,0.8].every(y=>el.contains(document.elementFromPoint(r.x+r.width*x,r.y+r.height*y))));}),'Modal is visually above page/sticky layers');
    await H.inspect(page,out,`schedule-modal-${close}-${meta.role}-${meta.lang}-${meta.width}`);
    if(close==='escape')await page.keyboard.press('Escape');else await modal.locator('.km-modal__actions button').first().click();
    await page.locator('.km-modal-backdrop').waitFor({state:'detached'});H.assert.equal(await value(),before,'Cancel/Escape preserve exact schedule');H.assert(await clear.evaluate(el=>document.activeElement===el),'Focus returns to clear trigger');
  }
  await clear.click();await page.locator('.km-modal:visible .km-modal__actions button').last().click();await page.locator('.km-modal-backdrop').waitFor({state:'detached'});
  H.assert.notEqual(await value(),before,'Confirmed clear changes schedule');const empty=JSON.parse(await value());H.assert(!JSON.stringify(empty).includes('09:00'),'Confirmed clear removed preset intervals');
  H.assert(await clear.evaluate(el=>document.activeElement===el));
  return{assertions:['custom modal rendered above all layers','cancel and Escape preserve exact JSON','focus restored','confirm clears schedule']};
}
async function eventsPricing(page,meta){
  await page.locator('[data-price-policy=tariffs]').click();const plans=page.locator('[name=pricing_plans]');
  if(!JSON.parse(await plans.inputValue()).length){await page.locator('[data-tariff-add]').click();await H.select(page,'[data-tariff-key=editor_kind]','lesson');await H.fill(page,'[data-tariff-key=price]','42');}
  const badge=page.locator('[name=custom_price_badge_az]');H.assert.equal(await badge.count(),1);await H.reveal(badge);await badge.fill('QA xüsusi qiymət');
  const before=JSON.parse(await plans.inputValue());
  for(const mode of ['events','free','free_entry_paid_services','tariffs','events']){
    await page.locator(`[data-price-policy=${mode}]`).click();H.assert.deepEqual(JSON.parse(await plans.inputValue()),before,`Mode ${mode} retains full tariff objects`);H.assert.equal(await badge.inputValue(),'QA xüsusi qiymət');
  }
  const state=page.locator('[data-tariff-events-state]:visible');H.assert.equal(await state.count(),1,'Exactly one event pricing notice');
  const phrase=(await state.locator('[data-price-events-title]').innerText()).trim();H.assert(phrase.length>10);const duplicate=await page.locator('[data-tariff-editor]').evaluate((root,text)=>[...root.querySelectorAll('*')].filter(n=>!n.children.length&&!n.closest('button,select,option')&&n.getClientRects().length&&n.textContent.trim()===text).length,phrase);H.assert.equal(duplicate,1,'No duplicate plain event-pricing state');
  await state.scrollIntoViewIfNeeded();await H.inspect(page,out,`events-pricing-${meta.role}-${meta.lang}-${meta.width}`);
  await page.locator('[data-price-policy=tariffs]').click();H.assert.deepEqual(JSON.parse(await plans.inputValue()),before);
  return{tariffs:before.length,assertions:['exactly one notice','mode switching preserves full tariff JSON and custom badge']};
}
(async()=>{
  sourceGuard();H.assert.deepEqual((await(await fetch(fixture.origin+'/__qa__/build/')).json()).sources,fixture.sources);
  const browser=await H.launch();
  try{
    for(const lang of (process.env.CONTACT_POLISH_STAFF_ONLY?[]:['az','ru','en'])){
      const context=await H.context(browser,fixture.origin,1440);try{const page=await H.login(context,fixture,'owner',lang),observed=watch(page);
        for(const width of [320,360,390,768,1024,1280,1440]){const meta={role:'owner',lang,width};await page.setViewportSize({width,height:1000});await fresh(page,'owner',lang);
          await checked('OWNER_LAYOUT',meta,page,async()=>{
            const metrics=await page.evaluate(()=>{const box=sel=>{const r=document.querySelector(sel).getBoundingClientRect();return{x:r.x,right:r.right,width:r.width,top:r.top,bottom:r.bottom,height:r.height};};return{header:box('.km-header-inner'),candidate:box('.pc-candidate'),workspace:box('.pc-workspace'),phones:box('.pc-contacts'),socials:box('.pc-socials')};});
            if(width>=1024)for(const name of ['candidate','workspace']){H.assert(Math.abs(metrics[name].x-metrics.header.x)<=2,`${name} left aligns header`);H.assert(Math.abs(metrics[name].right-metrics.header.right)<=2,`${name} right aligns header`);}
            const contactHeight=metrics.socials.bottom-metrics.phones.top;if(width>=1024)H.assert(contactHeight<(width===1024?650:600),`Default contact block ${contactHeight}px, baseline783px`);
            await H.inspect(page,out,`owner-layout-${lang}-${width}`);await page.locator('.pc-contacts').scrollIntoViewIfNeeded();await H.inspect(page,out,`owner-contacts-${lang}-${width}`);return{metrics,contactHeight,baseline:783};
          });
          if([390,1440].includes(width)){await checked('CONTACT_VALUES',meta,page,()=>contactControls(page,meta));await checked('SOCIAL_ERROR_REVEAL',meta,page,()=>realSocialError(page,meta));}
        }
        record({id:'OWNER_RUNTIME',role:'owner',lang,status:observed.errors.length||observed.assets.length||observed.native.length?'FAIL':'PASS',...observed});
      }finally{await context.close();}}
    for(const role of (process.env.CONTACT_POLISH_OWNER_ONLY?[]:['admin','volunteer']))for(const lang of ['az','ru','en']){
      const context=await H.context(browser,fixture.origin,1440);try{await context.addCookies([{name:'django_language',value:lang,url:fixture.origin}]);const page=await H.login(context,fixture,role,lang),observed=watch(page);
        for(const width of [390,1440]){const meta={role,lang,width};await page.setViewportSize({width,height:1000});await fresh(page,role,lang);await expand(page,role);
          await checked('STAFF_CONTACTS',meta,page,()=>contactControls(page,meta));
          await checked('SCHEDULE_MODAL',meta,page,()=>scheduleModal(page,meta));
          await checked('EVENTS_PRICING',meta,page,()=>eventsPricing(page,meta));
        }
        record({id:'STAFF_RUNTIME',role,lang,status:observed.errors.length||observed.assets.length||observed.native.length?'FAIL':'PASS',...observed});
      }finally{await context.close();}}
    sourceGuard();record({id:'FINAL_SOURCE_ATTESTATION',status:'PASS',browser:browser.version()});
  }finally{await browser.close();}
  if(results.some(row=>row.status==='FAIL'))process.exitCode=1;
})().catch(error=>{record({id:'HARNESS',status:'FAIL',error:String(error)});console.error(error);process.exitCode=1;});
