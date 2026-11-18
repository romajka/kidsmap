/* Live catalog search: results under the field as you type, as tiles.
 * Uses the catalog's current filters and public visibility rules (same API as before).
 * - previous results stay on screen while the next query loads (thin progress line, no flicker)
 * - answers are cached per query, so typing back is instant
 * - first load shows skeleton tiles; tiles cascade in; keyboard ↑ ↓ Enter Esc
 */
(function () {
  'use strict';
  const lang = (document.documentElement.lang || 'az').split('-')[0];
  const L = ({
    ru: {all: 'Все результаты', categories: 'Категории', orgs: 'Организации', empty: 'Ничего не нашли', emptyHint: 'Попробуйте другое слово или сбросьте фильтры', error: 'Не удалось загрузить. Попробуйте ещё раз.', retry: 'Повторить', free: 'Бесплатно', label: 'Результаты поиска'},
    az: {all: 'Bütün nəticələr', categories: 'Kateqoriyalar', orgs: 'Təşkilatlar', empty: 'Heç nə tapılmadı', emptyHint: 'Başqa söz yoxlayın və ya filtrləri sıfırlayın', error: 'Yüklənmədi. Yenidən cəhd edin.', retry: 'Yenidən', free: 'Pulsuz', label: 'Axtarış nəticələri'},
    en: {all: 'All results', categories: 'Categories', orgs: 'Organizations', empty: 'Nothing found', emptyHint: 'Try another word or reset the filters', error: 'Could not load results.', retry: 'Retry', free: 'Free', label: 'Search results'}
  })[lang] || null;
  const labels = L || {all: 'All results', categories: 'Categories', orgs: 'Organizations', empty: 'Nothing found', emptyHint: 'Try another word or reset the filters', error: 'Could not load results.', retry: 'Retry', free: 'Free', label: 'Search results'};

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const fold = s => String(s || '').toLocaleLowerCase(lang).normalize('NFD').replace(/[̀-ͯ]/g, '');

  function highlight(text, query) {
    text = String(text || '');
    const q = fold(query).trim();
    if (!q) return esc(text);
    // Accent-insensitive match on a folded copy; slice the original (same length after NFD-strip for these scripts).
    const folded = fold(text);
    const idx = folded.indexOf(q);
    if (idx < 0 || folded.length !== text.length) {
      const pattern = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return text.split(new RegExp('(' + pattern + ')', 'gi')).map((part, i) => i % 2 ? '<mark>' + esc(part) + '</mark>' : esc(part)).join('');
    }
    return esc(text.slice(0, idx)) + '<mark>' + esc(text.slice(idx, idx + q.length)) + '</mark>' + esc(text.slice(idx + q.length));
  }

  function safeUrl(value, image) {
    if (!value) return '';
    try {
      const url = new URL(value, location.href);
      return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password && (image || url.origin === location.origin) ? url.href : '';
    } catch (_) { return ''; }
  }

  const ICON = {
    search: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    place: '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 4.99-5.54 10.19-7.4 11.8a1 1 0 0 1-1.2 0C9.54 20.19 4 14.99 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/></svg>',
    arrow: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>',
    star: '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M11.52 2.3a.53.53 0 0 1 .95 0l2.31 4.68a2.12 2.12 0 0 0 1.6 1.16l5.16.76a.53.53 0 0 1 .3.9l-3.74 3.63a2.12 2.12 0 0 0-.61 1.88l.88 5.14a.53.53 0 0 1-.77.56l-4.62-2.43a2.12 2.12 0 0 0-1.97 0L6.4 21.01a.53.53 0 0 1-.77-.56l.88-5.13a2.12 2.12 0 0 0-.61-1.88L2.16 9.8a.53.53 0 0 1 .3-.9l5.16-.76a2.12 2.12 0 0 0 1.6-1.16z"/></svg>',
    tag: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>',
    org: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/></svg>'
  };

  function setup(inputId, panelId) {
    const input = document.getElementById(inputId);
    const panel = document.getElementById(panelId);
    if (!input || !panel) return;
    const form = input.form;
    const cache = new Map();
    let timer = 0, controller = null, generation = 0, active = -1, options = [], shownQuery = '';

    panel.classList.add('kms');
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-controls', panelId + '-options');
    input.setAttribute('aria-expanded', 'false');
    input.setAttribute('autocomplete', 'off');

    function params() {
      const result = new URLSearchParams(location.search);
      const filterForm = document.getElementById('filters-form') || form;
      if (filterForm) {
        const data = new FormData(filterForm);
        for (const key of new Set(data.keys())) { result.delete(key); for (const value of data.getAll(key)) result.append(key, value); }
      }
      result.set('q', input.value.trim()); result.delete('page'); result.delete('view');
      return result;
    }

    function fit() {
      if (panel.hidden) return;
      const vv = window.visualViewport;
      const bottom = vv ? vv.height + vv.offsetTop : innerHeight;
      panel.style.setProperty('--suggestions-available-height', Math.max(160, bottom - input.getBoundingClientRect().bottom - 16) + 'px');
    }
    window.visualViewport?.addEventListener('resize', fit);
    window.visualViewport?.addEventListener('scroll', fit);
    window.addEventListener('resize', fit);

    function open() {
      if (panel.hidden) {
        panel.hidden = false;
        panel.classList.remove('is-in');
        void panel.offsetWidth;
        panel.classList.add('is-in');
      }
      input.setAttribute('aria-expanded', 'true');
      fit();
    }

    function close() {
      generation++; clearTimeout(timer); controller?.abort();
      panel.hidden = true; panel.classList.remove('is-in', 'is-loading');
      panel.replaceChildren(); active = -1; options = []; shownQuery = '';
      input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant');
    }

    function setLoading(on) {
      panel.classList.toggle('is-loading', on);
      panel.setAttribute('aria-busy', String(on));
    }

    function skeleton() {
      let tiles = '';
      for (let i = 0; i < 4; i++) tiles += '<div class="kms-tile kms-tile--skeleton" style="--i:' + i + '"><span class="kms-thumb"></span><span class="kms-body"><span class="kms-line"></span><span class="kms-line kms-line--short"></span></span></div>';
      panel.innerHTML = '<div class="kms-progress" aria-hidden="true"></div><div class="kms-scroll"><div class="kms-grid">' + tiles + '</div></div>';
      setLoading(true);
      open();
    }

    function allResultsUrl() {
      const target = new URL(form?.action || '/catalog/', location.href);
      target.search = params().toString();
      return target.href;
    }

    function render(data, query) {
      const places = (data.places || []).filter(p => safeUrl(p.url, false));
      const categories = data.categories || [];
      const orgs = (data.organizations || []).filter(o => safeUrl(o.url, false)).slice(0, 4);
      setLoading(false);
      shownQuery = query;

      if (!places.length && !categories.length && !orgs.length) {
        panel.innerHTML = '<div class="kms-progress" aria-hidden="true"></div><div class="kms-empty" role="status"><span class="kms-empty__icon">' + ICON.search + '</span><strong>' + esc(labels.empty) + '</strong><span>' + esc(labels.emptyHint) + '</span></div>';
        options = [];
        open();
        return;
      }

      let chips = '';
      categories.forEach(cat => {
        const q = params(); q.delete('q'); q.delete('subcategory'); q.set('category', cat.code);
        chips += '<a class="kms-chip" href="' + esc((form?.action || '/catalog/') + '?' + q.toString()) + '">' + ICON.tag + '<span>' + highlight(cat.name, query) + '</span></a>';
      });
      orgs.forEach(org => {
        chips += '<a class="kms-chip kms-chip--org" href="' + esc(safeUrl(org.url, false)) + '">' + ICON.org + '<span>' + highlight(org.name, query) + '</span></a>';
      });

      let tiles = '';
      places.forEach((place, i) => {
        const photo = safeUrl(place.image, true);
        const meta = [place.category, place.age, place.district].filter(Boolean).map(esc).join('<i aria-hidden="true">·</i>');
        const rating = place.rating ? '<span class="kms-rating">' + ICON.star + esc(String(place.rating).replace('.', lang === 'en' ? '.' : ',')) + '</span>' : '';
        const price = place.price ? '<span class="kms-price">' + esc(place.price) + '</span>' : '';
        tiles += '<a class="kms-tile" href="' + esc(safeUrl(place.url, false)) + '" style="--i:' + Math.min(i, 9) + '">' +
          '<span class="kms-thumb">' + (photo ? '<img src="' + esc(photo) + '" alt="" loading="lazy" decoding="async">' : ICON.place) + '</span>' +
          '<span class="kms-body"><span class="kms-title">' + highlight(place.name, query) + '</span>' +
          '<span class="kms-meta">' + meta + '</span>' +
          ((price || rating) ? '<span class="kms-tags">' + price + rating + '</span>' : '') +
          '</span><span class="kms-go">' + ICON.arrow + '</span></a>';
      });

      panel.innerHTML =
        '<div class="kms-progress" aria-hidden="true"></div>' +
        '<div class="kms-scroll" id="' + panelId + '-options" role="listbox" aria-label="' + esc(labels.label) + '">' +
          (chips ? '<div class="kms-chips">' + chips + '</div>' : '') +
          (tiles ? '<div class="kms-grid">' + tiles + '</div>' : '') +
        '</div>' +
        (places.length ? '<a class="kms-all" href="' + esc(allResultsUrl()) + '"><span>' + esc(labels.all) + '</span>' + ICON.arrow + '</a>' : '');

      panel.querySelectorAll('img').forEach(img => img.addEventListener('error', () => { img.replaceWith(document.createRange().createContextualFragment(ICON.place)); }));
      options = [...panel.querySelectorAll('.kms-chip, .kms-tile, .kms-all')];
      options.forEach((option, i) => { option.id = panelId + '-option-' + i; option.setAttribute('role', 'option'); option.setAttribute('aria-selected', 'false'); option.tabIndex = -1; });
      active = -1;
      open();
    }

    function showError(query) {
      setLoading(false);
      panel.innerHTML = '<div class="kms-empty" role="status"><span class="kms-empty__icon">' + ICON.search + '</span><strong>' + esc(labels.error) + '</strong><button type="button" class="kms-retry">' + esc(labels.retry) + '</button></div>';
      panel.querySelector('.kms-retry').addEventListener('click', () => { cache.delete(query); schedule(); input.focus(); });
      open();
    }

    async function load(query, token) {
      const q = params(); q.set('lang', lang);
      const key = q.toString();
      if (cache.has(key)) { render(cache.get(key), query); return; }
      controller?.abort();
      controller = new AbortController();
      try {
        const response = await fetch('/api/catalog/suggestions/?' + key, {signal: controller.signal, headers: {'Accept': 'application/json'}});
        if (!response.ok) throw new Error('Suggestions unavailable');
        const data = await response.json();
        cache.set(key, data);
        if (cache.size > 40) cache.delete(cache.keys().next().value);
        if (token !== generation || query !== input.value.trim()) return;
        render(data, query);
      } catch (error) {
        if (token !== generation || error.name === 'AbortError') return;
        showError(key);
      }
    }

    function schedule(event) {
      if (event?.isComposing) return;
      clearTimeout(timer);
      const query = input.value.trim();
      if (!query) { close(); return; }
      const token = ++generation;
      const q = params(); q.set('lang', lang);
      if (cache.has(q.toString())) { render(cache.get(q.toString()), query); return; }
      // Keep what is on screen; just show that a new answer is coming.
      if (panel.hidden || !panel.firstChild) skeleton(); else setLoading(true);
      timer = setTimeout(() => load(query, token), 120);
    }

    input.addEventListener('input', schedule);
    input.addEventListener('compositionend', schedule);
    input.addEventListener('focus', () => { if (input.value.trim() && panel.hidden) schedule(); });

    // Clear buttons next to the field.
    form?.querySelectorAll('[type="reset"], [data-search-clear], .catalog-hero-search-clear, .catalog-search-clear').forEach(btn => btn.addEventListener('click', () => { setTimeout(close, 0); }));

    // The regular submit button/Enter uses exactly the same filters as the hints.
    form?.addEventListener('submit', () => {
      for (const [name, value] of params()) {
        let field = [...form.elements].find(element => element.name === name);
        if (!field) { field = document.createElement('input'); field.type = 'hidden'; field.name = name; form.append(field); }
        field.value = value;
      }
      close();
    }, true);
    document.getElementById('filters-form')?.addEventListener('change', () => { cache.clear(); if (!panel.hidden) close(); });

    input.addEventListener('keydown', event => {
      if (panel.hidden) return;
      if (event.key === 'Escape') { event.preventDefault(); close(); return; }
      if (event.key === 'Tab') { close(); return; }
      if (!options.length) return;
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        active = (active + (event.key === 'ArrowDown' ? 1 : -1) + options.length) % options.length;
        options.forEach((option, i) => { option.classList.toggle('is-selected', i === active); option.setAttribute('aria-selected', String(i === active)); });
        input.setAttribute('aria-activedescendant', options[active].id);
        options[active].scrollIntoView({block: 'nearest'});
      } else if (event.key === 'Enter' && active >= 0) {
        event.preventDefault(); options[active].click();
      }
    });
    document.addEventListener('pointerdown', event => { if (!panel.hidden && event.target !== input && !panel.contains(event.target)) close(); });
  }

  setup('catalog-hero-search-input', 'catalog-search-dropdown');
  setup('catalog-mobile-search', 'catalog-mobile-search-dropdown');
})();
