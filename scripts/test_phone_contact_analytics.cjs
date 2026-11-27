// Mock-only integration of the real phone reveal script and shared analytics bridge.
// Run: node --test scripts/test_phone_reveal.cjs scripts/test_phone_contact_analytics.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM, VirtualConsole} = require('../.tmp/phone-dom/node_modules/jsdom');
const base = fs.readFileSync(path.join(__dirname, '../src/catalog/templates/base.html'), 'utf8');
const bridgeStart = base.indexOf('function sendGoogleAnalyticsEvent');
const bridge = base.slice(base.lastIndexOf('(function () {', bridgeStart), base.indexOf('// Footer Accordion toggles', bridgeStart));
const phone = fs.readFileSync(path.join(__dirname, '../static/js/place_phone_reveal.js'), 'utf8');
const contacts = {phones: [{number: '+994501234567', href: 'tel:+994501234567', display: '+994 50 123 45 67'}], whatsapp: 'https://wa.me/994501234567'};
const settle = () => new Promise(resolve => setImmediate(resolve));
function setup(t, {compact = true, beacon = false, withBridge = true, preview = false, response} = {}) {
  const events = [], payloads = [], navigationEventCounts = [];
  let revealRequests = 0, beaconRequests = 0;
  const console = new VirtualConsole();
  console.on('jsdomError', error => {
    if (/navigation/.test(error.message)) navigationEventCounts.push(events.length);
    else throw error;
  });
  const dom = new JSDOM(`<html lang="ru"><body ${preview ? 'data-site-preview' : ''}>
    <div data-phone-config data-phone-endpoint="/api/places/0/phones/"><input name="csrfmiddlewaretoken" value="mock"></div>
    <button data-phone-reveal="7" ${compact ? 'class="card-contact-toggle"' : ''}>Reveal</button>
    <button data-phone-reveal="7" data-phone-whatsapp="1">WhatsApp</button>
    <script id="site-preview-phones" type="application/json">${JSON.stringify({...contacts, place_id: 7})}</script>
    </body></html>`, {url: 'https://kidsmap.example/ru/place/mock/', runScripts: 'outside-only', virtualConsole: console});
  t.after(() => dom.window.close());
  const w = dom.window;
  w.gtag = (...args) => events.push(args);
  w.navigator.sendBeacon = () => { beaconRequests++; return beacon; };
  w.fetch = async (url, options) => {
    if (url.includes('/phones/')) {
      revealRequests++;
      return response ? response() : {ok: true, json: async () => contacts};
    }
    payloads.push(JSON.parse(options.body));
    return {ok: true};
  };
  if (withBridge) w.eval(bridge);
  w.eval(phone);
  // Stop browser link navigation after the production click handlers run.
  w.document.addEventListener('click', event => { if (event.target.closest('a')) event.preventDefault(); });
  return {w, events, payloads, navigationEventCounts,
    get revealRequests() { return revealRequests; }, get beaconRequests() { return beaconRequests; }};
}
for (const beacon of [false, true]) {
  test(`first compact call emits once before direct tel navigation (beacon=${beacon})`, async t => {
    const s = setup(t, {beacon});
    s.w.document.querySelector('button').click(); await settle();
    assert.equal(s.events.length, 1);
    assert.equal(s.events[0][1], 'phone_click');
    assert.equal(s.events[0][2].place_id, 7);
    assert.equal(s.events[0][2].page_type, 'card-cta-call');
    assert.deepEqual(s.navigationEventCounts, [1]);
    assert.equal(s.beaconRequests, 1);
    assert.equal(s.payloads.length, beacon ? 0 : 1);
    if (!beacon) assert.deepEqual(s.payloads[0], {event_type: 'phone_click', place_id: 7, source: 'card-cta-call', path: '/ru/place/mock/'});
    assert.equal(JSON.stringify(s.events).includes('994501234567'), false);
    s.w.document.querySelector('a[href^="tel:"]').click(); await settle();
    assert.equal(s.events.length, 2, 'one additional explicit call click must not be doubled');
    assert.equal(s.beaconRequests, 2);
  });
}
test('compact call with cached contacts emits once without a second reveal request', async t => {
  const s = setup(t, {compact: false});
  s.w.document.querySelector('button').click(); await settle();
  assert.equal(s.events.length, 0);
  const popup = s.w.document.createElement('div');
  popup.innerHTML = s.w.kidsMapPhoneButton(7, 'card-contact-toggle');
  s.w.document.body.append(popup);
  popup.querySelector('button').click(); await settle();
  assert.equal(s.revealRequests, 1);
  assert.equal(s.events.length, 1);
  assert.equal(s.events[0][1], 'phone_click');
  assert.equal(s.events[0][2].place_id, 7);
  assert.deepEqual(s.navigationEventCounts, [1]);
});
for (const [label, response] of [
  ['429', () => ({ok: false, status: 429})],
  ['empty contacts', () => ({ok: true, json: async () => ({phones: [], whatsapp: ''})})],
  ['invalid phone', () => ({ok: true, json: async () => ({phones: [{number: '+994501234567', href: 'https://evil.example/'}], whatsapp: ''})})],
]) {
  test(`no call event or navigation after ${label}`, async t => {
    const s = setup(t, {response});
    s.w.document.querySelector('button').click(); await settle();
    assert.equal(s.events.length, 0);
    assert.equal(s.beaconRequests, 0);
    assert.deepEqual(s.navigationEventCounts, []);
    assert.ok(s.w.document.querySelector('.km-phone-error'));
  });
}
test('failed compact reveal then successful retry emits only the successful call', async t => {
  let tries = 0;
  const s = setup(t, {response: () => ++tries === 1 ? {ok: false, status: 429} : {ok: true, json: async () => contacts}});
  const button = s.w.document.querySelector('button');
  button.click(); await settle();
  assert.equal(s.events.length, 0);
  button.click(); await settle();
  assert.equal(s.events.length, 1);
  assert.equal(s.events[0][1], 'phone_click');
  assert.deepEqual(s.navigationEventCounts, [1]);
});
test('WhatsApp reveal does not count as contact until its explicit link is clicked', async t => {
  const s = setup(t);
  s.w.document.querySelector('[data-phone-whatsapp]').click(); await settle();
  assert.equal(s.events.length, 0);
  assert.deepEqual(s.navigationEventCounts, []);
  s.w.document.querySelector('a[href^="https://wa.me/"]').click(); await settle();
  assert.equal(s.events.length, 1);
  assert.equal(s.events[0][1], 'whatsapp_click');
  assert.equal(s.payloads.length, 1);
});
test('detail reveal remains quiet; explicit phone and WhatsApp each emit once', async t => {
  const s = setup(t, {compact: false});
  s.w.document.querySelector('button').click(); await settle();
  assert.equal(s.events.length, 0);
  s.w.document.querySelector('a[href^="tel:"]').click();
  s.w.document.querySelector('a[href^="https://wa.me/"]').click(); await settle();
  assert.deepEqual(s.events.map(event => event[1]), ['phone_click', 'whatsapp_click']);
  assert.equal(s.payloads.length, 2);
});
test('unavailable analytics bridge does not block a compact call', async t => {
  const s = setup(t, {withBridge: false});
  s.w.document.querySelector('button').click(); await settle();
  assert.deepEqual(s.navigationEventCounts, [0]);
  assert.equal(s.events.length, 0);
  assert.equal(s.w.document.querySelector('a').getAttribute('href'), 'tel:+994501234567');
});
test('preview compact call does not create external or local analytics events', async t => {
  const s = setup(t, {preview: true});
  s.w.document.querySelector('button').click(); await settle();
  assert.equal(s.events.length, 0);
  assert.equal(s.beaconRequests, 0);
  assert.equal(s.payloads.length, 0);
  assert.equal(s.revealRequests, 0);
});
