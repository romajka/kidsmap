/* "For specialists" landing: reveal on scroll and count-up numbers.
   Content is fully visible without this script; it only adds motion. */
(() => {
  'use strict';
  const root = document.querySelector('.spl');
  if (!root) return;
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (still || !('IntersectionObserver' in window)) return;

  document.documentElement.classList.add('js-spl');

  function countUp(el) {
    const target = parseInt(el.dataset.count, 10);
    if (!target || target < 10) return;
    const start = performance.now(), dur = 1100;
    const fmt = new Intl.NumberFormat(document.documentElement.lang || undefined);
    const tick = now => {
      const k = Math.min(1, (now - start) / dur), e = 1 - Math.pow(1 - k, 3);
      el.textContent = fmt.format(Math.round(target * e));
      if (k < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  const io = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('is-in');
      entry.target.querySelectorAll('[data-count]').forEach(countUp);
      io.unobserve(entry.target);
    }
  }, { rootMargin: '0px 0px -8% 0px', threshold: .12 });

  root.querySelectorAll('.spl-reveal, .spl-steps-wrap').forEach(el => io.observe(el));
})();
