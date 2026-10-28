const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
test('nested tariffs expose foreign budget limits and missing translations without changing stored money',()=>{
 const source=fs.readFileSync('static/js/owner_place_offerings.js','utf8');
 const ui=Object.fromEntries([...source.matchAll(/ui\.(\w+)/g)].map(match=>[match[1],match[1]+' (AZ)']));
 const choices={product_types:[['lesson','Lesson']],price_kinds:[['exact','Exact']],charge_roles:[['primary','Primary']],billing_modes:[['one_time','Once']],billing_intervals:[],quantity_units:[],lesson_formats:[['group','Group']]};
 const plan={id:1,title_az:'Tarif',conditions_ru:'По записи',currency:'USD',price_kind:'exact',price:20,product_type:'lesson',billing_mode:'one_time'};
 const tree={pricing_schema_version:2,activities:[{name_az:'Activity',groups:[{name_az:'Group',pricing_plans:[plan]}]}]};
 const d=new JSDOM(`<html lang=ru><script id=pw-copy type=application/json>${JSON.stringify(ui)}</script><script id=pc-offering-choices type=application/json>${JSON.stringify(choices)}</script><form><div data-pc-offerings><input name=nested_pricing><div data-pc-activity-list></div><button data-pc-add-activity></button></div></form>`,{runScripts:'outside-only'});
 try{const w=d.window,input=w.document.querySelector('[name=nested_pricing]');input.value=JSON.stringify(tree);w.eval(source);const row=w.document.querySelector('.pc-plan-card');assert.match(row.querySelector('[data-nested-currency-warning]').textContent,/USD.*AZN|AZN.*USD/);assert.match(row.querySelector('[data-nested-translation-warning]').textContent,/EN/);assert(row.querySelector('[data-offering-key=conditions_en]'));const amount=row.querySelector('[data-offering-key=price]');amount.value='25';amount.dispatchEvent(new w.Event('input',{bubbles:true}));assert.equal(JSON.parse(input.value).activities[0].groups[0].pricing_plans[0].currency,'USD');}finally{d.window.close();}
});
