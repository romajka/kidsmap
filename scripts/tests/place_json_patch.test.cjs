const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');

async function importPatch(data,withServer=false,formAttributes='data-km-admin-form'){
 const dom=new JSDOM(`<!doctype html><form ${formAttributes}>
 <input id="id_website" value="https://example.com/old"><input id="id_name_az" value="Existing">
 <input type="checkbox" id="id_age_varies_by_program" checked>
 <input id="id_schedule" value="Old text"><input id="id_phone2" value="old">
 <input id="id_price_per_lesson" value="35"><input id="id_pricing_plans" value="[]">
 <button type="button" data-place-json-import-open>Import</button>
 <dialog data-place-json-import-dialog><textarea data-place-json-import-input></textarea>
 <p data-place-json-import-message></p><button type="button" data-place-json-import-apply>Apply</button>
 <button type="button" data-place-json-import-close>Close</button></dialog></form>`,{runScripts:'outside-only'});
 const w=dom.window;w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};
 w.HTMLDialogElement.prototype.close=function(){this.open=false;};
 w.kmModal={show:options=>options.actions.find(a=>a.tone==='primary').onClick()};
 let toast;w.kmToast={success:(title,message)=>toast={title,message}};
 if(withServer){
  w.document.querySelector('[data-place-json-import-dialog]').dataset.pricingValidateUrl='/validate/';
  w.document.getElementById('id_pricing_plans').value='[{"product_type":"lesson","price":"35"}]';
  w.fetch=async()=>({ok:true,json:async()=>({ok:true,pricing_plans:[],contacts:{},warnings:[]})});
 }
 const ready=new Promise(resolve=>w.document.addEventListener('DOMContentLoaded',resolve,{once:true}));
 w.eval(fs.readFileSync('static/admin/js/kidsmap_place_json_import.js','utf8'));await ready;
 w.document.querySelector('[data-place-json-import-open]').click();
 w.document.querySelector('textarea').value=JSON.stringify(data);
 w.document.querySelector('[data-place-json-import-apply]').click();for(let i=0;i<8;i++)await Promise.resolve();
 return {checked:id=>w.document.getElementById('id_'+id).checked,value:id=>w.document.getElementById('id_'+id).value,toast:()=>toast,close:()=>w.close()};
}

test('explicit empty optional text clears while omitted and unknown-null values preserve data',async()=>{
 const m=await importPatch({website:'',phone2:null});try{assert.equal(m.value('website'),'');assert.equal(m.value('phone2'),'old');assert.equal(m.value('name_az'),'Existing');assert.equal(m.value('price_per_lesson'),'35');}finally{m.close();}
});
test('legacy text schedule from an actual export is applied with the other fields',async()=>{
 const m=await importPatch({schedule:'Mon-Fri 10:00-19:00',website:'https://example.com/new'});try{assert.equal(m.value('schedule'),'Mon-Fri 10:00-19:00');assert(!m.toast().message.includes('schedule.'));}finally{m.close();}
});
test('all unrecognized JSON fields are visible in the import result',async()=>{
 const m=await importPatch({website:'https://example.com/new',custom_one:1,custom_two:2,custom_three:3,custom_four:4});try{for(const key of ['custom_one','custom_two','custom_three','custom_four'])assert(m.toast().message.includes(key),key);}finally{m.close();}
});
test('unknown-null pricing survives server validation without clearing saved tariffs',async()=>{
 for(const key of ['pricing_plans','tariffs']){
  const m=await importPatch({website:'https://example.com/new',[key]:null},true);
  try{assert.deepEqual(JSON.parse(m.value('pricing_plans')),[{product_type:'lesson',price:'35'}]);}finally{m.close();}
 }
});
test('volunteer JSON uses the current owned form identity',async()=>{
 const m=await importPatch({place_id:12,website:'https://example.com/new'},true,'data-volunteer-admin-form data-place-id="12"');
 try{assert.equal(m.value('website'),'https://example.com/new');}finally{m.close();}
});

test('programme-dependent age checkbox accepts true and explicit false and preserves omitted values', async()=>{
 for(const [data,expected] of [[{age_varies_by_program:true},true],[{age_varies_by_program:false},false],[{age_varies_by_program:null},true],[{},true]]){
  const m=await importPatch(data);
  try{assert.equal(m.checked('age_varies_by_program'),expected);if(m.toast())assert(!m.toast().message.includes('age_varies_by_program'));}finally{m.close();}
 }
});

test('duplicate registry exports cannot be accidentally applied as an editing patch',async()=>{
 for(const scope of ['duplicate_registry','identity_comparison']){
  const m=await importPatch({export_scope:scope,website:'https://example.com/should-not-apply',records:[]});
  try{assert.equal(m.value('website'),'https://example.com/old');assert.equal(m.toast(),undefined);}finally{m.close();}
 }
});
