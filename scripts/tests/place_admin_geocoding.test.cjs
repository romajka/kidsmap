const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require(process.env.KIDSMAP_JSDOM || 'jsdom');

const script = fs.readFileSync(path.join(__dirname, '../../static/admin/js/kidsmap_place_location.js'), 'utf8');
const policy = {bounds:[38.3,41.9,44.7,50.8],types:['street_address','premise','subpremise','establishment','point_of_interest','intersection'],
  transit:['bus_station','subway_station','train_station','transit_station','light_rail_station'],precision:['ROOFTOP','GEOMETRIC_CENTER']};
const oldPoint = [40.409264, 49.867092];
const newPoint = [40.366667, 49.833333];

function place(label, coords = newPoint, type = 'street_address', precision = 'ROOFTOP') {
  return {
    formatted_address: label, types: [type],
    geometry: { location_type: precision, location: { lat: () => coords[0], lng: () => coords[1] } }
  };
}

function editor(t, coords = []) {
  const dom = new JSDOM(`<form><section data-km-place-location data-map-provider="google" data-geocoding-policy='${JSON.stringify(policy)}'
    data-search-error="No results" data-search-imprecise="Choose a point" data-search-unavailable="Service unavailable">
    <input id="id_address" value="Narimanov"><input id="id_lat" value="${coords[0] ?? ''}"><input id="id_lng" value="${coords[1] ?? ''}">
    <input type="hidden" name="_location_point_confirmed">
    <button type="button" data-km-place-location-search>Find</button><button type="button" data-km-place-location-clear>Clear</button>
    <button type="button" data-km-place-location-locate>Locate</button>
    <div data-km-place-location-panel hidden><div data-km-place-location-map></div></div>
    <p data-km-place-location-status></p><div data-km-place-location-choices hidden></div>
    <div data-km-place-location-found hidden><span data-km-place-location-found-text></span></div>
  </section></form>`, { runScripts: 'outside-only' });
  t.after(() => dom.window.close());
  const w = dom.window;
  const doc = w.document;
  const requests = [];
  const gps = [];
  class Map {
    addListener() {}
    setCenter() {}
    getZoom() { return 15; }
  }
  class Marker {
    addListener() {}
    setPosition() {}
    setMap() {}
  }
  class Geocoder {
    geocode(query, cb) { requests.push({query, cb}); }
  }
  let autocomplete;
  class Autocomplete {
    constructor() { autocomplete = this; }
    addListener(_, callback) { this.changed = callback; }
    bindTo() {}
    getPlace() { return this.place; }
  }
  w.google = { maps: { Map, Marker, Geocoder, places: {Autocomplete} } };
  w.HTMLElement.prototype.scrollIntoView = () => {};
  Object.defineProperty(w.navigator, 'geolocation', { value: { getCurrentPosition: (success, error) => gps.push({success, error}) } });
  w.eval(script);
  w.kidsMapInitAdminPlaceLocation();
  const node = key => doc.querySelector('[data-km-place-location-' + key + ']');
  const edit = (id, value) => {
    const input = doc.getElementById('id_' + id);
    input.value = value;
    input.dispatchEvent(new w.Event('input', { bubbles: true }));
  };
  const search = (address) => {
    edit('address', address);
    node('search').click();
    return requests.at(-1);
  };
  return {
    doc, w, node, gps, requests, edit, search,
    autocomplete: (place) => {autocomplete.place = place; autocomplete.changed();},
    point: () => ['lat', 'lng'].map(id => doc.getElementById('id_' + id).value),
    confirmation: () => doc.querySelector('[name="_location_point_confirmed"]').value,
    status: () => node('status').textContent
  };
}

test('editing a saved address immediately clears the old pair and negative results cannot re-confirm it', t => {
  const e = editor(t, oldPoint);
  e.edit('address', 'ичери шяхяр');
  assert.deepEqual(e.point(), ['', '']);
  e.node('search').click();
  e.requests.at(-1).cb([], 'ZERO_RESULTS');
  assert.deepEqual(e.point(), ['', '']);
  assert.equal(e.confirmation(), '');
  assert.equal(e.status(), 'No results');
});

test('automatic search skips city, partial, and malformed hits and uses a single precise location', t => {
  const e = editor(t);
  const city = place('Baku', oldPoint, 'locality', 'APPROXIMATE');
  const precise = place('Old City');
  const partial = {...place('Partial', oldPoint), partial_match: true};
  e.search('İçərişəhər').cb([city, partial, {types:['street_address']}, precise, precise], 'OK');
  assert.deepEqual(e.point(), newPoint.map(String));
  assert.equal(e.confirmation(), '1');
  assert.equal(e.node('found-text').textContent, 'Old City');
});

test('an approximate city leaves the fields empty and shows its name for refinement', t => {
  const e = editor(t);
  e.search('ичери шяхяр').cb([place('Baku, Azerbaijan', oldPoint, 'locality', 'APPROXIMATE')], 'OK');
  assert.deepEqual(e.point(), ['', '']);
  assert.equal(e.status(), 'Choose a point');
  assert.match(e.node('choices').textContent, /Baku, Azerbaijan/);
});

