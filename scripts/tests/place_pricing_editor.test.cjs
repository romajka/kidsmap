const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
const file='static/js/kidsmap_pricing_editor.js';

test('recurring period controls are visibly required without guessing a billing period count',()=>{const m=mount();try{m.q('[data-tariff-add]').click();m.change('editor_kind','membership');m.change('billing_mode','recurring');for(const key of ['billing_interval','billing_interval_count'])assert.equal(m.q(`[data-tariff-key=${key}]`).closest('.owner-tariff-field').dataset.kmRequired,'true');assert(!m.value()[0].billing_interval_count);assert.equal(m.q('[data-tariff-key=title_az]').closest('.owner-tariff-field').dataset.kmRequired,'false');}finally{m.close();}});

test('free entry changes visible plans to paid services without mutating saved pricing',()=>{const plan={id:17,product_type:'lesson',price_kind:'exact',price:'25',currency:'AZN',billing_mode:'one_time'},d=new JSDOM('<html lang="ru"><form data-permanent-place-form><div data-tariff-editor><input name="price_mode" value="tariffs"><input data-tariff-input><p data-tariff-heading>Тарифы места</p><p data-tariff-description></p><div data-tariff-list></div><button type="button" data-tariff-add>Добавить тариф</button><button type="button" data-price-policy="free_entry_paid_services">Free entry</button><button type="button" data-price-policy="tariffs">Tariffs</button></div></form></html>',{runScripts:'outside-only'}),w=d.window;w.document.querySelector('[data-tariff-input]').value=JSON.stringify([plan]);w.eval(fs.readFileSync(file,'utf8'));w.document.querySelector('[data-price-policy=free_entry_paid_services]').click();assert.equal(w.document.querySelector('[data-tariff-heading]').textContent,'Платные услуги');assert.match(w.document.querySelector('[data-tariff-add]').textContent,/Добавить платную услугу/);assert.deepEqual(JSON.parse(w.document.querySelector('[data-tariff-input]').value),[plan]);w.document.querySelector('[data-price-policy=tariffs]').click();assert.equal(w.document.querySelector('[data-tariff-heading]').textContent,'Тарифы места');w.close();});
test('active checkbox belongs to the action footer, outside the advanced grid',()=>{const m=mount([{product_type:'lesson',price_kind:'exact',price:'25',currency:'AZN'}]);try{const active=m.q('.owner-tariff-active');assert(active.closest('.owner-tariff-footer'));assert.equal(active.querySelector('input').type,'checkbox');active.querySelector('input').click();assert.equal(m.value()[0].is_active,false);}finally{m.close();}});
function mount(plans=[]){
 assert(fs.existsSync(file),'Both place forms need the shared pricing editor');
 const dom=new JSDOM('<html lang="ru"><form data-permanent-place-form><div data-tariff-editor data-can-verify="1"><input data-tariff-input><div data-tariff-list></div><button data-tariff-add type="button">Add</button></div></form></html>',{runScripts:'outside-only'});
 dom.window.document.querySelector('[data-tariff-input]').value=JSON.stringify(plans);
 dom.window.confirm=()=>true;
 dom.window.eval(fs.readFileSync(file,'utf8'));
 const q=s=>dom.window.document.querySelector(s);
 return {dom,q,value:()=>JSON.parse(q('[data-tariff-input]').value),change(key,value){const e=q(`[data-tariff-key="${key}"]`);assert(e,`Missing ${key}`);e.value=value;e.dispatchEvent(new dom.window.Event('change',{bubbles:true}));},close:()=>dom.window.close()};
}
test('opening a saved complex tariff does not rewrite its hidden business values',()=>{
 const plan={id:17,product_type:'membership',billing_mode:'recurring',billing_interval:'week',billing_interval_count:2,currency:'USD',price_kind:'exact',price:'45.00',quantity:7,quantity_unit:'visit',is_active:false,is_trial:true,is_unlimited:false,validity_interval:'month',validity_interval_count:3,sessions_per_month:8,day_type:'weekend',conditions_ru:'Свои условия',verified_at:'2026-01-02T00:00:00+00:00',sort_order:3};
 const m=mount([plan]);try{assert.deepEqual(m.value(),[plan]);assert.match(m.q('[data-tariff-list]').textContent,/USD/);assert.doesNotMatch(m.q('[data-tariff-list]').textContent,/45.00 AZN/);}finally{m.close();}
});
test('range uses two bounds and no exact amount',()=>{
 const m=mount([{product_type:'visit',price_kind:'range',price_min:'20',price_max:'40',currency:'AZN'}]);try{assert(m.q('[data-tariff-key="price"]').closest('label').hidden);assert(!m.q('[data-tariff-key="price_min"]').closest('label').hidden);assert(!m.q('[data-tariff-key="price_max"]').closest('label').hidden);}finally{m.close();}
});
test('editing a title preserves quantity, staff verification and a nonmonthly period',()=>{
 const plan={id:7,product_type:'membership',price_kind:'exact',price:'50.00',currency:'EUR',billing_mode:'recurring',billing_interval:'year',billing_interval_count:2,quantity:4,quantity_unit:'family',verified_at:'2026-01-01T00:00:00Z',is_active:true};
 const m=mount([plan]);try{m.change('title_az','Yeni');const after=m.value()[0];for(const [key,value]of Object.entries(plan))assert.deepEqual(after[key],value,key);assert.equal(after.title_az,'Yeni');}finally{m.close();}
});
test('adding a tariff does not silently choose a product or group format',()=>{
 const m=mount();try{m.q('[data-tariff-add]').click();assert.equal(m.q('[data-tariff-key="editor_kind"]').value,'');assert(!m.value()[0].product_type);assert(!m.value()[0].lesson_format);}finally{m.close();}
});
test('changing price kind can be cancelled before losing existing amounts',()=>{
 const m=mount([{product_type:'lesson',price_kind:'exact',price:'25.00',currency:'AZN'}]);try{m.dom.window.confirm=()=>false;m.change('price_kind','free');assert.equal(m.value()[0].price_kind,'exact');assert.equal(m.value()[0].price,'25.00');}finally{m.close();}
});
test('package selection writes canonical lesson quantity without claiming monthly billing',()=>{
 const m=mount();try{m.q('[data-tariff-add]').click();m.change('editor_kind','package');m.change('quantity','8');const p=m.value()[0];assert.equal(p.product_type,'lesson');assert.equal(p.quantity_unit,'lesson');assert.equal(p.billing_mode,'one_time');assert.equal(p.quantity,'8');}finally{m.close();}
});
test('monthly template keeps the canonical monthly payment and shows its editable period immediately',()=>{
 const m=mount();try{m.q('[data-tariff-add]').click();m.change('editor_kind','monthly');m.change('quantity','12');const p=m.value()[0];assert.equal(p.product_type,'membership');assert.equal(p.billing_mode,'recurring');assert.equal(p.billing_interval,'month');assert.equal(p.billing_interval_count,1);assert.equal(p.quantity_unit,'lesson');assert.equal(m.q('[data-tariff-key="billing_interval"]').closest('details'),null);}finally{m.close();}
});

