const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || 'jsdom');
const source = fs.readFileSync(path.join(__dirname, '../../static/js/specialists.js'), 'utf8');
const accessibility = fs.readFileSync(path.join(__dirname, '../../static/js/specialist_workspace.js'), 'utf8');
async function setup({locale = 'ru', format = 'online', phone = '+994501234567', row = '', errorLocale = '', desktop = false} = {}) {
  const rules = {location_required_formats: ['offline', 'both'], location_required_fields: ['region'], location_identity_fields: ['place', 'address']};
  const dom = new JSDOM(`<html lang="${locale}"><body><script id="specialist-readiness-rules" type="application/json">${JSON.stringify(rules)}</script>
    <form class="km-specialist-owner-form km-unified-form">
      <details class="km-section-navigation" open><summary>Sections</summary><a href="#km-sec-basic" data-toc-target="km-sec-basic">Personal</a></details><section id="km-sec-basic" class="km-unified-section"></section>
      <input id="id_name" value="Test specialist"><label class="owner-specialist-chip"><input name="specializations" type="checkbox" checked><span class="chip-title">Speech therapist</span></label>
      <label class="owner-specialist-chip"><input id="id_language_ru" name="language_ru" type="checkbox" checked><span class="chip-title">Russian</span></label>
      <div data-owner-selected-specs><span data-selected-count></span><div data-selected-chips></div><button type="button" data-clear-specs>Clear specializations</button></div>
      <select id="id_consultation_format"><option selected>${format}</option></select>
      <input id="id_phone" value="${phone}" pattern="[+0-9 ()-]{7,25}"><input id="id_whatsapp">
      <div data-req-progress-fill></div><span data-req-badge></span><span data-req-status-text data-all-done="Filled"></span>
      <div data-owner-spec-dropdown><button type="button" data-owner-spec-dropdown-trigger aria-expanded="false">Choose</button>
        <div data-owner-spec-dropdown-panel hidden><input data-spec-search></div></div>
      <div role="tablist">${['az','ru','en'].map(l=>`<button type="button" data-owner-lang-tab="${l}">${l}</button>`).join('')}</div>
      ${['az','ru','en'].map(l=>`<div data-owner-lang-panel="${l}"><textarea id="id_bio_${l}">${l==='ru'?'Biography':''}</textarea>${l===errorLocale?'<small class="auth-field-error">Invalid</small>':''}</div>`).join('')}
      ${row}
    </form></body></html>`, {runScripts:'outside-only', url:'http://localhost/ru/'});
  const w = dom.window;
  w.matchMedia = () => ({matches: desktop, addEventListener() {}});
  w.HTMLElement.prototype.scrollIntoView = function () {};
  Object.defineProperty(w.document, 'readyState', {value:'complete'});
  w.eval(source); w.eval(accessibility);
  w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
  await new Promise(resolve=>setTimeout(resolve, 65));
  return {dom, w, doc:w.document, form:w.document.querySelector('form')};
}
const locationRow = (fields='') => `<article data-practice-row><input name="locations-0-is_active" type="checkbox" checked><input name="locations-0-DELETE" type="checkbox">${fields}</article>`;
test('offline and mixed profiles without a practice location never show complete', async () => {
  for (const format of ['offline','both']) {
    const t = await setup({format});
    assert.equal(t.doc.querySelector('[data-req-progress-fill]').classList.contains('is-complete'), false);
    t.dom.window.close();
  }
});
test('location completeness follows active, deletion, address and region changes', async () => {
  const t = await setup({format:'offline', row:locationRow('<input name="locations-0-address" value="42 Street"><select name="locations-0-region"><option value="">Choose</option><option value="1">Baku</option></select>')});
  const complete=()=>t.doc.querySelector('[data-req-progress-fill]').classList.contains('is-complete');
  const change=(name, value)=>{const field=t.form.elements[name];if(field.type==='checkbox')field.checked=value;else field.value=value;field.dispatchEvent(new t.w.Event('change',{bubbles:true}));};
  assert.equal(complete(), false);
  change('locations-0-region','1'); assert.equal(complete(), true);
  change('locations-0-is_active',false); assert.equal(complete(), false);
  change('locations-0-is_active',true); change('locations-0-DELETE',true); assert.equal(complete(), false);
  t.dom.window.close();
});
test('invalid phone does not count as a completed contact', async () => {
  const t=await setup({phone:'abc'});
  assert.equal(t.doc.querySelector('[data-req-progress-fill]').classList.contains('is-complete'),false);
  t.dom.window.close();
});
test('Escape closes specializations from inside the popup and returns focus', async () => {
  const t=await setup(); const trigger=t.doc.querySelector('[data-owner-spec-dropdown-trigger]'); trigger.click();
  const search=t.doc.querySelector('[data-spec-search]');search.focus();search.dispatchEvent(new t.w.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
  assert.equal(t.doc.querySelector('[data-owner-spec-dropdown-panel]').hidden,true);
  assert.equal(trigger.getAttribute('aria-expanded'),'false');assert.equal(t.doc.activeElement,trigger);
  t.dom.window.close();
});
test('biography opens in the current locale with synchronized tab state', async () => {
  for (const locale of ['az','ru','en']) {
    const t=await setup({locale});
    assert.equal(t.doc.querySelector('[data-owner-lang-panel="'+locale+'"]').hidden,false);
    assert.equal(t.doc.querySelector('[data-owner-lang-tab="'+locale+'"]').getAttribute('aria-selected'),'true');
    t.dom.window.close();
  }
});
test('a biography error opens its language and error links focus the visible field', async () => {
  const t=await setup({locale:'ru',errorLocale:'en'});
  assert.equal(t.doc.querySelector('[data-owner-lang-panel="en"]').hidden,false);
  const link=t.doc.createElement('a');link.href='#id_bio_az';t.form.append(link);link.click();
  assert.equal(t.doc.querySelector('[data-owner-lang-panel="az"]').hidden,false);
  assert.equal(t.doc.activeElement.id,'id_bio_az');t.dom.window.close();
});

test('switching to a custom office clears the previously selected catalog place', () => {
  const dom=new JSDOM(`<form class="km-specialist-owner-form"><div data-practice-editor>
    <input name="locations-TOTAL_FORMS" value="1"><button data-practice-add></button><template></template><div data-practice-rows>
    <article data-practice-row><span data-practice-number></span><div data-location-type-selector><button type="button" data-type-target="place"></button><button type="button" data-type-target="custom"></button></div>
    <div data-location-panel="place"><select name="locations-0-place"><option value=""></option><option value="23" selected>Center</option></select></div>
    <div data-location-panel="custom"><input name="locations-0-address" value="Private office"></div></article></div></div></form>`,{runScripts:'outside-only'});
  dom.window.eval(fs.readFileSync(path.join(__dirname,'../../static/js/specialist_locations.js'),'utf8'));
  dom.window.document.querySelector('[data-type-target="custom"]').click();
  assert.equal(dom.window.document.querySelector('[name="locations-0-place"]').value,'');
  assert.equal(dom.window.document.querySelector('[name="locations-0-address"]').value,'Private office');
  dom.window.close();
});

test('legacy recovery restores text but never changes the server-owned profile subject', () => {
  for (const subject of ['self','other']) {
    const dom=new JSDOM(`<form class="km-specialist-owner-form" data-recovery-actor="42" data-recovery-entity="proposal-new" data-recovery-version="0" data-recovery-server-version="0">
      <input type="hidden" name="profile_subject" value="${subject}"><input name="name" value="">
      <div data-specialist-recovery hidden><p data-recovery-description data-same="Saved"></p><ul data-recovery-diff></ul><button type="button" data-recovery-restore>Restore</button><button type="button" data-recovery-discard>Discard</button></div></form>`,{runScripts:'outside-only',url:'http://localhost/'});
    dom.window.sessionStorage.setItem('specialist-entry-v1:42:proposal-new:0',JSON.stringify({version:'0',values:{profile_subject:[subject==='self'?'other':'self'],name:['Recovered name']}}));
    dom.window.eval(fs.readFileSync(path.join(__dirname,'../../static/js/specialist_recovery.js'),'utf8'));
    dom.window.document.querySelector('[data-recovery-restore]').click();
    assert.equal(dom.window.document.querySelector('[name=name]').value,'Recovered name');
    assert.equal(dom.window.document.querySelector('[name=profile_subject]').value,subject);
    dom.window.close();
  }
});

test('working languages are never displayed or counted as selected specializations', async () => {
  const t=await setup();
  assert.equal(t.doc.querySelector('[data-selected-count]').textContent,'1');
  assert.deepEqual(Array.from(t.doc.querySelectorAll('[data-selected-chips] .pill-name'),e=>e.textContent),['Speech therapist']);
  const language=t.doc.querySelector('#id_language_ru');
  language.checked=false;language.dispatchEvent(new t.w.Event('change',{bubbles:true}));
  assert.equal(language.closest('label').classList.contains('is-checked'),false);
  language.checked=true;language.dispatchEvent(new t.w.Event('change',{bubbles:true}));
  assert.equal(language.closest('label').classList.contains('is-checked'),true);
  assert.equal(t.doc.querySelector('[data-selected-count]').textContent,'1');
  t.dom.window.close();
});

test('clearing specializations preserves working languages and clears chip styling', async () => {
  const t=await setup();t.doc.querySelector('[data-clear-specs]').click();
  assert.equal(t.doc.querySelector('[name=specializations]').checked,false);
  assert.equal(t.doc.querySelector('[name=specializations]').closest('label').classList.contains('is-checked'),false);
  assert.equal(t.doc.querySelector('#id_language_ru').checked,true);
  assert.equal(t.doc.querySelector('[data-selected-count]').textContent,'0');
  t.dom.window.close();
});

test('mobile section navigation starts collapsed and closes after choosing a section', async () => {
  const t = await setup();
  const nav = t.doc.querySelector('.km-section-navigation');
  assert.equal(nav.open, false);
  nav.open = true;
  nav.querySelector('a').click();
  assert.equal(nav.open, false);
  assert.equal(t.doc.activeElement, t.doc.getElementById('km-sec-basic'));
  t.dom.window.close();
});
test('desktop section navigation stays expanded when its heading is clicked', async () => {
  const t = await setup({desktop: true});
  const nav = t.doc.querySelector('.km-section-navigation');
  assert.equal(nav.open, true);
  nav.querySelector('summary').click();
  assert.equal(nav.open, true);
  t.dom.window.close();
});
