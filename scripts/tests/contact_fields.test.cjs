const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || '../../.tmp/phone-dom/node_modules/jsdom');
const source = fs.readFileSync('static/js/kidsmap_contact_fields.js', 'utf8');
function editor(mode='separate', error='') {
 const dom = new JSDOM(`<form><select name="whatsapp_mode"><option>legacy</option><option>same</option><option>separate</option><option>none</option></select><div data-pw-field="whatsapp_number"><input name="whatsapp_number" value="+1 310 456 4918">${error}</div><input name="phone1" value="+994 50 427 43 93"></form>`, {runScripts:'outside-only'});
 dom.window.document.querySelector('select').value=mode;
 dom.window.eval(source);dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
 return dom;
}
test('mode changes hide separate field without losing or rewriting either contact', () => {
 const dom=editor(), doc=dom.window.document, mode=doc.querySelector('select'), number=doc.querySelector('[name=whatsapp_number]'), row=number.parentElement;
 assert.equal(row.hidden,false);
 for(const choice of ['none','same','legacy']) {mode.value=choice;mode.dispatchEvent(new dom.window.Event('change'));assert.equal(row.hidden,true);assert.equal(number.disabled,false);assert.equal(number.value,'+1 310 456 4918');assert.equal(doc.querySelector('[name=phone1]').value,'+994 50 427 43 93');}
 mode.value='separate';mode.dispatchEvent(new dom.window.Event('change'));assert.equal(row.hidden,false);assert.equal(number.getAttribute('aria-required'),'true');
 dom.window.close();
});
test('server validation errors remain visible even when separate mode is off', () => {
 const dom=editor('none','<p class="pw-error">Invalid contact</p>');assert.equal(dom.window.document.querySelector('[data-pw-field]').hidden,false);dom.window.close();
});
