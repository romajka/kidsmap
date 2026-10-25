const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || '../../.tmp/phone-dom/node_modules/jsdom');
const source = fs.readFileSync('static/js/kidsmap_contact_fields.js', 'utf8');

function phones(values=['','']){const d=new JSDOM(`<form data-km-editor><div data-km-phone-list><div data-pw-field="phone1"><input name="phone1"></div>${values.map((v,i)=>`<div data-km-phone-slot data-pw-field="phone${i+2}"><input name="phone${i+2}" value="${v}"><button type="button" data-km-phone-remove>Remove</button></div>`).join('')}<button type="button" data-km-phone-add>Add phone</button></div></form>`,{runScripts:'outside-only'});d.window.eval(source);d.window.document.dispatchEvent(new d.window.Event('DOMContentLoaded'));return d;}
test('phone editor starts with one phone and reveals at most three without shifting saved numbers',()=>{const d=phones(),w=d.window,slots=[...w.document.querySelectorAll('[data-km-phone-slot]')],add=w.document.querySelector('[data-km-phone-add]');assert(slots.every(s=>s.hidden));add.click();assert.equal(slots[0].hidden,false);assert.equal(slots[1].hidden,true);add.click();assert(slots.every(s=>!s.hidden));assert(add.disabled);const last=slots[1].querySelector('input');last.value='+994501234567';slots[0].querySelector('[data-km-phone-remove]').click();assert.equal(slots[0].querySelector('input').value,'');assert.equal(last.value,'+994501234567');assert.equal(add.disabled,false);w.close();});
test('saved secondary phone and a linked validation error are visible on restore',()=>{const d=phones(['','+13104564918']),w=d.window,slots=[...w.document.querySelectorAll('[data-km-phone-slot]')];assert.equal(slots[1].hidden,false);const input=slots[0].querySelector('input');input.value='bad';input.dispatchEvent(new w.Event('change',{bubbles:true}));assert.equal(slots[0].hidden,false);slots[0].hidden=true;w.document.querySelector('form').dispatchEvent(new w.CustomEvent('km:reveal-field',{detail:{element:input}}));assert.equal(slots[0].hidden,false);w.close();});
function editor(mode='separate', error='', enhanced=false) {
 const dom = new JSDOM(`<form><select name="whatsapp_mode"><option>legacy</option><option>same</option><option>separate</option><option>none</option></select><div data-pw-field="whatsapp_number"><input name="whatsapp_number" value="+1 310 456 4918">${error}</div><input name="phone1" value="+994 50 427 43 93"></form>`, {runScripts:'outside-only'});
 dom.window.document.querySelector('select').value=mode;
 if(enhanced){dom.window.eval(fs.readFileSync(process.env.KIDSMAP_JQUERY,'utf8'));dom.window.eval(fs.readFileSync(process.env.KIDSMAP_SELECT2,'utf8'));dom.window.jQuery('select').select2();}
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
test('actual Select2 change opens the separate WhatsApp number',{
 skip:!process.env.KIDSMAP_JQUERY||!process.env.KIDSMAP_SELECT2?'Real admin vendor paths required':false
},()=>{
 const dom=editor('none','',true),w=dom.window,field=w.document.querySelector('[name=whatsapp_number]');
 try{assert.equal(field.parentElement.hidden,true);w.jQuery('select').val('separate').trigger('change');assert.equal(field.parentElement.hidden,false);assert.equal(field.getAttribute('aria-required'),'true');}finally{w.jQuery('select').select2('destroy');w.close();}
});
test('shared validation reveals a hidden WhatsApp error and hides it after correction',()=>{
 const dom=editor('none'),w=dom.window,form=w.document.querySelector('form'),number=form.querySelector('[name=whatsapp_number]');
 form.setAttribute('data-km-editor','');w.HTMLElement.prototype.scrollIntoView=function(){};w.matchMedia=()=>({matches:true});
 w.eval(fs.readFileSync('static/js/kidsmap_editor_ux.js','utf8'));w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
 assert.equal(number.parentElement.hidden,true);w.KidsMapEditorUX.setErrors(form,{whatsapp_number:['Исправьте номер']},{focus:false});
 assert.equal(number.parentElement.hidden,false);number.value='';number.dispatchEvent(new w.Event('input',{bubbles:true}));
 assert.equal(number.parentElement.hidden,true);w.close();
});
