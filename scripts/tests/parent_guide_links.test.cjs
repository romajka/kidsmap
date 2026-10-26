const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const { JSDOM } = require(process.env.KIDSMAP_JSDOM || 'jsdom');
const source = fs.readFileSync(path.join(__dirname, '../../static/js/parent_guides.js'), 'utf8');

function page(hash = '', { reducedMotion = false, matchMedia = true } = {}) {
  const dom = new JSDOM(`<article class="parent-guide"><section class="pg-faq">
    <details id="guide-faq-rain" open><summary>Rain</summary><p>Indoor places</p></details>
    <details id="guide-faq-free"><summary>Free</summary><p>Admission conditions</p></details>
    <details id="guide-faq-weekend"><summary>Weekend</summary><p>Ideas</p></details>
    </section></article><details id="outside"><summary>Other</summary></details>`,
    { url: 'https://kidsmap.az/ru/parents/baku-with-kids/' + hash, runScripts: 'outside-only' });
  if (matchMedia) dom.window.matchMedia = () => ({ matches: reducedMotion });
  dom.window.eval(source);
  return dom;
}

for (const options of [{}, { reducedMotion: true }, { matchMedia: false }]) {
  test(`deep link opens its answer independently of animation: ${JSON.stringify(options)}`, () => {
    const dom = page('#guide-faq-free', options);
    assert.equal(dom.window.document.querySelector('#guide-faq-free').open, true);
    assert.equal(dom.window.document.querySelector('#guide-faq-weekend').open, false);
    dom.window.close();
  });
}

test('same page hash navigation opens the next answer', () => {
  const dom = page();
  dom.window.history.replaceState(null, '', '#guide-faq-weekend');
  dom.window.dispatchEvent(new dom.window.HashChangeEvent('hashchange'));
  assert.equal(dom.window.document.querySelector('#guide-faq-weekend').open, true);
  dom.window.close();
});

for (const hash of ['#outside', '#missing', '#%E0%A4%A', '#guide-faq-%66ree']) {
  test(`unknown or unrelated fragments are safe: ${hash}`, () => {
    const dom = page(hash);
    assert.equal(dom.window.document.querySelector('#outside').open, false);
    assert.equal(dom.window.document.querySelector('#guide-faq-weekend').open, false);
    dom.window.close();
  });
}
