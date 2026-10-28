/* Keep the chosen registration channel reachable while reading on a phone. */
(() => {
  const bar = document.querySelector('[data-event-mobile-registration]');
  const primary = document.querySelector('[data-event-registration]');
  if (!bar || !primary || !window.IntersectionObserver) return;
  document.querySelector('.event-detail-page')?.classList.add('event-detail-page--registration');
  document.body.appendChild(bar); // Keep fixed positioning outside animated/transformed panels.
  let visible = true;
  const update = () => { bar.hidden = visible || window.innerWidth >= 768; };
  const observer = new IntersectionObserver(entries => { visible = entries[0].isIntersecting; update(); });
  observer.observe(primary);
  window.addEventListener('resize', update, {passive: true});
})();
