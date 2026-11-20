/* Event detail interactions progressively enhance the ordinary links. */
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

  const dialog = document.querySelector('[data-event-photo-dialog]');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  const image = dialog.querySelector('img');
  const title = dialog.querySelector('h2');
  const eventName = title.textContent;
  let opener = null;

  document.querySelectorAll('[data-event-photo]').forEach(link => {
    link.addEventListener('click', event => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      opener = link;
      title.textContent = link.closest('figure')?.querySelector('figcaption > span')?.textContent || eventName;
      image.src = link.href;
      image.alt = link.querySelector('img')?.alt || title.textContent;
      dialog.showModal();
    });
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => {
    image.removeAttribute('src');
    opener?.focus({preventScroll: true});
  });
})();
