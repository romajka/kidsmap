/* Organization public page: count-up stats, scroll reveal, scrollspy for the
   section tabs, direction chips wired to the branch filter, and a lazily
   loaded branch map synced with the cards. Progressive: the page works fully
   without it. */
(() => {
  'use strict';
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const doc = document;

  // Scroll reveal ---------------------------------------------------------
  const reveal = doc.querySelectorAll('[data-orgv-reveal], .public-section, .public-branch-item, .public-review-card, .public-program-card');
  if ('IntersectionObserver' in window && !reduce) {
    doc.documentElement.classList.add('orgv-js');
    const io = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('is-in'); io.unobserve(entry.target); }
    }), { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    reveal.forEach(el => { el.classList.add('orgv-reveal'); io.observe(el); });
  }

  // Count-up --------------------------------------------------------------
  const counters = doc.querySelectorAll('[data-orgv-count]');
  if ('IntersectionObserver' in window && !reduce) {
    const io = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      io.unobserve(entry.target);
      const el = entry.target, end = Number(el.dataset.orgvCount) || 0;
      if (end < 2) return;
      const t0 = performance.now(), dur = Math.min(1100, 400 + end * 40);
      const step = now => {
        const k = Math.min(1, (now - t0) / dur);
        el.textContent = Math.round(end * (1 - Math.pow(1 - k, 3)));
        if (k < 1) requestAnimationFrame(step);
      };
      el.textContent = '0';
      requestAnimationFrame(step);
    }), { threshold: 0.6 });
    counters.forEach(el => io.observe(el));
  }

  // Scrollspy for the sticky section tabs ---------------------------------
  const links = [...doc.querySelectorAll('.public-entity-nav__link[href^="#"]')];
  const targets = links.map(a => doc.getElementById(a.getAttribute('href').slice(1))).filter(Boolean);
  if (links.length && 'IntersectionObserver' in window) {
    const setActive = id => links.forEach(a => {
      const on = a.getAttribute('href') === '#' + id;
      a.classList.toggle('is-active', on);
      if (on) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
    });
    const spy = new IntersectionObserver(entries => {
      const visible = entries.filter(e => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (visible[0]) setActive(visible[0].target.id);
    }, { rootMargin: '-30% 0px -60% 0px' });
    targets.forEach(t => spy.observe(t));
  }

  // Mobile action bar: shown once the hero scrolls away.
  const mbar = doc.querySelector('[data-orgv-mbar]');
  const hero = doc.querySelector('.public-org-hero-card');
  if (mbar && hero && 'IntersectionObserver' in window) {
    let heroGone = false;
    const update = () => {
      const on = heroGone;
      mbar.classList.toggle('is-visible', on);
      doc.body.classList.toggle('orgv-mbar-on', on);
      mbar.setAttribute('aria-hidden', String(!on));
      mbar.querySelectorAll('a').forEach(a => a.tabIndex = on ? 0 : -1);
    };
    new IntersectionObserver(([e]) => { heroGone = !e.isIntersecting; update(); }).observe(hero);
  }

  // Direction chips -> branch activity filter -----------------------------
  const chips = doc.querySelectorAll('[data-orgv-activity]');
  const activitySelect = doc.getElementById('branch-activity-filter');
  chips.forEach(chip => chip.addEventListener('click', () => {
    const value = chip.dataset.orgvActivity;
    const active = chip.getAttribute('aria-pressed') === 'true';
    chips.forEach(c => c.setAttribute('aria-pressed', 'false'));
    const next = active ? '' : value;
    if (!active) chip.setAttribute('aria-pressed', 'true');
    if (activitySelect) {
      const option = [...doc.querySelectorAll('#custom-select-activity .km-custom-select__option')].find(o => o.dataset.value === next);
      if (option) option.click();
      else { activitySelect.value = next; activitySelect.dispatchEvent(new Event('change', { bubbles: true })); }
    }
    const branches = doc.getElementById('branches');
    if (branches) branches.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
  }));

  // Branch map ------------------------------------------------------------
  const wrap = doc.querySelector('[data-orgv-branches]');
  const mapBox = doc.querySelector('[data-orgv-map]');
  const dataEl = doc.getElementById('orgv-map-points');
  if (!wrap || !mapBox || !dataEl) return;
  let points = [];
  try { points = JSON.parse(dataEl.textContent) || []; } catch (_) { points = []; }
  if (!points.length) return;

  doc.querySelectorAll('[data-orgv-view]').forEach(btn => btn.addEventListener('click', () => {
    doc.querySelectorAll('[data-orgv-view]').forEach(b => { b.classList.toggle('is-active', b === btn); b.setAttribute('aria-selected', String(b === btn)); });
    wrap.dataset.view = btn.dataset.orgvView;
    if (map) setTimeout(() => map.invalidateSize(), 320);
  }));

  const LEAFLET_CSS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
  const LEAFLET_JS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
  const load = (tag, attrs) => new Promise((resolve, reject) => {
    const el = doc.createElement(tag);
    Object.assign(el, attrs);
    el.crossOrigin = 'anonymous';
    el.onload = resolve; el.onerror = reject;
    doc.head.appendChild(el);
  });
  let map = null;
  const markers = new Map();

  const start = async () => {
    try {
      if (!window.L) {
        await Promise.all([
          load('link', { rel: 'stylesheet', href: LEAFLET_CSS, integrity: 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=' }),
          load('script', { src: LEAFLET_JS, integrity: 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=' }),
        ]);
      }
    } catch (_) {
      mapBox.classList.add('is-failed');
      return;
    }
    const L = window.L;
    const canvas = mapBox.querySelector('[data-orgv-map-canvas]');
    map = L.map(canvas, { scrollWheelZoom: false, zoomControl: true, attributionControl: true });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);
    const bounds = [];
    points.forEach((p, index) => {
      const icon = L.divIcon({
        className: 'orgv-pin',
        html: `<span class="orgv-pin__dot" style="--d:${index * 80}ms"><span class="orgv-pin__shape"><b>${index + 1}</b></span></span>`,
        iconSize: [40, 48], iconAnchor: [20, 46], popupAnchor: [0, -42],
      });
      const marker = L.marker([p.lat, p.lng], { icon, title: p.name, riseOnHover: true }).addTo(map);
      const safe = s => String(s || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
      marker.bindPopup(`<a class="orgv-popup" href="${safe(p.url)}">${p.image ? `<img src="${safe(p.image)}" alt="">` : ''}<strong>${safe(p.name)}</strong><span>${safe(p.address)}</span></a>`);
      marker.on('mouseover', () => highlight(p.id, true));
      marker.on('mouseout', () => highlight(p.id, false));
      marker.on('click', () => {
        const card = doc.querySelector(`.public-branch-item[data-branch-id="${p.id}"]`);
        if (card && wrap.dataset.view !== 'map') card.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'nearest' });
      });
      markers.set(String(p.id), marker);
      bounds.push([p.lat, p.lng]);
    });
    const fit = () => { if (bounds.length === 1) map.setView(bounds[0], 15); else map.fitBounds(bounds, { padding: [90, 90], maxZoom: 15 }); };
    fit();
    // The container may still be settling (sticky layout, fonts); refit once it has its final size.
    setTimeout(() => { map.invalidateSize(); fit(); }, 250);
    if ('ResizeObserver' in window) new ResizeObserver(() => map.invalidateSize()).observe(mapBox);
    mapBox.classList.add('is-ready');
    syncFilter();
  };

  const highlight = (id, on) => {
    const card = doc.querySelector(`.public-branch-item[data-branch-id="${id}"]`);
    if (card) card.classList.toggle('is-hot', on);
    const marker = markers.get(String(id));
    const el = marker && marker.getElement();
    if (el) el.classList.toggle('is-hot', on);
  };
  doc.querySelectorAll('.public-branch-item[data-branch-id]').forEach(card => {
    card.addEventListener('mouseenter', () => highlight(card.dataset.branchId, true));
    card.addEventListener('mouseleave', () => highlight(card.dataset.branchId, false));
    card.addEventListener('focusin', () => highlight(card.dataset.branchId, true));
    card.addEventListener('focusout', () => highlight(card.dataset.branchId, false));
  });

  // Filtered-out branches disappear from the map as well.
  const syncFilter = () => {
    if (!map) return;
    const shown = [];
    doc.querySelectorAll('.public-branch-item[data-branch-id]').forEach(card => {
      const marker = markers.get(card.dataset.branchId);
      if (!marker) return;
      if (card.hidden) { if (map.hasLayer(marker)) map.removeLayer(marker); }
      else { if (!map.hasLayer(marker)) marker.addTo(map); shown.push(marker.getLatLng()); }
    });
    if (shown.length > 1) map.flyToBounds(shown, { padding: [90, 90], maxZoom: 15, duration: reduce ? 0 : 0.6 });
    else if (shown.length === 1) map.flyTo(shown[0], 15, { duration: reduce ? 0 : 0.6 });
  };
  const list = doc.getElementById('public-branches-list');
  if (list && 'MutationObserver' in window) {
    let pending = 0;
    new MutationObserver(() => { cancelAnimationFrame(pending); pending = requestAnimationFrame(syncFilter); })
      .observe(list, { attributes: true, subtree: true, attributeFilter: ['hidden'] });
  }

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
      if (entries.some(e => e.isIntersecting)) { io.disconnect(); start(); }
    }, { rootMargin: '300px' });
    io.observe(mapBox);
  } else {
    start();
  }
})();
