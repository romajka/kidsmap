(() => {
  'use strict';
  const form = document.querySelector('[data-recovery-form]');
  if (form) {
    let submitting = false;
    form.addEventListener('submit', event => {
      if (submitting) { event.preventDefault(); return; }
      submitting = true;
      form.setAttribute('aria-busy', 'true');
      form.querySelector('[data-recovery-pending]').hidden = false;
      setTimeout(() => { form.querySelector('button').disabled = true; }, 0);
    });
    window.addEventListener('pageshow', () => {
      submitting = false;
      form.removeAttribute('aria-busy');
      form.querySelector('button').disabled = false;
      form.querySelector('[data-recovery-pending]').hidden = true;
    });
  }
  (document.querySelector('[data-recovery-error]') || document.querySelector('[data-recovery-result]'))?.focus();
})();
