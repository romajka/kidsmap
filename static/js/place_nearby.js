/* Keep the nearby rail controls in sync with native horizontal scrolling. */
(() => {
  const section = document.querySelector('[data-nearby]');
  if (!section) return;

  const rail = section.querySelector('[data-nearby-rail]');
  const controls = section.querySelector('[data-nearby-controls]');
  const previous = controls.querySelector('[data-nearby-prev]');
  const next = controls.querySelector('[data-nearby-next]');
  const dots = section.querySelector('[data-nearby-dots]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  function stepWidth() {
    const gap = parseFloat(getComputedStyle(rail).columnGap) || 0;
    return rail.firstElementChild.getBoundingClientRect().width + gap;
  }

  function move(button, direction) {
    if (button.getAttribute('aria-disabled') === 'true') return;
    rail.scrollBy({
      left: direction * stepWidth(),
      behavior: reducedMotion.matches ? 'instant' : 'smooth',
    });
  }

  function update() {
    const limit = rail.scrollWidth - rail.clientWidth;
    const hasOverflow = limit > 2;
    const position = rail.scrollLeft;
    controls.hidden = !hasOverflow;
    section.classList.toggle('is-scrollable', hasOverflow);
    previous.setAttribute('aria-disabled', String(position <= 2));
    next.setAttribute('aria-disabled', String(position >= limit - 2));

    const step = stepWidth();
    const count = hasOverflow ? 1 + Math.round(limit / step) : 0;
    const active = Math.round(position / step);
    if (dots.childElementCount !== count) {
      dots.replaceChildren(...Array.from({length: count}, () => document.createElement('span')));
    }
    Array.from(dots.children).forEach((dot, index) => dot.classList.toggle('is-active', index === active));
  }

  previous.addEventListener('click', () => move(previous, -1));
  next.addEventListener('click', () => move(next, 1));
  rail.addEventListener('scroll', update, {passive: true});
  if ('ResizeObserver' in window) new ResizeObserver(update).observe(rail);
  else window.addEventListener('resize', update);
  update();

  if (reducedMotion.matches || !('IntersectionObserver' in window)) {
    section.classList.add('is-in');
    return;
  }
  const entrance = new IntersectionObserver((entries) => {
    if (!entries.some((entry) => entry.isIntersecting)) return;
    section.classList.add('is-in');
    entrance.disconnect();
  }, {threshold: 0.15});
  entrance.observe(section);
})();
