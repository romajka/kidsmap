const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { JSDOM } = require(process.env.KIDSMAP_JSDOM || '../.tmp/coordinate-location/dom/node_modules/jsdom');
const script = () => fs.readFileSync('static/js/location_resolution.js', 'utf8');
function fixture(initial = {}) {
  const dom = new JSDOM(`<form><select name="region"><option value=""></option><option value="baku">Baku</option></select><select name="district"><option value=""></option><option value="baku_narimanov">Narimanov</option><option value="baku_sabail">Sabail</option></select><input name="lat"><input name="lng"><textarea name="location_override_reason">old reason</textarea><div data-location-resolution data-url="/api/location/resolve/" data-loading="Loading" data-empty="Choose point" data-error="Try again"><strong data-location-city></strong><strong data-location-district></strong><p role="status"></p><button type="button" data-location-retry hidden>Retry</button></div></form>`, {runScripts: 'outside-only', url: 'http://localhost/'});
  const pending = [];
  dom.window.fetch = (url) => new Promise(resolve => pending.push({url, resolve}));
  const root = dom.window.document.querySelector('[data-location-resolution]');
  Object.assign(root.dataset, initial.dataset || {});
  for (const [name,value] of Object.entries(initial.values || {})) dom.window.document.querySelector(`[name="${name}"]`).value=value;
  dom.window.eval(script());
  dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
  return {dom, pending, form: dom.window.document.querySelector('form')};
}
const flush = () => new Promise(r => setTimeout(r, 250));
function move(f, lat, lng) {
  f.form.elements.lat.value=lat; f.form.elements.lng.value=lng;
  f.form.dispatchEvent(new f.dom.window.CustomEvent('km:map-change', {bubbles:true}));
}
function response(district) { return {ok:true, json:async()=>({status:'resolved',city_key:'baku', district_key:district, city_label:'Baku',district_label:district,message:'Resolved'})}; }
test('moving clears stale district and ignores response for previous coordinates', async () => {
  const f=fixture(); move(f,40.4093,49.8671); await flush();
  move(f,40.36,49.835); await flush();
  assert.equal(f.form.elements.location_override_reason.value,'');
  f.pending[1].resolve(response('baku_sabail')); await flush();
  f.pending[0].resolve(response('baku_narimanov')); await flush();
  assert.equal(f.form.elements.district.value,'baku_sabail');
  move(f,0,0);
  assert.equal(f.form.elements.district.value,'');
  f.dom.window.close();
});
test('clearing coordinates cancels a pending result', async () => {
  const f=fixture(); move(f,40.4093,49.8671); await flush(); move(f,'','');
  f.pending[0].resolve(response('baku_narimanov')); await flush();
  assert.equal(f.form.elements.district.value,'');
  assert.equal(f.form.querySelector('[role=status]').textContent,'Choose point');
  f.dom.window.close();
});
test('uncovered result leaves old district empty and announces the reason', async () => {
  const f=fixture(); move(f,0,0); await flush();
  f.pending[0].resolve({ok:true,json:async()=>({status:'outside_coverage',city_key:'',district_key:'',message:'No boundaries'})}); await flush();
  assert.equal(f.form.elements.district.value,'');
  assert.equal(f.form.querySelector('[role=status]').textContent,'No boundaries');
  f.dom.window.close();
});

test('current override is preserved but an obsolete dataset triggers a new assignment', async () => {
  for (const version of ['v1','v2']) {
    const f=fixture({dataset:{initialStatus:'overridden',initialVersion:'v1',overridden:'Approved exception'}, values:{lat:'40.4093',lng:'49.8671',region:'baku',district:'baku_sabail'}});
    await flush();
    assert.equal(f.pending.length,1);
    const r=response('baku_narimanov');const json=await r.json();json.dataset_version=version;
    f.pending[0].resolve({ok:true,json:async()=>json});await flush();
    assert.equal(f.form.elements.district.value,version==='v1'?'baku_sabail':'baku_narimanov');
    f.dom.window.close();
  }
});

test('visual result clears while moving and network errors can be retried', async () => {
  const f=fixture();
  const root=f.form.querySelector('[data-location-resolution]');
  move(f,40.36,49.835); await flush();
  assert.equal(root.dataset.status,'loading');
  f.pending[0].resolve(response('baku_sabail')); await flush();
  assert.equal(root.querySelector('[data-location-district]').textContent,'Sabail');
  move(f,40.37,49.835);
  assert.equal(root.querySelector('[data-location-district]').textContent,'—');
  await flush();
  f.pending[1].resolve({json:async()=>{throw new Error('offline');}}); await flush();
  assert.equal(root.dataset.status,'unavailable');
  const retry=root.querySelector('[data-location-retry]');
  assert.equal(retry.hidden,false);
  retry.click(); await flush();
  assert.equal(root.dataset.status,'loading');
  assert.equal(retry.hidden,true);
  f.pending[2].resolve(response('baku_sabail')); await flush();
  assert.equal(root.dataset.status,'resolved');
  assert.equal(root.querySelector('[data-location-district]').textContent,'Sabail');
  f.dom.window.close();
});
