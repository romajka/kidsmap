const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM || '../../.tmp/phone-dom/node_modules/jsdom');
const source=fs.readFileSync('static/js/home_map.js','utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function setup(earlyQuery){
 const dom=new JSDOM(`<form data-home-map-filter-form><input name="q"><button data-home-search-clear type="button"></button><div id="home-search-autocomplete" hidden data-label-loading="Searching" data-label-error="Error"><p data-hs-ac-status hidden></p><ul data-hs-ac-list></ul><div data-hs-ac-empty hidden></div><div data-hs-ac-footer hidden><button type="button" data-hs-ac-show-all><span data-hs-ac-show-all-text></span></button></div></div></form>`,{runScripts:'outside-only',url:'http://localhost/ru/'});
 const w=dom.window,requests=[];let scheduled;
 w.setTimeout=fn=>{scheduled=fn;return 1;};w.clearTimeout=()=>{scheduled=null;};
 w.parsePlaces=()=>[];w.pointMembers=p=>[p];w.normalizeSearch=s=>s.trim().toLowerCase();
 w.fetchFilteredPoints=signal=>new Promise((resolve,reject)=>requests.push({signal,resolve,reject}));
 w.escapeHtml=s=>String(s).replaceAll('<','&lt;');w.highlightMatch=w.escapeHtml;w.formatAgeBadge=()=>'';
 w.eval(source.slice(source.indexOf('  function safeHomeMapUrl('),source.indexOf('  const CATEGORY_THEMES')));
 w.homeExplorer={showMap(){}};w.scrollToMap=()=>{};w.pendingFocusPlaceId=null;w.HTMLElement.prototype.scrollIntoView=function(){};
 if (earlyQuery) {
   const field = w.document.querySelector('input');
   field.focus();
   field.value = earlyQuery;
 }
 w.eval(source.slice(source.indexOf('  function initHomeSearchAutocomplete('),source.indexOf('  function bindFilterListeners('))+'\ninitHomeSearchAutocomplete(()=>{});');
 const input=w.document.querySelector('input'),panel=w.document.querySelector('#home-search-autocomplete');
 return {w,requests,input,panel,type(value){input.value=value;input.dispatchEvent(new w.Event('input'));},flush(){const fn=scheduled;scheduled=null;fn?.();},close(){w.close();}};
}
test('rapid typing cancels old work; stale failure cannot hide the current results',async()=>{
 const t=setup();try{
 t.type('a');t.type('art');assert.equal(t.requests.length,0);t.flush();assert.equal(t.requests.length,1);
 t.type('music');assert.equal(t.requests[0].signal.aborted,true);t.flush();
 t.requests[1].resolve([{id:2,name:'Music studio'}]);await tick();
 t.requests[0].reject(new Error('old request failed'));await tick();
 assert.equal(t.panel.hidden,false);assert.match(t.panel.textContent,/Music studio/);assert.equal(t.input.getAttribute('aria-expanded'),'true');
 }finally{t.close();}
});
test('clearing input prevents pending results from reopening suggestions',async()=>{
 const t=setup();try{t.type('art');t.flush();t.type('');t.requests[0].resolve([{id:1,name:'Art'}]);await tick();assert.equal(t.panel.hidden,true);assert.equal(t.input.getAttribute('aria-expanded'),'false');}finally{t.close();}
});
test('empty result and failed request are distinct; Escape closes either state',async()=>{
 const t=setup();try{t.type('none');t.flush();t.requests[0].resolve([]);await tick();assert.equal(t.panel.querySelector('[data-hs-ac-empty]').hidden,false);
 t.input.dispatchEvent(new t.w.KeyboardEvent('keydown',{key:'Escape'}));assert.equal(t.panel.hidden,true);
 t.type('art');t.flush();t.requests[1].reject(new Error('offline'));await tick();assert.equal(t.panel.querySelector('[data-hs-ac-status]').textContent,'Error');assert.equal(t.panel.querySelector('[data-hs-ac-empty]').hidden,true);
 }finally{t.close();}
});

test('photo tiles reject unsafe URLs and keep a fallback when a photo fails',async()=>{
 const t=setup();try{
 t.type('studio');t.flush();t.requests[0].resolve([{id:1,name:'Art studio',image_url:'/media/art.jpg',age:'5–12'},{id:2,name:'Music studio',image_url:'javascript:alert(1)'}]);await tick();
 const photos=t.panel.querySelectorAll('.hs-ac-item-photo');assert.equal(photos.length,1);assert.equal(photos[0].src,'http://localhost/media/art.jpg');
 photos[0].dispatchEvent(new t.w.Event('error'));assert.equal(photos[0].hidden,true);assert.equal(t.panel.querySelectorAll('.hs-ac-item-icon').length,2);
 assert.match(t.panel.textContent,/5–12/);assert.equal(t.panel.querySelector('[data-hs-ac-footer]').hidden,false);assert.equal(t.panel.querySelectorAll('.hs-ac-item-badge').length,0);
 t.input.dispatchEvent(new t.w.KeyboardEvent('keydown',{key:'ArrowDown'}));assert.equal(t.input.getAttribute('aria-activedescendant'),'home-search-option-0');
 t.input.dispatchEvent(new t.w.KeyboardEvent('keydown',{key:'Enter'}));assert.equal(t.input.value,'Art studio');assert.equal(t.panel.hidden,true);assert.equal(t.w.pendingFocusPlaceId,1);
 }finally{t.close();}
});

test('search picks up text entered before the map script arrives', () => {
 const fixture = setup('judo');
 try {
   fixture.flush();
   assert.equal(fixture.requests.length, 1);
 } finally { fixture.close(); }
});
