const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const{JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
const source=fs.readFileSync(require('node:path').join(__dirname,'../../static/admin/js/specialist_admin.js'),'utf8');
test('staff readiness distinguishes a missing price from a zero single-lesson price', () => {
 const dom = new JSDOM(`<div class="km-specialist-form-page"><form>
   <select id="id_lesson_type"><option selected value="individual">Individual</option></select>
   <input id="id_lesson_price" type="number" min="0" step="0.01">
   <div data-spec-readiness data-summary="{completed}/{total}" data-pricing="Single lesson"></div>
   <div data-readiness-missing></div></form></div>`, {runScripts:'outside-only'});
 const w = dom.window, doc = w.document;
 w.eval(source);
 const missing = doc.querySelector('[data-readiness-missing]');
 assert.match(missing.textContent, /Single lesson/);
 const price = doc.querySelector('#id_lesson_price');
 price.value = '0';
 price.dispatchEvent(new w.Event('input', {bubbles:true}));
 assert.doesNotMatch(missing.textContent, /Single lesson/);
 w.close();
});
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

function sectionEditor(t, fields) {
  const checks = Array.from({length: 12}, (_, i) =>
    `<span class="km-nav-check" data-nav-check="km-sec-${i + 1}"></span>`).join('');
  const {window} = new JSDOM(`<div class="km-specialist-form-page"><form>
    ${checks}${fields}<div data-spec-readiness data-summary="{completed}/{total}"></div>
    <span data-readiness-summary></span></form></div>`, {runScripts: 'outside-only'});
  t.after(() => window.close());
  window.eval(source);
  const doc = window.document;
  return {
    doc,
    done: number => doc.querySelector(`[data-nav-check="km-sec-${number}"]`).classList.contains('is-done'),
    set(id, value) {
      const field = doc.getElementById(id);
      field.value = value;
      field.dispatchEvent(new window.Event('input', {bubbles: true}));
    },
  };
}

function ageFields(from, to) {
  return `<input type="number" min="0" id="id_age_from" value="${from}">
    <input type="number" min="0" id="id_age_to" value="${to}">
    <input type="checkbox" id="spec_age_open_ended">`;
}

test('the saved age range has a checkmark and stays in sync while editing', t => {
  const {doc, done, set} = sectionEditor(t, ageFields(5, 11));
  assert.equal(done(4), true);
  const open = doc.getElementById('spec_age_open_ended');
  set('id_age_to', '4');
  assert.equal(done(4), false);
  open.click();
  assert.equal(done(4), true);
  open.click();
  assert.equal(done(4), false);
  set('id_age_from', '');
  assert.equal(done(4), true, 'upper bound only');
  set('id_age_to', '');
  assert.equal(done(4), false);
  open.click();
  assert.equal(done(4), false, 'open-ended without a lower bound');
  set('id_age_from', '0');
  assert.equal(done(4), true);
  set('id_age_from', '-1');
  assert.equal(done(4), false);
});

test('a saved zero upper bound is preserved when opening the editor', t => {
  const {doc, done} = sectionEditor(t, ageFields(0, 0));
  assert.equal(doc.getElementById('id_age_to').value, '0');
  assert.equal(doc.getElementById('spec_age_open_ended').checked, false);
  assert.equal(done(4), true);
});

test('education or work experience in any language counts independently of the required fields', t => {
  const fields = ['az', 'ru', 'en'].flatMap(lang =>
    ['education', 'experience_info'].map(name => `id_${name}_${lang}`));
  const {doc, done, set} = sectionEditor(t, `<section id="km-sec-9">
    <input type="number" min="0" id="id_experience_years" value="0">
    ${fields.map(id => `<textarea id="${id}"></textarea>`).join('')}</section>`);
  assert.equal(done(9), true);
  set('id_experience_years', '');
  assert.equal(done(9), false);
  for (const id of fields) {
    set(id, 'University');
    assert.equal(done(9), true);
    set(id, '  ');
    assert.equal(done(9), false);
  }
  assert.equal(doc.querySelector('[data-readiness-summary]').textContent, '0/6');
});

test('only a visible qualification marks the documents section as filled', t => {
  const withDiploma = sectionEditor(t, '<section data-qualification-document></section>');
  assert.equal(withDiploma.done(10), true);
  const withoutDiploma = sectionEditor(t, '<div id="documents-group-wrapper"><section class="inline-related">Identity</section></div>');
  assert.equal(withoutDiploma.done(10), false);
});

test('moderation has a checkmark after a decision, including rejection with a reason', t => {
  const {done, set} = sectionEditor(t, `<select id="id_status">
    <option>draft</option><option>pending</option><option>published</option><option>rejected</option>
    </select><textarea id="id_rejection_reason"></textarea>`);
  assert.equal(done(12), false);
  set('id_status', 'published');
  assert.equal(done(12), true);
  set('id_status', 'rejected');
  assert.equal(done(12), false);
  set('id_rejection_reason', 'Missing information');
  assert.equal(done(12), true);
  set('id_status', 'pending');
  assert.equal(done(12), false);
});

test('each required section follows its own fields, including conditional subjects and places', t => {
  const {doc, done} = sectionEditor(t, `
    <input id="id_name" value="Example"><textarea id="id_bio_az">Biography</textarea>
    <script id="specialist-subject-rules" type="application/json">{"requires":["tutor"],"subjects":["math"]}</script>
    <div id="id_specializations"><input type="checkbox" value="tutor" checked><input type="checkbox" value="math"></div>
    <input type="checkbox" id="id_language_ru" checked><input id="id_phone" value="+994501234567">
    <input type="checkbox" name="session_formats" value="visit" checked>
    <input type="checkbox" name="session_formats" value="office" checked>
    <fieldset data-specialist-visit-area><legend>Home visits</legend>
      <input name="visit_region" value="1"><input type="checkbox" name="visit_citywide"></fieldset>
    <section id="km-sec-8"><h2>Office</h2><div class="inline-related">
      <input name="practice_locations-0-region" value="1"><input name="practice_locations-0-address" value="Example">
      <input type="checkbox" name="practice_locations-0-is_active" checked>
      <input type="checkbox" name="practice_locations-0-DELETE"></div></section>
    <select id="id_lesson_type"><option>individual</option></select>
    <input type="number" id="id_lesson_price" min="0" value="0">`);
  for (const number of [1, 2, 5, 7, 8, 11]) assert.equal(done(number), true, `section ${number}`);
  assert.equal(done(3), false);
  assert.equal(done(6), false);
  doc.querySelector('[value="math"]').click();
  doc.querySelector('[name="visit_citywide"]').click();
  assert.equal(done(3), true);
  assert.equal(done(6), true);
  doc.querySelector('[name$="-DELETE"]').click();
  assert.equal(done(8), false);
});
