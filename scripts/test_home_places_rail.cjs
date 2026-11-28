const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
function setup({width = 390, count = 4, reduced = false} = {}){
 const cards = Array.from({length: count}, (_, index) => index + 1);
 const dom=new JSDOM(`<section data-places-rail><div data-rail-viewport><div data-rail-track>${cards.map(i=>`<article data-rail-original><a href="/place/${i}/">Place</a><form class="like-form" data-like-form action="/place/${i}/like/"><button class="like-btn" aria-pressed="false"><span class="like-count">0</span></button></form><button class="card-contact-toggle">Phone</button></article>`).join('')}</div></div><button data-rail-toggle data-pause-label="Pause" data-resume-label="Resume" hidden><span data-rail-toggle-label></span><span data-rail-toggle-icon></span></button></section>`,{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true}),w=dom.window;
 const frames = new Map();
 let frameId = 0;
 w.matchMedia=()=>({matches:reduced,addEventListener(){}});
 w.requestAnimationFrame=callback=>{const id=++frameId;frames.set(id,callback);return id;};
 w.cancelAnimationFrame=id=>frames.delete(id);
 const v=w.document.querySelector('[data-rail-viewport]');
 // jsdom does not calculate the scrollable width of the four cards and their gaps.
 Object.defineProperties(v, {
   clientWidth: {value: width},
   scrollWidth: {value: Math.max(width, count * 300 + (count - 1) * 18)},
 });
 for(const el of w.document.querySelectorAll('[data-rail-original]'))el.getBoundingClientRect=()=>({width:300});
 w.eval(fs.readFileSync('static/js/home_places_rail.js','utf8'));
 const pointer=(target,type,x)=>target.dispatchEvent(Object.assign(new w.MouseEvent(type,{bubbles:true,cancelable:true,clientX:x,button:0}),{pointerType:'mouse',pointerId:1}));
 const drag=()=>{pointer(v,'pointerdown',100);pointer(v,'pointermove',60);pointer(v,'pointerup',60);};
 const advance = time => {
  const pending = [...frames.values()];
  frames.clear();
  pending.forEach(callback => callback(time));
 };
 return{dom,w,v,pointer,drag,advance,button:w.document.querySelector('[data-rail-original] .like-btn')};
}

test('a three-card rail starts moving even when all the original cards fit',()=>{
 const {dom,w,v,advance}=setup({width: 1120, count: 3});
 try{
  const toggle=w.document.querySelector('[data-rail-toggle]');
  assert.equal(toggle.hidden,false);
  advance(16);
  advance(48);
  assert.ok(v.scrollLeft>0,'autoplay should advance the rail');
  toggle.click();
  const pausedAt=v.scrollLeft;
  advance(96);
  assert.equal(v.scrollLeft,pausedAt);
  toggle.click();
  advance(128);
  advance(160);
  assert.ok(v.scrollLeft>pausedAt,'resume should continue from the paused position');
 }finally{dom.window.close();}
});

test('a single card or a reduced-motion rail stays still without visual copies',()=>{
 for(const options of [{count:1},{width:1120,count:3,reduced:true}]){
  const {dom,w,v,advance}=setup(options);
  try{
   advance(16);
   advance(48);
   assert.equal(v.scrollLeft,0);
   assert.equal(w.document.querySelectorAll('[data-rail-copy]').length,0);
   assert.equal(w.document.querySelector('[data-rail-toggle]').hidden,true);
  }finally{dom.window.close();}
 }
});
test('hidden visual copies have no sequential keyboard targets, originals retain actions',()=>{
 const {dom,w}=setup();try{const copied=[...w.document.querySelectorAll('[data-rail-copy] a,[data-rail-copy] button')];assert.ok(copied.length>0);assert.ok(copied.every(x=>x.tabIndex===-1));assert.equal(w.document.querySelector('[data-rail-original] button').tabIndex,0);}finally{dom.window.close();}
});
test('replacing a copied phone control keeps new link outside Tab order and pointer-clickable',async()=>{
 const {dom,w}=setup();try{const old=w.document.querySelector('[data-rail-copy] .card-contact-toggle'),link=w.document.createElement('a');link.href='#local';old.replaceWith(link);await new Promise(r=>w.queueMicrotask(r));assert.equal(link.tabIndex,-1);let clicked=0;link.addEventListener('click',()=>clicked++);link.click();assert.equal(clicked,1);assert.equal(link.hasAttribute('inert'),false);}finally{dom.window.close();}
});
test('drag suppresses its generated click but a fresh pointer gesture reaches favorite',()=>{
 const {dom,w,pointer,drag,button}=setup();try{let actions=0;button.addEventListener('click',()=>actions++);drag();const trailing=new w.MouseEvent('click',{bubbles:true,cancelable:true,detail:1});button.dispatchEvent(trailing);assert.equal(trailing.defaultPrevented,true);assert.equal(actions,0);drag();pointer(button,'pointerdown',90);pointer(button,'pointerup',90);button.dispatchEvent(new w.MouseEvent('click',{bubbles:true,cancelable:true,detail:1}));assert.equal(actions,1);}finally{dom.window.close();}
});
test('keyboard activation after a drag is not swallowed',()=>{
 const {dom,w,drag,button}=setup();try{let actions=0;button.addEventListener('click',()=>actions++);drag();button.dispatchEvent(new w.MouseEvent('click',{bubbles:true,cancelable:true,detail:0}));assert.equal(actions,1);}finally{dom.window.close();}
});

test('a favorite result synchronizes original and visible copies in both directions',async()=>{const {dom,w,button}=setup();try{const action=button.form.getAttribute('action'),buttons=[...w.document.querySelectorAll('[data-like-form]')].filter(f=>f.getAttribute('action')===action).map(f=>f.querySelector('button'));assert.ok(buttons.length>1);for(const [source,pressed,count] of [[button,'true','1'],[buttons[1],'false','0']]){source.classList.toggle('active',pressed==='true');source.querySelector('.like-count').textContent=count;source.setAttribute('aria-pressed',pressed);await new Promise(resolve=>w.queueMicrotask(resolve));assert.ok(buttons.every(b=>b.getAttribute('aria-pressed')===pressed&&b.classList.contains('active')===(pressed==='true')&&b.querySelector('.like-count').textContent===count));}assert.equal(w.document.querySelector('[data-rail-original] form[action="/place/2/like/"] button').getAttribute('aria-pressed'),'false');}finally{dom.window.close();}});
