const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || '../../.tmp/phone-dom/node_modules/jsdom');

test('a visible section loads its scripts once, in order, with their map configuration', async () => {
  const dom = new JSDOM('<section id="map"></section><template data-scripts-near="#map">' +
    '<script src="/tools.js"></script><script src="/map.js" data-language="az"></script></template>',
    {runScripts: 'outside-only'});
  const {window} = dom;
  try {
    let observe;
    const map = window.document.querySelector('#map');
    map.getClientRects = () => [{}];
    window.IntersectionObserver = class {
      constructor(callback) { observe = callback; }
      observe() {}
      disconnect() {}
    };
    window.eval(fs.readFileSync('static/js/lazy_sections.js', 'utf8'));
    const scripts = () => [...window.document.head.querySelectorAll('script')];
    observe([{target: map, isIntersecting: false}]);
    assert.equal(scripts().length, 0);
    observe([{target: map, isIntersecting: true}]);
    assert.deepEqual(scripts().map(s => s.getAttribute('src')), ['/tools.js']);
    map.dispatchEvent(new window.Event('focusin'));
    scripts()[0].dispatchEvent(new window.Event('load'));
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(scripts()[1].dataset.language, 'az');
    scripts()[1].dispatchEvent(new window.Event('load'));
    await new Promise(resolve => setImmediate(resolve));
    map.dispatchEvent(new window.Event('focusin'));
    assert.equal(scripts().length, 2);
  } finally { window.close(); }
});
