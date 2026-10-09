(() => {
  'use strict';
  const selection = document.querySelector('[data-selection-form]');
  const refresh = () => {
    const count = selection.querySelectorAll('input[name="place_ids"]:checked,input[type="hidden"][name="place_ids"]').length;
    selection.querySelector('[data-selection-count]').textContent = count;
    selection.querySelector('[data-preview]').disabled = count === 0 || count > 100;
  };
  if (selection) { selection.addEventListener('change', refresh); refresh(); }
  const form = document.querySelector('[data-confirm-form]');
  if (form) form.addEventListener('submit', () => {
    // Keep submitter enabled until the browser has captured its name/value.
    const status = form.querySelector('[data-submit-status]');
    if (status) status.textContent = status.dataset.pending;
    setTimeout(() => { form.querySelector('button[type="submit"]').disabled = true; }, 0);
  });
  window.addEventListener('pageshow', () => {
    if (form) { const button = form.querySelector('button[type="submit"]'); button.disabled = button.hasAttribute('data-no-executable'); }
  });
  document.querySelector('[data-error-summary]')?.focus();
})();
