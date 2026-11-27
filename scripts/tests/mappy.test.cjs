const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require('../../.tmp/phone-dom/node_modules/jsdom');
const file=require('node:path').join(__dirname,'../../static/js/mappy.js');
function setup({dismissed=false,reduced=false,storageBlocked=false}={}) {
  const dom=new JSDOM(`<section data-mappy-helper><div data-mappy-content><img alt=""><p>Choose an area</p><button data-mappy-dismiss>Hide</button></div><button data-mappy-restore hidden>Show helper</button></section>`,{url:'https://kidsmap.example/',runScripts:'outside-only'});
  const w=dom.window;w.matchMedia=()=>({matches:reduced,addEventListener(){}});
  if(dismissed)w.sessionStorage.setItem('kidsmap:mappy:hidden','1');
  if(storageBlocked)Object.defineProperty(w,'sessionStorage',{get(){throw Error('blocked');}});
  if(fs.existsSync(file))w.eval(fs.readFileSync(file,'utf8'));
  w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
  return dom;
}
test('dismiss and restore preserve focus and session choice without removing guidance',()=>{
 const dom=setup(),d=dom.window.document;
 d.querySelector('[data-mappy-dismiss]').click();
 assert.equal(d.querySelector('[data-mappy-content]').hidden,true);
 assert.equal(d.activeElement,d.querySelector('[data-mappy-restore]'));
 assert.equal(dom.window.sessionStorage.getItem('kidsmap:mappy:hidden'),'1');
 d.querySelector('[data-mappy-restore]').click();
 assert.equal(d.querySelector('[data-mappy-content]').hidden,false);
 assert.equal(d.activeElement,d.querySelector('[data-mappy-dismiss]'));
 assert.equal(dom.window.sessionStorage.getItem('kidsmap:mappy:hidden'),null);
 dom.window.close();
});
test('prior dismissal persists after navigation',()=>{
 const dom=setup({dismissed:true});
 assert.equal(dom.window.document.querySelector('[data-mappy-content]').hidden,true);
 assert.equal(dom.window.document.querySelector('[data-mappy-restore]').hidden,false);dom.window.close();
});
test('reduced motion never adds entrance animation even when restored',()=>{
 const dom=setup({reduced:true}),d=dom.window.document;
 assert.equal(d.querySelector('[data-mappy-helper]').dataset.ready,'true');
 d.querySelector('[data-mappy-dismiss]').click();d.querySelector('[data-mappy-restore]').click();
 assert.equal(d.querySelector('[data-mappy-content]').classList.contains('mappy-enter'),false);dom.window.close();
});
test('storage disabled still allows dismissal and restoration',()=>{
 const dom=setup({storageBlocked:true}),d=dom.window.document;
 d.querySelector('[data-mappy-dismiss]').click();assert.equal(d.querySelector('[data-mappy-content]').hidden,true);
 d.querySelector('[data-mappy-restore]').click();assert.equal(d.querySelector('[data-mappy-content]').hidden,false);dom.window.close();
});
