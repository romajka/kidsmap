// Setup: npm install --prefix .tmp/phone-dom --no-save --package-lock=false jsdom
// Run: node --test scripts/test_phone_reveal.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require('../.tmp/phone-dom/node_modules/jsdom');
const script = fs.readFileSync(path.join(__dirname, '../static/js/place_phone_reveal.js'), 'utf8');
const contacts = {phones: [{number: '+994501234567', href: 'tel:+994501234567'}], whatsapp: 'https://wa.me/994501234567'};
function setup(fetch) {
  const dom = new JSDOM(`<html lang="ru"><body>
    <div data-phone-config data-phone-endpoint="/api/places/0/phones/"><input name="csrfmiddlewaretoken" value="csrf-test"></div>
    <div data-phone-status role="status"></div>
    <button data-phone-reveal="7">Показать номер</button>
    <button data-phone-reveal="7" data-phone-whatsapp="1">WhatsApp</button>
    </body></html>`, {url: 'https://kidsmap.example/', runScripts: 'outside-only'});
  dom.window.fetch = fetch;
  dom.window.eval(script);
  return dom;
}
const settle = () => new Promise(resolve => setImmediate(resolve));
test('no prefetch; click loads contacts, preserves focus and creates mobile call/WhatsApp links', async () => {
  let calls = 0;
  const dom = setup(async (url, options) => {
    calls++; assert.equal(url, '/api/places/7/phones/');
    assert.equal(options.method, 'POST'); assert.equal(options.headers['X-CSRFToken'], 'csrf-test');
    return {ok: true, json: async () => contacts};
  });
  const document = dom.window.document;
  assert.equal(calls, 0); assert.equal(document.querySelector('a'), null);
  const button = document.querySelector('button'); button.focus(); button.click();
  assert.equal(button.disabled, true);
  assert.equal(button.getAttribute('aria-busy'), 'true');
  await settle();
  assert.equal(calls, 1);
  assert.equal(document.querySelector('a').getAttribute('href'), 'tel:+994501234567');
  assert.equal(document.activeElement, document.querySelector('a'));
  assert.equal(document.querySelector('a').classList.contains('km-phone-control--revealed'), true);
  assert.equal(document.querySelector('[data-phone-status]').textContent, '');
  assert.equal(document.querySelectorAll('a')[1].href, 'https://wa.me/994501234567');
  const popup = document.createElement('div'); popup.innerHTML = dom.window.kidsMapPhoneButton(7);
  document.body.append(popup); popup.querySelector('button').click(); await settle();
  assert.equal(calls, 1); assert.equal(popup.querySelector('a').textContent, '+994501234567');
  dom.window.close();
});
test('failed request keeps a retry button and announces error; retry works', async () => {
  let calls = 0;
  const dom = setup(async () => ++calls === 1 ? {ok: false, status: 429} : {ok: true, json: async () => contacts});
  const document = dom.window.document, button = document.querySelector('button');
  button.click(); await settle();
  assert.equal(button.disabled, false);
  assert.equal(document.querySelector('a'), null);
  const error = document.getElementById(button.getAttribute('aria-describedby'));
  assert.match(error.textContent, /минуту/);
  assert.equal(error.getAttribute('role'), 'status');
  assert.equal(document.querySelector('[data-phone-status]').textContent, '');
  button.click(); await settle();
  assert.equal(document.querySelector('a').getAttribute('href'), 'tel:+994501234567');
  assert.equal(document.querySelector('.km-phone-error'), null);
  dom.window.close();
});
test('simultaneous controls share one request', async () => {
  let resolve, calls = 0;
  const dom = setup(() => {calls++; return new Promise(done => {resolve = done;});});
  dom.window.document.querySelectorAll('button').forEach(button => button.click());
  assert.equal(calls, 1);
  resolve({ok: true, json: async () => contacts}); await settle();
  assert.equal(dom.window.document.querySelectorAll('a').length, 2);
  dom.window.close();
});
