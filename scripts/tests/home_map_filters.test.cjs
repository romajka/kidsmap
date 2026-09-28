const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');
// Exercise the actual private predicate without starting a map provider.
const source = fs.readFileSync('static/js/home_map.js', 'utf8');
const context = {};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('  function normalizeValue('), source.indexOf('  function parsePlaces(')) +
  source.slice(source.indexOf('  function isPlaceInBaku('), source.indexOf('  function interpolateAgeLabel(')), context);
const base = {category_code:'TECH', district:'baku_yasamal', district_label:'Yasamal', search_text:'Robotics', age_from:6, age_to:12};
const matches = (place, filters) => context.placeMatchesFilters({...base, ...place}, {category:'', district:'', metro:'', age:'', query:'', ...filters});
for (const label of ['Sumgait', 'Сумгаит', 'Sumqayıt']) {
  test('Baku excludes explicit Sumgait despite coordinates/address: '+label, () => {
    assert.equal(matches({district:'sumgait', district_label:label, lat:40.589, lng:49.668, address:'Baku road', search_text:'Near Baku'}, {district:'baku'}), false);
  });
}
test('address cannot override an explicit district', () => {
  assert.equal(matches({search_text:'Yasamal, Narimanov street', district_label:'Narimanov street'}, {district:'baku_narimanov'}), false);
});
test('missing canonical district is not guessed from label or coordinates', () => {
  assert.equal(matches({district:'', district_label:'Baku', lat:40.4, lng:49.8, search_text:'Baku'}, {district:'baku'}), false);
});
test('Baku includes all canonical Baku districts, specific district is exact', () => {
  assert.equal(matches({}, {district:'baku'}), true);
  assert.equal(matches({}, {district:'baku_yasamal'}), true);
  assert.equal(matches({district:'baku_narimanov'}, {district:'baku_yasamal'}), false);
});
test('age is exact, inclusive, and supports one missing bound', () => {
  assert.equal(matches({}, {age:'6'}), true);
  assert.equal(matches({}, {age:'12'}), true);
  assert.equal(matches({age_from:8}, {age:'6'}), false);
  assert.equal(matches({age_from:null}, {age:'0'}), true);
  assert.equal(matches({age_to:null}, {age:'16'}), true);
  assert.equal(matches({age_from:null,age_to:null}, {age:'6'}), false);
  assert.equal(matches({age_from:null,age_to:null}, {}), true);
});
test('category, district, age and query are combined with AND', () => {
  assert.equal(matches({}, {category:'TECH', district:'baku_yasamal', age:'9', query:'robotics'}), true);
  for(const filters of [{category:'MUS'}, {district:'sumgait'}, {age:'16'}, {query:'swimming'}])
    assert.equal(matches({}, {category:'TECH', district:'baku_yasamal', age:'9', query:'robotics', ...filters}), false);
});

test('Leaflet fallback reads asset URLs and integrity from its script tag', async () => {
  const calls = [];
  const providerContext = {
    document: {currentScript: {dataset: {
      homeMapLeafletCss: 'https://example.test/leaflet.css',
      homeMapLeafletCssIntegrity: 'css-integrity',
      homeMapLeafletJs: 'https://example.test/leaflet.js',
      homeMapLeafletJsIntegrity: 'js-integrity'
    }}},
    mapEl: {dataset: {}},
    // Network loaders are isolated; config parsing and provider orchestration
    // below are the real implementation. Rendered fallback is checked separately.
    loadStylesheet: (url, integrity) => { calls.push({url, integrity}); return Promise.resolve(); },
    loadScript: (url, integrity) => { calls.push({url, integrity}); return Promise.resolve(); },
    tryMount: () => true,
    Promise
  };
  vm.createContext(providerContext);
  const configSource = source.slice(source.indexOf('  const SCRIPT_CONFIG ='), source.indexOf('  function escapeHtml('));
  const loaderSource = source.slice(source.indexOf('    function loadLeafletProvider('), source.indexOf('    function loadGoogleProvider('));
  vm.runInContext(configSource + loaderSource, providerContext);
  await providerContext.loadLeafletProvider();
  assert.deepEqual(calls.filter(call => call.url.startsWith('https://example.test/')), [
    {url:'https://example.test/leaflet.css', integrity:'css-integrity'},
    {url:'https://example.test/leaflet.js', integrity:'js-integrity'}
  ]);
});
