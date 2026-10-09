// ORG-06: current comparison must not silently substitute or destroy local input.
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require('jsdom');
const source=fs.readFileSync(path.join(__dirname,'../static/js/organization_workspace.js'),'utf8');
const names=['name_az','name_ru','name_en','description_az','phone','whatsapp','website'],key='kidsmap:org:2:99:draft';
function setup(current){
 const dom=new JSDOM(`<div data-workspace="detail" data-user-id="2"><div data-org-id="99"></div><form data-org-edit-form data-source-version="1" ${current?'data-org-current-data':''}>${names.map(n=>`<input name="${n}" value="Winner ${n}">`).join('')}<p data-draft-status></p></form></div>`,{url:'http://localhost/ru/account/organizations/99/?current=1',runScripts:'outside-only'});
 const {window:w}=dom;const local={source:'1',fields:Object.fromEntries(names.map(n=>[n,'Loser '+n]))};w.sessionStorage.setItem(key,JSON.stringify(local));let fetches=0;w.fetch=()=>{fetches++;throw Error('No automatic POST expected')};w.eval(source);return{dom,w,local,fetches:()=>fetches};
}
test('current comparison shows server winner and retains the original browser copy',()=>{
 const {dom,w,local,fetches}=setup(true);for(const n of names)assert.equal(w.document.querySelector(`[name=${n}]`).value,'Winner '+n);
 assert.deepEqual(JSON.parse(w.sessionStorage.getItem(key)),local);assert.equal(w.document.querySelector('[data-draft-status]').textContent,'');assert.equal(fetches(),0);dom.window.close();
});
test('ordinary GET still restores the existing local recovery',()=>{
 const {dom,w,fetches}=setup(false);for(const n of names)assert.equal(w.document.querySelector(`[name=${n}]`).value,'Loser '+n);assert.equal(fetches(),0);dom.window.close();
});
