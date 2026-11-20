(() => {
  'use strict';
  const dialog = document.querySelector('[data-document-dialog]');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  const section = dialog.closest('section');
  const body = dialog.querySelector('[data-document-body]');
  const loading = dialog.querySelector('[data-document-loading]');
  const error = dialog.querySelector('[data-document-error]');
  const retry = dialog.querySelector('[data-document-retry]');
  let controller;
  let currentUrl;
  let opener;
  let failedPage;

  async function openPage(url, focusPager) {
    controller?.abort();
    controller = new AbortController();
    const {signal} = controller;
    const fromRetry = document.activeElement === retry;
    const zoomed = Boolean(body.querySelector('.sp-doc-zoom input:checked'));
    body.setAttribute('aria-busy', 'true');
    loading.hidden = false;
    error.hidden = true;
    try {
      const response = await fetch(url, {signal, cache: 'no-store', credentials: 'same-origin'});
      if (!response.ok || new URL(response.url).origin !== location.origin) throw new Error();
      const html = new DOMParser().parseFromString(await response.text(), 'text/html');
      const reader = html.querySelector('[data-document-reader]');
      if (!reader) throw new Error();
      if (signal.aborted) return;
      for (const link of reader.querySelectorAll('.sp-doc-pager a')) {
        link.href = new URL(link.getAttribute('href'), response.url).href;
      }
      const nextReader = document.importNode(reader, true);
      const image = nextReader.querySelector('.sp-doc-sheet img');
      if (image?.decode) await image.decode();
      if (signal.aborted) return;
      currentUrl = response.url;
      const zoom = nextReader.querySelector('.sp-doc-zoom input');
      if (zoom) zoom.checked = zoomed;
      if (focusPager) nextReader.dataset.pageTurn = focusPager;
      body.replaceChildren(nextReader);
      failedPage = undefined;
      if (focusPager) {
        const focus = body.querySelector('[rel="' + focusPager + '"]') || body.querySelector('.sp-doc-pager a') || body.querySelector('h1');
        focus?.focus({preventScroll: true});
      } else if (fromRetry) {
        body.querySelector('h1')?.focus({preventScroll: true});
      }
    } catch {
      if (!signal.aborted) {
        failedPage = {url, focusPager};
        error.hidden = false;
        retry?.focus({preventScroll: true});
      }
    } finally {
      if (!signal.aborted) {
        loading.hidden = true;
        body.removeAttribute('aria-busy');
      }
    }
  }

  section.addEventListener('click', event => {
    if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.shiftKey || event.altKey || event.metaKey) return;
    const link = event.target.closest('a');
    if (!link) return;
    if (link.matches('[data-document-open]')) {
      event.preventDefault();
      opener = link;
      dialog.showModal();
      openPage(link.href);
    } else if (body.contains(link) && ['prev', 'next'].includes(link.rel)) {
      event.preventDefault();
      openPage(new URL(link.getAttribute('href'), currentUrl), link.rel);
    }
  });
  retry?.addEventListener('click', () => {
    if (failedPage) openPage(failedPage.url, failedPage.focusPager);
  });
  dialog.addEventListener('keydown', event => {
    const direction = {ArrowRight: 'next', ArrowLeft: 'prev'}[event.key];
    if (!direction || event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (body.hasAttribute('aria-busy') || body.querySelector('.sp-doc-zoom input:checked')) return;
    const page = body.querySelector('.sp-doc-pager [rel="' + direction + '"]');
    if (page) {
      event.preventDefault();
      openPage(page.href, direction);
    }
  });
  dialog.addEventListener('close', () => {
    controller?.abort();
    failedPage = undefined;
    loading.hidden = true;
    error.hidden = true;
    body.removeAttribute('aria-busy');
    body.replaceChildren();
    opener?.focus({preventScroll: true});
  });
  for (const link of section.querySelectorAll('[data-document-open]')) link.setAttribute('aria-haspopup', 'dialog');
  if ('IntersectionObserver' in window && window.matchMedia('(prefers-reduced-motion: no-preference)').matches) {
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add('is-revealed');
        observer.unobserve(entry.target);
      }
    }, {threshold: .12});
    for (const preview of section.querySelectorAll('.sp-doc-thumb')) observer.observe(preview);
  }
  for (const image of section.querySelectorAll('.sp-doc-thumb img')) {
    image.addEventListener('error', () => { image.hidden = true; });
    if (image.complete && !image.naturalWidth) image.hidden = true;
  }
})();
