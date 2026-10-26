const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || 'jsdom');

function mount(days, lang = 'ru') {
  const dom = new JSDOM(`<html lang="${lang}"><form><section data-km-schedule-editor
    data-preview-empty-label="Unknown hours" data-preview-closed-label="Closed"
    data-unknown-label="Unknown" data-open-label="Open" data-closed-label="Closed"><input data-km-schedule-editor-input>
    <div data-km-schedule-days><div data-km-schedule-row="mon">
      <span class="km-schedule-editor__toggle-text">${days.length ? 'Closed' : 'Unknown'}</span>
      <div class="km-schedule-editor__work"></div>
      <div class="km-schedule-editor__row-errors">Server validation error</div>
    </div></div><div data-km-schedule-preview></div>
    <button type="button" data-km-schedule-preset="clear">Clear</button>
    <button type="button" data-km-schedule-preset="weekdays">Weekdays</button>
    <button type="button" data-km-schedule-open-day="mon">Open Monday</button>
    </section></form></html>`, {runScripts: 'outside-only', url: 'http://localhost/'});
  const w = dom.window;
  w.kmModal = {confirm: async () => true};
  const input = w.document.querySelector('input');
  input.value = JSON.stringify(days);
  w.eval(fs.readFileSync('static/js/kidsmap_schedule_editor.js', 'utf8'));
  w.kidsMapInitScheduleEditors();
  return {w, input, q: s => w.document.querySelector(s), close: () => w.close()};
}

for (const lang of ['az', 'ru', 'en']) {
  test(`${lang}: empty import and clear stay unknown, never a closed week`, async () => {
    const m = mount([], lang);
    try {
      assert.match(m.q('[data-km-schedule-preview]').textContent, /Unknown hours/);
      assert.deepEqual(JSON.parse(m.input.value), []);
      assert.match(m.q('.km-schedule-editor__row-errors').textContent, /Server validation error/);
      m.q('[data-km-schedule-preset="weekdays"]').click();
      assert.equal(JSON.parse(m.input.value).length, 7);
      m.q('[data-km-schedule-preset="clear"]').click();
      await new Promise(resolve => setTimeout(resolve, 0));
      assert.deepEqual(JSON.parse(m.input.value), []);
      assert.match(m.q('[data-km-schedule-preview]').textContent, /Unknown hours/);
      m.q('[data-km-schedule-open-day="mon"]').click();
      assert.equal(JSON.parse(m.input.value)[0].is_closed, false);
      assert.equal(m.q('.km-schedule-editor__toggle-text').textContent, 'Open');
      m.input.value = '[]';
      m.input.dispatchEvent(new m.w.Event('km:schedule-import'));
      assert.match(m.q('[data-km-schedule-preview]').textContent, /Unknown hours/);
      assert.equal(m.q('.km-schedule-editor__toggle-text').textContent, 'Unknown');
    } finally { m.close(); }
  });
}

test('explicit closed week is displayed and preserved as closed', () => {
  const days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'].map(weekday =>
    ({weekday, is_closed: true, is_24_hours: false, intervals: []}));
  const m = mount(days);
  try {
    assert.match(m.q('[data-km-schedule-preview]').textContent, /Closed/);
    assert.deepEqual(JSON.parse(m.input.value), days);
  } finally { m.close(); }
});
