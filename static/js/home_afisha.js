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
  function edges() {
    var max = track.scrollWidth - track.clientWidth - 2;
    prev.disabled = track.scrollLeft <= 2;
    next.disabled = track.scrollLeft >= max;
    section.classList.toggle('is-scrollable', max > 2);
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
