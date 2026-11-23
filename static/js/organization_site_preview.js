'use strict';

document.querySelector('[data-organization-preview-close]')?.addEventListener('click', event => {
  event.preventDefault();
  const editor = event.currentTarget.href;
  window.close();
  setTimeout(() => location.assign(editor), 150);
});
