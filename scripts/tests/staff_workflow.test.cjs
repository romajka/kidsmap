const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');

function saveExitEnvironment(save){
 const source=fs.readFileSync('static/admin/js/kidsmap_place_form.js','utf8');
 const start=source.indexOf('onSaveAndExit: function () {')+'onSaveAndExit: '.length;
 const end=source.indexOf('\n        onExitWithoutSaving:',start);
 const callback=source.slice(start,end).trim().replace(/,$/,'');
 const sent=[];const location={href:'original'};
 const data=new Map([['_publish_place','1'],['_continue','1']]);
 const context={candidateConflict:false,form:{action:'/admin/catalog/place/1/change/',kmDraftSave:save},submitting:false,isDirty:true,bypassNavigationPrompt:false,
  targetUrl:'/admin/catalog/place/',window:{location},labels:{},setSaveState(){},kmToast:{info(){},error(){}},pauseCandidateSave(){},
  FormData:class{constructor(){}has(k){return data.has(k)}append(k,v){data.set(k,v)}set(k,v){data.set(k,v)}delete(k){data.delete(k)}},
  fetch:async(url,options)=>{sent.push({url,options});return {ok:true,redirected:true,url:'/admin/catalog/place/1/change/'};}};
 vm.createContext(context);vm.runInContext(`(${callback})()`,context);
 return {context,sent,data,location};
}
test('admin save-and-exit uses only draft intent in fallback request',async()=>{
 const m=saveExitEnvironment();await new Promise(setImmediate);
 assert.equal(m.data.get('_save_draft'),'1');for(const key of ['_continue','_publish_place','_save','_addanother'])assert(!m.data.has(key),key);
});
test('admin save-and-exit waits for the existing private draft adapter and stays on failure',async()=>{
 let resolve;const m=saveExitEnvironment(()=>new Promise(r=>{resolve=r}));
 assert.equal(m.sent.length,0);assert.equal(m.location.href,'original');await Promise.resolve();resolve(false);await new Promise(setImmediate);
 assert.equal(m.location.href,'original');assert.equal(m.context.submitting,false);
});
function volunteer(){
 const d=new JSDOM(`<html lang="ru"><form data-volunteer-admin-form><button data-editor-collapse></button><button data-editor-expand></button><button data-guide-open></button><dialog data-volunteer-guide><button data-guide-close></button></dialog><input name="name_az"><input name="age_open_ended" type="checkbox"><input name="age_to"><span data-editor-save-state></span><strong data-progress-pct></strong><span data-progress-done></span><span data-progress-total></span><span data-progress-bar></span><button data-km-preview type="submit"></button></form><a href="/admin/volunteer/">Leave</a></html>`,{runScripts:'outside-only',url:'http://localhost/admin/volunteer/add/'});
 d.window.HTMLDialogElement.prototype.showModal=function(){this.open=true};d.window.HTMLDialogElement.prototype.close=function(){this.open=false};
 d.window.eval(fs.readFileSync('static/admin/js/volunteer_place_form.js','utf8'));return d;
}
test('volunteer readiness uses the returned server counts',()=>{
 const d=volunteer();try{const form=d.window.document.querySelector('form');form.dispatchEvent(new d.window.CustomEvent('km:readiness',{detail:{readiness:{required_count:10,completed_count:3,is_ready:false,sections:[],items:[]}}}));
 assert.equal(form.querySelector('[data-progress-pct]').textContent,'30%');assert.equal(form.querySelector('[data-progress-done]').textContent,'3');
 }finally{d.window.close();}
});
test('volunteer preview submit leaves unsaved-page protection active',()=>{
 const d=volunteer();try{const w=d.window,f=w.document.querySelector('form');f.kmDraftHasPending=()=>true;
 f.dispatchEvent(new w.SubmitEvent('submit',{bubbles:true,cancelable:true,submitter:f.querySelector('[data-km-preview]')}));
 const e=new w.Event('beforeunload',{cancelable:true});w.dispatchEvent(e);assert(e.defaultPrevented);
 }finally{d.window.close();}
});

test('admin header follows confirmed private draft state despite widget-only snapshot changes',()=>{
 const source=fs.readFileSync('static/admin/js/kidsmap_place_form.js','utf8');const start=source.indexOf('    function syncDirty() {'),end=source.indexOf('\n    window.kmDirtyState',start);
 let state;const context={submitting:false,serializeFormState:()=> 'widget-normalized',initialSnapshot:'old',isDirty:true,candidateConflict:false,form:{kmDraftHasPending:()=>false,dataset:{placeId:'1'}},placeEntry:true,errorSummary:null,labels:{labelSaved:'Saved'},setSaveState:(value)=>state=value};
 vm.createContext(context);vm.runInContext(source.slice(start,end)+'\nsyncDirty();',context);assert.equal(context.isDirty,false);assert.equal(state,'saved');
});

test('a later cancelled admin submit restores the unsaved-page guard',async()=>{
 const source=fs.readFileSync('static/admin/js/kidsmap_place_form.js','utf8');const at=source.indexOf("if (event.submitter && event.submitter.hasAttribute('data-km-preview')) return;");const start=source.lastIndexOf('function (event) {',at),end=source.indexOf('}, true);',at)+1;
 const event={submitter:null,defaultPrevented:false};const context={event,candidateConflict:false,submitting:false,setSaveState(){},syncDirty(){},labels:{},queueMicrotask};vm.createContext(context);vm.runInContext(`(${source.slice(start,end)})(event)`,context);assert.equal(context.submitting,true);event.defaultPrevented=true;await Promise.resolve();assert.equal(context.submitting,false);
});
