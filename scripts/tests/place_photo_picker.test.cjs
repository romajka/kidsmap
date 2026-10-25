const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
function mount(hasCover=false){
 const file='static/js/kidsmap_place_photo_picker.js';assert(fs.existsSync(file),'Place needs a unified photo picker');
 const d=new JSDOM(`<form><div data-place-media-section><input data-place-photos-picker type=file multiple><input id=id_photo type=file><div data-main-photo-root class="${hasCover?'has-photo':''}"></div><div data-gallery-root></div></div></form>`,{runScripts:'outside-only'});
 class Transfer{constructor(){this.files=[];this.items={add:file=>this.files.push(file)};}}
 d.window.DataTransfer=Transfer;
 const main=d.window.document.getElementById('id_photo');let files=[];Object.defineProperty(main,'files',{get:()=>files,set:v=>{files=v}});
 const gallery=[];d.window.document.querySelector('[data-gallery-root]').kidsmapAddGalleryPhotos=added=>gallery.push(...added);
 d.window.eval(fs.readFileSync(file,'utf8'));d.window.document.dispatchEvent(new d.window.Event('DOMContentLoaded'));
 return{d,main,gallery,pick(values){const input=d.window.document.querySelector('[data-place-photos-picker]');Object.defineProperty(input,'files',{value:values,configurable:true});input.dispatchEvent(new d.window.Event('change',{bubbles:true}));}};
}
test('one batch routes first new photo to cover and remaining photos to the real gallery handler',()=>{const m=mount();try{m.pick([{name:'one.png'},{name:'two.png'},{name:'three.png'}]);assert.equal(m.main.files[0].name,'one.png');assert.deepEqual(m.gallery.map(x=>x.name),['two.png','three.png']);}finally{m.d.window.close();}});
test('adding photos never replaces an existing cover',()=>{const m=mount(true);try{m.pick([{name:'new.png'}]);assert.equal(m.main.files.length,0);assert.equal(m.gallery[0].name,'new.png');}finally{m.d.window.close();}});
test('mounted admin picker advertises the unified controls while preserving native transport',()=>{const m=mount();try{assert(m.d.window.document.querySelector('[data-place-media-section][data-km-photo-unified]'));assert(m.main);}finally{m.d.window.close();}});
test('visible shared drop zone handles file drop exactly like the native picker',()=>{const m=mount();try{const zone=m.d.window.document.querySelector('[data-place-photos-picker]').closest('[data-km-photo-drop]');assert.ok(zone,'shared picker must expose the actual drop target');const e=new m.d.window.Event('drop',{bubbles:true,cancelable:true});Object.defineProperty(e,'dataTransfer',{value:{types:['Files'],files:[{name:'main.png'},{name:'gallery.png'}]}});zone.dispatchEvent(e);assert.equal(e.defaultPrevented,true);assert.equal(m.main.files[0].name,'main.png');assert.equal(m.gallery[0].name,'gallery.png');}finally{m.d.window.close();}});
