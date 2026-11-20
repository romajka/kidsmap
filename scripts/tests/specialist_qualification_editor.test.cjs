const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || 'jsdom');

function row(index) {
  return `<fieldset data-qual-row>
    <legend><img hidden data-qual-preview alt=""><span data-qual-heading>Document</span><small data-qual-meta hidden></small></legend><span data-qual-body>
    <input type="hidden" name="qual-${index}-id"><input type="file" name="qual-${index}-file">
    <input name="qual-${index}-name"><select name="qual-${index}-type"><option value="diploma">Diploma</option><option value="certificate">Certificate</option></select>
    <input type="checkbox" name="qual-${index}-publish"></span><input type="checkbox" name="qual-${index}-DELETE"></fieldset>`;
}

function setup(withTransfer = true) {
  const dom = new JSDOM(`<form><section data-qualification-editor data-max-files="3" data-max-bytes="100" data-batch-bytes="120"
      data-size-error="File size" data-batch-error="Batch size" data-count-error="Count" data-format-error="Format" data-count-label="Documents">
    <div data-qual-picker hidden><input multiple type="file"></div><p data-qual-message></p><input name="qual-TOTAL_FORMS" value="1">
    <div data-qual-rows>${row(0)}</div><template>${row('__prefix__')}</template></section></form>`, {runScripts:'outside-only'});
  const w = dom.window;
  const lists = new WeakMap();
  Object.defineProperty(w.HTMLInputElement.prototype,'files',{get(){return lists.get(this) || [];},set(value){lists.set(this,value);}});
  if(withTransfer) w.DataTransfer = class {
    constructor(){this.files=[]; this.items={add:file => this.files.push(file)};}
  };
  w.eval(fs.readFileSync('static/js/specialist_qualification_editor.js','utf8'));
  w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
  const field = name => w.document.querySelector('[name="' + name + '"]');
  const select = (...files) => {
    const picker = w.document.querySelector('[data-qual-picker] input');
    picker.files = files;
    picker.dispatchEvent(new w.Event('change',{bubbles:true}));
  };
  const file = (name,size = 5) => new w.File([new Uint8Array(size)], name);
  return {dom,w,field,select,file};
}

test('multiple selections retain each row’s file, title and default private choice',()=>{
  const {dom,field,select,file} = setup();
  select(file('first.pdf'),file('second.jpg'));
  assert.equal(field('qual-0-file').files[0].name,'first.pdf');
  assert.equal(field('qual-1-name').value,'second');
  assert.equal(field('qual-1-publish').checked,false);
  field('qual-0-name').value='My title';
  select(file('third.png'));
  assert.equal(field('qual-0-name').value,'My title');
  assert.equal(field('qual-2-file').files[0].name,'third.png');
  assert.equal(field('qual-TOTAL_FORMS').value,'3');
  dom.window.close();
});

test('rejected files never become posted rows and selected files survive a capped batch',()=>{
  const {dom,w,field,select,file} = setup();
  select(file('ok.jpg',90),file('wrong.html'),file('over.pdf',102),file('next.png',50));
  assert.equal(field('qual-0-file').files[0].name,'ok.jpg');
  assert.equal(field('qual-TOTAL_FORMS').value,'1');
  const note=w.document.querySelector('[data-qual-message]').textContent;
  for(const name of ['wrong.html','over.pdf','next.png']) assert.ok(note.includes(name));
  dom.window.close();
});

test('document type uses the same keyboard picker on initial and appended rows', async () => {
  const {dom, w, field, select, file} = setup();
  try {
    const form = w.document.querySelector('form');
    form.className = 'km-specialist-owner-form';
    w.matchMedia = () => ({matches: false});
    w.eval(fs.readFileSync('static/js/specialist_form_fx.js', 'utf8'));
    select(file('first.pdf'), file('next.pdf'));
    await Promise.resolve();
    for (const index of [0, 1]) {
      const native = field('qual-' + index + '-type');
      const picker = native.closest('.kmfx-select');
      const trigger = picker.querySelector('[aria-haspopup=listbox]');
      trigger.click();
      const list = picker.querySelector('[role=listbox]');
      assert.equal(w.document.activeElement, list);
      for (const key of ['End', 'Enter']) {
        list.dispatchEvent(new w.KeyboardEvent('keydown', {key, bubbles: true}));
      }
      assert.equal(new w.FormData(form).get(native.name), 'certificate');
      assert.equal(trigger.getAttribute('aria-expanded'), 'false');
      assert.equal(w.document.activeElement, trigger);
    }
  } finally {
    dom.window.close();
  }
});

test('without FileList assignment support the native single-file row remains available',()=>{
  const {dom,w,field} = setup(false);
  assert.equal(w.document.querySelector('[data-qual-picker]').hidden,true);
  assert.equal(field('qual-0-file').closest('[data-qual-row]').hidden,false);
  dom.window.close();
});

test('removing a queued file releases its place without shifting other documents or consent',()=>{
  const {dom,w,field,select,file} = setup();
  select(file('one.png'),file('two.pdf'));
  field('qual-0-publish').checked = true;
  field('qual-1-type').value = 'certificate';
  const remove = field('qual-0-DELETE');
  remove.checked = true;
  remove.dispatchEvent(new w.Event('change',{bubbles:true}));
  assert.equal(field('qual-0-DELETE').checked, true);
  select(file('replacement.jpg'));
  assert.equal(field('qual-0-DELETE').checked, false);
  assert.equal(field('qual-0-file').files[0].name,'replacement.jpg');
  assert.equal(field('qual-0-publish').checked,false);
  assert.equal(field('qual-1-file').files[0].name,'two.pdf');
  assert.equal(field('qual-1-type').value,'certificate');
  assert.equal(field('qual-TOTAL_FORMS').value,'2');
  dom.window.close();
});

test('picked files show localized metadata and image-only previews, releasing discarded URLs', () => {
  const {dom,w,field,select,file} = setup();
  const released = [];
  w.URL.createObjectURL = () => 'blob:local-image';
  w.URL.revokeObjectURL = url => released.push(url);
  const picture = new w.File([new Uint8Array(25)], 'photo.png', {type: 'image/png'});
  select(picture, file('study.pdf'));
  const photo = field('qual-0-name').closest('fieldset');
  const pdf = field('qual-1-name').closest('fieldset');
  assert.match(photo.querySelector('[data-qual-meta]').textContent, /PNG.*25/);
  assert.match(pdf.querySelector('[data-qual-meta]').textContent, /PDF/);
  assert.equal(photo.querySelector('[data-qual-preview]').getAttribute('src'), 'blob:local-image');
  assert.equal(pdf.querySelector('[data-qual-preview]').hasAttribute('src'), false);
  const remove = field('qual-0-DELETE');
  remove.checked = true;
  remove.dispatchEvent(new w.Event('change', {bubbles:true}));
  assert.deepEqual(released, ['blob:local-image']);
  dom.window.close();
});
