async original=>{const c=await original.context().browser().newContext(),p=await c.newPage();p.on('dialog',d=>d.accept());await c.route('**/*',r=>r.request().url().startsWith('http://localhost:8792/')?r.continue():r.abort());try{await p.goto("http://localhost:8792/qa/");await p.getByRole("button",{name:"Войти: demo_owner",exact:true}).click();const r=await (async (page) => {
 const kind='venue'; const name='QA Tədbir məkanı 8792';
 const out={kind,name,steps:[]};
 await page.goto('http://localhost:8792/ru/account/places/create/?type=permanent&fresh=1');
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
   await page.locator('[data-price-kind=exact]').press('Enter');await page.locator('[data-tariff-key=price]').fill(kind==='venue'?'30':'12');
 }
 await page.waitForFunction(()=>document.querySelector('[data-pc-save-status]').dataset.state==='saved');
 await page.reload(); await page.waitForFunction(()=>document.querySelector('[data-pc-save-status]').dataset.state==='saved');
 out.reloadedFull={name:await page.locator('[name=name_az]').inputValue(),pricing:await page.locator('[name=pricing_plans]').inputValue(),nested:await page.locator('[name=nested_pricing]').inputValue(),hours:await page.locator('[name=structured_schedule]').inputValue()};
 await page.locator('[name=photo]').setInputFiles('/home/ramin/kidsmap/.tmp/content-entry-final-20261007/assets/cover.png');
 await page.waitForFunction(()=>document.querySelector('[data-photo-id]')?.dataset.state==='ready');
 await page.locator('[data-pc-save-draft]').press('Enter');await page.waitForURL('**/account/places/*/edit/**');
 out.placeId=Number(page.url().match(/places\/(\d+)\/edit/)[1]);
 await page.locator('[data-pc-submit]').press('Enter');
 try {await page.waitForURL('**/account/places/',{timeout:8000}); out.submitted=true;}catch {out.submitted=false;out.errors=await page.locator('[data-pc-errors]').innerText();}
 out.url=page.url();
 return out;
}
)(p);return {rows:[{id:'venue-draft-reload',status:r.restored?'PASS':'FAIL'},{id:'venue-filled-reload',status:r.reloadedFull.name===r.name&&r.reloadedFull.pricing.includes('30')?'PASS':'FAIL'},{id:'venue-submit',status:r.submitted?'PASS':'FAIL'}],result:r};}finally{await c.close();}}