const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || 'jsdom');
const source = fs.readFileSync('static/admin/js/kidsmap_notifications.js', 'utf8');

function mount() {
  const dom = new JSDOM('<!doctype html><button id="trigger">Open</button><svg><symbol id="kmi-warning" viewBox="0 0 24 24"></symbol></svg>', {runScripts:'outside-only', pretendToBeVisual:true});
  const w = dom.window, frames = [], timers = [];
  w.requestAnimationFrame = fn => {frames.push(fn); return frames.length;};
  w.setTimeout = fn => {timers.push(fn); return timers.length;};
  // jsdom has no layout: visible rects explicitly include SVG use, reproducing
  // the real dialog's icon. This does not simulate native keyboard navigation.
  w.Element.prototype.getClientRects = function () {return this.hidden || this.style.display === 'none' ? [] : [{width:20,height:20}];};
  w.eval(source);
  const trigger = w.document.getElementById('trigger'); trigger.focus();
  const flushFrames = () => {for (let n=0; (frames.length || timers.length) && n<10;n++) {const pending=frames.splice(0);pending.forEach(fn=>fn());timers.splice(0).forEach(fn=>fn());}};
  const flushTimers = () => timers.splice(0).forEach(fn=>fn());
  const key = (shift=false) => w.document.dispatchEvent(new w.KeyboardEvent('keydown', {key:'Tab',shiftKey:shift,bubbles:true,cancelable:true}));
  return {w,trigger,key,flushFrames,flushTimers,close:()=>w.close()};
}

test('forward wrap excludes a visible SVG use and focuses the first real button', () => {
  const m=mount();try {
    m.w.kmModal.unsavedChanges();m.flushFrames();
    const buttons=m.w.document.querySelectorAll('.km-modal button');
    assert(m.w.document.querySelector('.km-modal use[href]'), 'Real icon must exist');
    buttons[2].focus();m.key();
    assert.equal(m.w.document.activeElement,buttons[0]);
    m.key(true);assert.equal(m.w.document.activeElement,buttons[2]);
  } finally {m.close();}
});

test('Tab from outside the dialog enters a real action rather than the SVG icon', () => {
  const m=mount();try {
    m.w.kmModal.unsavedChanges();m.flushFrames();m.trigger.focus();m.key();
    assert.equal(m.w.document.activeElement,m.w.document.querySelector('.km-btn-modal--quiet'));
  } finally {m.close();}
});

test('disabled, hidden and negative-tabindex controls do not become wrap targets', () => {
  const m=mount();try {
    m.w.kmModal.unsavedChanges();m.flushFrames();const dialog=m.w.document.querySelector('.km-modal');
    for (const attr of ['disabled','hidden','tabindex="-1"']) dialog.insertAdjacentHTML('afterbegin',`<button ${attr}>Excluded</button>`);
    m.w.document.querySelector('.km-btn-modal--danger-quiet').focus();m.key();
    assert.equal(m.w.document.activeElement,m.w.document.querySelector('.km-btn-modal--quiet'));
  } finally {m.close();}
});

test('opening and Escape/Stay restore focus while preserving callback behavior', () => {
  const m=mount();try {
    let stayed=0;m.w.kmModal.unsavedChanges({onStay:()=>stayed++});m.flushFrames();
    assert.equal(m.w.document.activeElement,m.w.document.querySelector('.km-btn-modal--primary'));
    m.w.document.dispatchEvent(new m.w.KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));m.flushTimers();
    assert.equal(m.w.document.activeElement,m.trigger);assert.equal(stayed,1);
    m.w.kmModal.unsavedChanges({onStay:()=>stayed++});m.flushFrames();m.w.document.querySelector('.km-btn-modal--quiet').click();m.flushTimers();
    assert.equal(m.w.document.activeElement,m.trigger);
    // Existing Stay invokes both onClose and onStay; this focus-only patch
    // must preserve that baseline callback behavior.
    assert.equal(stayed,3);
  } finally {m.close();}
});

test('an old close timer must not steal focus from the newly opened dialog',()=>{
 const d=new JSDOM('<button id="trigger">Open</button><svg><symbol id="kmi-warning"></symbol></svg>',{runScripts:'outside-only',pretendToBeVisual:true});
 const w=d.window,frames=[],timers=[];let now=0;
 w.requestAnimationFrame=fn=>frames.push(fn);
 w.setTimeout=(fn,delay=0)=>{timers.push({fn,at:now+delay});return timers.length;};
 w.Element.prototype.getClientRects=function(){return[{width:20,height:20}];};
 const flush=()=>{while(timers.some(t=>t.at<=now)){timers.sort((a,b)=>a.at-b.at);timers.shift().fn();}};
 const paint=()=>{frames.splice(0).forEach(fn=>fn());flush();};
 try{
  w.eval(fs.readFileSync('static/admin/js/kidsmap_notifications.js','utf8'));
  const trigger=w.document.getElementById('trigger');trigger.focus();w.kmModal.unsavedChanges();paint();
  w.document.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));
  trigger.focus();w.kmModal.unsavedChanges();paint();
  const current=w.document.querySelector('.is-visible .km-btn-modal--primary');assert.equal(w.document.activeElement,current);
  now=220;flush();assert.equal(w.document.activeElement,current);
 }finally{w.close();}
});


test('shared show waits for visible controls and cancels focus when closed', () => {
  const m=mount();try {
    let hidden=true;const original=m.w.getComputedStyle.bind(m.w);
    m.w.getComputedStyle=el=>hidden && el.closest('.km-modal-backdrop') ? {visibility:'hidden',display:'block'} : original(el);
    m.w.kmModal.show({title:'Confirm',buttons:[{text:'Continue',primary:true}]});
    m.flushFrames();assert.equal(m.w.document.activeElement,m.trigger);
    hidden=false;m.flushFrames();assert(m.w.document.activeElement.closest('.km-modal'));
    m.w.kmModal.close();m.flushTimers();assert.equal(m.w.document.activeElement,m.trigger);
    hidden=true;m.w.kmModal.show({title:'Closed before visible'});m.w.kmModal.close();hidden=false;m.flushFrames();
    assert.equal(m.w.document.activeElement,m.trigger);
  } finally {m.close();}
});

test('closing a dialog with a removed, disabled or hidden trigger is harmless', () => {
  for(const state of ['removed','disabled','hidden']) {
    const m=mount();try {
      m.w.kmModal.unsavedChanges();m.flushFrames();
      if(state==='removed')m.trigger.remove();else if(state==='disabled')m.trigger.disabled=true;else m.trigger.style.visibility='hidden';
      m.w.kmModal.close();assert.doesNotThrow(()=>m.flushTimers());
      assert.notEqual(m.w.document.activeElement,m.trigger);
    } finally {m.close();}
  }
});
