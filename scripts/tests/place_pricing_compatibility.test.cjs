const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');

for(const file of ['static/js/owner_pricing_plans.js','static/js/permanent_place_pricing.js']){
 test(`retained renderer preserves supplied canonical business values: ${file}`,()=>{
  const plans=[
   {id:501,product_type:'membership',price_kind:'exact',price:'45.00',currency:'USD',billing_mode:'recurring',billing_interval:'week',billing_interval_count:2,quantity:7,quantity_unit:'visit',validity_interval:'month',validity_interval_count:3,is_trial:false,is_active:true,conditions_ru:'Fictional retained conditions'},
   {id:502,product_type:'lesson',price_kind:'range',price_min:'100.00',price_max:'150.00',currency:'AZN',billing_mode:'one_time',quantity:8,quantity_unit:'lesson',is_active:false}
  ];
  const dom=new JSDOM('<html lang="ru"><form><input id="id_price_mode" value="tariffs"><div data-tariff-editor><input data-tariff-input><div data-tariff-list></div><button type="button" data-tariff-add>Add</button></div></form></html>',{runScripts:'outside-only'});
  try{const input=dom.window.document.querySelector('[data-tariff-input]');input.value=JSON.stringify(plans);dom.window.eval(fs.readFileSync(file,'utf8'));assert.equal(dom.window.document.querySelectorAll('.owner-tariff-row').length,2);const actual=JSON.parse(input.value);assert.equal(actual.length,plans.length);for(let i=0;i<plans.length;i++)for(const [key,value]of Object.entries(plans[i]))assert.deepEqual(actual[i][key],value,`${i}/${key}`);}finally{dom.window.close();}
 });
}
