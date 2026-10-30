const H=require('./helpers.cjs');
async function addTariff(p,kind='monthly'){
 await p.locator('[data-tariff-add]').click();
 await H.select(p,'[data-tariff-key=editor_kind]',kind);
 if(kind==='monthly'||kind==='package')await H.fill(p,'[data-tariff-key=quantity]','12');
 await H.fill(p,'[data-tariff-key=price]','120');
}
async function fillPlace(p,role,name){
 if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
 await H.fill(p,'#id_name_az',name);
 await H.fill(p,'#id_description_az','Bu, yalnız yerli sınaq üçün hazırlanmış məkanın təsviridir. Uşaqlar üçün dərslər və ailələr üçün ziyarət imkanları haqqında sintetik məlumat.');
 await H.select(p,'#id_category','EDU');
 const sub=p.locator('#id_subcategory');
 await p.waitForFunction(()=>document.querySelector('#id_subcategory')?.options.length>1);
 const option=await sub.locator('option').evaluateAll(es=>es.find(e=>e.value)?.value);
 await H.select(p,'#id_subcategory',option);
 await H.select(p,'#id_region','baku');
 await H.select(p,'#id_district','baku_yasamal');
 // Every creation is a separate fictional business; shared contacts and the
 // same address would correctly trigger the production duplicate guard.
 await H.fill(p,'#id_address',`Bakı, Yerli QA küçəsi, ${name}`);
 await H.fill(p,'#id_phone1','+994501112233');
 if(role==='admin'){
  await H.fill(p,'#id_age_from','6');await H.fill(p,'#id_age_to','12');
 }else{
  const from=p.locator('#id_age_from_range');await from.focus();await from.press('Home');for(let i=0;i<6;i++)await from.press('ArrowRight');
  const to=p.locator('#id_age_to_range');await to.focus();await to.press('End');for(let i=0;i<6;i++)await to.press('ArrowLeft');
 }
 await H.select(p,'#id_schedule_mode','by_appointment');
 if(role==='admin'){
  await p.locator('[data-km-place-location-toggle]').click();
 }
 await H.fill(p,'#id_lat','40.4093');await H.fill(p,'#id_lng','49.8671');
 await addTariff(p);
}
async function create(Hctx,role,lang='ru',width=1440){
 const {browser,fixture,out,record}=Hctx,c=await H.context(browser,fixture.origin,width);
 try{
  const p=await H.login(c,fixture,role,lang),watch=H.watch(p,fixture.origin);
  const url=role==='admin'?'/admin/catalog/place/add/?type=permanent':`/${lang==='az'?'':lang+'/'}account/places/create/?type=permanent&fresh=1`;
  if(role==='admin')await c.addCookies([{name:'django_language',value:lang,url:fixture.origin}]);
  await p.goto(fixture.origin+url);
  const name=`Place E2E ${role} ${lang} ${Date.now()}`;
  if(Hctx.intake)await Hctx.intake(p,role,name);else await fillPlace(p,role,name);
  const picker=p.locator('[data-place-photos-picker]');H.assert.equal(await picker.getAttribute('data-mounted'),'1','Unified picker mounted');
  await picker.setInputFiles(fixture.images.slice(0,2).map(image=>H.path.join(Hctx.fixtureDir,image)));
  if(role==='owner')await p.waitForFunction(()=>{const e=document.querySelector('[data-photo-editor]');return e&&e.querySelectorAll('[data-photo-id]').length>=2&&!e.querySelector('[data-state="error"],[data-state="queued"],[data-state="preparing"]')&&document.querySelector('#id_photo').files.length===1&&document.querySelector('#id_gallery_images').files.length===1;},{},{timeout:30000});
  await H.inspect(p,out,`filled-${role}-${lang}-${width}`);
  const button=p.locator(role==='admin'?'[name=_save_draft]':'[name=form_action][value=save_draft]').first();
  await button.click();
  await p.waitForURL(url=>role==='admin'?/\/place\/\d+\/change\//.test(url.pathname):/\/places\/(\d+\/edit\/)?$/.test(url.pathname),{timeout:30000});
  if(role==='owner'&&!/\/places\/\d+\/edit\//.test(new URL(p.url()).pathname)){
   const link=p.locator('a[href*="/edit/"]').filter({hasText:name});
   if(await link.count())await link.first().click();
   else {const card=p.getByText(name,{exact:true}).first();await card.locator('xpath=ancestor::*[self::article or self::div[contains(@class,"card")]][1]').locator('a[href*="/edit/"]').first().click();}
  }
  await p.waitForSelector('#id_name_az');
  H.assert.equal(await p.locator('#id_name_az').inputValue(),name);
  const saved=JSON.parse(await p.locator('[name=pricing_plans]').inputValue());H.assert.equal(saved[0].currency,'AZN');H.assert.equal(saved[0].billing_interval,'month');
  await H.inspect(p,out,`saved-${role}-${lang}-${width}`);
  record({id:role==='admin'?'A01':'A03',role,lang,width,status:'PASS',url:p.url(),name,assertions:['real text input','canonical monthly tariff','actual two-file upload','server draft save','reopen retained values']});
  return {role,lang,width,name,editUrl:p.url(),watch};
 }catch(error){record({id:role==='admin'?'A01':'A03',role,lang,width,status:'FAIL',error:String(error)});const p=c.pages().at(-1);if(p){await p.screenshot({path:H.path.join(out,`failure-create-${role}-${lang}.png`),fullPage:true});H.fs.writeFileSync(H.path.join(out,`failure-create-${role}-${lang}.txt`),await p.locator('body').innerText());H.fs.writeFileSync(H.path.join(out,`failure-create-${role}-${lang}-controls.json`),JSON.stringify(await p.locator('form[data-km-editor]').evaluate(form=>({invalid:[...form.querySelectorAll('input,select,textarea')].filter(e=>!e.validity.valid||e.getAttribute('aria-invalid')==='true').map(e=>({name:e.name,id:e.id,hidden:!!e.closest('[hidden]'),message:e.validationMessage})),summary:form.querySelector('[data-km-errors]')?.outerHTML,errors:[...form.querySelectorAll('.km-editor-field-error,.errorlist')].map(e=>e.outerHTML)})),null,2));}throw error;}finally{await c.close();}
}
module.exports={create,fillPlace,addTariff};
