const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || 'jsdom');

function setup() {
  const dom = new JSDOM('<div data-specialist-documents data-selected-label="Selected:" data-remove-label="Remove" data-invalid-label="Invalid:"><input type="file" multiple><p data-document-status></p><ul data-document-files></ul><p data-document-error></p></div>', {runScripts:'outside-only'});
  const w=dom.window, input=w.document.querySelector('input');
  Object.defineProperty(input,'files',{writable:true,value:[]});
  w.DataTransfer=class {constructor(){this.files=[];this.items={add:file=>this.files.push(file)};}};
  w.eval(fs.readFileSync('static/js/specialist_documents.js','utf8'));
  w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
  const choose=files=>{input.files=files;input.dispatchEvent(new w.Event('change',{bubbles:true}));};
  return {dom,w,input,choose};
}
test('PDF and image names/count match submitted files and individual removal',()=>{
  const t=setup();
  t.choose([new t.w.File(['pdf'],'qualification.pdf',{type:'application/pdf'}),new t.w.File(['img'],'certificate.png',{type:'image/png'})]);
  assert.equal(t.w.document.querySelector('[data-document-status]').textContent,'Selected: 2');
  assert.match(t.w.document.querySelector('ul').textContent,/qualification.pdf/);
  assert.match(t.w.document.querySelector('ul').textContent,/certificate.png/);
  t.w.document.querySelector('button').click();
  assert.equal(t.input.files.length,1);assert.equal(t.input.files[0].name,'certificate.png');
  assert.equal(t.w.document.querySelector('[data-document-status]').textContent,'Selected: 1');
  t.dom.window.close();
});
test('additional selection preserves previous files and filenames are text, not HTML',()=>{
  const t=setup();
  t.choose([new t.w.File(['1'],'first.pdf')]);
  t.choose([new t.w.File(['2'],'<img src=x>.png')]);
  assert.equal(t.input.files.length,2);assert.equal(t.w.document.querySelectorAll('img').length,0);
  assert.match(t.w.document.querySelector('ul').textContent,/<img src=x>.png/);t.dom.window.close();
});
test('unsupported and empty files do not replace valid selection',()=>{
  const t=setup();t.choose([new t.w.File(['1'],'valid.pdf')]);
  t.choose([new t.w.File(['bad'],'file.exe'),new t.w.File([],'empty.png')]);
  assert.equal(t.input.files.length,1);assert.equal(t.input.files[0].name,'valid.pdf');
  assert.match(t.w.document.querySelector('[data-document-error]').textContent,/file.exe/);t.dom.window.close();
});
