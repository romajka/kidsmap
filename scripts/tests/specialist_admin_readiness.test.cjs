const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const{JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
const source=fs.readFileSync(require('node:path').join(__dirname,'../../static/admin/js/specialist_admin.js'),'utf8');
test('admin counts the required tutor subject separately and updates after selection/removal',()=>{
 const dom=new JSDOM(`<div class="km-specialist-form-page"><form><script id="specialist-subject-rules" type="application/json">{"requires":["tutor"],"subjects":["math"]}</script><input id="id_name" value="Tutor"><div id="id_specializations"><div><label><input type="checkbox" value="tutor" checked>Tutor</label></div><div><label><input type="checkbox" value="math">Math</label></div></div><label><input type="checkbox" name="session_formats" value="online" checked>Online</label><input id="id_language_ru" type="checkbox" checked><input id="id_phone" value="+994501234567"><textarea id="id_bio_ru">Teaching</textarea><div data-spec-readiness data-summary="{completed}/{total}" data-subject="Subject"></div><span data-readiness-summary></span><span data-readiness-pct></span><div data-readiness-missing></div></form></div>`,{runScripts:'outside-only'});
 const w=dom.window,d=w.document;w.eval(source);
 const summary=()=>d.querySelector('[data-readiness-summary]').textContent;
 assert.equal(summary(),'6/7');assert.match(d.querySelector('[data-readiness-missing]').textContent,/Subject/);
 const subject=d.querySelector('[value=math]');subject.checked=true;subject.dispatchEvent(new w.Event('change',{bubbles:true}));assert.equal(summary(),'7/7');
 subject.checked=false;subject.dispatchEvent(new w.Event('change',{bubbles:true}));assert.equal(summary(),'6/7');
 w.close();
});

test('office controls follow the office checkbox independently of online and home visits',()=>{
 const dom=new JSDOM(`<div class="km-specialist-form-page"><form>
   <input type="checkbox" name="session_formats" value="online" checked>
   <input type="checkbox" name="session_formats" value="office">
   <input type="checkbox" name="session_formats" value="visit" checked>
   <section id="km-sec-8" data-office-section><h2>Office</h2></section>
 </form></div>`,{runScripts:'outside-only'});
 const w=dom.window,d=w.document;w.eval(source);
 const office=d.querySelector('[value=office]'),section=d.querySelector('#km-sec-8');
 assert.equal(section.hidden,true);
 office.click();assert.equal(section.hidden,false);
 assert.equal(d.querySelector('[value=online]').checked,true);
 assert.equal(d.querySelector('[value=visit]').checked,true);
 office.click();assert.equal(section.hidden,true);
 w.close();
});

test('an invalid submitted office row stays visible when only online is selected',()=>{
 const dom=new JSDOM(`<div class="km-specialist-form-page"><form>
   <input type="checkbox" name="session_formats" value="online" checked>
   <section id="km-sec-8" data-office-section><ul class="errorlist"><li>Invalid price</li></ul></section>
 </form></div>`,{runScripts:'outside-only'});
 dom.window.eval(source);
 assert.equal(dom.window.document.querySelector('#km-sec-8').hidden,false);
 dom.window.close();
});
