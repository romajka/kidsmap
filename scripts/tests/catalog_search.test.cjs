const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM || '../../.tmp/phone-dom/node_modules/jsdom');
const source=fs.readFileSync('static/js/catalog_search.js','utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function setup(id='catalog-hero-search-input',panelId='catalog-search-dropdown') {
 const dom=new JSDOM(`<html lang="ru"><form id="filters-form"><input name="category" value="ART"><input name="age" value="5"></form><form action="/ru/catalog/"><input name="q" id="${id}"></form><div id="${panelId}" hidden></div></html>`,{url:'http://localhost/ru/catalog/?district=Baku&page=3',runScripts:'outside-only'});
 const w=dom.window, requests=[];let timer;
 w.setTimeout=fn=>{timer=fn;return 1;};w.clearTimeout=()=>{timer=null;};w.HTMLElement.prototype.scrollIntoView=function(){};
 w.fetch=(url,opts)=>new Promise((resolve,reject)=>requests.push({url,signal:opts.signal,resolve:data=>resolve({ok:true,json:async()=>data}),reject}));
 w.eval(source);const input=w.document.getElementById(id),panel=w.document.getElementById(panelId);
 return {w,input,panel,requests,type(value){input.value=value;input.dispatchEvent(new w.Event('input'));},flush(){timer?.();timer=null;},close(){w.close();}};
}
test('catalog suggestions carry current filters and discard stale failures',async()=>{
 const t=setup();try{
 t.type('old');t.flush();const params=new URL(t.requests[0].url,'http://localhost').searchParams;assert.equal(params.get('category'),'ART');assert.equal(params.get('age'),'5');assert.equal(params.has('page'),false);
 t.type('new');t.flush();assert.equal(t.requests[0].signal.aborted,true);
 t.requests[1].resolve({places:[{id:1,name:'new studio',url:'/ru/place/studio/',image:'/photo.jpg'}]});await tick();t.requests[0].reject(new Error('stale'));await tick();assert.equal(t.panel.hidden,false);assert.match(t.panel.textContent,/new/);assert.match(t.panel.textContent,/Все результаты/);
 t.input.dispatchEvent(new t.w.KeyboardEvent('keydown',{key:'ArrowDown'}));assert.ok(t.input.getAttribute('aria-activedescendant'));t.input.dispatchEvent(new t.w.KeyboardEvent('keydown',{key:'Escape'}));assert.equal(t.panel.hidden,true);
 }finally{t.close();}
});
test('clearing or dismissing cannot reopen results from an old request',async()=>{
 const t=setup();try{t.type('art');t.flush();t.type('');t.requests[0].resolve({places:[{name:'Art',url:'/art/'}]});await tick();assert.equal(t.panel.hidden,true);}finally{t.close();}
});
test('mobile search shows safe text and replaces a broken thumbnail with a decorative icon', async () => {
 const t = setup('catalog-mobile-search', 'catalog-mobile-search-dropdown');
 try {
  t.type('<'); t.flush();
  t.requests[0].resolve({places: [{name: '<studio>', url: '/ru/place/art/', image: '/photo.jpg'}]});
  await tick();
  const card = t.panel.querySelector('a[href$="/ru/place/art/"]');
  assert.match(card.textContent, /<studio>/);
  assert.equal(card.querySelector('studio'), null);
  const image = card.querySelector('img');
  const container = image.parentElement;
  image.dispatchEvent(new t.w.Event('error'));
  assert.equal(container.querySelector('img'), null);
  assert.ok(container.querySelector('svg[aria-hidden="true"]'));
 } finally { t.close(); }
});
test('empty, error and retry states are distinct, with no stale keyboard target', async () => {
 const t = setup('catalog-mobile-search', 'catalog-mobile-search-dropdown');
 try {
  t.type('none'); t.flush(); t.requests[0].resolve({places: []}); await tick();
  assert.match(t.panel.querySelector('[role="status"]').textContent, /Ничего не нашли/);
  assert.equal(t.panel.querySelector('button'), null);
  t.type('studio'); t.flush(); t.requests[1].resolve({places: [{name: 'Studio', url: '/ru/place/art/'}]}); await tick();
  t.input.dispatchEvent(new t.w.KeyboardEvent('keydown', {key: 'ArrowDown'}));
  assert.ok(t.input.getAttribute('aria-activedescendant'));
  t.type('offline'); t.flush(); t.requests[2].reject(new Error('offline')); await tick();
  assert.match(t.panel.querySelector('[role="status"]').textContent, /Не удалось загрузить/);
  assert.equal(t.input.hasAttribute('aria-activedescendant'), false);
  t.input.dispatchEvent(new t.w.KeyboardEvent('keydown', {key: 'ArrowDown'}));
  assert.equal(t.input.hasAttribute('aria-activedescendant'), false);
  const retry = t.panel.querySelector('button');
  assert.equal(retry.textContent, 'Повторить');
  retry.click(); t.flush();
  assert.equal(new URL(t.requests[3].url, 'http://localhost').searchParams.get('q'), 'offline');
  t.requests[3].resolve({places: [{name: 'Restored', url: '/ru/place/restored/'}]}); await tick();
  assert.match(t.panel.textContent, /Restored/);
 } finally { t.close(); }
});
test('regular form submission preserves the same filters as suggestions',()=>{
 const t=setup();try{
 t.type('studio');const form=t.input.form;
 form.addEventListener('submit',event=>event.preventDefault());
 form.dispatchEvent(new t.w.Event('submit',{bubbles:true,cancelable:true}));
 const data=new t.w.FormData(form);assert.equal(data.get('q'),'studio');assert.equal(data.get('category'),'ART');assert.equal(data.get('age'),'5');assert.equal(data.get('district'),'Baku');assert.equal(t.panel.hidden,true);
 }finally{t.close();}
});
