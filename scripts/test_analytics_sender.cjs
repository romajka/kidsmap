const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = process.argv[2] || path.resolve(__dirname, '..');
const template = fs.readFileSync(path.join(root, 'src/catalog/templates/base.html'), 'utf8');
const start = template.indexOf('function send(payload) {');
const end = template.indexOf('window.kidsMapTrackEvent = send;', start);
assert.ok(start >= 0 && end > start, 'Actual client sender must be available');
const sender = template.slice(start, end);
const results = [];
for (const mode of ['rejected', 'accepted', 'throws', 'missing']) {
  const fetches = [], beacons = [], emitted = [];
  const navigator = {};
  if (mode !== 'missing') navigator.sendBeacon = (...args) => {
    beacons.push(args);
    if (mode === 'throws') throw new TypeError('fictional transport failure');
    return mode === 'accepted';
  };
  const context = {
    navigator, Blob, trackUrl: '/ru/events/track/',
    emitAnalyticsEvent: event => emitted.push(event),
    fetch: (...args) => { fetches.push(args); return Promise.resolve({ok: true}); },
  };
  try {
    vm.runInNewContext(sender + ';send({event_type:"cta_call",place_id:7,source:"place-detail"});', context);
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
}
process.stdout.write(JSON.stringify({tests: results.length, results}, null, 2) + '\n');
process.exitCode = results.every(r => r.PASS) ? 0 : 1;
