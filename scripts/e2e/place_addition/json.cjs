const H=require('./helpers.cjs');
async function apply(p,data,expected=200,confirm=true){
 const old=await p.locator('[name=pricing_plans]').inputValue();
 const hasData=!!await p.locator('#id_name_az').inputValue();
 await p.locator('[data-place-json-import-open]').click();
 await p.locator('[data-place-json-import-input]').fill(typeof data==='string'?data:JSON.stringify(data));
 const response=typeof data==='string'?null:p.waitForResponse(r=>r.url().includes('/pricing/import/validate/'));
 await p.locator('[data-place-json-import-apply]').click();
 if(response){const r=await response;H.assert.equal(r.status(),expected);}
 const modal=p.locator('.km-modal-backdrop');
 if(expected===200&&typeof data!=='string'&&hasData){await modal.waitFor({state:'visible'});await modal.getByRole('button',{name:confirm?'Продолжить импорт':'Отмена',exact:true}).click();await modal.waitFor({state:'hidden'});}
 if(expected!==200||!confirm||typeof data==='string')H.assert.equal(await p.locator('[name=pricing_plans]').inputValue(),old,'Rejected/cancelled JSON cannot mutate prices');
 if(await p.locator('[data-place-json-import-dialog]').isVisible())await p.locator('[data-place-json-import-close]').first().click();
}
async function json(ctx){
 const imported=await require('./create.cjs').create({...ctx,intake:async(p,role,name)=>{
  await p.locator('[data-place-accordion-expand-all]').click();
  const options=await(await p.context().request.get(ctx.fixture.origin+`/admin/catalog/place/${ctx.fixture.fixtures.direct.id}/export-json/`)).json();
  await apply(p,{name_az:name,description_az:'Bu, yalnız yerli JSON sınağı üçün hazırlanmış məkanın təsviridir. Uşaqlar üçün dərslər və ailələr üçün ziyarət imkanları haqqında sintetik məlumat.',category:options.category,subcategory:options.subcategory,region:'baku',district:'baku_narimanov',address:`Bakı, Yerli QA küçəsi, ${name}`,phone1:'+994501112233',whatsapp_mode:null,age_from:6,age_to:12,schedule_mode:'by_appointment',lat:40.4093,lng:49.8671,price_mode:'tariffs',public_links:[{label:'Запись из JSON',url:'https://example.com/json-booking'}],pricing_plans:[{product_type:'membership',billing_mode:'recurring',billing_interval:'month',billing_interval_count:1,quantity:12,quantity_unit:'lesson',price_kind:'exact',price:120,currency:'AZN'}]});
 }},'admin');
 const published=await require('./publication.cjs').publish(ctx,imported);await require('./publication.cjs').publicCheck(ctx,published);
 const linked=await H.context(ctx.browser,ctx.fixture.origin);try{const p=await H.login(linked,ctx.fixture,'admin');const data=await(await linked.request.get(ctx.fixture.origin+`/admin/catalog/place/${published.id}/export-json/`)).json();H.assert.deepEqual(data.public_links,[{label:'Запись из JSON',url:'https://example.com/json-booking'}]);await p.goto(published.publicUrl);H.assert(await p.locator('[data-place-public-link][href="https://example.com/json-booking"]').count());}finally{await linked.close();}
 ctx.record({id:'E02',role:'admin',status:'PASS',placeId:published.id,assertions:['new JSON imported through dialog','real upload and draft save','same place published','public catalog and saved photos verified']});
 const c=await H.context(ctx.browser,ctx.fixture.origin);
 try{const p=await H.login(c,ctx.fixture,'admin');
  await p.goto(ctx.fixture.origin+'/admin/catalog/place/add/?type=permanent');
  await p.locator('[data-place-json-prompt-copy]').click();await p.locator('[data-place-json-prompt-mode][value=json]').check();
  const text=await p.locator('[data-place-json-prompt-input]').inputValue();
  const samples=JSON.parse(text.split('Примеры объектов pricing_plans (вымышленные):')[1].split('Полная структура JSON:')[0].trim());
  H.assert.equal(samples.package.quantity,8);H.assert.equal(samples.prepaid.billing_mode,'one_time');
  await p.locator('[data-place-json-prompt-mode][value=update]').check();const update=await p.locator('[data-place-json-prompt-input]').inputValue();H.assert(update.includes('свежему экспорту'));H.assert(!update.includes('Полная структура JSON:'));
  await p.locator('[data-place-json-prompt-close]').first().click();
  ctx.record({id:'E01',role:'admin',status:'PASS',assertions:['real instruction dialog','parser-valid canonical examples','separate update prompt preserves full export']});
  const saved=ctx.fixture.fixtures.foreign.id;
  const edit=ctx.fixture.origin+`/admin/catalog/place/${saved}/change/`;
  await p.goto(edit);await p.locator('[data-place-accordion-expand-all]').click();
  const exported=await (await c.request.get(ctx.fixture.origin+`/admin/catalog/place/${saved}/export-json/?pricing_schema_version=2`)).json();
  H.assert(exported.region);H.assert(Array.isArray(exported.schedule_days));H.assert(exported.nested_pricing);
  const before=JSON.parse(await p.locator('[name=pricing_plans]').inputValue());
  await apply(p,exported);
  H.assert.deepEqual(JSON.parse(await p.locator('[name=pricing_plans]').inputValue()).map(x=>({id:x.id,currency:x.currency,billing_interval:x.billing_interval,quantity_unit:x.quantity_unit})),before.map(x=>({id:x.id,currency:x.currency,billing_interval:x.billing_interval,quantity_unit:x.quantity_unit})));
  await require('./pricing.cjs').save(p,'admin');
  const after=await (await c.request.get(ctx.fixture.origin+`/admin/catalog/place/${saved}/export-json/?pricing_schema_version=2`)).json();
  for(const key of ['pricing_plans','schedule_days','region','district','name_az','name_ru','name_en','extra_conditions_ru','custom_price_badge_ru','public_links'])H.assert.deepEqual(after[key],exported[key],key);
  ctx.record({id:'E04',role:'admin',status:'PASS',placeId:saved,assertions:['actual export-import-save-export','region and structured days retained','foreign currency and nonmonthly period retained','same tariff IDs']});
  const source=await p.locator('[name=pricing_plans]').inputValue();
  await apply(p,{place_id:saved,base_content_version:after.base_content_version,phone2:'+994551112233'});
  H.assert.equal(await p.locator('[name=pricing_plans]').inputValue(),source);
  await require('./pricing.cjs').save(p,'admin');
  ctx.record({id:'E05',role:'admin',status:'PASS',placeId:saved,assertions:['contact-only JSON does not replace omitted pricing list','real save']});
  await apply(p,'{"pricing_plans":');
  ctx.record({id:'E07',role:'admin',status:'PASS',assertions:['malformed JSON rejected before mutating form']});
  const fresh=await(await c.request.get(ctx.fixture.origin+`/admin/catalog/place/${saved}/export-json/`)).json();
  await apply(p,{place_id:saved,base_content_version:fresh.base_content_version-1,phone1:'+994551112244'},409);
  ctx.record({id:'E08',role:'admin',status:'PASS',assertions:['stale version rejected by server before applying data']});
  await apply(p,{place_id:saved,base_content_version:fresh.base_content_version,pricing_plans:[]},200,false);
  ctx.record({id:'E06',role:'admin',status:'PASS',assertions:['explicit empty array offers warning','cancel keeps existing tariffs']});
  await apply(p,{pricing_plans:[{product_type:'lesson',price_kind:'exact',price:-1}]},400);
  ctx.record({id:'E12',role:'admin',status:'PASS',assertions:['invalid tariff rejected by actual validator','no partial form mutation']});
 }catch(error){const p=c.pages().at(-1);if(p)await p.screenshot({path:H.path.join(ctx.out,'failure-json.png'),fullPage:true});ctx.record({id:'json',status:'FAIL',error:String(error)});throw error;}finally{await c.close();}
}
module.exports={json,apply};
