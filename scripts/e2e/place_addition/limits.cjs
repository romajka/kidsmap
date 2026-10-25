const H=require('./helpers.cjs');
async function limits(ctx){
 for(const role of ['admin','owner']){
  const item=await require('./create.cjs').create(ctx,role);const c=await H.context(ctx.browser,ctx.fixture.origin);
  const responses=[];
  try{const p=await H.login(c,ctx.fixture,role);p.on('dialog',d=>d.accept());p.on('response',async r=>{if(r.request().method()==='POST'&&r.url().includes('/drafts/')){const row={status:r.status(),url:r.url()};responses.push(row);try{row.result=await r.json();delete row.result.fields;}catch{}}});await p.goto(item.editUrl);
   if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   while(await p.locator('.owner-tariff-remove').count())await p.locator('.owner-tariff-remove').last().click();
   for(let i=0;i<12;i++){
    await p.locator('[data-tariff-add]').click();const row=p.locator('[data-tariff-row]').last();
    await row.locator('[data-tariff-key=editor_kind]').selectOption('visit');
    await row.locator('[data-tariff-key=price]').fill(String(i+1));
   }
   H.assert(await p.locator('[data-tariff-add]').isDisabled());
   await p.locator('[data-tariff-row]').last().locator('.owner-tariff-move').first().click();
   await require('./pricing.cjs').save(p,role);
   let plans=JSON.parse(await p.locator('[name=pricing_plans]').inputValue());H.assert.equal(plans.length,12);H.assert.equal(Number(plans[10].price),12);H.assert.equal(Number(plans[11].price),11);
   if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   await p.locator('[data-tariff-row]').last().locator('.owner-tariff-remove').click();await require('./pricing.cjs').save(p,role);
   plans=JSON.parse(await p.locator('[name=pricing_plans]').inputValue());H.assert.equal(plans.length,11);H.assert.equal(Number(plans[10].price),12);
   ctx.record({id:'C21',role,status:'PASS',assertions:['12 real tariffs saved','add disabled at limit','reorder saved','only explicitly deleted row removed']});
   if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   while(await p.locator('.owner-tariff-remove').count()>1)await p.locator('.owner-tariff-remove').last().click();
   const {setField,save}=require('./pricing.cjs');await setField(p,'price_kind','range');await setField(p,'price_min',40);await setField(p,'price_max',20);
   const title=await p.locator('#id_name_az').inputValue();
   const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(role==='owner'?'/save-photos/':`/place/${item.editUrl.match(/\/(\d+)\//)[1]}/change/`));
   await p.locator(role==='admin'?'[name=_save_draft]':'[name=form_action][value=save_draft]').first().click();const rejected=await response;
   H.assert([200,400,422].includes(rejected.status()));
   await p.locator(role==='admin'?'[data-tariff-editor] .km-editor-field-error':'[data-photo-save-status]').filter({hasText:/./}).first().waitFor({state:'visible'});
   await H.inspect(p,ctx.out,`limits-error-${role}`);
   H.assert.equal(await p.locator('#id_name_az').inputValue(),title);
   if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   await setField(p,'price_max',60);await save(p,role);
   plans=JSON.parse(await p.locator('[name=pricing_plans]').inputValue());H.assert.equal(Number(plans[0].price_max),60);
   ctx.record({id:'C25',role,status:'PASS',assertions:['server rejects inverted range','entered place text retained','corrected range saves successfully']});
   // Native keyboard operation of the new optional controls and tariff selector.
   if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   const advanced=p.locator('.owner-tariff-advanced').first(),summary=advanced.locator(':scope>summary');
   await summary.focus();await summary.press('Enter');H.assert(await advanced.getAttribute('open')!==null);await summary.press('Space');H.assert.equal(await advanced.getAttribute('open'),null);
   const kind=p.locator('[data-tariff-key=editor_kind]').first();await kind.focus();await kind.press('Tab');H.assert(await p.evaluate(()=>!!document.activeElement?.closest('[data-tariff-row]')&&document.activeElement.checkVisibility()&&document.activeElement.dataset.tariffKey!=='editor_kind'));
   await p.locator('[data-price-kind=free]').first().focus();await p.keyboard.press('Enter');H.assert.equal(await p.evaluate(()=>document.activeElement?.dataset.priceKind),'free');
   await p.locator('[data-price-kind=range]').first().focus();await p.keyboard.press('Enter');H.assert.equal(await p.evaluate(()=>document.activeElement?.dataset.priceKind),'range');
   await setField(p,'price_min',40);await setField(p,'price_max',60);await save(p,role);
   ctx.record({id:'G04',role,status:'PASS',assertions:['details opens with Enter and closes with Space','Tab reaches next pricing control']});
  }catch(error){const p=c.pages().at(-1);if(p){await p.screenshot({path:H.path.join(ctx.out,`failure-limits-${role}.png`),fullPage:true});H.fs.writeFileSync(H.path.join(ctx.out,`failure-limits-${role}.txt`),await p.locator('body').innerText());}H.fs.writeFileSync(H.path.join(ctx.out,`failure-limits-${role}-drafts.json`),JSON.stringify(responses,null,2));ctx.record({id:'limits',role,status:'FAIL',error:String(error)});throw error;}finally{await c.close();}
 }
}
module.exports={limits};
