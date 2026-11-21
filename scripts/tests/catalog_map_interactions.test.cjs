const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || 'jsdom');
const source = fs.readFileSync('static/js/catalog_map.js', 'utf8');

function loadCatalogInternals(window) {
  window.eval(source.replace(/  initCatalogMapUi\(\);\s*\}\)\(\);\s*$/,
    '  window.catalogTest = {resetCatalogPaging, rebindActiveCard};\n})();'));
  return window.catalogTest;
}

test('opening the catalog while the Google SDK is loading waits for the map API before clustering', () => {
  const dom = new JSDOM(`
    <button data-catalog-map-open></button>
    <section id="map-panel" data-catalog-map-panel data-map-provider="google" hidden>
      <div data-catalog-map></div><button data-catalog-map-close></button>
    </section>
    <script id="catalog-map-data" type="application/json">[{"id":1,"lat":40,"lng":49}]</script>
  `, {url: 'https://example.test/catalog/', runScripts: 'outside-only'});
  const {window} = dom;
  const {document} = window;
  try {
    window.matchMedia = () => ({matches: false, addEventListener() {}});
    window.requestAnimationFrame = callback => callback();
    window.google = {maps: {}};
    window.eval(source);
    document.querySelector('[data-catalog-map-open]').click();
    const clusterScript = () => document.querySelector('script[src*="markerclusterer"]');
    assert.ok(document.querySelector('.catalog-map-loading'));
    assert.equal(clusterScript(), null, 'starting the cluster library early can disable clustering');
    window.google.maps.Map = class {};
    window.google.maps.ControlPosition = {RIGHT_TOP: 1};
    window.kidsMapInitCatalogResultsMap();
    assert.ok(clusterScript());
  } finally {
    window.close();
  }
});

test('a delayed catalog viewport response preserves the current selection and camera', () => {
  const dom = new JSDOM('<section><div data-map-pagination="catalog"></div></section><script id="catalog-map-page">{}</script>', {runScripts: 'outside-only'});
  const {window} = dom;
  try {
    const {resetCatalogPaging} = loadCatalogInternals(window);
    const selected = {id: 1};
    let apply, synced = false, cancels = 0;
    window.KidsMapPaging = {create(options) { apply = options.onChange; return {}; }};
    const state = {
      panel: window.document.querySelector('section'), places: [selected], activePlace: selected,
      googleMap: {}, motion: {cancel() { cancels++; }, select() {}},
      syncGooglePlaces() { synced = true; },
    };
    resetCatalogPaging(state);
    apply([selected], {bounds: {north: 41, south: 40, west: 49, east: 50}});
    assert.equal(state.activePlace, selected);
    assert.equal(cancels, 0);
    assert.equal(synced, true);
    apply([], {bounds: null});
    assert.equal(state.activePlace, null, 'a new filter result still dismisses the old selection');
  } finally {
    window.close();
  }
});

test('a refreshed pin keeps its selected member and dismisses a member missing from the results', () => {
  const dom = new JSDOM('<div id="card"></div>', {runScripts: 'outside-only'});
  const {window} = dom;
  try {
    window.matchMedia = () => ({matches: false});
    const {rebindActiveCard} = loadCatalogInternals(window);
    const place = {url: '/place/one/', name: 'Museum'};
    const oldPin = {__kidsMapPlace: {members: [place]}};
    const updated = {...place, name: 'Updated Museum'};
    const newPin = {__kidsMapPlace: {members: [updated]}};
    const card = window.document.getElementById('card');
    let selected;
    const state = {activePlace: place, activeMarker: oldPin, desktopCardEl: card,
      motion: {select(marker) { selected = marker; }}};
    rebindActiveCard(state, newPin);
    assert.equal(state.activePlace, updated);
    assert.equal(selected, newPin);
    assert.match(card.textContent, /Updated Museum/);
    rebindActiveCard(state, {__kidsMapPlace: {members: [{url: '/place/two/'}]}});
    assert.equal(state.activePlace, null);
    assert.equal(selected, null);
    assert.equal(card.hidden, true);
  } finally {
    window.close();
  }
});
