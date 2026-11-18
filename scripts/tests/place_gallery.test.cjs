const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || '../../.tmp/phone-dom/node_modules/jsdom');
const source = fs.readFileSync('static/js/place_gallery.js', 'utf8');

function mount(t, reduced = false) {
  const slides = [1, 2, 3].map(index => `<figure class="place-gallery__slide"><img class="place-gallery__image" src="/photo-${index}.jpg" alt="Студия"></figure>`).join('');
  const buttons = [1, 2, 3].map(index => `<button data-place-gallery-thumb>${index}</button>`).join('');
  const dom = new JSDOM(`<html lang="ru"><section data-place-gallery><div data-place-gallery-main>${slides}
    <button data-place-gallery-prev aria-label="Предыдущее фото"></button><button data-place-gallery-next aria-label="Следующее фото"></button>
    <span data-place-gallery-current></span></div><div class="place-gallery__thumbs">${buttons}</div></section></html>`,
    {url: 'https://example.test/ru/place/', runScripts: 'outside-only', pretendToBeVisual: true});
  t.after(() => dom.window.close());
  const {window} = dom;
  const {document} = window;
  const strip = document.querySelector('.place-gallery__thumbs');
  const thumbs = Array.from(strip.querySelectorAll('button'));
  Object.defineProperty(strip, 'clientWidth', {value: 180});
  thumbs.forEach((thumb, index) => Object.defineProperties(thumb, {
    offsetLeft: {value: index * 90}, offsetWidth: {value: 80},
  }));
  const stripScrolls = [];
  const pageScrolls = [];
  strip.scrollTo = options => stripScrolls.push(options);
  window.scrollTo = window.HTMLElement.prototype.scrollIntoView = options => pageScrolls.push(options);
  const sliders = [];
  window.matchMedia = () => ({matches: reduced});
  window.Swiper = class {
    constructor(element, options) {
      this.options = options;
      this.realIndex = options.initialSlide || 0;
      sliders.push(this);
      options.on.init?.(this);
    }
    slideTo(index) {
      this.realIndex = index;
      this.options.on.slideChange(this);
    }
    destroy() {}
  };
  window.eval(source);
  return {window, document, sliders, thumbs, stripScrolls, pageScrolls};
}

test('mounting the gallery does not scroll the document or thumbnail strip', t => {
  const {pageScrolls, stripScrolls, thumbs} = mount(t);
  assert.equal(thumbs[0].getAttribute('aria-current'), 'true');
  assert.equal(pageScrolls.length, 0);
  assert.equal(stripScrolls.length, 0);
});

test('reduced motion uses instant transitions and thumbnail scrolling', t => {
  const {sliders, stripScrolls} = mount(t, true);
  assert.equal(sliders[0].options.speed, 0);
  sliders[0].slideTo(2);
  assert.equal(stripScrolls[0].behavior, 'auto');
});

test('gallery navigation keeps server-localized accessible labels', t => {
  const {sliders} = mount(t);
  assert.equal(sliders[0].options.a11y.prevSlideMessage, 'Предыдущее фото');
  assert.equal(sliders[0].options.a11y.nextSlideMessage, 'Следующее фото');
});

test('selecting a thumbnail scrolls only the strip and updates the counter and dots', t => {
  const {document, thumbs, stripScrolls, pageScrolls} = mount(t);
  thumbs[2].click();
  assert.equal(pageScrolls.length, 0);
  assert.equal(stripScrolls.length, 1);
  assert.equal(stripScrolls[0].left, 130);
  assert.equal(stripScrolls[0].behavior, 'smooth');
  assert.equal(thumbs[2].getAttribute('aria-current'), 'true');
  assert.equal(document.querySelector('[data-place-gallery-current]').textContent, '3');
  assert.equal(document.querySelector('.place-gallery__dots').children[2].classList.contains('is-active'), true);
});

test('a keyboard user can open the current photo, use localized viewer controls, and return to the gallery', async t => {
  const {window, document, thumbs, sliders} = mount(t, true);
  thumbs[1].click();
  const images = document.querySelectorAll('.place-gallery__image');
  assert.equal(images[0].tabIndex, -1);
  assert.equal(images[1].tabIndex, 0);
  images[1].focus();
  images[1].dispatchEvent(new window.KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
  const dialog = document.querySelector('[role="dialog"]');
  assert.ok(dialog);
  const close = dialog.querySelector('button[aria-label="Закрыть"]');
  const previous = dialog.querySelector('button[aria-label="Предыдущее фото"]');
  const next = dialog.querySelector('button[aria-label="Следующее фото"]');
  assert.ok(previous && next);
  assert.equal(sliders[1].options.a11y.nextSlideMessage, 'Следующее фото');
  assert.equal(document.activeElement, close);
  const tab = new window.KeyboardEvent('keydown', {key: 'Tab', bubbles: true, cancelable: true});
  close.dispatchEvent(tab);
  assert.equal(tab.defaultPrevented, false);
  sliders[1].slideTo(2);
  document.dispatchEvent(new window.KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
  await new Promise(resolve => window.setTimeout(resolve, 10));
  assert.equal(document.querySelector('[role="dialog"]'), null);
  assert.equal(thumbs[2].getAttribute('aria-current'), 'true');
  assert.equal(document.activeElement, images[2]);
});
