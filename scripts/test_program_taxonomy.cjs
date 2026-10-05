const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require('../.tmp/phone-dom/node_modules/jsdom');
test('Program category reset announces incompatible child without losing keyboard focus', () => {
  const dom = new JSDOM('<form><select name="category"><option value="ART">Art</option><option value="SPORT">Sport</option></select><select name="subcategory" data-reset-message="Subcategory cleared" aria-describedby="taxonomy-status"><option value="">—</option><option value="1" data-category="ART" selected>Painting</option><option value="2" data-category="SPORT">Swimming</option></select><p id="taxonomy-status" role="status"></p></form>', {runScripts:'outside-only'});
  try {
    dom.window.eval(fs.readFileSync(require('node:path').join(__dirname, '../static/js/kidsmap_dependent_subcategory.js'), 'utf8'));
    dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
    const category = dom.window.document.querySelector('[name="category"]'), child=dom.window.document.querySelector('[name="subcategory"]');
    assert.equal(child.value, '1');
    category.focus(); category.value='SPORT'; category.dispatchEvent(new dom.window.Event('change'));
    assert.equal(child.value, ''); assert.equal(dom.window.document.activeElement, category);
    assert.deepEqual([...child.options].map(x=>x.value), ['', '2']);
    assert.equal(dom.window.document.getElementById('taxonomy-status').textContent, 'Subcategory cleared');
  } finally {dom.window.close();}
});
