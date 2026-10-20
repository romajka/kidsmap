const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('static/js/home_map.js','utf8');
function setup(){
 const low=new EventTarget(),high=new EventTarget(),reset=new EventTarget();low.value='0';high.value='12';
 const form={dataset:{},querySelector:s=>({'[name="age_from"]':low,'[name="age_to"]':high,'[data-home-search-reset]':reset}[s]||null),addEventListener(){}};
 let updates=0;const ctx={document:{querySelector:()=>form},getDistrictOptions:()=>[],getAgeInput:()=>null,getAgeButtons:()=>[],syncAgeButtons(){},initHomeSearchAutocomplete(){},scrollToMap(){},normalizeValue:v=>String(v??'').trim(),normalizeSearch:v=>String(v??'').trim(),window:{setTimeout:f=>{f();return 1},clearTimeout(){}}};
 vm.createContext(ctx);vm.runInContext(source.slice(source.indexOf('  function bindFilterListeners('),source.indexOf('  function mountGoogleMap(')),ctx);
 vm.runInContext(source.slice(source.indexOf('  function getFilterState('),source.indexOf('  function isPlaceInBaku(')),ctx);
 vm.runInContext(source.slice(source.indexOf('  function hasActiveFilters('),source.indexOf('  // Baku bounding box')),ctx);
 ctx.bindFilterListeners(()=>updates++);return{ctx,low,high,reset,get updates(){return updates}};
}
test('both range bounds trigger existing map updater',()=>{const t=setup();t.low.dispatchEvent(new Event('change'));t.high.dispatchEvent(new Event('change'));assert.equal(t.updates,2)});
test('reset clears both bounds',()=>{const t=setup();t.reset.dispatchEvent(new Event('click'));assert.equal(t.low.value,'');assert.equal(t.high.value,'')});
test('zero is an active lower bound in map viewport state',()=>{const t=setup();const state=t.ctx.getFilterState();assert.equal(state.age_from,'0');assert.equal(state.age_to,'12');assert.equal(t.ctx.hasActiveFilters(state),true)});
test('an invalid bound does not refresh the map',()=>{const t=setup();t.low.checkValidity=()=>false;t.low.dispatchEvent(new Event('change'));assert.equal(t.updates,0)});
