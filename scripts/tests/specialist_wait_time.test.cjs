const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || 'jsdom');

test('elapsed time follows the submission timestamp across minute boundaries and time away', () => {
  const start = '2026-11-20T10:00:00+04:00';
  const dom = new JSDOM(`<html lang="en"><dl><dt>Submitted</dt><dd><time datetime="${start}"></time></dd>
    <dt>Time waiting</dt><dd data-wait-elapsed data-under-minute="Less than a minute">0 minutes</dd></dl></html>`,
    {runScripts: 'outside-only', pretendToBeVisual: true});
  try {
    const {window} = dom;
    const value = window.document.querySelector('[data-wait-elapsed]');
    let elapsed = 59500;
    let scheduled;
    window.Date.now = () => Date.parse(start) + elapsed;
    window.setTimeout = (fn, delay) => { scheduled = {fn, delay}; return 1; };
    window.eval(fs.readFileSync('static/js/specialist_wait_time.js', 'utf8'));
    assert.equal(value.textContent, 'Less than a minute');
    assert.equal(scheduled.delay, 500);

    elapsed = 60000;
    scheduled.fn();
    assert.equal(value.textContent, '1 min');
    elapsed = 25 * 3600000;
    window.dispatchEvent(new window.Event('pageshow'));
    assert.equal(value.textContent, '1 day 1 hr');
  } finally {
    dom.window.close();
  }
});
