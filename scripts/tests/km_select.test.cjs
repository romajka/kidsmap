const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || 'jsdom');

const source = fs.readFileSync(path.join(__dirname, '../../static/js/km_select.js'), 'utf8');

function page(width) {
  const dom = new JSDOM(`<!doctype html><html lang="ru"><body><form>
    <div class="km-filter-group"><label for="d"><span class="material-symbols-rounded" aria-hidden="true">pin</span> Район</label>
    <select id="d" name="district" data-km-select>
      <option value="">Все районы</option>
      <option value="a" data-region="baku">Ясамал (3)</option>
      <option value="b" data-region="baku">Насими (0)</option>
      <option value="c" data-region="ganja">Гянджа центр</option>
    </select></div>
    <select id="s" name="sort" data-km-select data-km-select-clear="false"><option value="new" selected>Новые</option><option value="rating">Рейтинг</option></select>
  </form></body></html>`, {runScripts: 'outside-only', pretendToBeVisual: true});
  const w = dom.window;
  w.matchMedia = () => ({matches: width <= 860, addEventListener() {}});
  w.HTMLElement.prototype.scrollIntoView = function () {};
  w.eval(source);
  w.kmSelect.init(); // the document may still be "loading" right after construction
  return w;
}

const key = (w, el, k) => el.dispatchEvent(new w.KeyboardEvent('keydown', {key: k, bubbles: true, cancelable: true}));

test('native select stays the source of truth and keeps its name', () => {
  const w = page(1280), d = w.document;
  const select = d.getElementById('d');
  const root = select.closest('.km-select');
  assert.ok(root);
  assert.equal(select.name, 'district');
  assert.equal(root.querySelector('.km-select__value').textContent, 'Все районы');
  assert.equal(root.querySelector('.km-select__panel .km-select__sheet-head strong').textContent, 'Район');
  let changes = 0;
  select.addEventListener('change', () => changes++);
  root.querySelector('.km-select__trigger').click();
  assert.equal(root.querySelector('.km-select__trigger').getAttribute('aria-expanded'), 'true');
  const options = root.querySelectorAll('.km-select__option');
  assert.equal(options[1].querySelector('.km-select__label').textContent, 'Ясамал');
  assert.equal(options[1].querySelector('.km-select__count').textContent, '3');
  assert.ok(options[2].classList.contains('is-empty'));
  options[1].click();
  assert.equal(select.value, 'a');
  assert.equal(changes, 1);
  assert.ok(root.classList.contains('has-value'));
  assert.equal(root.querySelector('.km-select__clear').hidden, false);
  root.querySelector('.km-select__clear').click();
  assert.equal(select.value, '');
  assert.equal(changes, 2);
  w.close();
});

test('keyboard: open, move, choose, escape stays inside', () => {
  const w = page(1280), d = w.document;
  const select = d.getElementById('d');
  const root = select.closest('.km-select');
  const trigger = root.querySelector('.km-select__trigger');
  trigger.focus();
  key(w, trigger, 'ArrowDown');
  const list = root.querySelector('.km-select__list');
  assert.equal(d.activeElement, list);
  key(w, list, 'ArrowDown');
  key(w, list, 'ArrowDown');
  key(w, list, 'Enter');
  assert.equal(select.value, 'b');
  assert.equal(d.activeElement, trigger);
  let escapes = 0;
  d.addEventListener('keydown', (e) => { if (e.key === 'Escape') escapes++; });
  key(w, trigger, 'Enter');
  key(w, d.activeElement, 'Escape');
  assert.equal(escapes, 0);
  assert.equal(trigger.getAttribute('aria-expanded'), 'false');
  w.close();
});

test('options hidden or disabled by other scripts are not offered; programmatic values sync', () => {
  const w = page(1280), d = w.document;
  const select = d.getElementById('d');
  const root = select.closest('.km-select');
  select.options[3].hidden = true;
  select.options[3].disabled = true;
  root.querySelector('.km-select__trigger').click();
  assert.deepEqual([...root.querySelectorAll('.km-select__option')].map((li) => li.dataset.value), ['', 'a', 'b']);
  select.value = 'a';
  select.dispatchEvent(new w.Event('change', {bubbles: true}));
  assert.equal(root.querySelector('.km-select__value').textContent, 'Ясамал');
  w.close();
});

test('phones get a sheet at the end of body; sorting has no clear button', () => {
  const w = page(375), d = w.document;
  const root = d.getElementById('d').closest('.km-select');
  root.querySelector('.km-select__trigger').click();
  const sheet = d.querySelector('.km-select__panel.is-sheet');
  assert.ok(sheet);
  assert.equal(sheet.parentElement, d.body);
  assert.equal(d.querySelector('.km-select-backdrop').hidden, false);
  sheet.querySelector('.km-select__sheet-close').click();
  assert.equal(sheet.parentElement, root);
  assert.equal(d.querySelector('.km-select-backdrop').hidden, true);
  const sort = d.getElementById('s').closest('.km-select');
  assert.equal(sort.querySelector('.km-select__clear'), null);
  assert.ok(sort.classList.contains('km-select--plain'));
  w.close();
});
