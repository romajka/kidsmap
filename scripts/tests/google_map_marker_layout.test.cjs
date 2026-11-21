const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || 'jsdom');

test('raster pins track projected anchors with a transform and update keyboard visibility after resize', () => {
  const dom = new JSDOM('<div id="map"></div>', {runScripts: 'outside-only'});
  const w = dom.window;
  try {
    const el = w.document.getElementById('map');
    const map = {getDiv: () => el};
    const overlays = [];
    let width = 320;
    let panX = 0;
    Object.defineProperties(el, {
      clientWidth: {get() { return width; }},
      clientHeight: {value: 240},
    });
    w.google = {maps: {
      Marker: class {
        constructor(options) { this.position = options.position; }
        getMap() { return map; }
        getPosition() { return this.position; }
        getZIndex() { return 0; }
        addListener() {}
      },
      MVCObject: class {},
      OverlayView: class {
        setMap() { overlays.push(this); this.onAdd(); this.draw(); }
        getPanes() { return {overlayMouseTarget: el}; }
        getProjection() {
          const project = p => ({x: p.x + panX, y: p.y});
          return {fromLatLngToDivPixel: project, fromLatLngToContainerPixel: project};
        }
      },
    }};
    w.eval(fs.readFileSync('static/js/google_maps_markers.js', 'utf8'));
    const pins = [80, 400].map(x => w.kidsMapCreateGoogleMarker({
      map, publicVisual: true, position: {x, y: 90},
      icon: {url: 'pin.svg', scaledSize: {width: 40, height: 50}},
    }).getElement());
    assert.deepEqual(pins.map(pin => pin.tabIndex), [0, -1]);
    assert.equal(pins[0].style.transform, 'translate(58px, 40px)');
    assert.equal(pins[1].getAttribute('aria-hidden'), 'true');
    width = 480;
    panX = 7;
    overlays.forEach(overlay => overlay.draw());
    assert.deepEqual(pins.map(pin => pin.tabIndex), [0, 0]);
    assert.equal(pins[1].style.transform, 'translate(385px, 40px)');
    assert.equal(pins[1].getAttribute('aria-hidden'), 'false');
  } finally {
    w.close();
  }
});
