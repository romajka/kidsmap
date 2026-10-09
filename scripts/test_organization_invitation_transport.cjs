// ORG-07: install real POST interception before releasing invitation controls.
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require('jsdom');
const source=fs.readFileSync(path.join(__dirname,'../static/js/organization_workspace.js'),'utf8');
function setup(ok=true){
 const dom=new JSDOM(`<html lang="en"><div data-workspace="detail" data-user-id="2"><form method="post" action="/team/invite/" data-team-form data-team-url="/team/invite/"><input type="hidden" name="csrfmiddlewaretoken" value="synthetic-token"><p data-team-unavailable>Requires JavaScript</p><input name="email" type="email" disabled data-team-control value="org07@example.invalid"><select name="role" disabled data-team-control data-team-role><option value="EDITOR" data-summary="Edit">Editor</option></select><p data-team-role-summary></p><select name="scope" disabled data-team-control data-team-scope><option value="all_network">All</option><option value="selected_places">Selected</option></select><fieldset data-team-branches hidden><input name="place_ids" type="checkbox" value="42" disabled data-team-control></fieldset><button type="submit" disabled data-team-control>Invite</button><p data-team-status></p></form></div></html>`,{url:'http://localhost/organizations/99/',runScripts:'outside-only'});
 const w=dom.window,calls=[];w.fetch=async(url,options)=>{calls.push({url,options});return{ok};};return{dom,w,calls,form:w.document.querySelector('form')};
}
test('initial disabled invitation becomes keyboard operable only with installed POST handler',async()=>{
 const {dom,w,calls,form}=setup();assert.equal(form.elements.email.matches(':disabled'),true);w.eval(source);
 assert.equal(form.elements.email.matches(':disabled'),false);assert.equal(form.querySelector('button').matches(':disabled'),false);assert.equal(form.querySelector('[data-team-unavailable]').hidden,true);
 const event=new w.Event('submit',{bubbles:true,cancelable:true});form.dispatchEvent(event);await new Promise(resolve=>setImmediate(resolve));
 assert.equal(event.defaultPrevented,true);assert.equal(calls.length,1);assert.equal(calls[0].url,'/team/invite/');assert.equal(calls[0].options.method,'POST');assert.equal(calls[0].options.headers['X-CSRFToken'],'synthetic-token');assert.equal(calls[0].url.includes('@'),false);assert.equal(form.querySelector('[data-team-status]').textContent,'Invitation sent');dom.window.close();
});
test('failed invitation retains input and handler prevents native navigation',async()=>{
 const {dom,w,calls,form}=setup(false);w.eval(source);form.elements.scope.value='selected_places';form.querySelector('[name=place_ids]').checked=true;
 const event=new w.Event('submit',{bubbles:true,cancelable:true});form.dispatchEvent(event);await new Promise(resolve=>setImmediate(resolve));
 assert.equal(event.defaultPrevented,true);assert.equal(calls.length,1);assert.equal(form.elements.email.value,'org07@example.invalid');assert.equal(form.querySelector('[name=place_ids]').checked,true);assert.ok(form.querySelector('[data-team-status]').textContent);dom.window.close();
});
