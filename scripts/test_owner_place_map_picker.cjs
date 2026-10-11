// Controls exercise the actual script without an external map SDK.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require(process.env.KIDSMAP_JSDOM);
const source = fs.readFileSync(path.resolve('static/js/owner_place_map_picker.js'), 'utf8');

function fixture(provider = 'unavailable', geolocation) {
  const dom = new JSDOM(`<html lang="en"><body><form>
    <input name="address" value="Synthetic address"><input name="name_az" value="Synthetic place">
    <section data-owner-map-picker data-permanent-map data-map-provider="${provider}"
      data-empty-label="No point selected" data-selected-prefix="Selected point:"
      data-locate-error="Location failed. Enter coordinates manually."
      data-locating="Detecting location"
      data-locate-unsupported="Geolocation unavailable. Enter coordinates manually."
      data-search-unsupported="Map unavailable. Enter coordinates manually.">
      <input name="lat" value="40.4093"><input name="lng" value="49.8671">
      <button type="button" data-map-clear>Clear</button>
      <button type="button" data-map-locate>Locate</button>
      <input data-map-search-input><button type="button" data-map-search>Search</button>
      <span data-map-status>Selected point: 40.4093, 49.8671</span>
      <span data-geocoding-status-badge></span><div data-map-canvas></div>
    </section></form></body></html>`, { runScripts: 'outside-only', url: 'http://localhost/' });
  dom.window.fetch = () => { throw new Error('External network prohibited in audit fixture'); };
  Object.defineProperty(dom.window.navigator, 'geolocation', { configurable: true, value: geolocation });
  const root = dom.window.document.querySelector('[data-owner-map-picker]');
  let changes = 0;
  root.closest('form').addEventListener('km:map-change', () => changes++);
  dom.window.eval(source);
  dom.window.document.dispatchEvent(new dom.window.Event('DOMContentLoaded'));
  return { dom, root, input: name => root.querySelector(`[name="${name}"]`),
    status: () => root.querySelector('[data-map-status]').textContent,
    click: name => root.querySelector(`[data-map-${name}]`).click(), changes: () => changes };
}

for (const provider of ['unavailable', 'google']) {
  test(`clear manual point with ${provider} provider and no SDK`, () => {
    const f = fixture(provider);
    try {
      f.click('clear');
      assert.equal(f.input('lat').value, '');
      assert.equal(f.input('lng').value, '');
      assert.equal(f.status(), 'No point selected');
      assert.equal(f.changes(), 1);
      assert.equal(f.root.closest('form').elements.address.value, 'Synthetic address');
    } finally { f.dom.window.close(); }
  });
}

test('no navigator.geolocation gives visible feedback without map SDK', () => {
  const f = fixture();
  try {
    f.click('locate');
    assert.equal(f.status(), 'Geolocation unavailable. Enter coordinates manually.');
    assert.equal(f.input('lat').value, '40.4093');
    assert.equal(f.input('lng').value, '49.8671');
  } finally { f.dom.window.close(); }
});

test('denied geolocation is requested once and explained without map SDK', () => {
  let calls = 0;
  const f = fixture('unavailable', { getCurrentPosition(_success, failure) {
    calls++;
    failure({ code: 1 });
  } });
  try {
    f.click('locate');
    assert.equal(calls, 1);
    assert.equal(f.status(), 'Location failed. Enter coordinates manually.');
    assert.equal(f.input('lat').value, '40.4093');
  } finally { f.dom.window.close(); }
});

test('late Leaflet initialization is not blocked by unavailable placeholder', () => {
  const f = fixture('leaflet');
  let maps = 0;
  try {
    // Local adapter stub only, not a real SDK/provider-integration test.
    const map = { on() {}, setView() {}, getZoom() { return 15; }, invalidateSize() {},
      removeLayer() {}, scrollWheelZoom: { enable() {}, disable() {} } };
    f.dom.window.L = {
      map() { maps++; return map; },
      tileLayer() { return { addTo() {} }; },
      marker() { return { addTo() { return this; }, on() {}, setLatLng() {} }; },
    };
    f.dom.window.kidsMapInitOwnerMapPickers();
    assert.equal(maps, 1);
  } finally { f.dom.window.close(); }
});

