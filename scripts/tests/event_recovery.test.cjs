const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('older event recovery keeps new contact defaults and restores legacy price explicitly', () => {
  const buttons = new Map();
  const node = () => ({hidden: true, disabled: false, textContent: '', append() {}, addEventListener(type, fn) { this[type] = fn; }});
  const panel = node(); panel.querySelector = selector => { if (!buttons.has(selector)) buttons.set(selector, node()); return buttons.get(selector); };
  const fields = Object.fromEntries(Object.entries({name_az:'Server title', category:'art',price_mode:'unknown', price_text:'',registration_method:'phone',phone:''}).map(([name,value]) => [name,{name,value,labels:[]}]));
  const toggle = {checked:false};
  const form = {dataset:{recoveryKey:'event',recoveryActor:'123',baseVersion:'',serverVersion:''},elements:{namedItem:name => fields[name]},
    querySelector: selector => selector === '[data-event-recovery]' ? panel : toggle, addEventListener() {}};
  let saved;
  const old = {schema:2,actor:'123',base:'',step:0,values:{name_az:'Recovered title',category:'art',price_text:'15 AZN'}};
  const entry = {getStep:()=>0,setValue:(name,value)=>{ if(fields[name]) fields[name].value=value; },refresh(){},showStep(){},setStatus(){}};
  const document = {documentElement:{lang:'ru'}, querySelector:()=>form,createElement:node,
    getElementById:()=>({textContent:JSON.stringify({priceFields:{legacy:['price_text'],unknown:[]}})})};
  vm.runInNewContext(fs.readFileSync('static/js/owner_event_recovery.js','utf8'), {
    document,window:{kidsMapOwnerEventEntry:entry},sessionStorage:{getItem:()=>JSON.stringify(old),setItem:(_,value)=>{saved=JSON.parse(value);},removeItem(){}},RadioNodeList:class {},
  });
  panel.querySelector('[data-recovery-restore]').click();
  assert.equal(fields.name_az.value,'Recovered title');
  assert.equal(fields.registration_method.value,'phone');
  assert.equal(fields.price_mode.value,'legacy');
  assert.equal(saved.values.registration_method,'phone');
});
