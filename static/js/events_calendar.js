/* Afisha calendar: pick a day or change month without a full page reload.
   Links stay real URLs (works without JS); here we fetch the same server page
   and swap only the calendar parts, then update the address bar. */
(function () {
  'use strict';
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var cache = new Map();
  var busy = false;

  function root() { return document.querySelector('[data-km-calendar]'); }

  function load(url) {
    if (!cache.has(url)) {
      cache.set(url, fetch(url, { credentials: 'same-origin', headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
        .then(function (html) { return new DOMParser().parseFromString(html, 'text/html'); })
        .catch(function (err) { cache.delete(url); throw err; }));
    }
    return cache.get(url);
  }

  function rescan(scope) {
    if (window.KidsMapTimers) window.KidsMapTimers.scan(scope);
    stagger(scope);
  }

  function stagger(scope) {
    if (reduce) return;
    Array.prototype.forEach.call((scope || document).querySelectorAll('[data-km-stagger] > *'), function (el, i) {
      el.style.setProperty('--km-i', Math.min(i, 8));
      el.classList.remove('km-in');
      void el.offsetWidth;
      el.classList.add('km-in');
    });
  }

  function syncModeLinks(doc) {
    ['#events-mode', '.events-quick-chips', '#events-filters'].forEach(function (sel) {
      var fresh = doc.querySelector(sel), current = document.querySelector(sel);
      if (fresh && current) current.replaceWith(fresh);
    });
  }

  function selectDay(link) {
    var cal = root();
    var url = link.href;
    cal.querySelectorAll('.km-cal__cell.is-selected').forEach(function (c) { c.classList.remove('is-selected'); });
    cal.querySelectorAll('.km-cal__day[aria-current]').forEach(function (a) { a.removeAttribute('aria-current'); });
    link.setAttribute('aria-current', 'date');
    link.closest('.km-cal__cell').classList.add('is-selected');
    var list = document.getElementById('events-day-list');
    list.classList.add('is-loading');
    return load(url).then(function (doc) {
      var fresh = doc.getElementById('events-day-list');
      if (!fresh) { location.href = url; return; }
      list.innerHTML = fresh.innerHTML;
      list.classList.remove('is-loading');
      syncModeLinks(doc);
      history.pushState({ kmCal: true }, '', url);
      rescan(list);
      if (window.matchMedia('(max-width: 899px)').matches) {
        list.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
      }
    }).catch(function () { location.href = url; });
  }

  function changeMonth(link, direction) {
    var cal = root();
    var url = link.href;
    cal.classList.add('is-leaving', direction > 0 ? 'to-left' : 'to-right');
    return load(url).then(function (doc) {
      var fresh = doc.querySelector('[data-km-calendar]');
      if (!fresh) { location.href = url; return; }
      fresh.classList.add('is-entering', direction > 0 ? 'from-right' : 'from-left');
      cal.replaceWith(fresh);
      syncModeLinks(doc);
      history.pushState({ kmCal: true }, '', url);
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { fresh.classList.remove('is-entering', 'from-right', 'from-left'); });
      });
      rescan(fresh);
    }).catch(function () { location.href = url; });
  }

  document.addEventListener('click', function (event) {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    var cal = root();
    if (!cal || !cal.contains(event.target)) return;
    var day = event.target.closest('a.km-cal__day');
    var nav = event.target.closest('a[data-events-month], a.km-cal__today');
    if (!day && !nav) return;
    event.preventDefault();
    if (busy) return;
    busy = true;
    var job = day ? selectDay(day)
      : changeMonth(nav, nav.dataset.eventsMonth === 'previous' ? -1 : nav.dataset.eventsMonth === 'next' ? 1 : 0);
    Promise.resolve(job).then(function () { busy = false; }, function () { busy = false; });
  });

  // Prefetch on hover / touch so the swap feels instant.
  ['mouseover', 'touchstart', 'focusin'].forEach(function (type) {
    document.addEventListener(type, function (event) {
      var link = event.target.closest && event.target.closest('[data-km-calendar] a.km-cal__day, [data-km-calendar] a[data-events-month]');
      if (link) load(link.href).catch(function () {});
    }, { passive: true });
  });

  // Arrow keys move between days like a real date grid.
  document.addEventListener('keydown', function (event) {
    var link = event.target.closest && event.target.closest('a.km-cal__day');
    if (!link) return;
    var step = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[event.key];
    if (!step) return;
    var days = Array.prototype.slice.call(root().querySelectorAll('a.km-cal__day'));
    var next = days[days.indexOf(link) + step];
    if (next) { event.preventDefault(); next.focus(); }
  });

  if (root() && !history.state) history.replaceState({ kmCal: true }, '', location.href);
  window.addEventListener('popstate', function (event) {
    if (event.state && event.state.kmCal) location.reload();
  });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { stagger(document); });
  else stagger(document);
})();
