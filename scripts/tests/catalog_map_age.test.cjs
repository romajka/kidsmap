const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
const source=fs.readFileSync('static/js/catalog_map.js','utf8');
const context={window:{},document:{},console,setTimeout,clearTimeout};
vm.createContext(context);
vm.runInContext(source.replace(/  initCatalogMapUi\(\);\n\}\)\(\);\s*$/, '  globalThis.renderMapCard = renderMapCard;\n})();'),context);
const labels={noRatingLabel:'No reviews',noAddressLabel:'No address',noImageLabel:'No photo',detailsLabel:'Details',routeLabel:'Route',closeLabel:'Close'};
function card(members){return new JSDOM(context.renderMapCard({members},labels,false));}
test('catalogue map shows approximate ages and escapes the programme clarification',()=>{
 const dom=card([{id:1,name:'Theatre',url:'/place/1/',age:'Approximately 3–12 years',age_note:'Age depends on programme <img src=x onerror=alert(1)>'}]);
 try{
  assert.equal(dom.window.document.querySelector('.catalog-map-card-age')?.textContent,'Approximately 3–12 years');
  assert.match(dom.window.document.querySelector('.catalog-map-card-age-note')?.textContent||'',/Age depends on programme <img/);
  assert.equal(dom.window.document.querySelectorAll('[onerror]').length,0);
 }finally{dom.window.close();}
});
test('shared venue members keep individual ages and unknown ages make no claim',()=>{
 const dom=card([{id:1,name:'Theatre',age:'Approximately 3–12 years',age_note:'Age depends on programme'}, {id:2,name:'School',age:'10–15 years',age_note:''},{id:3,name:'Unknown',age:'',age_note:''}]);
 try{
  const rows=[...dom.window.document.querySelectorAll('.catalog-map-members > li')];
  assert.equal(rows[0].querySelector('.catalog-map-card-age')?.textContent,'Approximately 3–12 years');
  assert.equal(rows[1].querySelector('.catalog-map-card-age')?.textContent,'10–15 years');
  assert.equal(rows[1].querySelector('.catalog-map-card-age-note'),null);
  assert.equal(rows[2].querySelector('.catalog-map-card-age'),null);
 }finally{dom.window.close();}
});
