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


test('invalid numeric coordinates never announce a selected map point', () => {
  const f = fixture({dataset: {pointSelected: 'Selected', pointEmpty: 'Not chosen'}});
  const label = f.dom.window.document.createElement('strong');
  label.setAttribute('data-location-point', '');
  f.form.querySelector('[data-location-resolution]').append(label);
  try {
    for (const [lat, lng] of [['999', '49.8'], ['40.4', '190'], ['Infinity', '49.8']]) {
      move(f, lat, lng);
      assert.equal(label.textContent, 'Not chosen');
    }
  } finally { f.dom.window.close(); }
});

test('valid zero coordinates still announce a selected map point', () => {
  const f = fixture({dataset: {pointSelected: 'Selected', pointEmpty: 'Not chosen'}});
  const label = f.dom.window.document.createElement('strong');
  label.setAttribute('data-location-point', '');
  f.form.querySelector('[data-location-resolution]').append(label);
  try { move(f, '0', '0'); assert.equal(label.textContent, 'Selected'); }
  finally { f.dom.window.close(); }
});

function manualFixture(saved = {}) {
  const dom = new JSDOM(`<html lang="en"><body><div data-place-mode="continuous"><form data-permanent-place-form>
    <select name="region"><option value=""></option><option value="baku">Baku</option><option value="sumgait">Sumqayit</option></select>
    <select name="district"><option value=""></option><option value="baku_narimanov">Narimanov</option><option value="baku_yasamal">Yasamal</option></select>
    <input name="lat"><input name="lng"><input name="address" value="Synthetic address">
    <div data-location-resolution data-url="/api/location/resolve/" data-empty="Choose point" data-loading="Loading" data-error="Try again" data-point-empty="No point" data-point-selected="Selected">
      <strong data-location-point></strong><strong data-location-city></strong><strong data-location-district></strong>
      <p role="status"></p><button type="button" data-location-retry hidden>Retry</button>
    </div></form></div></body></html>`, { runScripts: 'outside-only', url: 'http://localhost/' });
  const form = dom.window.document.querySelector('form');
  for (const [name, value] of Object.entries(saved)) form.elements[name].value = value;
  const pending = [];
  dom.window.fetch = url => new Promise(resolve => pending.push({url, resolve}));
  dom.window.eval(script());
  dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
  return {dom, form, pending, root: form.querySelector('[data-location-resolution]')};
}

function manualPoint(f, lat, lng) {
  f.form.elements.lat.value = lat;
  f.form.elements.lng.value = lng;
  f.form.dispatchEvent(new f.dom.window.CustomEvent('km:map-change', {bubbles:true}));
}
function manualRegion(f, value) {
  f.form.elements.region.value = value;
  f.form.elements.region.dispatchEvent(new f.dom.window.Event('change', {bubbles:true}));
}
const manualTick = () => new Promise(resolve => setTimeout(resolve, 210));
const manualResolved = () => ({ok:true, json:async()=>({status:'resolved',city_key:'baku',district_key:'baku_narimanov',city_label:'Baku',district_label:'Narimanov',message:'Resolved'})});

test('restoring manual district cancels an already pending coordinate lookup', async () => {
  const f=manualFixture({lat:'40.4093',lng:'49.8671'});
  try {
    await manualTick();
    f.form.dispatchEvent(new f.dom.window.CustomEvent('km:location-restore-start'));
    f.form.elements.lat.value=f.form.elements.lng.value='';
    f.form.elements.region.value='baku';f.form.elements.district.value='baku_yasamal';
    f.form.dispatchEvent(new f.dom.window.CustomEvent('km:location-restore-end'));
    f.pending[0].resolve(manualResolved());await manualTick();
    assert.equal(f.form.elements.district.value,'baku_yasamal');
    assert.equal(f.form.elements.district.disabled,false);
  }finally{f.dom.window.close();}
});

test('non-continuous empty-point behavior is preserved', () => {
  const f=fixture();
  try {
    f.form.elements.region.value='baku';
    f.form.elements.region.dispatchEvent(new f.dom.window.Event('change'));
    move(f,'40.4','49.8');move(f,'','');
    assert.equal(f.form.elements.region.value,'');
    assert.equal(f.form.elements.district.disabled,true);
  }finally{f.dom.window.close();}
});

