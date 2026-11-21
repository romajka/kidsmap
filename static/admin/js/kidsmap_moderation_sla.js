/* Moderation deadlines: health counters count up once on load. */
(function () {
  'use strict';
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  Array.prototype.forEach.call(document.querySelectorAll('.km-sla [data-km-count]'), function (el, index) {
    var target = parseInt(el.getAttribute('data-km-count'), 10) || 0;
    if (target < 2) return;
    var start = null, duration = 700 + Math.min(target, 50) * 6, delay = 150 + index * 60;
    el.textContent = '0';
    setTimeout(function () {
      requestAnimationFrame(function step(now) {
        if (start === null) start = now;
        var t = Math.min(1, (now - start) / duration);
        el.textContent = String(Math.round(target * (1 - Math.pow(1 - t, 3))));
        if (t < 1) requestAnimationFrame(step);
      });
    }, delay);
  });
})();
