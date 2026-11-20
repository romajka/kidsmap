const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || '../../.tmp/phone-dom/node_modules/jsdom');

test('Google renders ticket pins with languages and counts nearby events in their own cluster', () => {
  const dom = new JSDOM('<section data-home-map-explorer><div id="home-map"></div></section><script id="home-map-events" type="application/json"></script>', {runScripts: 'outside-only'});
  const w = dom.window;
  try {
    const now = Date.now();
    const events = ['Workshop', 'Concert'].map((name, index) => ({
      name, lat: 40.4 + index / 10000, lng: 49.8, languages: ['RU'],
      start: new Date(now + 3600000).toISOString(), end: new Date(now + 7200000).toISOString(),
    }));
    w.document.getElementById('home-map-events').textContent = JSON.stringify(events);
    const mapEl = w.document.getElementById('home-map');
    const map = {getMapCapabilities: () => ({isAdvancedMarkersAvailable: true})};
    mapEl.__kidsMapMounted = {engine: 'google', map, mapId: 'test'};
    class AdvancedMarker extends w.HTMLElement {
      constructor({content}) {
        super();
        if (content) this.append(content);
      }
      addListener() {}
    }
    w.customElements.define('test-google-marker', AdvancedMarker);
    w.google = {maps: {
      marker: {AdvancedMarkerElement: AdvancedMarker},
      Size: class {constructor(width, height) {Object.assign(this, {width, height});}},
      Point: class {constructor(x, y) {Object.assign(this, {x, y});}},
    }};
    let clusterOptions;
    w.markerClusterer = {MarkerClusterer: class {constructor(options) {clusterOptions = options;}}};
    for (const file of ['google_maps_markers', 'map_event_layer']) {
      w.eval(fs.readFileSync('static/js/' + file + '.js', 'utf8'));
    }
    w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
    const {markers, renderer} = clusterOptions;
    assert.equal(markers.length, 2);
    for (const pin of markers) {
      assert.ok(pin.querySelector('.km-evpin__ticket'));
      assert.equal(pin.querySelector('.km-evpin__langs').textContent, 'RU');
      assert.ok(pin.querySelector('[data-km-evpin-left]').textContent.trim());
    }
    const cluster = renderer.render({markers, count: markers.length, position: events[0]});
    assert.equal(cluster.querySelector('.km-evcluster__core b').textContent, '2');
  } finally {
    w.close();
  }
});
