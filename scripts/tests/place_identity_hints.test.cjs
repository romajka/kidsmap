const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function harness(fetch){
 const dom=new JSDOM(`<script type="application/json" id="km-identity-copy">{"title":"Check duplicates","not_found":"No matches within access","scope_hint":"Access is limited","failed":"Check failed","checking":"Checking","show_all":"All results","source":"Source","generated":"Snapshot","retry":"Retry"}</script><form data-duplicate-candidates-url="/duplicates/" data-duplicate-exclude="42"><input name="name_en"><input name="phone1"><input name="phone2"><input name="website"><input name="instagram"><input name="address"><input name="server_draft_id" value="own-draft"></form><section data-place-duplicate-alert hidden></section>`,{url:'http://localhost/admin/catalog/place/add/',runScripts:'outside-only'});
 const w=dom.window;w.fetch=fetch;w.eval(fs.readFileSync('static/admin/js/kidsmap_place_duplicates.js','utf8'));
 return{w,form:w.document.querySelector('form'),alert:w.document.querySelector('section'),
  change(name,value){const el=w.document.querySelector(`[name=${name}]`);el.value=value;el.dispatchEvent(new w.Event('blur'));},close:()=>w.close()};
}
const payload={results:[],total:0,decision:'not_found_within_access',generated_at:'2026-10-29',coverage:{complete_within_access:true},registry_url:'/registry/'};
test('names and secondary phones are submitted and current private draft is excluded',async()=>{
 const calls=[],h=harness(async url=>{calls.push(url);return{ok:true,json:async()=>payload}});
 try{h.change('name_en','Little Academy');h.change('phone2','+994501234567');await tick();
 const q=new URL(calls.at(-1),'http://localhost').searchParams;
 assert.equal(q.get('name_en'),'Little Academy');assert.equal(q.get('phone2'),'+994501234567');assert.equal(q.get('exclude_draft_id'),'own-draft');
 }finally{h.close()}
});
test('empty matches show access limits rather than claiming absence',async()=>{
 const h=harness(async()=>({ok:true,json:async()=>payload}));try{h.change('address','Some Avenue 10');await tick();
 assert.equal(h.alert.hidden,false);assert.match(h.alert.textContent,/No matches within access/);assert.match(h.alert.textContent,/Access is limited/);
 }finally{h.close()}
});
test('network failure remains visible and can be retried',async()=>{
 let calls=0;const h=harness(async()=>{calls++;throw Error('offline')});try{h.change('address','Some Avenue 10');await tick();
 assert.equal(h.alert.hidden,false);assert.match(h.alert.textContent,/Check failed/);
 h.alert.querySelector('[data-identity-retry]').click();await tick();assert.equal(calls,2);
 }finally{h.close()}
});
test('stale responses cannot replace a newer identity check',async()=>{
 const pending=[];const h=harness(url=>new Promise(resolve=>pending.push(resolve)));try{
 h.change('address','First Avenue 10');h.change('address','Second Avenue 20');
 pending[1]({ok:true,json:async()=>({...payload,generated_at:'NEW_SNAPSHOT'})});await tick();
 pending[0]({ok:true,json:async()=>({...payload,generated_at:'OLD_SNAPSHOT'})});await tick();
 assert.match(h.alert.textContent,/NEW_SNAPSHOT/);assert.doesNotMatch(h.alert.textContent,/OLD_SNAPSHOT/);
 }finally{h.close()}
});
test('matching version evidence and pagination limits remain visible without HTML injection',async()=>{
 const data={...payload,total:13,has_next:true,results:[{id:2,title:'<img src=x onerror=alert(1)>',url:'/edit/2',compare_url:'/compare/2',address:'Saved address',matched:['Phone'],evidence:[{source_label:'Saved changes',version:3,signal_labels:'Phone'}]}]};
 const h=harness(async()=>({ok:true,json:async()=>data}));try{h.change('phone1','+994501234567');await tick();
 assert.equal(h.alert.querySelector('img'),null);assert.match(h.alert.textContent,/Saved changes/);assert.match(h.alert.textContent,/13/);assert(h.alert.querySelector('a[href="/registry/"]'));
 }finally{h.close()}
});
