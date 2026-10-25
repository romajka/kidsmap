const H=require('./helpers.cjs');
const cases=[
 ['C01','admission',{quantity:1,quantity_unit:'entry',audience_type:'child',age_from:4,age_to:12,day_type:'weekend'}],
 ['C02','visit',{quantity:1,quantity_unit:'visit',audience_type:'adult',day_type:'weekday'}],
 ['C03','lesson',{quantity:1,quantity_unit:'lesson',lesson_format:'individual'}],
 ['C04','package',{quantity:8,quantity_unit:'lesson',validity_interval:'month',validity_interval_count:2}],
 ['C05','monthly',{quantity:12,quantity_unit:'lesson'}],
 ['C06','monthly',{is_unlimited:true}],
 ['C07','membership',{quantity:8,quantity_unit:'lesson',validity_interval:'month',validity_interval_count:1}],
 ['C08','membership',{billing_mode:'recurring',billing_interval:'week',billing_interval_count:2,quantity:7,quantity_unit:'visit'}],
 ['C09','course',{billing_mode:'installment',billing_cycles:3}],
 ['C10','camp',{quantity:1,quantity_unit:'camp_shift'}],
 ['C11','event',{quantity:1,quantity_unit:'event'}],
 ['C12','excursion',{quantity:1,quantity_unit:'family',audience_type:'family'}],
 ['C13','tour',{quantity:1,quantity_unit:'group',min_people:3,max_people:5}],
 ['C14','rental',{quantity:2,quantity_unit:'hour'}],
 ['C15','addon',{is_required:true}],
 ['C16','registration_fee',{}],['C17','deposit',{}],
 ['C18','lesson',{price_kind:'free',is_trial:true}],
 ['C19','visit',{price_kind:'range',price_min:20,price_max:40}],
 ['C19','visit',{price_kind:'from',price_min:20}],
 ['C19','visit',{price_kind:'on_request'}],
 ['C22','lesson',{title_az:'Sınaq tarifi',title_ru:'Тестовый тариф',title_en:'Test plan',conditions_az:'Şərtlər',conditions_ru:'Условия',conditions_en:'Terms',valid_from:'2026-10-01',valid_until:'2027-01-01',source_url:'https://example.invalid/fictional-price'}],
 ['C23','lesson',{is_active:false}]
];
async function save(p,role){
 const next=p.waitForEvent('domcontentloaded',{timeout:30000});
 await p.locator(role==='admin'?'[name=_save_draft]':'[name=form_action][value=save_draft]').first().click();
 await next;await p.waitForSelector('[data-tariff-list]',{state:'attached'});await p.waitForLoadState('networkidle');
}
async function setField(p,key,value){
 const input=p.locator(`[data-tariff-key="${key}"]`).first();await H.reveal(input);
 if(['title_ru','title_en'].includes(key)&&!await input.isVisible())await p.locator('[data-tariff-row] .km-btn-link').first().click();
 if(key==='price_kind'){await p.locator(`[data-price-kind="${value}"]`).first().click();return;}
 const type=await input.getAttribute('type');
 if(type==='checkbox')await input.setChecked(value);
 else if(await input.evaluate(e=>e.tagName==='SELECT'))await H.select(p,`[data-tariff-key="${key}"]`,value);
 else await H.fill(p,`[data-tariff-key="${key}"]`,value);
}
async function pricing(ctx){
 const {create}=require('./create.cjs');
 for(const role of ['admin','owner']){
  const item=await create(ctx,role);const c=await H.context(ctx.browser,ctx.fixture.origin);
  try{const p=await H.login(c,ctx.fixture,role);let accept=true;p.on('dialog',d=>accept?d.accept():d.dismiss());await p.goto(item.editUrl);
   for(const [id,kind,fields]of cases){
    if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
    while(await p.locator('.owner-tariff-remove').count())await p.locator('.owner-tariff-remove').last().click();
    await p.locator('[data-tariff-add]').click();await setField(p,'editor_kind',kind);
    for(const [key,value]of Object.entries(fields))if(!['price_kind','price_min','price_max','is_active'].includes(key))await setField(p,key,value);
    if(fields.price_kind)await setField(p,'price_kind',fields.price_kind);
    if(!fields.price_kind||fields.price_kind==='exact')await setField(p,'price','25');
    if(fields.price_min)await setField(p,'price_min',fields.price_min);
    if(fields.price_max)await setField(p,'price_max',fields.price_max);
    if(fields.is_active===false){const active=p.locator('.owner-tariff-active input');await H.reveal(active);await active.uncheck();}
    await save(p,role);
    const plans=JSON.parse(await p.locator('[name=pricing_plans]').inputValue());H.assert.equal(plans.length,1);const stored=plans[0];
    H.assert.equal(stored.product_type,kind==='monthly'?'membership':kind==='package'?'lesson':kind);
    for(const [key,value]of Object.entries(fields)){
     if(['price','price_min','price_max'].includes(key))H.assert.equal(Number(stored[key]),Number(value),`${role}/${id}/${key}`);
     else H.assert.equal(String(stored[key]),String(value),`${role}/${id}/${key}`);
    }
    ctx.record({id,role,status:'PASS',kind,tariffId:stored.id||null,assertions:['real editor controls','server candidate saved and reloaded','canonical product','all supplied conditions and flags retained']});
   }
   // A mode switch hides the editor but must never clear its saved rows.
   const before=JSON.parse(await p.locator('[name=pricing_plans]').inputValue());
   for(const mode of ['free','events','free_entry_paid_services','tariffs']){
    await p.locator(`[data-price-policy="${mode}"]`).click();await save(p,role);
    H.assert.equal(await p.locator('[name=price_mode]').inputValue(),mode);
    H.assert.deepEqual(JSON.parse(await p.locator('[name=pricing_plans]').inputValue()),before);
   }
   ctx.record({id:'C20',role,status:'PASS',assertions:['all four modes saved','hidden tariffs retained with same IDs']});
   if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   // Check cancellation with actual native confirmation, not a mocked callback.
   const old=await p.locator('[name=pricing_plans]').inputValue();accept=false;
   await p.locator('[data-price-kind=free]').first().click();accept=true;
   H.assert.equal(await p.locator('[name=pricing_plans]').inputValue(),old);
   ctx.record({id:'C26',role,status:'PASS',assertions:['cancel destructive change in actual browser','original tariff retained']});
  }catch(error){const p=c.pages().at(-1);if(p)await p.screenshot({path:H.path.join(ctx.out,`failure-pricing-${role}.png`),fullPage:true});ctx.record({id:'pricing',role,status:'FAIL',error:String(error)});throw error;}finally{await c.close();}
 }
}
module.exports={pricing,save,setField};
