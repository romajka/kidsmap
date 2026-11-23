/* Event detail: the sticky mobile registration bar. */
(() => {
  const bar = document.querySelector('[data-event-mobile-registration]');
  const primary = document.querySelector('[data-event-registration]');
  if (bar && primary && 'IntersectionObserver' in window) {
    document.querySelector('.event-detail-page')?.classList.add('event-detail-page--registration');
    document.body.appendChild(bar);
    const mobile = window.matchMedia('(max-width: 767px)');
    let primaryVisible = true;
    const update = () => { bar.hidden = primaryVisible || !mobile.matches; };
    const observer = new IntersectionObserver(([entry]) => {
      primaryVisible = entry.isIntersecting;
      update();
    });
    observer.observe(primary);
    mobile.addEventListener('change', update);
  }

  // Photos open in the shared viewer (event_media.js).
})();
