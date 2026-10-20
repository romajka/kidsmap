const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { JSDOM } = require(process.env.KIDSMAP_JSDOM || 'jsdom');

const source = fs.readFileSync('static/admin/js/kidsmap_place_json_import.js', 'utf8');
const template = fs.readFileSync('src/catalog/templates/admin/catalog/place/form/json_prompt_dialog.html', 'utf8')
  .replace(/{%\s*translate\s+(['"])(.*?)\1\s*%}/g, '$2').replace(/{%[\s\S]*?%}/g, '');
const taxonomy = {
  categories: [{ code: 'SPRT', label: 'Спорт' }, { code: 'ART', label: 'Творчество' }],
  subcategories: [
    { id: '10', code: 'football', label: 'Футбол', category: 'SPRT' },
    { id: '11', code: 'swimming', label: 'Плавание', category: 'SPRT' },
    { id: '20', code: 'painting', label: 'Рисование', category: 'ART' }
  ],
  price_modes: [{ code: 'tariffs', label: 'Тарифы' }, { code: 'free', label: 'Бесплатно' }],
  schedule_modes: [{ code: 'regular', label: 'По дням' }],
  regions: [{ code: 'baku', name_ru: 'Баку', name_az: 'Bakı' }],
  districts: [{ code: 'baku_yasamal', name_ru: 'Ясамал', name_az: 'Yasamal' }]
};

async function mount(config = taxonomy, enhanced = false) {
  const dom = new JSDOM(`<!doctype html><div class="km-pf"><button data-place-json-prompt-copy>Open</button>
    <input id="id_category" value="ART"><input id="id_subcategory" value="20">
    <script id="km-place-taxonomy-config" type="application/json">${JSON.stringify(config)}</script>${template}</div>`,
  { runScripts: 'outside-only', pretendToBeVisual: true });
  const w = dom.window;
  if (enhanced) {
    w.eval(fs.readFileSync(process.env.KIDSMAP_JQUERY, 'utf8'));
    w.eval(fs.readFileSync(process.env.KIDSMAP_SELECT2, 'utf8'));
  }
  // Only native dialog/clipboard APIs are substituted. Browser tests cover their real behavior.
  w.HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  w.HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); this.dispatchEvent(new w.Event('close')); };
  let copied;
  Object.defineProperty(w.navigator, 'clipboard', { value: { writeText: async text => { copied = text; } } });
  Object.defineProperty(w, 'isSecureContext', { value: true });
  const ready = new Promise(resolve => w.document.addEventListener('DOMContentLoaded', resolve, { once: true }));
  w.eval(source);
  await ready;
  // Jazzmin initializes widgets after the prompt listeners are registered.
  if (enhanced) w.jQuery('select').select2({ width: 'element' });
  const q = selector => w.document.querySelector(selector);
  const click = selector => { const element = q(selector); assert(element, 'Missing control: ' + selector); element.click(); };
  const select = (selector, value) => { const element = q(selector); assert(element, 'Missing control: ' + selector); element.value = value; element.dispatchEvent(new w.Event('change', { bubbles: true })); };
  const input = () => q('[data-place-json-prompt-input]');
  click('[data-place-json-prompt-copy]');
  return { dom, w, q, click, select, input, copied: () => copied, mode: value => click(`[data-place-json-prompt-mode][value="${value}"]`), close: () => w.close() };
}

test('search works without category and selecting a subcategory only narrows the prompt', async () => {
  const m = await mount();
  try {
    assert.equal(m.q('[data-place-json-prompt-mode]:checked').value, 'search');
    const initial = m.input().value;
    assert(!initial.includes('Полная структура JSON'), 'Search must not include the import contract');
    m.select('[data-place-json-search-category]', 'SPRT');
    const options = Array.from(m.q('[data-place-json-search-subcategory]').options, option => option.value);
    assert.deepEqual(options, ['', 'football', 'swimming']);
    m.select('[data-place-json-search-subcategory]', 'football');
    assert(m.input().value.includes('Спорт'));
    assert(m.input().value.includes('Футбол'));
    assert(!m.input().value.includes('Рисование'));
    assert.equal(m.q('#id_category').value, 'ART');
    assert.equal(m.q('#id_subcategory').value, '20');
    m.select('[data-place-json-search-category]', 'ART');
    assert.equal(m.q('[data-place-json-search-subcategory]').value, '');
    assert.deepEqual(Array.from(m.q('[data-place-json-search-subcategory]').options, option => option.value), ['', 'painting']);
  } finally { m.close(); }
});

test('Select2 options stay in the dialog and plugin selection updates dependent choices and prompt', {
  skip: !process.env.KIDSMAP_JQUERY || !process.env.KIDSMAP_SELECT2 ? 'Set KIDSMAP_JQUERY and KIDSMAP_SELECT2 to real admin vendor assets' : false
}, async () => {
  const m = await mount(taxonomy, true);
  try {
    const category = m.q('[data-place-json-search-category]');
    const sub = m.q('[data-place-json-search-subcategory]');
    const jq = m.w.jQuery;
    jq(category).select2('open');
    assert(m.q('[data-place-json-prompt-dialog]').contains(m.q('.select2-dropdown')),
      'Select2 dropdown must belong to the native dialog top layer');
    jq(category).val('SPRT').trigger('change');
    assert(m.input().value.includes('Спорт'));
    assert.deepEqual(Array.from(sub.options, o => o.value), ['', 'football', 'swimming']);
    jq(sub).val('football').trigger('change');
    assert(m.input().value.includes('Футбол'));
    jq(category).val('ART').trigger('change');
    assert.equal(sub.value, '');
    assert.equal(jq(sub).next().find('.select2-selection__rendered').text(), 'Любая подкатегория');
    assert.deepEqual(Array.from(sub.options, o => o.value), ['', 'painting']);
    assert.equal(m.q('#id_category').value, 'ART');
    assert.equal(m.q('#id_subcategory').value, '20');
  } finally { m.close(); }
});

test('switching modes and closing/reopening preserves each edited prompt', async () => {
  const m = await mount();
  try {
    m.input().value = 'My edited search';
    m.mode('json');
    assert(m.q('[data-place-json-search-options]').hidden);
    assert(m.input().value.includes('Полная структура JSON'));
    m.input().value = 'My edited JSON';
    m.mode('search');
    assert.equal(m.input().value, 'My edited search');
    assert(!m.q('[data-place-json-search-options]').hidden);
    m.mode('json');
    assert.equal(m.input().value, 'My edited JSON');
    m.click('[data-place-json-prompt-close]');
    m.click('[data-place-json-prompt-copy]');
    assert.equal(m.input().value, 'My edited JSON');
  } finally { m.close(); }
});

test('copy uses current edited prompt; reset restores only the current mode', async () => {
  const m = await mount();
  try {
    m.input().value = 'Keep edited search';
    m.mode('json');
    m.input().value = 'Copy this edited JSON';
    m.click('[data-place-json-prompt-copy-text]');
    await Promise.resolve();
    assert.equal(m.copied(), 'Copy this edited JSON');
    m.click('[data-place-json-prompt-reset]');
    assert(m.input().value.includes('Полная структура JSON'));
    m.mode('search');
    assert.equal(m.input().value, 'Keep edited search');
  } finally { m.close(); }
});

test('JSON mode includes current taxonomy automatically and unknown facts have no fabricated defaults', async () => {
  const m = await mount();
  try {
    m.mode('json');
    const text = m.input().value;
    assert(text.includes('SPRT — Спорт'));
    assert(text.includes('painting — Рисование (категория: ART)'));
    assert(text.includes('baku_yasamal — Ясамал / Yasamal'));
    const example = JSON.parse(text.split('Полная структура JSON:')[1].split('Доступные категории:')[0].trim());
    assert.equal(example.age_open_ended, null);
    assert.equal(example.offers_adult_classes, null);
    assert.equal(example.schedule_mode, '');
    assert.equal(example.lesson_format, '');
    assert.equal(example.price_mode, '');
    assert.equal(example.editor_review.status, 'incomplete');
  } finally { m.close(); }
});

test('empty taxonomy still allows general search and never enables invented subcategories', async () => {
  const m = await mount({});
  try {
    assert(m.input().value.trim());
    assert.equal(m.q('[data-place-json-search-category]').options.length, 1);
    assert.equal(m.q('[data-place-json-search-subcategory]').options.length, 1);
    assert(m.q('[data-place-json-search-subcategory]').disabled);
  } finally { m.close(); }
});
