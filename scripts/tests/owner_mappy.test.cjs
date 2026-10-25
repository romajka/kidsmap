const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
function mount({desktop=true,reduced=false}={}){
 const d=new JSDOM('<html lang="ru"><aside data-pc-mappy data-sprite="/mappy-sprite.webp" data-welcome="/welcome.webp"><button data-pc-mappy-wave><img data-mappy-sprite></button><p data-pc-mappy-title></p><p data-pc-mappy-caption></p></aside></html>',{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true});
 const w=d.window,media={desktop:{matches:desktop},reduced:{matches:reduced}};
 Object.values(media).forEach(item=>{item.addEventListener=(_,fn)=>item.change=fn;item.removeEventListener=()=>{};});
 w.matchMedia=query=>query.includes('reduced-motion')?media.reduced:media.desktop;
 w.eval(fs.readFileSync('static/js/owner_place_mappy.js','utf8'));
 const root=w.document.querySelector('aside'),controller=w.KidsMapOwnerMappy.mount(root);return {d,w,media,root,controller,image:root.querySelector('img')};
}
test('mobile does not request mascot graphics or start movement, including after readiness changes',()=>{
 const t=mount({desktop:false});try{t.controller.update({required_count:10,completed_count:10,is_ready:true},false);assert.equal(t.image.hasAttribute('src'),false);assert.equal(t.root.classList.contains('is-waving'),false);
 t.media.desktop.matches=true;t.media.desktop.change();assert.equal(t.image.getAttribute('src'),'/mappy-sprite.webp');assert.equal(t.root.dataset.pose,'ready');
 }finally{t.controller.destroy();t.w.close();}
});
test('confirmed progress selects writing/ready poses; pending checks do not restart or replace the pose',()=>{
 const t=mount();try{t.controller.update({required_count:10,completed_count:3,is_ready:false},false);assert.equal(t.root.dataset.pose,'writing');
 t.controller.update({required_count:10,completed_count:3,is_ready:false},true);assert.equal(t.root.dataset.pose,'writing');
 t.controller.update({required_count:10,completed_count:10,is_ready:true},false);assert.equal(t.root.dataset.pose,'ready');assert.match(t.root.querySelector('[data-pc-mappy-title]').textContent,/Готово/);
 assert.equal(t.w.KidsMapOwnerMappy.mount(t.root),t.controller,'mount must be idempotent');
 }finally{t.controller.destroy();t.w.close();}
});
test('waving is short, user-triggered and disabled for reduced motion or hidden desktop panel',()=>{
 const t=mount();try{t.image.dispatchEvent(new t.w.Event('load'));t.root.querySelector('button').click();assert.equal(t.root.classList.contains('is-waving'),true);
 t.media.reduced.matches=true;t.media.reduced.change();assert.equal(t.root.classList.contains('is-waving'),false);t.root.querySelector('button').click();assert.equal(t.root.classList.contains('is-waving'),false);
 t.media.reduced.matches=false;t.media.reduced.change();t.root.querySelector('button').click();assert.equal(t.root.classList.contains('is-waving'),true);
 Object.defineProperty(t.w.document,'hidden',{value:true,configurable:true});t.w.document.dispatchEvent(new t.w.Event('visibilitychange'));assert.equal(t.root.classList.contains('is-waving'),false);t.root.querySelector('button').click();assert.equal(t.root.classList.contains('is-waving'),false);
 Object.defineProperty(t.w.document,'hidden',{value:false,configurable:true});t.w.document.dispatchEvent(new t.w.Event('visibilitychange'));t.root.querySelector('button').click();assert.equal(t.root.classList.contains('is-waving'),true);
 t.media.desktop.matches=false;t.media.desktop.change();assert.equal(t.root.classList.contains('is-waving'),false);
 }finally{t.controller.destroy();t.w.close();}
});
test('an unavailable sprite uses the existing mascot once and retains useful text',()=>{
 const t=mount();try{t.image.dispatchEvent(new t.w.Event('error'));assert.equal(t.image.getAttribute('src'),'/welcome.webp');assert.equal(t.root.hasAttribute('data-fallback'),true);t.image.dispatchEvent(new t.w.Event('error'));assert.equal(t.image.getAttribute('src'),'/welcome.webp');assert(t.root.querySelector('p').textContent);
 }finally{t.controller.destroy();t.w.close();}
});