test('required payment fields are outside collapsed additional terms for every paid scenario',()=>{
 for(const kind of ['lesson','package','admission','membership','monthly','course']){
  const m=mount();try{m.q('[data-tariff-add]').click();m.change('editor_kind',kind);
   for(const field of m.dom.window.document.querySelectorAll('.owner-tariff-field[data-km-required=true]')){
    if(!field.hidden)assert.equal(field.closest('details'),null,`${kind}: ${field.className}`);
   }
  }finally{m.close();}
 }
});

test('unlimited preserves the checkbox, section, focus and other tariff DOM nodes',()=>{
 const m=mount([{product_type:'lesson',quantity:8,quantity_unit:'lesson',price_kind:'exact',price:'100',billing_mode:'one_time'}]);try{
  const checkbox=m.q('[data-tariff-key=is_unlimited]'),section=checkbox.closest('.owner-tariff-section'),title=m.q('[data-tariff-key=title_az]');
  assert(section);checkbox.focus();checkbox.click();
  assert.equal(m.q('[data-tariff-key=is_unlimited]'),checkbox);assert.equal(checkbox.closest('.owner-tariff-section'),section);
  assert.equal(m.dom.window.document.activeElement,checkbox);assert.equal(m.q('[data-tariff-key=title_az]'),title);
  assert.equal(m.value()[0].is_unlimited,true);assert(!m.value()[0].quantity);assert(!m.value()[0].quantity_unit);
  checkbox.click();assert.equal(m.q('[data-tariff-key=is_unlimited]'),checkbox);
 }finally{m.close();}
});

test('validity stays grouped and visible independently from optional offer dates and billing',()=>{
 const plan={id:9,product_type:'membership',billing_mode:'one_time',price_kind:'exact',price:'100',quantity:8,quantity_unit:'lesson',valid_from:'2026-06-01',valid_until:'2026-08-31'};
 const m=mount([plan]);try{
  const count=m.q('[data-tariff-key=validity_interval_count]'),unit=m.q('[data-tariff-key=validity_interval]');
  assert.equal(count.closest('[data-tariff-validity]'),unit.closest('[data-tariff-validity]'));assert(count.closest('[data-tariff-validity]'));
  assert.equal(count.closest('details'),null);m.change('validity_interval_count','1');
  assert.equal(unit.closest('.owner-tariff-field').dataset.kmRequired,'true');m.change('validity_interval','month');
  assert.equal(m.q('[data-tariff-key=validity_interval_count]'),count);
  assert(m.q('[data-tariff-key=valid_from]').closest('[data-tariff-offer-dates]'));
  assert(m.q('[data-tariff-key=valid_from]').closest('details'));
  const result=m.value()[0];for(const [key,value]of Object.entries(plan))assert.deepEqual(result[key],value,key);
  assert.equal(result.validity_interval,'month');assert.equal(result.validity_interval_count,'1');
 }finally{m.close();}
});

