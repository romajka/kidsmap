const assert = require('node:assert/strict');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || '../.tmp/phone-dom/node_modules/jsdom');
const path = require('node:path');
const loadPublicActions = require('./tests/helpers/public_actions.cjs');
const root = process.argv[2] || path.resolve(__dirname, '..');
const results = [];
for (const mode of ['rejected', 'accepted', 'throws', 'missing']) {
  const fetches = [], beacons = [], emitted = [];
  const dom = new JSDOM('<body></body>', {url: 'https://kidsmap.example/ru/', runScripts: 'dangerously'});
  const {window} = dom;
  const {navigator} = window;
  if (mode !== 'missing') navigator.sendBeacon = (...args) => {
    beacons.push(args);
    if (mode === 'throws') throw new TypeError('fictional transport failure');
    return mode === 'accepted';
  };
  window.gtag = (...event) => emitted.push(event);
  window.fetch = (...args) => { fetches.push(args); return Promise.resolve({ok: true}); };
  try {
    loadPublicActions(window, root);
    window.kidsMapTrackEvent({event_type: 'cta_call', place_id: 7, source: 'place-detail'});
    assert.equal(emitted.length, 1, 'One logical event sent to the GA bridge');
    assert.equal(fetches.length, mode === 'accepted' ? 0 : 1, 'Rejected/unavailable beacon must fall back once');
    if (mode !== 'missing') assert.equal(beacons.length, 1);
    if (fetches.length) {
      assert.equal(fetches[0][0], '/ru/events/track/');
      assert.equal(fetches[0][1].credentials, 'same-origin');
      assert.equal(fetches[0][1].keepalive, true);
      assert.deepEqual(JSON.parse(fetches[0][1].body), {event_type:'phone_click',place_id:7,source:'place-detail'});
    }
    results.push({mode, PASS: true});
  } catch (error) { results.push({mode, PASS: false, reason: error.message}); }
  finally { dom.window.close(); }
}
process.stdout.write(JSON.stringify({tests: results.length, results}, null, 2) + '\n');
process.exitCode = results.every(r => r.PASS) ? 0 : 1;
