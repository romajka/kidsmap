/* KidsMap select: a styled, accessible dropdown over a native <select data-km-select>.
 *
 * The native select stays in the form and stays the source of truth: other
 * scripts may change its value, hide or disable options, or disable it, and
 * the dropdown follows. Desktop: a popover under (or above) the field.
 * Phones (<= 860px): a sheet from the bottom of the screen.
 */
(function () {
  'use strict';

  var PHONE = window.matchMedia('(max-width: 860px)');
  var SEARCH_FROM = 9; // options before a search field appears
  var uid = 0;
  var instances = [];
  var backdrop = null;

  function text(el) { return (el.textContent || '').replace(/\s+/g, ' ').trim(); }

  // "Narimanov (4)" -> {label: "Narimanov", count: "4"}
  function splitCount(label) {
    var match = /^(.*?)\s*\((\d+)\)$/.exec(label);
    return match ? {label: match[1], count: match[2]} : {label: label, count: ''};
  }

  function getBackdrop() {
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.className = 'km-select-backdrop';
      backdrop.hidden = true;
      backdrop.addEventListener('click', function () { closeAll(true); });
      document.body.appendChild(backdrop);
    }
    return backdrop;
  }

  function closeAll(restoreFocus) {
    instances.forEach(function (instance) { instance.close(restoreFocus); });
  }

  function labelFor(select) {
    var group = select.closest('.km-filter-group, [data-km-select-group]');
    var label = (select.id && document.querySelector('label[for="' + select.id + '"]')) ||
      (group && group.querySelector('label, legend, .km-filter-label'));
    return label;
  }

  function scrollParent(node) {
    for (var el = node.parentElement; el && el !== document.body; el = el.parentElement) {
      var style = getComputedStyle(el);
      if (/(auto|scroll)/.test(style.overflowY) && el.scrollHeight > el.clientHeight) return el;
    }
    return null;
  }

  function enhance(select) {
    if (select.dataset.kmSelectReady) return;
    select.dataset.kmSelectReady = '1';
    var id = 'km-select-' + (++uid);
    var labelEl = labelFor(select);
    if (labelEl && !labelEl.id) labelEl.id = id + '-label';
    var labelText = select.getAttribute('aria-label') || '';
    if (labelEl) {
      // Icon fonts are ligature text ("school"): read the label without them.
      var copy = labelEl.cloneNode(true);
      copy.querySelectorAll('.material-symbols-rounded, [aria-hidden="true"]').forEach(function (icon) { icon.remove(); });
      labelText = text(copy);
    }
    var lang = (document.documentElement.lang || 'az').slice(0, 2);
    var words = {
      az: {search: 'Axtar…', empty: 'Heç nə tapılmadı', clear: 'Seçimi təmizlə', close: 'Bağla'},
      ru: {search: 'Поиск…', empty: 'Ничего не найдено', clear: 'Сбросить выбор', close: 'Закрыть'},
      en: {search: 'Search…', empty: 'Nothing found', clear: 'Clear selection', close: 'Close'}
    }[lang] || {search: 'Search…', empty: 'Nothing found', clear: 'Clear', close: 'Close'};

    var root = document.createElement('div');
    root.className = 'km-select';
    if (select.dataset.kmSelectAlign === 'end') root.classList.add('km-select--end');
    // Always-set choices (sorting) are not "active filters": no highlight, no clear button.
    if (select.dataset.kmSelectClear === 'false') root.classList.add('km-select--plain');
    select.parentNode.insertBefore(root, select);
    root.appendChild(select);
    select.classList.add('km-select__native');
    select.tabIndex = -1;
    select.setAttribute('aria-hidden', 'true');

    var trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'km-select__trigger';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-controls', id + '-panel');
    trigger.innerHTML = '<span class="km-select__value" id="' + id + '-value"></span>' +
      '<span class="km-select__chev material-symbols-rounded" aria-hidden="true">expand_more</span>';
    if (labelEl) trigger.setAttribute('aria-labelledby', labelEl.id + ' ' + id + '-value');
    root.appendChild(trigger);
    var valueEl = trigger.querySelector('.km-select__value');

    var clear = null;
    if (select.dataset.kmSelectClear !== 'false') {
      clear = document.createElement('button');
      clear.type = 'button';
      clear.className = 'km-select__clear';
      clear.setAttribute('aria-label', words.clear + (labelText ? ': ' + labelText : ''));
      clear.innerHTML = '<span class="material-symbols-rounded" aria-hidden="true">close</span>';
      root.appendChild(clear);
    }

    var panel = document.createElement('div');
    panel.className = 'km-select__panel';
    panel.id = id + '-panel';
    panel.hidden = true;
    panel.innerHTML =
      '<div class="km-select__sheet-head"><strong>' + labelText.replace(/[<>&]/g, '') + '</strong>' +
      '<button type="button" class="km-select__sheet-close" aria-label="' + words.close + '">' +
      '<span class="material-symbols-rounded" aria-hidden="true">close</span></button></div>' +
      '<div class="km-select__search" hidden><span class="material-symbols-rounded" aria-hidden="true">search</span>' +
      '<input type="search" autocomplete="off" spellcheck="false" placeholder="' + words.search + '" aria-label="' + words.search + '"></div>' +
      '<ul class="km-select__list" role="listbox" tabindex="-1" id="' + id + '-list"></ul>' +
      '<p class="km-select__empty" hidden>' + words.empty + '</p>';
    root.appendChild(panel);
    var list = panel.querySelector('.km-select__list');
    var search = panel.querySelector('.km-select__search');
    var searchInput = search.querySelector('input');
    var emptyNote = panel.querySelector('.km-select__empty');
    if (labelEl) list.setAttribute('aria-labelledby', labelEl.id);

    var items = [];
    var active = -1;
    var isOpen = false;

    function visibleOptions() {
      return Array.from(select.options).filter(function (option) { return !option.hidden && !option.disabled; });
    }

    function sync() {
      var selected = select.options[select.selectedIndex];
      var parts = splitCount(selected ? text(selected) : '');
      valueEl.textContent = parts.label;
      root.classList.toggle('has-value', Boolean(select.value));
      trigger.disabled = select.disabled;
      root.classList.toggle('is-disabled', select.disabled);
      if (clear) clear.hidden = !select.value || select.disabled;
    }

    function render() {
      var options = visibleOptions();
      list.innerHTML = '';
      items = options.map(function (option, index) {
        var parts = splitCount(text(option));
        var li = document.createElement('li');
        li.className = 'km-select__option';
        li.id = id + '-opt-' + index;
        li.setAttribute('role', 'option');
        li.dataset.value = option.value;
        li.dataset.search = parts.label.toLowerCase();
        var chosen = option.value === select.value;
        li.setAttribute('aria-selected', String(chosen));
        if (chosen) li.classList.add('is-selected');
        if (!option.value) li.classList.add('is-all');
        li.innerHTML = '<span class="km-select__check material-symbols-rounded" aria-hidden="true">check</span>' +
          '<span class="km-select__label"></span>' + (parts.count ? '<span class="km-select__count"></span>' : '');
        li.querySelector('.km-select__label').textContent = parts.label;
        if (parts.count) li.querySelector('.km-select__count').textContent = parts.count;
        if (parts.count === '0') li.classList.add('is-empty');
        li.style.setProperty('--i', Math.min(index, 12));
        list.appendChild(li);
        return li;
      });
      search.hidden = options.length < SEARCH_FROM;
      searchInput.value = '';
      emptyNote.hidden = true;
    }

    function shown() { return items.filter(function (li) { return !li.hidden; }); }

    function setActive(index, scroll) {
      var pool = shown();
      if (!pool.length) { active = -1; list.removeAttribute('aria-activedescendant'); return; }
      index = Math.max(0, Math.min(index, pool.length - 1));
      items.forEach(function (li) { li.classList.remove('is-active'); });
      var li = pool[index];
      li.classList.add('is-active');
      active = index;
      list.setAttribute('aria-activedescendant', li.id);
      if (scroll !== false) li.scrollIntoView({block: 'nearest'});
    }

    function place() {
      root.classList.remove('is-up');
      if (PHONE.matches) return;
      var box = trigger.getBoundingClientRect();
      var container = scrollParent(root);
      var limit = container ? container.getBoundingClientRect() : {top: 0, bottom: window.innerHeight};
      var need = Math.min(panel.scrollHeight, 340) + 12;
      var below = Math.min(limit.bottom, window.innerHeight) - box.bottom;
      var above = box.top - Math.max(limit.top, 0);
      if (below < need && above > below) root.classList.add('is-up');
    }

    function open() {
      if (isOpen || select.disabled) return;
      closeAll(false);
      render();
      isOpen = true;
      panel.hidden = false;
      root.classList.add('is-open');
      trigger.setAttribute('aria-expanded', 'true');
      panel.classList.toggle('is-sheet', PHONE.matches);
      if (PHONE.matches) {
        // A sheet lives at the end of <body>: it must cover the filter sheet too.
        document.body.appendChild(panel);
        var shade = getBackdrop();
        shade.hidden = false;
        document.documentElement.classList.add('km-select-sheet-open');
        requestAnimationFrame(function () { shade.classList.add('is-visible'); });
      }
      place();
      requestAnimationFrame(function () { panel.classList.add('is-visible'); });
      var selectedIndex = shown().findIndex(function (li) { return li.classList.contains('is-selected'); });
      setActive(selectedIndex < 0 ? 0 : selectedIndex);
      (search.hidden || PHONE.matches ? list : searchInput).focus({preventScroll: true});
    }

    function close(restoreFocus) {
      if (!isOpen) return;
      isOpen = false;
      root.classList.remove('is-open', 'is-up');
      trigger.setAttribute('aria-expanded', 'false');
      panel.classList.remove('is-visible');
      panel.hidden = true;
      if (panel.parentNode !== root) root.appendChild(panel);
      if (backdrop && !instances.some(function (other) { return other.isOpen(); })) {
        backdrop.classList.remove('is-visible');
        backdrop.hidden = true;
        document.documentElement.classList.remove('km-select-sheet-open');
      }
      if (restoreFocus) trigger.focus({preventScroll: true});
    }

    function choose(value) {
      var changed = select.value !== value;
      select.value = value;
      sync();
      close(true);
      if (changed) select.dispatchEvent(new Event('change', {bubbles: true}));
      root.classList.remove('is-picked');
      void root.offsetWidth;
      root.classList.add('is-picked');
    }

    function filter() {
      var query = searchInput.value.trim().toLowerCase();
      items.forEach(function (li) { li.hidden = Boolean(query) && li.dataset.search.indexOf(query) === -1; });
      emptyNote.hidden = shown().length > 0;
      setActive(0, false);
    }

    trigger.addEventListener('click', function () { isOpen ? close(true) : open(); });
    trigger.addEventListener('keydown', function (event) {
      if (['ArrowDown', 'ArrowUp', 'Enter', ' '].indexOf(event.key) !== -1) {
        event.preventDefault();
        open();
      }
    });
    if (clear) clear.addEventListener('click', function () { choose(''); });
    panel.querySelector('.km-select__sheet-close').addEventListener('click', function () { close(true); });

    list.addEventListener('click', function (event) {
      var li = event.target.closest('.km-select__option');
      if (li) choose(li.dataset.value);
    });
    list.addEventListener('mousemove', function (event) {
      var li = event.target.closest('.km-select__option');
      if (li) setActive(shown().indexOf(li), false);
    });

    var typed = '';
    var typedAt = 0;
    function keys(event) {
      var pool = shown();
      if (event.key === 'ArrowDown') { event.preventDefault(); setActive(active + 1); }
      else if (event.key === 'ArrowUp') { event.preventDefault(); setActive(active - 1); }
      else if (event.key === 'Home') { event.preventDefault(); setActive(0); }
      else if (event.key === 'End') { event.preventDefault(); setActive(pool.length - 1); }
      else if (event.key === 'Enter') { event.preventDefault(); if (pool[active]) choose(pool[active].dataset.value); }
      else if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); close(true); }
      else if (event.key === 'Tab') { close(false); }
      else if (event.target === list && event.key.length === 1 && /\S/.test(event.key)) {
        var now = Date.now();
        typed = (now - typedAt < 700 ? typed : '') + event.key.toLowerCase();
        typedAt = now;
        var hit = pool.findIndex(function (li) { return li.dataset.search.indexOf(typed) === 0; });
        if (hit >= 0) setActive(hit);
      }
    }
    list.addEventListener('keydown', keys);
    searchInput.addEventListener('keydown', keys);
    searchInput.addEventListener('input', filter);

    select.addEventListener('change', sync);
    new MutationObserver(function () {
      if (!select.isConnected) return;
      sync();
      if (isOpen) render();
    })
      .observe(select, {attributes: true, attributeFilter: ['disabled'], childList: true, subtree: true});

    var instance = {root: root, sync: sync, close: close, isOpen: function () { return isOpen; }};
    instances.push(instance);
    sync();
    return instance;
  }

  function syncAll() { instances.forEach(function (instance) { instance.sync(); }); }

  function init(scope) {
    (scope || document).querySelectorAll('select[data-km-select]').forEach(enhance);
  }

  document.addEventListener('click', function (event) {
    if (!event.target.closest('.km-select, .km-select__panel, .km-select-backdrop')) closeAll(false);
  });
  // Other scripts set values without events (e.g. clearing a district): re-read after any form change.
  document.addEventListener('change', function () { setTimeout(syncAll, 0); });
  window.addEventListener('resize', function () { closeAll(false); });
  PHONE.addEventListener('change', function () { closeAll(false); });

  window.kmSelect = {init: init, syncAll: syncAll, closeAll: closeAll};
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { init(); }, {once: true});
  else init();
})();
