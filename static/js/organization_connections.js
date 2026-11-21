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
  // Relationship type as two choice cards (the native select stays the source of truth).
  const kind = document.getElementById('org-kind');
  if (kind && !kind.dataset.kmCards) {
    kind.dataset.kmCards = '1';
    const icons = {
      business: '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><rect x="3" y="7.5" width="18" height="12" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M9 7.5V6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v1.5M3 12.5h18" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
      informational: '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 11v6M12 7.5v.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    };
    const group = document.createElement('div');
    group.className = 'org-connect__kinds';
    group.setAttribute('role', 'radiogroup');
    group.setAttribute('aria-labelledby', 'org-kind-label');
    const label = document.querySelector('label[for="org-kind"]');
    if (label) label.id = label.id || 'org-kind-label';
    const options = Array.from(kind.options).filter((option) => option.value);
    options.forEach((option) => {
      const [title, ...rest] = option.textContent.split(':');
      const card = document.createElement('label');
      card.className = 'org-connect__kind';
      card.dataset.kind = option.value;
      // form="" keeps the visual radios out of the submitted data.
      card.innerHTML = '<input type="radio" name="org-kind-card" form="org-kind-none" value="' + option.value + '">' +
        '<span class="org-connect__kind-icon">' + (icons[option.value] || '') + '</span>' +
        '<span class="org-connect__kind-text"><b></b><small></small></span><span class="org-connect__kind-check" aria-hidden="true"></span>';
      card.querySelector('b').textContent = title.trim();
      card.querySelector('small').textContent = rest.join(':').trim();
      const radio = card.querySelector('input');
      radio.checked = kind.value === option.value;
      radio.addEventListener('change', () => {
        kind.value = option.value;
        kind.dispatchEvent(new Event('change', { bubbles: true }));
        group.classList.remove('is-missing');
      });
      group.appendChild(card);
    });
    kind.classList.add('org-connect__sr');
    kind.tabIndex = -1;
    kind.setAttribute('aria-hidden', 'true');
    kind.insertAdjacentElement('afterend', group);
    if (label) label.removeAttribute('for');
    // The hidden select would get the browser's own bubble; show it on the cards instead.
    kind.addEventListener('invalid', (event) => {
      event.preventDefault();
      group.classList.remove('is-missing');
      void group.offsetWidth;
      group.classList.add('is-missing');
      group.querySelector('input')?.focus();
    });
    kind.form?.addEventListener('submit', (event) => {
      if (kind.required && !kind.value) {
        event.preventDefault();
        group.classList.remove('is-missing');
        void group.offsetWidth;
        group.classList.add('is-missing');
        group.querySelector('input')?.focus();
      }
    });
    if (document.querySelector('[data-error-summary]') && !kind.value) group.classList.add('is-missing');
  }
  document.querySelector('[data-error-summary]')?.focus();
})();
