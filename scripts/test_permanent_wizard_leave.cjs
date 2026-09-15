// Behavioral test of the real wizard handlers; DOM/server are explicit test boundaries.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('static/js/permanent_place_wizard.js', 'utf8');
const handlers = source.slice(source.indexOf("  form.addEventListener('submit', async event =>"), source.indexOf("  document.addEventListener('click', (event) =>", source.indexOf("  form.addEventListener('submit', async event =>")));
function mount({volunteer=false, online=true, modal=true, photo=true, blockedStorage=false, missingButton=false}={}) {
  const clicks={}, events={}, navigations=[], messages=[], saves=[];
  const button={name:volunteer?'action':'form_action',value:volunteer?'draft':'save_draft',disabled:false};
  const leave={querySelector:sel=>({addEventListener:(_,fn)=>clicks[sel]=fn}),addEventListener(){},showModal(){},close(){},setAttribute(){},removeAttribute(){}};
  let resolveSave, rejectSave;
  const pending = new Promise((resolve,reject)=>{resolveSave=resolve;rejectSave=reject;});
  const form={dataset:{draftKey:'fixture'},querySelector:()=>missingButton?null:button,addEventListener:(name,fn)=>events[name]=fn,requestSubmit(submitter){this.requested=submitter;this.completion=events.submit({submitter,preventDefault(){}});}};
  const location={origin:'https://local.test',assign:url=>navigations.push(url)};
  const context=vm.createContext({form,volunteer,photoEditor:photo?{save:submitter=>{saves.push(submitter);return pending;}}:null,
    navigator:{onLine:online},window:{location,confirm:()=>true},location,document:{getElementById:()=>modal?leave:null},URL,
    localStorage:{removeItem(){if(blockedStorage)throw Error('blocked');}},sessionStorage:{setItem(){}},draftKey:'fixture',
    ui:{save_failed:'server save failed',storage_error:'save failed',offline:'offline',browser_saved:'cached text',draft_saved_toast:'server success',unsaved:'unsaved'},
    text:(_,message)=>messages.push(message),saveBrowser:()=>{messages.push(blockedStorage?'save failed':'cached text');},issues:()=>new Map(),displayIssues(){},reveal(){},box:()=>null,go(){},value:()=>'',Map});
  vm.runInContext('let submitting=false, dirty=true;\n'+handlers,context);
  return {context,clicks,form,navigations,messages,saves,resolveSave,rejectSave,
    leave(){vm.runInContext("showLeaveModal('https://local.test/next');",context);return clicks['[data-pw-leave-save]']?.();}};
}
(async()=>{
  for(const options of [{},{blockedStorage:true},{volunteer:true},{modal:false}]){
    const t=mount(options);t.leave();
    assert.equal(t.navigations.length,0,'Save-and-leave must wait for durable server save, including photos');
    assert.equal(t.saves.length,1,'Save-and-leave must submit the real draft action');
    assert(!t.messages.includes('server success'),'No success message before server response');
    t.resolveSave({ok:true,redirect:'/saved'});await t.form.completion;
    assert.deepEqual(t.navigations,['https://local.test/next']);
  }
  for(const rejects of [false,true]){
    const t=mount();t.leave();
    if(rejects)t.rejectSave(Error('network'));else t.resolveSave({ok:false,errors:{photo:['invalid image']}});
    await t.form.completion;
    assert.equal(t.navigations.length,0,'Save failure must retain the form and selected files');
    if(rejects)assert(t.messages.includes('server save failed'));
    assert.equal(vm.runInContext('submitting',t.context),false,'Failed save must allow retry');
  }
  const missing=mount({missingButton:true});missing.leave();assert.equal(missing.navigations.length,0);assert(missing.messages.includes('server save failed'));
  const offline=mount({online:false});offline.leave();assert.equal(offline.navigations.length,0);assert.equal(offline.saves.length,0);assert.equal(vm.runInContext('saveDestination',offline.context),null,'Offline failure clears stale navigation destination');
  const native=mount({photo:false});native.leave();assert.equal(native.form.requested.value,'save_draft');assert.equal(native.navigations.length,0,'Native server submit determines successful redirect');
  console.log('PASS 9 wizard save-and-leave scenarios: durable save, blocked storage, volunteer action, no dialog, validation failure, network failure, offline, missing draft control, native submit');
})().catch(error=>{console.error(error);process.exitCode=1;});
