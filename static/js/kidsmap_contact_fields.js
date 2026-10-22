/* Contact choices never rewrite or truncate user input. */
(() => {
  'use strict';
  function mount() {
    document.querySelectorAll('select[name="whatsapp_mode"]').forEach(mode => {
      const form = mode.form;
      const number = form?.elements.namedItem('whatsapp_number');
      if (!number) return;
      const wrapper = number.closest('[data-pw-field], [data-pf-field], .form-row');
      if (!wrapper) return;
      function update() {
        const hasError = Boolean(wrapper.querySelector('.pw-error, .km-pf-field__error, .errorlist'));
        wrapper.hidden = mode.value !== 'separate' && !hasError;
        number.setAttribute('aria-required', mode.value === 'separate' ? 'true' : 'false');
        // Keep the value enabled: switching modes must not discard saved contacts.
      }
      mode.addEventListener('change', update);
      form.addEventListener('reset', () => setTimeout(update, 0));
      update();
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
