const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const{JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
const source=fs.readFileSync(require('node:path').join(__dirname,'../../static/admin/js/specialist_admin.js'),'utf8');
test('admin counts the required tutor subject separately and updates after selection/removal',()=>{
 const dom=new JSDOM(`<div class="km-specialist-form-page"><form><script id="specialist-subject-rules" type="application/json">{"requires":["tutor"],"subjects":["math"]}</script><input id="id_name" value="Tutor"><div id="id_specializations"><div><label><input type="checkbox" value="tutor" checked>Tutor</label></div><div><label><input type="checkbox" value="math">Math</label></div></div><select id="id_consultation_format"><option value="online" selected>Online</option></select><input id="id_language_ru" type="checkbox" checked><input id="id_phone" value="+994501234567"><textarea id="id_bio_ru">Teaching</textarea><div data-spec-readiness data-summary="{completed}/{total}" data-subject="Subject"></div><span data-readiness-summary></span><span data-readiness-pct></span><div data-readiness-missing></div></form></div>`,{runScripts:'outside-only'});
 const w=dom.window,d=w.document;w.eval(source);
 const summary=()=>d.querySelector('[data-readiness-summary]').textContent;
 assert.equal(summary(),'6/7');assert.match(d.querySelector('[data-readiness-missing]').textContent,/Subject/);
 const subject=d.querySelector('[value=math]');subject.checked=true;subject.dispatchEvent(new w.Event('change',{bubbles:true}));assert.equal(summary(),'7/7');
 subject.checked=false;subject.dispatchEvent(new w.Event('change',{bubbles:true}));assert.equal(summary(),'6/7');
 w.close();
});