test('manual point -> clear -> Baku enables district and includes it in submitted data', () => {
  const f = manualFixture();
  try {
    manualPoint(f, '40.4093', '49.8671'); manualPoint(f, '', ''); manualRegion(f, 'baku');
    assert.equal(f.form.elements.district.disabled, false);
    f.form.elements.district.value = 'baku_yasamal';
    assert.equal(new f.dom.window.FormData(f.form).get('district'), 'baku_yasamal');
    assert.equal(f.form.elements.address.value, 'Synthetic address');
  } finally { f.dom.window.close(); }
});

test('manual point -> clear -> another region -> Baku enables district', () => {
  const f = manualFixture();
  try {
    manualPoint(f, '40.4093', '49.8671'); manualPoint(f, '', ''); manualRegion(f, 'sumgait');
    assert.equal(f.form.elements.district.disabled, true);
    manualRegion(f, 'baku');
    assert.equal(f.form.elements.district.disabled, false);
  } finally { f.dom.window.close(); }
});

test('manual region change away from Baku disables and clears stale Baku district', () => {
  const f = manualFixture({region:'baku',district:'baku_yasamal'});
  try {
    manualRegion(f, 'sumgait');
    assert.equal(f.form.elements.district.disabled, true);
    assert.equal(f.form.elements.district.value, '');
  } finally { f.dom.window.close(); }
});

test('saved manual Baku district without coordinates survives initial boot', () => {
  const f = manualFixture({region:'baku',district:'baku_yasamal'});
  try {
    assert.equal(f.form.elements.district.disabled, false);
    assert.equal(f.form.elements.district.value, 'baku_yasamal');
    assert.equal(f.form.elements.lat.value, '');
    assert.equal(f.pending.length, 0);
  } finally { f.dom.window.close(); }
});

for(const point of [['40.4',''],['','49.8'],['bad','49.8'],['91','49.8']]) {
  test(`restored invalid/partial point does not grant manual district: ${point.join('|')}`, () => {
    const f=manualFixture({region:'baku',district:'baku_yasamal',lat:point[0],lng:point[1]});
    try {assert.equal(f.form.elements.district.disabled,true);}
    finally {f.dom.window.close();}
  });
}

test('partial point is not equivalent to manual mode', () => {
  const f = manualFixture();
  try {
    manualPoint(f, '40.4093', ''); manualRegion(f, 'baku');
    assert.equal(f.form.elements.district.disabled, true);
  } finally { f.dom.window.close(); }
});

test('resolved point in Baku still enables its district', async () => {
  const f = manualFixture();
  try {
    manualPoint(f, '40.4093', '49.8671'); await manualTick();
    assert.equal(f.pending.length, 1);
    f.pending[0].resolve(manualResolved()); await manualTick();
    assert.equal(f.form.elements.district.disabled, false);
    assert.equal(f.form.elements.district.value, 'baku_narimanov');
  } finally { f.dom.window.close(); }
});

test('stale lookup cannot overwrite manual region/district after clear', async () => {
  const f = manualFixture();
  try {
    manualPoint(f, '40.4093', '49.8671'); await manualTick();
    manualPoint(f, '', ''); manualRegion(f, 'baku'); f.form.elements.district.value = 'baku_yasamal';
    f.pending[0].resolve(manualResolved()); await manualTick();
    assert.equal(f.form.elements.region.value, 'baku');
    assert.equal(f.form.elements.district.value, 'baku_yasamal');
    assert.equal(f.form.elements.lat.value, '');
  } finally { f.dom.window.close(); }
});

// Replay apply(saved)'s observed per-field assignment/change contract, not the
// entire continuous editor. Its real local/server restore is a browser gate.
for (const coordinatesFirst of [false, true]) {
  test(`draft field/change replay restores manual district (coordinates first: ${coordinatesFirst})`, () => {
    const f = manualFixture({region:'baku',district:'baku_narimanov',lat:'40.4093',lng:'49.8671'});
    try {
      const geography = [['region','baku'],['district','baku_yasamal']];
      const coordinates = [['lat',''],['lng','']];
      const entries = coordinatesFirst ? [...coordinates,...geography] : [...geography,...coordinates];
      f.form.dispatchEvent(new f.dom.window.CustomEvent('km:location-restore-start'));
      for (const [name,value] of entries) {
        f.form.elements[name].value = value;
        f.form.elements[name].dispatchEvent(new f.dom.window.Event('change', {bubbles:true}));
      }
      f.form.dispatchEvent(new f.dom.window.CustomEvent('km:location-restore-end'));
      assert.equal(f.form.elements.region.value, 'baku');
      assert.equal(f.form.elements.district.value, 'baku_yasamal');
      assert.equal(f.form.elements.district.disabled, false);
    } finally { f.dom.window.close(); }
  });
}
