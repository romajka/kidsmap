const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');
const source = fs.readFileSync('static/js/home_map.js', 'utf8');
function contextFor(fields, fetch) {
  const context = {URLSearchParams, AbortController, fetch,
    FormData: class { constructor() { return fields; } },
    document: {querySelector: () => ({}), getElementById: () => ({dataset:{mapEndpoint:'/api/map/points/'}})}};
  vm.createContext(context);
  vm.runInContext(source.slice(source.indexOf('  function normalizeValue('), source.indexOf('  function parsePlaces(')) +
    source.slice(source.indexOf('  function isPlaceInBaku('), source.indexOf('  function interpolateAgeLabel(')) +
    source.slice(source.indexOf('  function hasValidCoordinates('), source.indexOf('  function hasActiveFilters(')), context);
  return context;
}
for (const label of ['Sumgait', 'Сумгаит', 'Sumqayıt']) {
  test('Baku excludes explicit Sumgait despite coordinates/address: '+label, () => {
    assert.equal(contextFor([]).isPlaceInBaku({district:'sumgait',district_label:label,lat:40.589,lng:49.668,address:'Baku road'}),false);
  });
}
test('district classification uses canonical keys and never guesses from address or coordinates', () => {
  const context=contextFor([]);
  assert.equal(context.isPlaceInBaku({district:'',district_label:'Baku',lat:40.4,lng:49.8}),false);
  assert.equal(context.isPlaceInBaku({district:'baku_yasamal',address:'Sumgait road'}),true);
  assert.equal(context.isPlaceInBaku({district:'baku_narimanov'}),true);
});
test('category, subcategory, district, age and query go together to canonical server search', async () => {
  const fields=[['category','TECH'],['subcategory','17'],['district','baku_yasamal'],['age','6'],['q','robotics & art']];
  let request;
  const approved={lat:40.4,lng:49.8,members:[{id:7}]};
  const context=contextFor(fields,async(url,options)=>{
    request={url,options};return {ok:true,json:async()=>({points:[approved,{lat:null,lng:null}]})};
  });
  const signal=new AbortController().signal;
  const points=await context.fetchFilteredPoints(signal);
  assert.deepEqual([...new URL(request.url,'http://localhost').searchParams],fields);
  assert.equal(request.options.signal,signal);assert.equal(request.options.credentials,'same-origin');
  assert.equal(request.options.headers.Accept,'application/json');
  assert.equal(points.length,1);assert.equal(points[0],approved);
});
test('failed server filter request is reported, not replaced by guessed client results', async () => {
  const context=contextFor([],async()=>({ok:false}));
  await assert.rejects(context.fetchFilteredPoints(),/Map filter request failed/);
});
test('latest filter response wins, aborted and stale results cannot overwrite the map', async () => {
  const pending=[],applied=[],errors=[],context=contextFor([],(_url,options)=>new Promise(resolve=>pending.push({resolve,options})));
  const update=context.serverFilterUpdater(points=>applied.push(points),()=>{},()=>errors.push('error'));
  const first=update(),second=update();
  assert.equal(pending[0].options.signal.aborted,true);
  const newer={lat:40.4,lng:49.8,members:[{id:2}]},older={lat:40.5,lng:49.9,members:[{id:1}]};
  pending[1].resolve({ok:true,json:async()=>({points:[newer]})});await second;
  pending[0].resolve({ok:true,json:async()=>({points:[older]})});await first;
  assert.equal(applied.at(-1)[0],newer);assert.equal(applied.length,3);assert.deepEqual(errors,[]);
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
