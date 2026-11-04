const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
const read=p=>fs.readFileSync(path.join(__dirname,'../../',p),'utf8').replace(/\r\n/g,'\n');
const catalog=read('src/catalog/templates/catalog/place_list.html').split('/* ─── Unified Custom Selects Interactivity ─── */')[1].split('\n\n\n    (function ()')[0];
const organization=read('static/js/public_organization.js').split('    function initCustomSelects() {')[1].split('\n    function resetFilters()')[0];
for(const [name,source] of [['catalog',catalog],['organization','function initCustomSelects(){'+organization+';initCustomSelects();']]){
 test(name+': keyboard opens, selects and restores focus',()=>{
 const dom=new JSDOM(`<div class="km-custom-select"><button class="km-custom-select__trigger">Category</button><span class="km-custom-select__value"></span><div class="km-custom-select__menu" role="listbox"><div class="km-custom-select__option is-selected" data-value="">All</div><div class="km-custom-select__option" data-value="art">Art</div></div><select><option value="">All</option><option value="art">Art</option></select></div>`,{runScripts:'outside-only'});
 const w=dom.window,d=w.document;w.eval(source);const trigger=d.querySelector('button'),opts=d.querySelectorAll('.km-custom-select__option');
 const key=k=>d.activeElement.dispatchEvent(new w.KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true}));
 trigger.focus();key('ArrowDown');assert.equal(d.activeElement,opts[0]);key('ArrowDown');key('Enter');assert.equal(d.querySelector('select').value,'art');assert.equal(d.activeElement,trigger);assert.equal(trigger.getAttribute('aria-expanded'),'false');
 let escapedParent=0;d.addEventListener('keydown',e=>{if(e.key==='Escape')escapedParent++});key('ArrowDown');key('Escape');assert.equal(escapedParent,0);assert.equal(d.activeElement,trigger);assert.equal(trigger.getAttribute('aria-expanded'),'false');w.close();
 });
}
