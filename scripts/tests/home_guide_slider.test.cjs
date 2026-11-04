const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || 'jsdom');
const source = fs.readFileSync(require('node:path').join(__dirname, '../../static/js/home_guide_slider.js'), 'utf8');
function setup(count=4, reduced=false, padding=0) {
 const dom=new JSDOM(`<section data-guide-slider><div data-guide-controls hidden><button data-guide-prev></button><button data-guide-motion data-pause-label="Pause animation" data-play-label="Resume animation"><span data-guide-motion-icon></span></button><button data-guide-next></button></div><div data-guide-track tabindex="0">${'<a href="/guide/">Guide</a>'.repeat(count)}</div><span data-guide-progress></span></section>`,{runScripts:'outside-only'});
 const w=dom.window,track=w.document.querySelector('[data-guide-track]');
 Object.defineProperty(w.document,'hidden',{value:false,configurable:true});const timers=new Map();let timerID=0;w.setTimeout=(callback,delay)=>{timers.set(++timerID,{callback,delay});return timerID;};w.clearTimeout=id=>timers.delete(id);const advanceAuto=()=>{const item=[...timers].find(([,t])=>t.delay>=1000);if(item){timers.delete(item[0]);item[1].callback();}};track.style.paddingLeft=padding+'px';w.matchMedia=()=>({matches:reduced}); w.ResizeObserver=class{observe(){}};
 Object.defineProperty(track,'clientWidth',{value:300,configurable:true});Object.defineProperty(track,'scrollWidth',{value:count*200});
 [...track.children].forEach((e,i)=>e.getBoundingClientRect=()=>({left:padding+i*200-track.scrollLeft,right:padding+(i+1)*200-track.scrollLeft,width:200}));track.getBoundingClientRect=()=>({left:0,right:300});
 track.scrollTo=options=>{track.lastScroll=options;track.scrollLeft=options.left;track.dispatchEvent(new w.Event('scroll'));};
 w.eval(source);return{dom,w,track,timers,advanceAuto,prev:w.document.querySelector('[data-guide-prev]'),next:w.document.querySelector('[data-guide-next]')};
}
test('next, previous and boundaries work with more guides',()=>{const x=setup(12);assert.equal(x.prev.disabled,true);x.next.click();assert.equal(x.track.scrollLeft,200);assert.equal(x.prev.disabled,false);x.track.focus();x.track.dispatchEvent(new x.w.KeyboardEvent('keydown',{key:'End',bubbles:true}));assert.equal(x.track.scrollLeft,2100);assert.equal(x.next.disabled,true);x.prev.click();assert.ok(x.track.scrollLeft<2100);x.dom.window.close();});
test('reduced motion uses immediate scrolling and Home returns to start',()=>{const x=setup(4,true);x.next.click();assert.equal(x.track.lastScroll.behavior,'auto');x.track.dispatchEvent(new x.w.KeyboardEvent('keydown',{key:'Home',bubbles:true}));assert.equal(x.track.scrollLeft,0);x.dom.window.close();});
test('controls hide when there is nothing to scroll',()=>{const x=setup(1);assert.equal(x.w.document.querySelector('[data-guide-controls]').hidden,true);x.dom.window.close();});

test('track inset does not make next scroll to the current first card',()=>{const x=setup(4,false,3);x.next.click();assert.equal(x.track.lastScroll.left,200);x.dom.window.close();});

test('tabbing to a partially visible guide brings the whole card into view',()=>{const x=setup();x.track.children[1].focus();assert.equal(x.track.scrollLeft,200);x.dom.window.close();});

test('floating motion has a persistent pause toggle',()=>{const x=setup();const root=x.w.document.querySelector('[data-guide-slider]'),button=x.w.document.querySelector('[data-guide-motion]');button.click();assert.equal(root.dataset.guideMotionState,'paused');assert.equal(button.getAttribute('aria-pressed'),'true');assert.equal(button.getAttribute('aria-label'),'Resume animation');button.click();assert.equal(button.getAttribute('aria-pressed'),'false');x.dom.window.close();});
test('reduced motion hides animation control and keeps floating stopped',()=>{const x=setup(4,true);assert.equal(x.w.document.querySelector('[data-guide-motion]').hidden,true);assert.equal(x.w.document.querySelector('[data-guide-slider]').dataset.guideMotionState,'paused');x.dom.window.close();});

test('carousel advances by default, pause cancels autoplay',()=>{const x=setup();x.advanceAuto();assert.equal(x.track.scrollLeft,200);x.w.document.querySelector('[data-guide-motion]').click();x.advanceAuto();assert.equal(x.track.scrollLeft,200);x.dom.window.close();});
test('reduced motion never schedules autoplay',()=>{const x=setup(4,true);x.advanceAuto();assert.equal(x.track.scrollLeft,0);assert.equal([...x.timers.values()].some(t=>t.delay>=1000),false);x.dom.window.close();});
