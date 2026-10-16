const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM);
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
