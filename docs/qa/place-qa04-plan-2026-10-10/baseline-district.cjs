// Audit-only DOM baseline against the unchanged resolver, no map SDK required.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { JSDOM } = require(process.env.KIDSMAP_JSDOM);
const source = fs.readFileSync('static/js/location_resolution.js', 'utf8');

function fixture(saved = {}) {
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
  dom.window.eval(source);
  dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
  return {dom, form, pending, root: form.querySelector('[data-location-resolution]')};
}

function point(f, lat, lng) {
  f.form.elements.lat.value = lat;
  f.form.elements.lng.value = lng;
  f.form.dispatchEvent(new f.dom.window.CustomEvent('km:map-change', {bubbles:true}));
}
function region(f, value) {
  f.form.elements.region.value = value;
  f.form.elements.region.dispatchEvent(new f.dom.window.Event('change', {bubbles:true}));
}
const tick = () => new Promise(resolve => setTimeout(resolve, 210));
const resolved = () => ({ok:true, json:async()=>({status:'resolved',city_key:'baku',district_key:'baku_narimanov',city_label:'Baku',district_label:'Narimanov',message:'Resolved'})});

test('manual point -> clear -> Baku enables district and includes it in submitted data', () => {
  const f = fixture();
  try {
    point(f, '40.4093', '49.8671'); point(f, '', ''); region(f, 'baku');
    assert.equal(f.form.elements.district.disabled, false);
    f.form.elements.district.value = 'baku_yasamal';
    assert.equal(new f.dom.window.FormData(f.form).get('district'), 'baku_yasamal');
    assert.equal(f.form.elements.address.value, 'Synthetic address');
  } finally { f.dom.window.close(); }
});

test('manual point -> clear -> another region -> Baku enables district', () => {
  const f = fixture();
  try {
    point(f, '40.4093', '49.8671'); point(f, '', ''); region(f, 'sumgait');
    assert.equal(f.form.elements.district.disabled, true);
    region(f, 'baku');
    assert.equal(f.form.elements.district.disabled, false);
  } finally { f.dom.window.close(); }
});

test('manual region change away from Baku disables and clears stale Baku district', () => {
  const f = fixture({region:'baku',district:'baku_yasamal'});
  try {
    region(f, 'sumgait');
    assert.equal(f.form.elements.district.disabled, true);
    assert.equal(f.form.elements.district.value, '');
  } finally { f.dom.window.close(); }
});

test('saved manual Baku district without coordinates survives initial boot', () => {
  const f = fixture({region:'baku',district:'baku_yasamal'});
  try {
    assert.equal(f.form.elements.district.disabled, false);
    assert.equal(f.form.elements.district.value, 'baku_yasamal');
    assert.equal(f.form.elements.lat.value, '');
    assert.equal(f.pending.length, 0);
  } finally { f.dom.window.close(); }
});

test('partial point is not equivalent to manual mode', () => {
  const f = fixture();
  try {
    point(f, '40.4093', ''); region(f, 'baku');
    assert.equal(f.form.elements.district.disabled, true);
  } finally { f.dom.window.close(); }
});

test('resolved point in Baku still enables its district', async () => {
  const f = fixture();
  try {
    point(f, '40.4093', '49.8671'); await tick();
    assert.equal(f.pending.length, 1);
    f.pending[0].resolve(resolved()); await tick();
    assert.equal(f.form.elements.district.disabled, false);
    assert.equal(f.form.elements.district.value, 'baku_narimanov');
  } finally { f.dom.window.close(); }
});

test('stale lookup cannot overwrite manual region/district after clear', async () => {
  const f = fixture();
  try {
    point(f, '40.4093', '49.8671'); await tick();
    point(f, '', ''); region(f, 'baku'); f.form.elements.district.value = 'baku_yasamal';
    f.pending[0].resolve(resolved()); await tick();
    assert.equal(f.form.elements.region.value, 'baku');
    assert.equal(f.form.elements.district.value, 'baku_yasamal');
    assert.equal(f.form.elements.lat.value, '');
  } finally { f.dom.window.close(); }
});

// Replay apply(saved)'s observed per-field assignment/change contract, not the
// entire continuous editor. Its real local/server restore is a browser gate.
for (const coordinatesFirst of [false, true]) {
  test(`draft field/change replay restores manual district (coordinates first: ${coordinatesFirst})`, () => {
    const f = fixture({region:'baku',district:'baku_narimanov',lat:'40.4093',lng:'49.8671'});
    try {
      const geography = [['region','baku'],['district','baku_yasamal']];
      const coordinates = [['lat',''],['lng','']];
      const entries = coordinatesFirst ? [...coordinates,...geography] : [...geography,...coordinates];
      for (const [name,value] of entries) {
        f.form.elements[name].value = value;
        f.form.elements[name].dispatchEvent(new f.dom.window.Event('change', {bubbles:true}));
      }
      assert.equal(f.form.elements.region.value, 'baku');
      assert.equal(f.form.elements.district.value, 'baku_yasamal');
      assert.equal(f.form.elements.district.disabled, false);
    } finally { f.dom.window.close(); }
  });
}
