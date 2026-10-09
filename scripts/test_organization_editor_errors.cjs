// ORG-05: real editor script, bound errors must not be replaced by old recovery data.
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require('jsdom');
const source=fs.readFileSync(path.join(__dirname,'../static/js/organization_workspace.js'),'utf8');
const names=['name_az','name_ru','name_en','description_az','phone','whatsapp','website'],key='kidsmap:org:2:99:draft';
function setup({errors=true,cache=true}={}){
 const values=Object.fromEntries(names.map(n=>[n,'Posted '+n]));
 const dom=new JSDOM(`<div data-workspace="detail" data-user-id="2"><div data-org-id="99"></div><form data-org-edit-form data-source-version="1" data-schema-version="1" ${errors?'data-org-server-errors':''}>${errors?'<div id="org-editor-errors" tabindex="-1" data-org-error-summary><a href="#id_name_ru" data-org-error-target="id_name_ru">Error</a></div>':''}${names.map(n=>`<label>${n}<input id="id_${n}" name="${n}" value="${values[n]}"></label>`).join('')}<p data-draft-status></p></form></div>`,{url:'http://localhost/ru/account/organizations/99/save/',runScripts:'outside-only'});
 const {window:w}=dom;let fetches=0;w.fetch=()=>{fetches++;throw Error('No automatic save expected')};
 w.HTMLElement.prototype.scrollIntoView=function(){this.dataset.scrolled='1'};
 if(cache)w.sessionStorage.setItem(key,JSON.stringify({source:'1',fields:Object.fromEntries(names.map(n=>[n,'OLD '+n]))}));
 w.eval(source);return{dom,w,values,fetches:()=>fetches};
}
test('bound invalid POST remains authoritative over older recovery values',()=>{
 const {dom,w,values,fetches}=setup();
 for(const n of names)assert.equal(w.document.querySelector(`[name=${n}]`).value,values[n]);
 assert.deepEqual(JSON.parse(w.sessionStorage.getItem(key)).fields,values);assert.equal(fetches(),0);dom.window.close();
});
test('fresh bound errors retain the posted input for reload without creating a server draft',()=>{
 const {dom,w,values,fetches}=setup({cache:false});
 assert.deepEqual(JSON.parse(w.sessionStorage.getItem(key)).fields,values);assert.equal(fetches(),0);dom.window.close();
});
test('error summary receives focus and its link focuses the rejected field',()=>{
 const {dom,w}=setup();assert.equal(w.document.activeElement.id,'org-editor-errors');
 w.document.querySelector('[data-org-error-target]').click();assert.equal(w.document.activeElement.id,'id_name_ru');assert.equal(w.document.activeElement.dataset.scrolled,'1');dom.window.close();
});
test('a clean GET continues restoring the existing local recovery without focus theft',()=>{
 const {dom,w}=setup({errors:false});for(const n of names)assert.equal(w.document.querySelector(`[name=${n}]`).value,'OLD '+n);
 assert.equal(w.document.activeElement,w.document.body);dom.window.close();
});
