async (page) => {
 const kind='studio'; const name='QA Foto yaddaşı 20261007';
 page.on('dialog',d=>d.accept().catch(()=>{}));
 await page.goto('http://localhost:8784/qa/');await Promise.all([page.waitForNavigation(),page.getByRole('button',{name:'Войти: demo_owner',exact:true}).press('Enter')]);
 const out={kind,name,steps:[]};
 await page.goto('http://localhost:8784/ru/account/places/create/?type=permanent&fresh=1');
 await page.locator('[name=name_az]').fill(name);
 await page.locator('[data-pc-save-draft]').press('Enter');
 await page.waitForFunction(()=>document.querySelector('[data-pc-save-status]').dataset.state==='saved');
 const draftUrl=page.url(); await page.reload();
 await page.waitForFunction(()=>document.querySelector('[data-pc-save-status]').dataset.state==='saved');
 out.restored=(await page.locator('[name=name_az]').inputValue())===name;
 await page.locator('[name=description_az]').fill('Uşaqlar üçün yaşa uyğun fəaliyyətlər və valideynlərlə açıq əlaqə. Yalnız yerli yoxlama üçün uydurma məlumat: təhlükəsiz yaradıcılıq mərkəzi, müxtəlif yaş qrupları.');
 await page.locator('[name=category]').selectOption('EDU');
 await page.waitForFunction(()=>document.querySelector('[name=subcategory]').options.length>1);
 await page.locator('[name=subcategory]').selectOption({index:1});
 await page.locator('[name=region]').selectOption('baku');
 await page.locator('[name=district]').selectOption('baku_yasamal');
 await page.locator('[name=address]').fill('QA uydurma küçəsi '+(kind==='studio'?'20':kind==='center'?'30':'40'));
 await page.locator('[name=age_from]').fill('3'); await page.locator('[name=age_to]').fill('15');
 await page.locator('[name=website]').locator('xpath=ancestor::details').locator(':scope > summary').press('Enter');
 await page.locator('[name=website]').fill('https://example.invalid');
 await page.locator('[name=schedule_mode]').selectOption(kind==='venue'?'events':kind==='studio'?'by_appointment':'regular');
 if(kind==='center') {
   await page.locator('[data-km-schedule-preset]').first().click();
   await page.locator('[data-pc-add-activity]').press('Enter');
   const a=page.locator('[data-activity-index="0"]');
   await a.locator(':scope > .pc-offering-grid [data-offering-key=name_az]').fill('QA Robototexnika');
   await a.locator(':scope > .pc-offering-grid [data-offering-key=description_az]').fill('Uşaqlar üçün uydurma robototexnika dərsləri.');
   await a.locator('[data-copy-place-taxonomy]').press('Enter');
   await a.getByRole('button',{name:/Добавить группу/}).press('Enter');
   for(let i=0;i<2;i++) {
     const g=a.locator('[data-group-index="'+i+'"]');
     await g.locator(':scope > .pc-offering-grid [data-offering-key=name_az]').fill('QA Qrup '+(i+1));
     await g.locator(':scope > .pc-offering-grid [data-offering-key=age_from]').fill(i?'8':'3');
     await g.locator(':scope > .pc-offering-grid [data-offering-key=age_to]').fill(i?'15':'7');
     await g.locator('[data-offering-key=schedule_text]').fill(i?'Cümə 16:00–17:00':'Çərşənbə 14:00–15:00');
     await g.locator('[data-plan-index="0"] > .pc-offering-grid [data-offering-key=title_az]').fill('QA Bir dərs '+(i+1));
     await g.locator('[data-plan-index="0"] > .pc-offering-grid [data-offering-key=price]').fill(i?'25':'15');
   }
   out.nested=JSON.parse(await page.locator('[name=nested_pricing]').inputValue());
 } else {
   await page.locator('[data-tariff-add]').press('Enter');
   await page.locator('[data-tariff-key=editor_kind]').selectOption(kind==='venue'?'event':'admission');
   await page.locator('[data-tariff-key=title_az]').fill(kind==='venue'?'QA Tədbir bileti':'QA Giriş bileti');
   await page.locator('[data-tariff-key=price]').fill(kind==='venue'?'30':'12');
 }
 await page.waitForFunction(()=>document.querySelector('[data-pc-save-status]').dataset.state==='saved');
 await page.reload(); await page.waitForFunction(()=>document.querySelector('[data-pc-save-status]').dataset.state==='saved');
 out.reloadedFull={name:await page.locator('[name=name_az]').inputValue(),pricing:await page.locator('[name=pricing_plans]').inputValue(),nested:await page.locator('[name=nested_pricing]').inputValue(),hours:await page.locator('[name=structured_schedule]').inputValue()};
 await page.locator('[name=photo]').setInputFiles('/home/ramin/kidsmap/.tmp/place-form-implementation-20261007/assets/cover.png');
 await page.locator('[name=gallery_images]').setInputFiles(['/home/ramin/kidsmap/.tmp/place-form-implementation-20261007/assets/gallery-one.png','/home/ramin/kidsmap/.tmp/place-form-implementation-20261007/assets/gallery-two.png']);
 await page.waitForTimeout(700);
 let saves=0;
 await page.route('**/account/places/save-photos/',async route=>{saves++;await route.fetch();await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({ok:false,errors:{gallery_images:['QA: ответ сохранения потерян. Повторите.']}})});});
 await page.locator('[data-pc-save-draft]').press('Enter');
 await page.waitForFunction(()=>document.querySelector('[data-photo-save-status]').dataset.savedError==='1');
 out.failedResponse={message:await page.locator('[data-pc-errors]').innerText(),mainRetained:await page.locator('[data-photo-items=main] img').count()};
 await page.unroute('**/account/places/save-photos/');
 await page.locator('[data-pc-save-draft]').press('Enter');
 await page.waitForURL('**/account/places/*/edit/**',{timeout:10000});
 out.editUrl=page.url();out.placeId=Number(out.editUrl.match(/places\/(\d+)\/edit/)[1]);
 await page.reload();await page.waitForTimeout(350);
 out.mainBeforeSubmit=await page.locator('[data-photo-items=main] img').getAttribute('src');
 out.galleryBeforeSubmit=await page.locator('[data-pc-saved-gallery] img').evaluateAll(ns=>ns.map(n=>n.getAttribute('src')));
 await page.screenshot({path:'/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/photo-draft-before-submit-1440.png'});
 await page.locator('[data-pc-submit]').press('Enter');
 try {await page.waitForURL('**/account/places/',{timeout:8000}); out.submitted=true;}catch {out.submitted=false;out.errors=await page.locator('[data-pc-errors]').innerText();}
 out.url=page.url();
 return out;
}
