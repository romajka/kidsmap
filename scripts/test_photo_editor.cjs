// Uses the same temporary jsdom setup as scripts/test_phone_reveal.cjs.
// Run: node --test scripts/test_photo_editor.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require('../.tmp/phone-dom/node_modules/jsdom');
const source = fs.readFileSync(path.join(__dirname,'../static/js/permanent_place_photos.js'),'utf8');
const tick = () => new Promise(resolve => setImmediate(resolve));
function setup({saved=false, failSave=false, rendered=''}={}) {
  const savedNode = id => `<div data-photo-saved="${id}" data-photo-name="${id}.webp" data-photo-url="/media/${id}.webp" data-photo-preview="/thumb/${id}"></div>`;
  const dom = new JSDOM(rendered || `<html lang="ru"><script id="pw-photo-config" type="application/json">${JSON.stringify({sourceBytes:15*1024*1024,outputBytes:2*1024*1024,batchBytes:22*1024*1024,maxPixels:50000000,maxDimension:12000,maxGallery:10,heif:true})}</script>
    <form><input name="csrfmiddlewaretoken" value="csrf">
    <section data-photo-editor data-prepare-url="/prepare/" data-save-url="/save/">
    <div data-photo-zone="main"><input type="file" name="photo"></div><div data-photo-errors="main"></div>
    <div data-photo-items="main">${saved?savedNode('main'):''}</div>
    <label data-photo-fallback-clear><input name="photo-clear" type="checkbox"></label>
    <div data-photo-zone="gallery"><input type="file" name="gallery_images" multiple></div><div data-photo-errors="gallery"></div>
    <p data-photo-gallery-help></p><span data-photo-count></span>
    <div data-photo-items="gallery">${saved?savedNode('11')+savedNode('12'):''}</div>
    <div data-photo-fallback-delete>${saved?'<input name="delete_gallery_ids" type="checkbox" value="11"><input name="delete_gallery_ids" type="checkbox" value="12">':''}</div>
    <input name="gallery_order"><p data-photo-save-status></p></section>
    <button name="form_action" value="save_draft" type="submit">Save</button></form></html>`, {url:'https://kidsmap.example/',runScripts:'outside-only'});
  const w = dom.window, calls=[], revoked=[];
  // jsdom lacks native file transfer, canvas and image decoding. Only those
  // platform boundaries and network are substituted; editor logic is real.
  w.DataTransfer = class {constructor(){this.files=[];this.items={add:file=>this.files.push(file)};}};
  Object.defineProperty(w.HTMLInputElement.prototype,'files',{get(){return this._files||[];},set(files){this._files=files;}});
  w.Blob.prototype.arrayBuffer = function(){return new Promise(resolve=>{const reader=new w.FileReader();reader.onload=()=>resolve(reader.result);reader.readAsArrayBuffer(this);});};
  w.Blob.prototype.text = function(){return new Promise(resolve=>{const reader=new w.FileReader();reader.onload=()=>resolve(reader.result);reader.readAsText(this);});};
  let seq=0;w.URL.createObjectURL=()=>`blob:thumb-${++seq}`;w.URL.revokeObjectURL=url=>revoked.push(url);
  w.createImageBitmap=async()=>({width:1200,height:800,close(){}});
  w.HTMLCanvasElement.prototype.getContext=()=>({drawImage(){}});
  w.HTMLCanvasElement.prototype.toBlob=function(done){assert.ok(this.width<=320);assert.ok(this.height<=320);done(new w.Blob(['thumbnail'],{type:'image/webp'}));};
  let saveCount=0;
  w.XMLHttpRequest = class {
    constructor(){this.upload={};}
    open(method,url){this.url=url;assert.equal(method,'POST');}
    setRequestHeader(name,value){assert.equal(name,'X-CSRFToken');assert.equal(value,'csrf');}
    async send(data){
      calls.push({url:this.url,data});
      if(this.url==='/prepare/') {
        this.status=200;this.response=new w.Blob([await data.get('photo').arrayBuffer()],{type:'image/webp'});
      } else {
        saveCount++;this.status=failSave && saveCount===1 ? 422 : 200;
        this.response=this.responseText=JSON.stringify(this.status===200?{ok:true,redirect:'/edit/#photos'}:{errors:{photo:['storage unavailable']}});
      }
      this.onload();
    }
  };
  w.fetch=async()=>({ok:true,blob:async()=>new w.Blob(['saved-image'],{type:'image/webp'})});
  w.eval(source);
  const form=w.document.querySelector('[data-permanent-place-form]') || w.document.querySelector('form'), editor=rendered ? null : w.KidsMapPhotoEditor.mount(form);
  function file(name,tag=1){const bytes=new Uint8Array(32);bytes.set([137,80,78,71,13,10,26,10]);new DataView(bytes.buffer).setUint32(16,64);new DataView(bytes.buffer).setUint32(20,48);bytes[31]=tag;return new w.File([bytes],name,{type:'image/png'});}
  return {dom,w,form,editor,file,calls,revoked};
}
test('gallery accumulates selections and rejects content duplicates with different names',async()=>{
  const t=setup();
  t.editor.addFiles([t.file('a.png',1)],'gallery');await t.editor.ready();
  t.editor.addFiles([t.file('b.png',2),t.file('renamed.png',1)],'gallery');await t.editor.ready();
  assert.equal(t.form.elements.gallery_images.files.length,2);
  assert.equal(t.w.document.querySelector('[data-photo-count]').textContent,'2 из 10');
  assert.match(t.w.document.querySelector('[data-photo-errors=gallery]').textContent,/уже добавлено/);
  assert.equal(t.calls.length,2);t.dom.window.close();
});
test('invalid format, size and count are rejected before uploading',async()=>{
  const t=setup();
  t.editor.addFiles([new t.w.File(['bad'],'bad.gif',{type:'image/gif'}),new t.w.File([],'empty.png',{type:'image/png'})],'gallery');
  assert.equal(t.calls.length,0);
  t.editor.addFiles(Array.from({length:11},(_,i)=>t.file(`${i}.png`,i)),'gallery');await t.editor.ready();
  assert.equal(t.calls.length,10);assert.equal(t.form.elements.gallery_images.files.length,10);
  assert.match(t.w.document.querySelector('[data-photo-errors=gallery]').textContent,/10 дополнительных/);t.dom.window.close();
});
test('file drop adds photos, arrows reorder them and make-main moves the selected photo',async()=>{
  const t=setup(),zone=t.w.document.querySelector('[data-photo-zone=gallery]');
  const event=new t.w.Event('drop',{bubbles:true,cancelable:true});Object.defineProperty(event,'dataTransfer',{value:{files:[t.file('a.png',1),t.file('b.png',2)],types:['Files']}});zone.dispatchEvent(event);await t.editor.ready();
  assert.equal(event.defaultPrevented,true);
  t.w.document.querySelector('[data-photo-items=gallery] [data-photo-action=down]').click();
  assert.equal(t.form.elements.gallery_images.files[0].name,'b.webp');
  t.w.document.querySelector('[data-photo-items=gallery] [data-photo-action=main]').click();await tick();
  assert.equal(t.form.elements.photo.files[0].name,'b.webp');assert.equal(t.form.elements.gallery_images.files.length,1);
  t.w.document.querySelector('[data-photo-items=main] [data-photo-action=remove]').click();assert.ok(t.revoked.length);t.dom.window.close();
});
test('saved gallery promotion swaps the old main and marks only the promoted stored row for deletion',async()=>{
  const t=setup({saved:true});
  t.w.document.querySelector('[data-photo-items=gallery] [data-photo-action=main]').click();await tick();
  assert.equal(t.form.elements.photo.files[0].name,'11.webp');
  assert.equal(t.form.elements.gallery_images.files[0].name,'main.webp');
  assert.deepEqual([...t.form.querySelectorAll('[name=delete_gallery_ids]:checked')].map(node=>node.value),['11']);
  assert.deepEqual(JSON.parse(t.form.elements.gallery_order.value),['new:0','saved:12']);t.dom.window.close();
});
test('failed save retains selected files, retry uses the same request ID and success is marked saved',async()=>{
  const t=setup({failSave:true});t.editor.addFiles([t.file('main.png')],'main');await t.editor.ready();
  const button=t.form.querySelector('[name=form_action]');
  const first=await t.editor.save(button);assert.equal(first.ok,false);assert.equal(t.form.elements.photo.files.length,1);
  assert.match(t.w.document.querySelector('[data-photo-save-status]').textContent,/Не удалось сохранить/);
  const second=await t.editor.save(button);assert.equal(second.ok,true);
  const saves=t.calls.filter(call=>call.url==='/save/');assert.equal(saves[0].data.get('photo_request_id'),saves[1].data.get('photo_request_id'));
  assert.equal(saves[0].data.get('photo').name,'main.webp');
  assert.equal(t.w.document.querySelector('[data-photo-save-status]').textContent,'Сохранено');t.dom.window.close();
});
test('preview falls back to Image when createImageBitmap is unavailable',async()=>{
  const t=setup();delete t.w.createImageBitmap;
  t.w.Image=class {constructor(){this.width=this.naturalWidth=1200;this.height=this.naturalHeight=800;}set src(value){queueMicrotask(()=>this.onload());}};
  t.editor.addFiles([t.file('main.png')],'main');await t.editor.ready();
  assert.equal(t.editor.hasMain(),true);assert.ok(t.revoked.length);t.dom.window.close();
});
test('oversized resolution is rejected before network and a failed replacement can be removed without losing the saved main',async()=>{
  const t=setup({saved:true});
  const bytes=await t.file('huge.png').arrayBuffer();new DataView(bytes).setUint32(16,12001);
  t.editor.addFiles([new t.w.File([bytes],'huge.png',{type:'image/png'})],'main');await t.editor.ready();
  assert.equal(t.calls.length,0);assert.match(t.w.document.querySelector('[data-photo-items=main]').textContent,/12000/);
  t.w.document.querySelector('[data-photo-items=main] [data-photo-action=remove]').click();
  assert.equal(t.editor.hasMain(),true);assert.equal(t.form.elements['photo-clear'].checked,false);t.dom.window.close();
});
const renderedFile=path.join(__dirname,'../.tmp/photo-form.html');
test('photo editor boots inside the actual Django wizard HTML', {skip:!fs.existsSync(renderedFile)},async()=>{
  const t=setup({rendered:fs.readFileSync(renderedFile,'utf8')});
  t.w.HTMLElement.prototype.scrollIntoView=function(){};
  t.w.matchMedia=()=>({matches:false});
  t.w.localStorage.setItem('kidsmap:permanent:v1:'+t.form.dataset.draftKey,JSON.stringify({at:Date.now(),step:6,ageMode:'range',data:{gallery_order:'["new:0"]','photo-clear':true}}));
  t.w.eval(fs.readFileSync(path.join(__dirname,'../static/js/permanent_place_wizard.js'),'utf8'));
  assert.ok(t.form.photoEditor);
  assert.equal(t.form.elements.gallery_order.value,'[]');
  assert.equal(t.form.elements['photo-clear'].checked,false);
  t.form.querySelector('[data-pw-go="6"]').click();
  assert.equal(t.form.querySelector('[data-pw-step="6"]').hidden,false);
  assert.equal(t.form.querySelectorAll('input[name=photo]').length,1);
  assert.equal(t.form.querySelectorAll('input[name=gallery_images]').length,1);
  t.dom.window.close();
});