test('free one-time plan does not ask for payment parameters or alter stored billing',()=>{
 const m=mount([{product_type:'lesson',price_kind:'free',price:'0.00',billing_mode:'one_time'}]);try{
  const billing=m.q('[data-tariff-key=billing_mode]');assert(billing.closest('.owner-tariff-field').hidden);assert.equal(billing.required,false);
  assert.equal(m.value()[0].billing_mode,'one_time');
 }finally{m.close();}
});

test('payment and usage summaries distinguish one payment, recurring and installments',()=>{
 const m=mount([{product_type:'membership',billing_mode:'one_time',price_kind:'exact',price:'140',is_unlimited:true,validity_interval:'month',validity_interval_count:1}]);try{
  assert.match(m.q('.owner-tariff-card-copy small').textContent,/Один платёж/);
  assert.match(m.q('.owner-tariff-card-copy small').textContent,/Использовать за: 1 месяц/);
  m.change('billing_mode','recurring');m.change('billing_interval','month');m.change('billing_interval_count','2');
  assert.match(m.q('.owner-tariff-card-copy small').textContent,/Оплата каждые 2 месяца/);
  m.change('billing_mode','installment');m.change('billing_cycles','3');
  assert.match(m.q('.owner-tariff-card-copy small').textContent,/Количество платежей: 3/);
  assert.equal(m.value()[0].price,'140');
 }finally{m.close();}
});

test('a package makes its missing included quantity required immediately',()=>{
 const m=mount();try{m.q('[data-tariff-add]').click();m.change('editor_kind','package');
  assert.equal(m.q('[data-tariff-key=quantity]').closest('.owner-tariff-field').dataset.kmRequired,'true');
 }finally{m.close();}
});
test('an unlimited monthly plan does not submit a quantity unit without quantity',()=>{
 const m=mount();try{m.q('[data-tariff-add]').click();m.change('editor_kind','monthly');const e=m.q('[data-tariff-key=is_unlimited]');e.checked=true;e.dispatchEvent(new m.dom.window.Event('change',{bubbles:true}));const p=m.value()[0];assert.equal(p.is_unlimited,true);assert(!p.quantity);assert(!p.quantity_unit);}finally{m.close();}
});
test('changing the payment period no longer labels a plan as monthly',()=>{
 const m=mount();try{m.q('[data-tariff-add]').click();m.change('editor_kind','monthly');m.change('billing_interval','week');assert.equal(m.q('[data-tariff-key=editor_kind]').value,'membership');assert.equal(m.value()[0].billing_interval,'week');assert(!m.q('[data-tariff-key=billing_interval]').closest('details'));}finally{m.close();}
});
test('changing price kind keeps keyboard focus on its replacement button',()=>{
 const m=mount([{product_type:'lesson',price_kind:'exact',price:'25',currency:'AZN'}]);try{m.q('[data-price-kind=free]').focus();m.q('[data-price-kind=free]').click();assert.equal(m.dom.window.document.activeElement.dataset.priceKind,'free');}finally{m.close();}
});
test('new tariffs use AZN with the currency beside money and no currency selector',()=>{
 const m=mount();try{m.q('[data-tariff-add]').click();m.change('editor_kind','monthly');assert.equal(m.value()[0].currency,'AZN');assert.equal(m.q('[data-tariff-key=currency]').type,'hidden');assert.equal(m.q('[data-tariff-key=price]').closest('label').querySelector('[data-money-currency]').textContent,'₼');}finally{m.close();}
});
test('saved foreign currency remains explicit at both range bounds without allowing accidental conversion',()=>{
 const plan={id:77,product_type:'visit',currency:'USD',price_kind:'range',price_min:'20.00',price_max:'40.00'};
 const m=mount([plan]);try{assert.equal(m.q('[data-tariff-key=currency]').type,'hidden');for(const key of ['price_min','price_max'])assert.equal(m.q(`[data-tariff-key=${key}]`).closest('label').querySelector('[data-money-currency]').textContent,'USD');m.change('price_max','45');assert.equal(m.value()[0].currency,'USD');assert.equal(m.value()[0].id,77);}finally{m.close();}
});