test('competing exact matches need explicit selection, and new input removes the choices', t => {
  const e = editor(t);
  const matches = [place('First', oldPoint), place('Second')];
  e.search('Baku address').cb(matches, 'OK');
  assert.deepEqual(e.point(), ['', '']);
  e.node('choices').querySelectorAll('button')[1].click();
  assert.deepEqual(e.point(), newPoint.map(String));
  assert.equal(e.confirmation(), '1');
  e.search('Another search').cb(matches, 'OK');
  e.edit('address', 'new text');
  assert.equal(e.node('choices').hidden, true);
  assert.deepEqual(e.point(), ['', '']);
});

test('failure and unusable coordinates display provider feedback separately from ZERO_RESULTS', t => {
  const e = editor(t);
  for (const [results,status] of [[[], 'REQUEST_DENIED'], [[place('Broken', [91,181])], 'OK'], [[null], 'OK']]) {
    e.search('query').cb(results,status);
    assert.equal(e.status(), 'Service unavailable');
    assert.deepEqual(e.point(), ['', '']);
  }
});

test('a late response cannot replace a newer result or return a cleared point', t => {
  const e = editor(t);
  const first = e.search('first');
  e.search('second').cb([place('Old City')], 'OK');
  first.cb([place('Narimanov',oldPoint)], 'OK');
  assert.deepEqual(e.point(), newPoint.map(String));
  const pending = e.search('third');
  e.node('clear').click();
  pending.cb([place('Narimanov',oldPoint)], 'OK');
  assert.deepEqual(e.point(), ['', '']);
  assert.equal(e.node('found').hidden,true);
});

test('late search and device results cannot overwrite manually entered coordinates', t => {
  const e = editor(t);
  const pending = e.search('query');
  e.node('locate').click();
  e.edit('lat', String(newPoint[0]));
  e.edit('lng', String(newPoint[1]));
  e.gps[0].success({coords:{latitude:oldPoint[0],longitude:oldPoint[1]}});
  pending.cb([place('Narimanov',oldPoint)], 'OK');
  assert.deepEqual(e.point(), newPoint.map(String));
  assert.equal(e.confirmation(), '1');
});

test('replaying a complete draft preserves its own point even when address is applied last', t => {
  const e = editor(t, oldPoint);
  const form = e.doc.querySelector('form');
  form.dispatchEvent(new e.w.CustomEvent('km:location-restore-start', {bubbles:true}));
  e.edit('lat', String(newPoint[0]));
  e.edit('lng', String(newPoint[1]));
  e.edit('address','restored');
  form.dispatchEvent(new e.w.CustomEvent('km:location-restore-end', {bubbles:true}));
  assert.deepEqual(e.point(), newPoint.map(String));
  e.edit('address', 'new address');
  assert.deepEqual(e.point(), ['', '']);
});


test('an out-of-country or transit result cannot be applied as the address of a venue', t => {
  const e = editor(t);
  const station = {...place('Metro'),types:['subway_station','establishment','point_of_interest']};
  const foreign = {...place('Foreign'),address_components:[{types:['country'],short_name:'TR'}]};
  for (const candidate of [place('Swapped',[49.833333,40.366667]), station, foreign]) {
    e.search('Some venue').cb([candidate], 'OK');
    assert.deepEqual(e.point(), ['', '']);
    assert.equal(e.status(), 'Choose a point');
  }
});


test('malformed Google metadata never counts as an exact venue', t => {
  const e = editor(t);
  const valid = place('Title');
  for (const broken of [{...valid, address_components:'AZ'}, {...valid, address_components:[{}]}, {...valid, types:null}]) {
    e.search('text').cb([broken], 'OK');
    assert.deepEqual(e.point(), ['', '']);
    assert.equal(e.status(), 'Service unavailable');
  }
});

test('an incomplete Places event on Enter leaves the free-text lookup running', t => {
  const e = editor(t);
  e.search('valid initial lookup').cb([place('Initial', oldPoint)], 'OK');
  const pending = e.search('new typed text');
  e.autocomplete({name:'new typed text'});
  pending.cb([place('Exact match')], 'OK');
  assert.deepEqual(e.point(), newPoint.map(String));
  assert.equal(e.node('found-text').textContent, 'Exact match');
});

test('replacing the address through autofill before submit cannot keep an old confirmed point', t => {
  const e = editor(t);
  e.search('Nərimanov').cb([place('Narimanov', oldPoint)], 'OK');
  e.doc.getElementById('id_address').value = 'İçərişəhər';
  e.doc.querySelector('form').dispatchEvent(new e.w.Event('submit', {cancelable:true}));
  assert.deepEqual(e.point(), ['', '']);
  assert.equal(e.confirmation(), '');
});

test('equally named alternatives can be distinguished and keyboard focus survives selection', t => {
  const e = editor(t);
  e.search('repeat').cb([place('Same title', oldPoint), place('Same title')], 'OK');
  const [first,second] = e.node('choices').querySelectorAll('button');
  assert.notEqual(first.textContent, second.textContent);
  second.focus();
  second.click();
  assert.deepEqual(e.point(), newPoint.map(String));
  assert.equal(e.doc.activeElement, e.node('search'));
});

test('the legitimate numeric value zero remains usable for a manual point and cannot match an Azerbaijani address', t => {
  const e = editor(t);
  e.node('locate').click();
  e.gps[0].success({coords:{latitude:0,longitude:0}});
  assert.deepEqual(e.point(), ['0.000000','0.000000']);
  assert.equal(e.confirmation(), '1');
  e.search('Baku').cb([place('Unresolved',[0,0])], 'OK');
  assert.deepEqual(e.point(), ['', '']);
  assert.equal(e.confirmation(), '');
});
