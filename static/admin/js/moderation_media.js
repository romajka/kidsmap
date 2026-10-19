(() => {
  const init = () => document.querySelectorAll('.km-hub-media-comparison [data-km-hub-image]').forEach(image => {
    const unavailable = () => {
      image.closest('a').hidden = true;
      image.closest('figure').querySelector('[data-km-hub-image-fallback]').hidden = false;
    };
    image.addEventListener('error', unavailable, {once: true});
    if (image.complete && !image.naturalWidth) unavailable();
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once: true});
  else init();
})();
