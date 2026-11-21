/* Home afisha rail: arrow scrolling, edge state and a one-time staggered reveal. */
(function () {
  'use strict';
  var section = document.querySelector('[data-km-home-afisha]');
  if (!section) return;
  var track = section.querySelector('[data-km-rail]');
  var prev = section.querySelector('[data-km-rail-prev]');
  var next = section.querySelector('[data-km-rail-next]');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function step() {
    var item = track.querySelector('.km-home-afisha__item');
    return item ? item.getBoundingClientRect().width + 16 : track.clientWidth * 0.8;
  }
  // Progress dots: one per event, the first fully visible card is active.
  var items = Array.prototype.slice.call(track.querySelectorAll('.km-home-afisha__item'));
  var dots = document.createElement('div');
  dots.className = 'km-home-afisha__dots';
  dots.setAttribute('aria-hidden', 'true');
  items.forEach(function (item, i) {
    var dot = document.createElement('button');
    dot.type = 'button';
    dot.tabIndex = -1;
    dot.addEventListener('click', function () { track.scrollTo({ left: item.offsetLeft - track.offsetLeft - parseFloat(getComputedStyle(track).paddingLeft || 0), behavior: reduce ? 'auto' : 'smooth' }); });
    dots.appendChild(dot);
  });
  track.parentNode.appendChild(dots);
  function edges() {
    var max = track.scrollWidth - track.clientWidth - 2;
    prev.disabled = track.scrollLeft <= 2;
    next.disabled = track.scrollLeft >= max;
    section.classList.toggle('is-scrollable', max > 2);
    section.classList.toggle('is-at-start', track.scrollLeft <= 2);
    section.classList.toggle('is-at-end', track.scrollLeft >= max);
    var left = track.getBoundingClientRect().left, active = 0;
    items.forEach(function (item, i) { if (item.getBoundingClientRect().left - left < 40 && i > active - 1) active = i; });
    if (track.scrollLeft >= max) active = items.length - 1;
    Array.prototype.forEach.call(dots.children, function (dot, i) { dot.classList.toggle('is-active', i === active); });
  }
  prev.addEventListener('click', function () { track.scrollBy({ left: -step(), behavior: reduce ? 'auto' : 'smooth' }); });
  next.addEventListener('click', function () { track.scrollBy({ left: step(), behavior: reduce ? 'auto' : 'smooth' }); });
  track.addEventListener('scroll', edges, { passive: true });
  window.addEventListener('resize', edges);
  edges();

  if (reduce || !('IntersectionObserver' in window)) { section.classList.add('is-revealed'); return; }
  Array.prototype.forEach.call(track.children, function (el, i) { el.style.setProperty('--km-i', Math.min(i, 6)); });
  var io = new IntersectionObserver(function (entries) {
    if (entries.some(function (e) { return e.isIntersecting; })) {
      section.classList.add('is-revealed');
      io.disconnect();
    }
  }, { threshold: 0.18 });
  io.observe(section);
})();
