(() => {
  'use strict';
  if (!document.body.hasAttribute('data-site-preview')) return;
  const feedback = document.querySelector('[data-site-preview-feedback]');
  function inform() { if (feedback) feedback.hidden = false; }
  document.addEventListener('submit', event => {
    if (event.target.method.toLowerCase() !== 'post') return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const favorite = event.target.querySelector('[aria-pressed]');
    if (favorite && event.target.matches('[data-like-form]')) {
      const pressed = favorite.getAttribute('aria-pressed') !== 'true';
      favorite.setAttribute('aria-pressed', String(pressed));
      favorite.classList.toggle('active', pressed);
    }
    inform();
  }, true);
  document.addEventListener('click', event => {
    const favorite = event.target.closest('.detail-fav-btn');
    if (favorite) {
      event.preventDefault();event.stopImmediatePropagation();
      const pressed = favorite.getAttribute('aria-pressed') !== 'true';
      favorite.setAttribute('aria-pressed',String(pressed));
      favorite.classList.toggle('active',pressed);inform();return;
    }
    if (event.target.closest('.detail-page a[href=""]')) {
      event.preventDefault();event.stopImmediatePropagation();inform();return;
    }
    if (!event.target.closest('[data-review-vote]')) return;
    event.preventDefault();event.stopImmediatePropagation();inform();
  }, true);
})();
