/* Catalog suggestions share the catalog's filters and public visibility rules. */
(function () {
  'use strict';
  const lang = (document.documentElement.lang || 'az').split('-')[0];
  const labels = ({
    ru: {title:'Найденные места',hint:'Нажмите, чтобы открыть карточку',all:'Все результаты',loading:'Ищем места…',empty:'Ничего не найдено. Попробуйте другой запрос или измените фильтры.',error:'Не удалось загрузить результаты. Попробуйте ещё раз.'},
    az: {title:'Tapılan məkanlar',hint:'Kartı açmaq üçün klikləyin',all:'Bütün nəticələr',loading:'Axtarılır…',empty:'Nəticə tapılmadı. Sorğunu və ya filtrləri dəyişin.',error:'Nəticələr yüklənmədi. Yenidən cəhd edin.'},
    en: {title:'Found places',hint:'Click to open the place',all:'All results',loading:'Searching…',empty:'No results. Try another search or change the filters.',error:'Could not load results. Please try again.'}
  })[lang] || {title:'Found places',hint:'Click to open the place',all:'All results',loading:'Searching…',empty:'No results. Try another search or change the filters.',error:'Could not load results. Please try again.'};
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function highlight(text, query) {
    const pattern = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return String(text || '').split(new RegExp('(' + pattern + ')', 'gi')).map((part, i) => i % 2 ? '<mark class="search-highlight">' + escape(part) + '</mark>' : escape(part)).join('');
  }
  function safeUrl(value, image) {
    if (!value) return '';
    try {
      const url = new URL(value, location.href);
      return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password && (image || url.origin === location.origin) ? url.href : '';
    } catch (_) { return ''; }
  }
  function setup(inputId, panelId) {
    const input = document.getElementById(inputId), panel = document.getElementById(panelId);
    if (!input || !panel) return;
    const form = input.form;
    let timer, controller, generation = 0, active = -1, options = [];
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-controls', panelId + '-options');
    input.setAttribute('aria-expanded', 'false');
    function close() {
      generation++; clearTimeout(timer); controller?.abort();
      panel.hidden = true; panel.replaceChildren(); active = -1; options = [];
      input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant');
    }
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
      const viewport = window.visualViewport;
      const bottom = viewport ? viewport.height + viewport.offsetTop : innerHeight;
      panel.style.setProperty('--suggestions-available-height', Math.max(100, bottom - input.getBoundingClientRect().bottom - 20) + 'px');
    }
    window.visualViewport?.addEventListener('resize', fit);
    window.visualViewport?.addEventListener('scroll', fit);
    function open() { panel.hidden = false; input.setAttribute('aria-expanded', 'true'); fit(); }
    function status(message, busy) {
      panel.innerHTML = '<p class="catalog-suggestions-status" role="status">' + escape(message) + '</p>';
      panel.setAttribute('aria-busy', String(busy)); open();
    }
    function render(data, query) {
      const places = data.places || [], categories = data.categories || [];
      panel.setAttribute('aria-busy', 'false');
      if (!places.length && !categories.length) { status(labels.empty, false); return; }
      panel.innerHTML = '<div class="catalog-suggestions-heading"><strong>' + escape(labels.title) + '</strong><span>' + escape(labels.hint) + '</span></div><div class="catalog-suggestions-scroll"><div role="listbox" id="' + panelId + '-options" aria-label="' + escape(labels.title) + '"><div class="search-dropdown-category-chips"></div><div class="search-dropdown-cards-list"></div></div></div><div class="search-dropdown-footer"><button type="button" class="search-dropdown-all-btn">' + escape(labels.all) + ' <span aria-hidden="true">→</span></button></div>';
      const chips = panel.querySelector('.search-dropdown-category-chips');
      categories.forEach(cat => {
        const link = document.createElement('a'), queryParams = params();
        queryParams.delete('q'); queryParams.delete('subcategory'); queryParams.set('category', cat.code);
        link.href = form.action + '?' + queryParams.toString(); link.className = 'search-dropdown-cat-chip'; link.textContent = cat.name;
        chips.append(link);
      });
      const grid = panel.querySelector('.search-dropdown-cards-list');
      places.forEach(place => {
        const href = safeUrl(place.url, false); if (!href) return;
        const card = document.createElement('a'); card.href = href; card.className = 'search-card-item';
        const photo = safeUrl(place.image, true);
        card.innerHTML = '<div class="catalog-suggestion-cover" aria-hidden="true"><span>◇</span>' + (photo ? '<img class="search-card-thumb" src="' + escape(photo) + '" alt="" decoding="async">' : '') + '</div><div class="search-card-body"><div class="search-card-title">' + highlight(place.name, query) + '</div>' + (place.price ? '<span class="search-card-price">' + escape(place.price) + '</span>' : '') + '<div class="search-card-meta-primary">' + [place.category, place.age, place.district].filter(Boolean).map(escape).join(' · ') + '</div></div>';
        card.querySelector('img')?.addEventListener('error', event => { event.target.hidden = true; });
        grid.append(card);
      });
      options = [...panel.querySelectorAll('a')];
      options.forEach((option, i) => { option.id = panelId + '-option-' + i; option.setAttribute('role', 'option'); option.setAttribute('aria-selected', 'false'); option.tabIndex = -1; });
      panel.querySelector('button').addEventListener('click', () => {
        const target = new URL(form.action, location.href); target.search = params().toString();
        close(); window.location.assign(target.href);
      });
      open();
    }
    function schedule(event) {
      close();
      const query = input.value.trim(); if (!query || event?.isComposing) return;
      const token = generation; status(labels.loading, true);
      timer = setTimeout(async () => {
        controller = new AbortController(); const queryParams = params(); queryParams.set('lang', lang);
        try {
          const response = await fetch('/api/catalog/suggestions/?' + queryParams, {signal:controller.signal});
          if (!response.ok) throw new Error('Suggestions unavailable');
          const data = await response.json();
          if (token !== generation || query !== input.value.trim()) return;
          render(data, query);
        } catch (error) {
          if (token !== generation || error.name === 'AbortError') return;
          status(labels.error, false);
        }
      }, 180);
    }
    input.addEventListener('input', schedule); input.addEventListener('compositionend', schedule); input.addEventListener('focus', schedule);
    // The regular submit button/Enter must use exactly the same filters as hints.
    form?.addEventListener('submit', () => {
      for (const [name, value] of params()) {
        let field = [...form.elements].find(element => element.name === name);
        if (!field) { field = document.createElement('input'); field.type = 'hidden'; field.name = name; form.append(field); }
        field.value = value;
      }
      close();
    }, true);
    document.getElementById('filters-form')?.addEventListener('change', close);
    input.addEventListener('keydown', event => {
      if (panel.hidden) return;
      if (event.key === 'Escape' || event.key === 'Tab') { close(); return; }
      if (!options.length) return;
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault(); active = (active + (event.key === 'ArrowDown' ? 1 : -1) + options.length) % options.length;
        options.forEach((option, i) => { option.classList.toggle('is-selected', i === active); option.setAttribute('aria-selected', String(i === active)); });
        input.setAttribute('aria-activedescendant', options[active].id); options[active].scrollIntoView({block:'nearest'});
      } else if (event.key === 'Enter' && active >= 0) { event.preventDefault(); options[active].click(); }
    });
    document.addEventListener('click', event => { if (event.target !== input && !panel.contains(event.target)) close(); });
  }
  setup('catalog-hero-search-input', 'catalog-search-dropdown');
  setup('catalog-mobile-search', 'catalog-mobile-search-dropdown');
})();
