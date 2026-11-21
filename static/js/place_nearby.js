/* Place page: "More places nearby" rail — arrows, dots, edge fades, reveal on scroll. */
(function () {
  'use strict';
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function init(section) {
    if (section.__kmNearby) return;
    section.__kmNearby = true;
    var rail = section.querySelector('[data-nearby-rail]');
    var prev = section.querySelector('[data-nearby-prev]');
    var next = section.querySelector('[data-nearby-next]');
    var dotsBox = section.querySelector('[data-nearby-dots]');
    if (!rail) return;
    var items = Array.prototype.slice.call(rail.children);
    var dots = items.map(function (item) {
      var dot = document.createElement('button');
      dot.type = 'button';
      dot.tabIndex = -1;
      dot.addEventListener('click', function () { go(item); });
      if (dotsBox) dotsBox.appendChild(dot);
      return dot;
    });
    function go(item) {
      rail.scrollTo({ left: item.offsetLeft - rail.offsetLeft - (parseFloat(getComputedStyle(rail).paddingLeft) || 0), behavior: reduce ? 'auto' : 'smooth' });
    }
    function step(dir) {
      var width = items[0] ? items[0].getBoundingClientRect().width + 16 : rail.clientWidth;
      rail.scrollBy({ left: dir * Math.max(width, rail.clientWidth * 0.8), behavior: reduce ? 'auto' : 'smooth' });
    }
    function update() {
      var max = rail.scrollWidth - rail.clientWidth - 2;
      var x = rail.scrollLeft;
      section.classList.toggle('is-scrollable', max > 2);
      section.classList.toggle('is-at-start', x <= 2);
      section.classList.toggle('is-at-end', x >= max);
      if (prev) prev.disabled = x <= 2;
      if (next) next.disabled = x >= max;
      var left = rail.getBoundingClientRect().left, active = 0;
      items.forEach(function (item, i) { if (item.getBoundingClientRect().left - left < 40) active = i; });
      if (x >= max) active = items.length - 1;
      dots.forEach(function (dot, i) { dot.classList.toggle('is-active', i === active); });
    }
    if (prev) prev.addEventListener('click', function () { step(-1); });
    if (next) next.addEventListener('click', function () { step(1); });
    var raf = 0;
    rail.addEventListener('scroll', function () { cancelAnimationFrame(raf); raf = requestAnimationFrame(update); }, { passive: true });
    window.addEventListener('resize', update);
    update();
    // Cards rise in when the block scrolls into view (once).
    if (reduce || !('IntersectionObserver' in window)) { section.classList.add('is-in'); return; }
    var io = new IntersectionObserver(function (entries) {
      if (entries.some(function (entry) { return entry.isIntersecting; })) { section.classList.add('is-in'); io.disconnect(); }
    }, { threshold: 0.15 });
    io.observe(section);
  }
  function boot() { Array.prototype.forEach.call(document.querySelectorAll('[data-nearby]'), init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
