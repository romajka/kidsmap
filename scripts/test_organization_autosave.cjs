// ORG-02: exercise the actual editor script; controlled HTTP delivery and time.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require('jsdom');
const source = fs.readFileSync(path.join(__dirname, '../static/js/organization_workspace.js'), 'utf8');
const names = ['name_az','name_ru','name_en','description_az','phone','whatsapp','website'];
const key = 'kidsmap:org:2:99:draft';
const settle = async () => {for (let i=0; i<10; i++) await Promise.resolve();};
function editor({storageFails=false}={}) {
 const dom = new JSDOM(`<html lang="en"><div data-workspace data-user-id="2"><div data-org-id="99"></div><form data-org-edit-form data-draft-url="/api/drafts/" data-source-version="1" data-schema-version="1" data-draft-id="draft-existing" data-draft-version="1">${names.map(n=>`<input name="${n}" value="Initial">`).join('')}<input name="csrfmiddlewaretoken" value="synthetic-csrf"><span data-draft-status></span></form></div></html>`,{url:'http://localhost:8788',runScripts:'outside-only'});
 const w=dom.window, form=w.document.querySelector('form'), jobs=new Map(), requests=[];
 let now=0, id=0;
 w.setTimeout=(callback,delay)=>{jobs.set(++id,{callback,at:now+delay});return id;};
 w.clearTimeout=n=>jobs.delete(n);
 w.fetch=(url,options)=>new Promise((resolve,reject)=>requests.push({body:JSON.parse(options.body),
  respond:(status,version)=>resolve({status,ok:status===200,json:async()=>({draft_id:'draft-existing',version,status:status===200?'server_saved':'conflict'})}),reject}));
 if(storageFails) w.Storage.prototype.setItem=()=>{throw new Error('Storage unavailable');};
 w.eval(source);
 return {form,requests,dom,window:w,
  type(value){form.elements.name_en.value=value;form.elements.name_en.dispatchEvent(new w.Event('input',{bubbles:true}));},
  async tick(ms=650){now+=ms;for(const [n,job]of [...jobs])if(job.at<=now){jobs.delete(n);job.callback();}await settle();},
  local(){const raw=w.sessionStorage.getItem(key);return raw?JSON.parse(raw):null;},
  status(){return form.querySelector('[data-draft-status]').textContent;},
  close(){w.close();}
 };
}

test('Delayed acknowledgement of A cannot clear B or claim B is saved',async()=>{
 const e=editor();try{
  e.type('A');await e.tick();e.type('B');await e.tick();
  // The old implementation sends B with v1 while A is still in flight; its CAS fails.
  if(e.requests[1]){e.requests[1].respond(409,2);await settle();}
  e.requests[0].respond(200,2);await settle();
  assert.equal(e.form.elements.name_en.value,'B');
  assert.equal(e.local()?.fields.name_en,'B','Old success must not erase the latest local copy');
  assert.notEqual(e.status(),'Saved on server','A acknowledgement cannot confirm B');
  await e.tick();const latest=e.requests.at(-1);
  assert.equal(latest.body.fields.name_en,'B');assert.equal(latest.body.expected_version,2);
  latest.respond(200,3);await settle();
  assert.equal(e.status(),'Saved on server');assert.equal(e.local(),null);
 }finally{e.close();}
});

test('Queued edits coalesce to C while the previous request is pending',async()=>{
 const e=editor();try{
  e.type('A');await e.tick();e.type('B');await e.tick();e.type('C');await e.tick();
  e.requests[0].respond(200,2);await settle();await e.tick();
  assert.equal(e.requests.length,2,'Only A and the latest C should be submitted');
  assert.equal(e.requests[1].body.fields.name_en,'C');assert.equal(e.requests[1].body.expected_version,2);
  e.requests[1].respond(200,3);await settle();assert.equal(e.status(),'Saved on server');assert.equal(e.local(),null);
 }finally{e.close();}
});

test('Another tab wins CAS:409 preserves the latest input and stops automatic overwrite',async()=>{
 const e=editor();try{
  e.type('A');await e.tick();e.type('B');await e.tick();e.requests[0].respond(409,2);await settle();
  await e.tick();e.type('C');await e.tick();
  assert.equal(e.requests.length,1,'Conflict must require a reload, not blind retry');
  assert.equal(e.local()?.fields.name_en,'C');assert.match(e.status(),/^Conflict:/);
 }finally{e.close();}
});

test('403 or network failure retains input; an old failed response never clears newer edits',async()=>{
 for(const mode of ['forbidden','network']){
  const e=editor();try{
   e.type('A');await e.tick();e.type('B');
   if(mode==='forbidden')e.requests[0].respond(403,1);else e.requests[0].reject(new Error('Offline'));
   await settle();assert.equal(e.local()?.fields.name_en,'B');assert.notEqual(e.status(),'Saved on server');
  }finally{e.close();}
 }
});

test('Server confirmation of unchanged input clears the matching local draft',async()=>{
 const e=editor();try{e.type('A');await e.tick();e.requests[0].respond(200,2);await settle();
  assert.equal(e.form.dataset.draftVersion,'2');assert.equal(e.status(),'Saved on server');assert.equal(e.local(),null);
 }finally{e.close();}
});

test('Unavailable browser storage does not turn an old response into confirmation of B',async()=>{
 const e=editor({storageFails:true});try{
  e.type('A');await e.tick();e.type('B');e.requests[0].respond(200,2);await settle();
  assert.equal(e.form.elements.name_en.value,'B');assert.notEqual(e.status(),'Saved on server');
  await e.tick();e.requests.at(-1).respond(200,3);await settle();assert.equal(e.status(),'Saved on server');
 }finally{e.close();}
});
