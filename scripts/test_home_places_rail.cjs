const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
function setup(){
 const dom=new JSDOM(`<section data-places-rail><div data-rail-viewport><div data-rail-track>${[1,2,3,4].map(i=>`<article data-rail-original><a href="/place/${i}/">Place</a><form class="like-form" data-like-form action="/place/${i}/like/"><button class="like-btn" aria-pressed="false"><span class="like-count">0</span></button></form><button class="card-contact-toggle">Phone</button></article>`).join('')}</div></div><button data-rail-toggle><span data-rail-toggle-label></span><span data-rail-toggle-icon></span></button></section>`,{url:'http://localhost/',runScripts:'outside-only'}),w=dom.window;
 w.matchMedia=()=>({matches:false,addEventListener(){}});w.requestAnimationFrame=()=>1;w.cancelAnimationFrame=()=>{};
 const v=w.document.querySelector('[data-rail-viewport]');Object.defineProperty(v,'clientWidth',{value:390});
 for(const el of w.document.querySelectorAll('[data-rail-original]'))el.getBoundingClientRect=()=>({width:300});
 w.eval(fs.readFileSync('static/js/home_places_rail.js','utf8'));
 const pointer=(target,type,x)=>target.dispatchEvent(Object.assign(new w.MouseEvent(type,{bubbles:true,cancelable:true,clientX:x,button:0}),{pointerType:'mouse',pointerId:1}));
 const drag=()=>{pointer(v,'pointerdown',100);pointer(v,'pointermove',60);pointer(v,'pointerup',60);};
 return{dom,w,v,pointer,drag,button:w.document.querySelector('[data-rail-original] .like-btn')};
}
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
