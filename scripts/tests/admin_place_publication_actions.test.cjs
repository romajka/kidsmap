const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM_MODULE||'jsdom');
async function harness({published=false,confirmed=true,menuAllowed='0'}={}){
 const dom=new JSDOM(`<form id="changelist-form"></form><table><tr><td><button type="button" data-publication-action="toggle_pub" data-place-id="42" data-status="${published?'published':'draft'}" data-is-active="${published?'1':'0'}" data-toggle-publication-url="/admin/catalog/place/42/toggle-publication/">Action</button><button type="button" data-more-actions-btn data-place-id="42" data-status="draft" data-is-active="0" data-has-coords="1" data-can-toggle-publication="${menuAllowed}" data-publication-reason="Missing price">More</button></td></tr></table><div id="km-row-actions-dropdown" hidden><button id="km-row-act-pub" data-row-action="toggle_pub"><svg id="km-row-act-pub-icon"><use></use></svg><span id="km-row-act-pub-label"></span></button></div>`,{url:'http://localhost/admin/catalog/place/',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window,calls=[];w.document.cookie='csrftoken=fixture-csrf';
 w.kmModal={confirm:async()=>confirmed};w.kmToast={info:()=>1,dismiss(){},error(){},success(){},warning(){}};
 w.fetch=async(url,options)=>{calls.push({url,options});return{json:async()=>({ok:false,message:'Fixture refused'})}};
 w.eval(fs.readFileSync('static/admin/js/kidsmap_place_changelist.js','utf8'));
 w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
 await new Promise(resolve=>setImmediate(resolve));
 return{w,calls,close:()=>w.close()};
}
test('visible publish control sends exactly one CSRF protected POST',async()=>{
 const h=await harness();try{
 h.w.document.cookie='csrftoken=fixture-csrf';
 h.w.document.querySelector('[data-publication-action]').click();
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(h.calls.length,1);assert.equal(h.calls[0].url,'/admin/catalog/place/42/toggle-publication/');
 assert.equal(h.calls[0].options.body.get('intent'),'publish');
 assert.equal(h.calls[0].options.method,'POST');assert.equal(h.calls[0].options.headers['X-CSRFToken'],'fixture-csrf');
 }finally{h.close()}
});
test('unpublish cancellation does not change publication',async()=>{
 const h=await harness({published:true,confirmed:false});try{
 h.w.document.querySelector('[data-publication-action]').click();
 await new Promise(resolve=>setImmediate(resolve));assert.equal(h.calls.length,0);
 }finally{h.close()}
});
test('row menu respects full server readiness even when coordinates exist',async()=>{
 const h=await harness();try{
 h.w.document.querySelector('[data-more-actions-btn]').click();
 const action=h.w.document.querySelector('#km-row-act-pub');assert.equal(action.disabled,true);assert.equal(action.title,'Missing price');
 }finally{h.close()}
});
