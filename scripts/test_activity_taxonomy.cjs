// Run: node --test scripts/test_activity_taxonomy.cjs (same jsdom dependency as phone tests)
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require('../.tmp/phone-dom/node_modules/jsdom');
const source = fs.readFileSync(require('node:path').join(__dirname, '../static/js/owner_place_offerings.js'), 'utf8');
function setup(activity = {id:null, program_id:null, groups:[]}) {
  const dom = new JSDOM('<html lang="en"><body><script id="pw-copy" type="application/json"></script><script id="pc-offering-choices" type="application/json"></script><div data-pc-offerings><input name="nested_pricing"><div data-pc-activity-list></div><button data-pc-add-activity></button></div></body></html>', {runScripts:'outside-only'});
  const doc = dom.window.document;
  doc.getElementById('pw-copy').textContent = JSON.stringify({add_activity:'Activity',activity_name:'Name (AZ)',activity_description:'Description (AZ)',shared_program:'Program',local_activity:'Standalone',translations:'Translations',category:'Category',subcategory:'Subcategory',copy_place_taxonomy:'Copy Place category',taxonomy_reset:'Subcategory cleared',add_group:'Group',remove_activity:'Remove'});
  doc.getElementById('pc-offering-choices').textContent = JSON.stringify({categories:[{id:'ART',label:'Art'},{id:'SPORT',label:'Sport'}],subcategories:[{id:1,category_id:'ART',label:'Painting'},{id:2,category_id:'SPORT',label:'Swimming'}],place_taxonomy:{category_id:'ART',subcategory_id:1},programs:[{id:8,name_az:'Approved program'}]});
  const input = doc.querySelector('[name="nested_pricing"]');
  input.value = JSON.stringify({pricing_schema_version:2,activities:[activity]});
  dom.window.eval(source);
  return {dom,doc,read:()=>JSON.parse(input.value).activities[0]};
}
test('standalone taxonomy stays own; Place is copied only by explicit action', () => {
  const {dom,doc,read} = setup();
  try {
    assert.equal(doc.querySelector('[data-activity-category]').value, '');
    assert.equal(read().category_id, undefined);
    doc.querySelector('[data-copy-place-taxonomy]').click();
    assert.equal(read().category_id, 'ART');
    assert.equal(read().subcategory_id, 1);
    assert.equal(doc.querySelector('[data-activity-subcategory]').value, '1');
  } finally {dom.window.close();}
});
test('changing category clears incompatible child, announces it and preserves focus', () => {
  const {dom,doc,read} = setup({id:4,program_id:null,category_id:'ART',subcategory_id:1,groups:[]});
  try {
    const category = doc.querySelector('[data-activity-category]'); category.focus(); category.value='SPORT';
    category.dispatchEvent(new dom.window.Event('change', {bubbles:true}));
    assert.equal(read().category_id, 'SPORT'); assert.equal(read().subcategory_id, null);
    assert.equal(doc.activeElement, category);
    assert.deepEqual([...doc.querySelector('[data-activity-subcategory]').options].map(x=>x.value), ['', '2']);
    assert.equal(doc.querySelector('[data-taxonomy-status][role="status"]').textContent, 'Subcategory cleared');
  } finally {dom.window.close();}
});
test('linked activity offers no local taxonomy override', () => {
  const {dom,doc} = setup({id:5,program_id:8,groups:[]});
  try {assert.equal(doc.querySelector('[data-activity-category], [data-copy-place-taxonomy]'), null);} finally {dom.window.close();}
});
