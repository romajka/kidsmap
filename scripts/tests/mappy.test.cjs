const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require('../../.tmp/phone-dom/node_modules/jsdom');
const file=require('node:path').join(__dirname,'../../static/js/mappy.js');
function setup({dismissed=false,reduced=false,storageBlocked=false,withBubble=false}={}) {
  const dom=new JSDOM(`<section data-mappy-helper><div data-mappy-content><img alt=""><p>Choose an area</p><button data-mappy-dismiss>Hide</button></div><button data-mappy-restore hidden>Show helper</button></section>`,{url:'https://kidsmap.example/',runScripts:'outside-only',pretendToBeVisual:withBubble});
  const w=dom.window;w.matchMedia=()=>({matches:reduced,addEventListener(){}});
  if(withBubble)w.document.querySelector('[data-mappy-content]').insertAdjacentHTML('beforeend','<button class="mappy-bubble" type="button">Next tip</button>');
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

test('a manual tip remains usable with reduced motion',()=>{
 const dom=setup({reduced:true,withBubble:true}),d=dom.window.document;
 try {
  d.querySelector('.mappy-bubble').click();
  assert.match(d.querySelector('p').textContent,/Ищете спорт/);
  assert.equal(d.querySelector('p').classList.contains('is-switching'),false);
 } finally {dom.window.close();}
});

test('a 3D response cancels a pending tip so it cannot overwrite the bear',async()=>{
 const dom=setup({withBubble:true}),d=dom.window.document;
 try {
  d.querySelector('.mappy-bubble').click();
  d.querySelector('[data-mappy-helper]').dispatchEvent(new dom.window.Event('mappy:say'));
  d.querySelector('p').textContent='Щекотно!';
  await new Promise(resolve=>setTimeout(resolve,260));
  assert.equal(d.querySelector('p').textContent,'Щекотно!');
  assert.equal(d.querySelector('p').classList.contains('is-switching'),false);
 } finally {dom.window.close();}
});

test('sleep owns the cloud until wake, including pending and manual tips',async()=>{
 const dom=setup({withBubble:true}),w=dom.window,d=w.document;
 try {
  const helper=d.querySelector('[data-mappy-helper]'),text=d.querySelector('p');
  d.querySelector('.mappy-bubble').click();
  helper.dispatchEvent(new w.Event('mappy:sleep'));
  text.textContent='Маппи спит. Нажмите, чтобы разбудить.';
  d.querySelector('.mappy-bubble').click();
  await new Promise(resolve=>setTimeout(resolve,260));
  assert.equal(text.textContent,'Маппи спит. Нажмите, чтобы разбудить.');
  assert.equal(text.classList.contains('is-switching'),false);
  helper.dispatchEvent(new w.Event('mappy:wake'));
  d.querySelector('.mappy-bubble').click();
  await new Promise(resolve=>setTimeout(resolve,260));
  assert.notEqual(text.textContent,'Маппи спит. Нажмите, чтобы разбудить.');
 } finally {w.close();}
});

test('visibility changes do not resume automatic tips while asleep',()=>{
 const dom=setup({withBubble:true}),w=dom.window,d=w.document;
 try {
  let starts=0;
  w.setInterval=()=>{starts++;return 1;};w.clearInterval=()=>{};
  const helper=d.querySelector('[data-mappy-helper]');
  helper.dispatchEvent(new w.Event('mappy:sleep'));
  d.dispatchEvent(new w.Event('visibilitychange'));
  helper.dispatchEvent(new w.Event('mappy:say'));
  assert.equal(starts,0);
  helper.dispatchEvent(new w.Event('mappy:wake'));
  assert.equal(starts,1);
 } finally {w.close();}
});
