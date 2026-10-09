// ORG-03: real browser script, with page navigation modelled by fresh DOMs.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require('jsdom');
const source = fs.readFileSync(path.join(__dirname, '../static/js/organization_workspace.js'), 'utf8');
const names = ['name_az','name_ru','name_en','description_az','phone','whatsapp','website'];
const key = 'kidsmap:org:create:2';
const values = Object.fromEntries(names.map(n=>[n, n==='name_az'?'Fictional organization':'']));
function page({local=null, confirmation=null, create=true, boundName='', user='2', unavailable=false}={}) {
 const dom = new JSDOM(`<html lang="en"><div data-workspace="${create?'create':'detail'}" data-user-id="${user}">${create?`<form data-org-create-form>${names.map(n=>`<input name="${n}">`).join('')}<span data-create-status></span></form>`:''}</div>${confirmation?`<script type="application/json" id="org-create-confirmation">${JSON.stringify(confirmation)}</script>`:''}</html>`,{url:'http://localhost:8788',runScripts:'outside-only'});
 const w=dom.window, form=w.document.querySelector('form');
 if(local)w.sessionStorage.setItem(key,JSON.stringify(local));
 if(form)form.elements.name_az.value=boundName;
 if(unavailable)w.Storage.prototype.setItem=()=>{throw new Error('Storage unavailable');};
 w.eval(source);
 return {dom,w,form,local:()=>JSON.parse(w.sessionStorage.getItem(key)||'null'),
  type(name,value){form.elements[name].value=value;form.elements[name].dispatchEvent(new w.Event('input',{bubbles:true}));},
  submit(){return form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));},
  close(){w.close();}};
}
test('Native submit keeps input for reopening after a failed network POST',()=>{
 const p=page();try{p.type('name_az','Latest unsent input');p.submit();
  assert.equal(p.local()?.name_az,'Latest unsent input');
  const reopened=page({local:p.local()});try{assert.equal(reopened.form.elements.name_az.value,'Latest unsent input');}finally{reopened.close();}
 }finally{p.close();}
});
test('Submit captures autofilled values even without an input event',()=>{
 const p=page();try{p.form.elements.name_az.value='Autofilled before failed submit';p.submit();assert.equal(p.local()?.name_az,'Autofilled before failed submit');}finally{p.close();}
});
test('Only confirmed creation of the matching input clears its local copy',()=>{
 const p=page({create:false,local:values,confirmation:values});try{assert.equal(p.local(),null);}finally{p.close();}
});
test('Confirmation of older input cannot erase a newer local draft',()=>{
 const p=page({create:false,local:{...values,phone:'Latest phone'},confirmation:values});try{assert.equal(p.local()?.phone,'Latest phone');}finally{p.close();}
});
test('A normal workspace visit without creation confirmation keeps the draft',()=>{
 const p=page({create:false,local:values});try{assert.deepEqual(p.local(),values);}finally{p.close();}
});
test('400/409 bound forms preserve local recovery without replacing server values',()=>{
 const p=page({local:{...values,name_en:'Local translation'},boundName:'Server bound value'});try{
  assert.equal(p.form.elements.name_az.value,'Server bound value');assert.equal(p.form.elements.name_en.value,'Local translation');
  assert.equal(p.local()?.name_en,'Local translation');p.submit();assert.equal(p.local()?.name_az,'Server bound value');
 }finally{p.close();}
});
test('Confirmation never clears another user draft',()=>{
 const p=page({create:false,user:'3',local:values,confirmation:values});try{assert.deepEqual(p.local(),values);}finally{p.close();}
});
test('Unavailable storage leaves native submission available',()=>{
 const p=page({unavailable:true});try{p.form.elements.name_az.value='Still submitted';assert.equal(p.submit(),true);assert.equal(p.form.elements.name_az.value,'Still submitted');}finally{p.close();}
});
