const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || '../../.tmp/phone-dom/node_modules/jsdom');

test('Google stacks sessions at one venue, opens each one and counts them in mixed clusters', () => {
  const dom = new JSDOM('<section data-home-map-explorer><div id="home-map"></div></section><script id="home-map-events" type="application/json"></script>', {runScripts: 'outside-only'});
  const w = dom.window;
  try {
    const now = Date.now();
    const events = ['Concert', 'Concert', 'Workshop'].map((name, index) => ({
      name, lat: index < 2 ? 40.4 : 40.41, lng: 49.8, languages: [index === 1 ? 'AZ' : 'RU'],
      url: '/events/session-' + index + '/',
      start: new Date(now + (index + 1) * 3600000).toISOString(),
      end: new Date(now + (index + 2) * 3600000).toISOString(),
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
      addListener(type, handler) { this.addEventListener(type, handler); }
    }
    w.customElements.define('test-google-marker', AdvancedMarker);
    w.google = {maps: {
      marker: {AdvancedMarkerElement: AdvancedMarker},
      Size: class {constructor(width, height) {Object.assign(this, {width, height});}},
      Point: class {constructor(x, y) {Object.assign(this, {x, y});}},
    }};
    for (const file of ['kidsmap_map_pins', 'google_maps_markers', 'map_event_layer']) {
      w.eval(fs.readFileSync('static/js/' + file + '.js', 'utf8'));
    }
    w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
    const markers = mapEl.__kmEventLayer.visibleMarkers();
    assert.equal(markers.length, 2);
    for (const pin of markers) {
      assert.ok(pin.querySelector('.km-evpin__ticket'));
    }
    const [stack, single] = markers;
    assert.equal(stack.querySelector('.km-evpin__count').textContent, '2');
    assert.ok(single.querySelector('[data-km-evpin-left]').textContent.trim());
    const place = {__kidsMapPlace: {name: 'Museum'}};
    const {element} = w.KidsMapPins.cluster([...markers, place]);
    assert.ok(element.classList.contains('km-cluster--mixed'));
    assert.equal(element.querySelector('.km-cluster__count').textContent, '4');
    assert.equal(element.querySelector('.km-cluster__events').lastChild.textContent, '3');

    stack.click();
    const card = w.document.querySelector('.km-evcard');
    for (const [index, session] of events.slice(0, 2).entries()) {
      const sessions = card.querySelectorAll('[data-km-venue-event]');
      assert.equal(sessions.length, 2);
      sessions[index].click();
      assert.equal(card.querySelector('.km-evcard__title a').getAttribute('href'), session.url);
      assert.equal(card.querySelector('.km-evcard__langs b').textContent, session.languages[0]);
      card.querySelector('[data-km-evcard-back]').click();
    }
  } finally {
    w.close();
  }
});
