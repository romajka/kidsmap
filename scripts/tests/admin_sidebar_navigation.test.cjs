const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function harness({ width = 390, stored = {}, current = 1, storageBlocked = false, reducedMotion = false, savedScroll = null } = {}) {
  const resizeListeners = [];
  const writes = [];
  const scrollCalls = [];
  const sessionWrites = [];
  const scrollerListeners = {};
  const groups = Array.from({ length: 3 }, (_, index) => {
    const attrs = { 'data-km-sidebar-key': `group${index}`, 'data-default-open': String(index === current) };
    const buttonAttrs = {};
    const listeners = {};
    const button = {
      getAttribute: key => buttonAttrs[key], setAttribute: (key, value) => { buttonAttrs[key] = value; },
      addEventListener: (name, callback) => {
        assert.equal(listeners[name], undefined, `duplicate ${name} handler`);
        listeners[name] = callback;
      },
      click: () => listeners.click(), scrollIntoView: options => scrollCalls.push(options),
      getBoundingClientRect: () => ({ top: 100, bottom: 144 }),
    };
    const panel = { hidden: false };
    return {
      button, panel, listeners,
      getAttribute: key => attrs[key], setAttribute: (key, value) => { attrs[key] = value; },
      querySelector: selector => selector === '[data-km-sidebar-toggle]' ? button : panel,
    };
  });
  const scroller = {
    scrollTop: 0, addEventListener: (name, callback) => { scrollerListeners[name] = callback; },
    getBoundingClientRect: () => ({ top: 0, bottom: 200 }),
    querySelector: () => null,
  };
  const document = {
    readyState: 'complete',
    querySelector: selector => selector === '.km-admin-sidebar__scroller' ? scroller : null,
    querySelectorAll: selector => selector === '[data-km-sidebar-group]' ? groups : [],
  };
  const window = {
    innerWidth: width,
    localStorage: {
      getItem(key) { if (storageBlocked) throw new Error('blocked'); return stored[key] ?? null; },
      setItem(key, value) { if (storageBlocked) throw new Error('blocked'); writes.push([key, value]); stored[key] = value; },
    },
    sessionStorage: { getItem: () => savedScroll, setItem: (key, value) => sessionWrites.push([key, value]) },
    requestAnimationFrame: callback => callback(),
    matchMedia: query => ({ matches: query === '(prefers-reduced-motion: reduce)' && reducedMotion }),
    addEventListener: (name, callback) => { if (name === 'resize') resizeListeners.push(callback); },
  };
  vm.runInNewContext(fs.readFileSync('static/admin/js/kidsmap_admin_sidebar.js', 'utf8'), {
    window, document, setTimeout, clearTimeout,
  });
  return {
    groups, writes, scrollCalls, scroller, scrollerListeners, sessionWrites,
    open: () => groups.map(group => group.getAttribute('data-open') === 'true'),
    resize(nextWidth) { window.innerWidth = nextWidth; resizeListeners.forEach(callback => callback()); },
  };
}

test('mobile ignores old desktop storage and opens only the current section', () => {
  const sidebar = harness({ stored: { 'km-admin-sidebar:group0': '1', 'km-admin-sidebar:group2': '1' } });
  assert.deepEqual(sidebar.open(), [false, true, false]);
});

test('mobile opens one section at a time without overwriting desktop preferences', () => {
  const sidebar = harness();
  sidebar.groups[2].button.click();
  assert.deepEqual(sidebar.open(), [false, false, true]);
  sidebar.groups[2].button.click();
  assert.deepEqual(sidebar.open(), [false, false, false]);
  assert.equal(sidebar.writes.length, 0);
});

test('overview on mobile starts with all sections collapsed', () => {
  assert.deepEqual(harness({ current: -1 }).open(), [false, false, false]);
});

test('desktop keeps independent persisted groups and the current section open', () => {
  const sidebar = harness({ width: 768, stored: { 'km-admin-sidebar:group0': '1' } });
  assert.deepEqual(sidebar.open(), [true, true, false]);
  sidebar.groups[2].button.click();
  assert.deepEqual(sidebar.open(), [true, true, true]);
  assert.deepEqual(sidebar.writes, [['km-admin-sidebar:group2', '1']]);
});

test('crossing the breakpoint resets mobile to current and restores desktop preferences', () => {
  const sidebar = harness({ width: 1024, stored: { 'km-admin-sidebar:group0': '1' } });
  sidebar.resize(390);
  assert.deepEqual(sidebar.open(), [false, true, false]);
  sidebar.groups[2].button.click();
  sidebar.resize(360);
  assert.deepEqual(sidebar.open(), [false, false, true]);
  sidebar.resize(768);
  assert.deepEqual(sidebar.open(), [true, true, false]);
});

test('storage failure does not stop keyboard activation', () => {
  const sidebar = harness({ storageBlocked: true });
  let prevented = false;
  sidebar.groups[0].listeners.keydown({ key: ' ', preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.deepEqual(sidebar.open(), [true, false, false]);
});

test('reduced motion avoids smooth scrolling when opening a section', () => {
  const sidebar = harness({ reducedMotion: true });
  sidebar.scroller.getBoundingClientRect = () => ({ top: 300, bottom: 500 });
  sidebar.groups[0].button.click();
  assert.equal(sidebar.scrollCalls.at(-1).behavior, 'auto');
});

test('existing scroll position restores and remains saved when following a menu link', () => {
  const sidebar = harness({ savedScroll: '240' });
  assert.equal(sidebar.scroller.scrollTop, 240);
  sidebar.scroller.scrollTop = 360;
  sidebar.scrollerListeners.click({ target: { closest: () => ({}) } });
  assert.deepEqual(sidebar.sessionWrites.at(-1), ['km-admin-sidebar-scroll', '360']);
});

test('repeated breakpoint changes do not duplicate activation handlers', () => {
  const sidebar = harness();
  for (let i = 0; i < 5; i++) {
    sidebar.resize(1024);
    sidebar.resize(390);
  }
  sidebar.groups[2].button.click();
  assert.deepEqual(sidebar.open(), [false, false, true]);
});
