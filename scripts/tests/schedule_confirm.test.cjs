const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
function mount(lang='ru'){
 const d=new JSDOM(`<html lang="${lang}"><form><div data-km-schedule-editor><input data-km-schedule-editor-input><div data-km-schedule-days></div><div data-km-schedule-preview></div><button type=button data-km-schedule-preset=clear>Clear</button><button type=button data-km-schedule-preset=weekdays>Weekdays</button><button type=button data-km-schedule-copy-day=mon>Copy</button></div></form></html>`,{runScripts:'outside-only',pretendToBeVisual:true,url:'http://localhost/'}),w=d.window;
 w.HTMLElement.prototype.getClientRects=function(){return this.hidden?[]:[this.getBoundingClientRect()];};w.confirm=()=>{throw new Error('Native confirm is forbidden');};
 const input=w.document.querySelector('input');input.value=JSON.stringify([{weekday:'mon',is_closed:false,intervals:[{start:'09:00',end:'18:00'}]},{weekday:'tue',is_closed:false,intervals:[{start:'10:00',end:'17:00'}]}]);
 w.eval(fs.readFileSync('static/admin/js/kidsmap_notifications.js','utf8'));w.eval(fs.readFileSync('static/js/kidsmap_schedule_editor.js','utf8'));w.kidsMapInitScheduleEditors();
 return {d,w,input,q:s=>w.document.querySelector(s),close:()=>w.close(),settle:()=>new Promise(r=>setTimeout(r,25))};
}
for(const lang of ['az','ru','en'])test(`${lang}: clear uses one branded dialog, cancellation and Escape preserve hours, acceptance clears once`,async()=>{
 const m=mount(lang);try{const clear=m.q('[data-km-schedule-preset=clear]'),before=m.input.value;let changes=0;m.input.addEventListener('km:schedule-change',()=>changes++);
 clear.focus();clear.click();clear.click();await m.settle();assert.equal(m.w.document.querySelectorAll('.km-modal-backdrop').length,1);assert.equal(m.input.value,before);assert.equal(changes,0);
 const dialog=m.q('[role=alertdialog],[role=dialog]');assert(dialog);const buttons=dialog.querySelectorAll('button');buttons[buttons.length-1].focus();const tab=new m.w.KeyboardEvent('keydown',{key:'Tab',bubbles:true,cancelable:true});buttons[buttons.length-1].dispatchEvent(tab);assert(dialog.contains(m.w.document.activeElement));assert(tab.defaultPrevented);
 m.w.document.dispatchEvent(new m.w.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));await new Promise(r=>setTimeout(r,240));assert.equal(m.input.value,before);assert.equal(m.w.document.activeElement,clear);
 clear.click();await m.settle();m.q('.km-btn-modal--secondary').click();await new Promise(r=>setTimeout(r,240));assert.equal(m.input.value,before);
 clear.click();await m.settle();const text=m.q('.km-modal-backdrop').textContent;assert(text.includes({az:'Cədvəli təmizləmək',ru:'Очистить расписание',en:'Clear the schedule'}[lang]));m.q('.km-btn-modal--danger').click();await m.settle();assert(JSON.parse(m.input.value).every(day=>day.is_closed&&day.intervals.length===0));assert.equal(changes,1);
 }finally{m.close();}
});
for(const lang of ['az','ru','en'])test(lang+': copy overwrite keeps selected days on cancel, blocks repeat confirmation and applies only on acceptance',async()=>{
 const m=mount(lang);try{m.q('[data-km-schedule-copy-day]').click();m.q('.km-schedule-editor__copy-popover [value=tue]').checked=true;const apply=m.q('.km-schedule-editor__popover-btn--apply'),before=m.input.value;apply.click();apply.click();await m.settle();assert.equal(m.w.document.querySelectorAll('.km-modal-backdrop').length,1);m.q('.km-btn-modal--secondary').click();await new Promise(r=>setTimeout(r,240));assert.equal(m.input.value,before);assert(m.q('.km-schedule-editor__copy-popover [value=tue]').checked);apply.click();await m.settle();m.q('.km-btn-modal--warning').click();await m.settle();const days=JSON.parse(m.input.value);assert.deepEqual(days.find(x=>x.weekday==='tue').intervals,days.find(x=>x.weekday==='mon').intervals);assert.equal(m.q('.km-schedule-editor__copy-popover'),null);assert.equal(m.w.document.activeElement,m.q('[data-km-schedule-copy-day]')); }finally{m.close();}
});