test('success without SDK updates one point; clearing cancels delayed geolocation', () => {
  let success;
  const f = fixture('unavailable',{getCurrentPosition(callback) { success=callback; }});
  try {
    f.click('locate'); assert.equal(f.status(),'Detecting location');
    success({coords:{latitude:40.4,longitude:49.8}});
    assert.equal(f.input('lat').value,'40.400000'); assert.equal(f.changes(),1);
    f.click('locate'); f.click('clear');
    success({coords:{latitude:40.5,longitude:49.9}});
    assert.equal(f.input('lat').value,''); assert.equal(f.input('lng').value,'');
    assert.equal(f.changes(),2); assert.equal(f.status(),'No point selected');
  } finally { f.dom.window.close(); }
});

test('manual edits and malformed geolocation cannot overwrite entered values', () => {
  let success;
  const f = fixture('unavailable',{getCurrentPosition(callback) { success=callback; }});
  try {
    f.click('locate'); f.input('lat').value='40.2';
    f.input('lat').dispatchEvent(new f.dom.window.Event('input',{bubbles:true}));
    success({coords:{latitude:40.5,longitude:49.9}});
    assert.equal(f.input('lat').value,'40.2');
    f.click('locate'); success({coords:{latitude:Infinity,longitude:49.9}});
    assert.equal(f.input('lat').value,'40.2'); assert.equal(f.status(),'Location failed. Enter coordinates manually.');
  } finally { f.dom.window.close(); }
});

test('repeated boot never duplicates independent control listeners', () => {
  const f=fixture();
  try {
    f.dom.window.kidsMapInitOwnerMapPickers(); f.dom.window.kidsMapRefreshOwnerMapPickers();
    f.click('clear'); assert.equal(f.changes(),1);
  } finally { f.dom.window.close(); }
});

for (const mode of ['timeout','throw']) {
  test(`${mode} geolocation preserves fields and resets busy state`, () => {
    const f=fixture('unavailable',{getCurrentPosition(_ok,fail) {
      if(mode==='throw')throw new Error('Synthetic unavailable');
      fail({code:3});
    }});
    try {
      f.click('locate');
      assert.equal(f.status(),'Location failed. Enter coordinates manually.');
      assert.equal(f.input('lat').value,'40.4093');
      assert.equal(f.root.querySelector('[data-map-locate]').getAttribute('aria-busy'),'false');
      assert.equal(f.changes(),0);
    } finally {f.dom.window.close();}
  });
}

test('late Google callback initializes once and independent controls emit once', () => {
  const f=fixture('google');let maps=0;
  try {
    f.dom.window.google={maps:{
      Map:function(){maps++;this.addListener=()=>{};this.setCenter=()=>{};this.getZoom=()=>15;},
      Marker:function(){this.addListener=()=>{};this.setPosition=()=>{};this.setMap=()=>{};},
      Geocoder:function(){},event:{trigger(){}}
    }};
    f.dom.window.kidsMapInitOwnerMapPickers();f.dom.window.kidsMapInitOwnerMapPickers();
    assert.equal(maps,1);assert.equal(f.changes(),0);
    f.click('clear');assert.equal(f.changes(),1);assert.equal(f.input('lat').value,'');
    assert.equal(f.root.querySelector('[data-map-search]').disabled,false);
  } finally {f.dom.window.close();}
});

test('failed renderer construction leaves controls and safe placeholder available', () => {
  const f=fixture('leaflet');
  try {
    f.dom.window.L={map(){throw new Error('Synthetic constructor failure');}};
    f.root.dataset.searchUnsupported='<script>unsafe()</script>';
    f.dom.window.kidsMapInitOwnerMapPickers();
    assert.equal(f.root.dataset.mapInitialized,undefined);
    assert.equal(f.root.querySelector('[data-map-canvas] script'),null);
    f.click('clear');assert.equal(f.input('lat').value,'');assert.equal(f.changes(),1);
    f.click('locate');assert.match(f.status(),/Geolocation unavailable/);
  } finally {f.dom.window.close();}
});
