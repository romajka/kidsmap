(() => {
  'use strict';
  const form = document.getElementById('organization_form');
  if (!form) return;

  const hint = form.querySelector('[data-org-dirty-hint]');
  let dirty = false;
  function markDirty(event) {
    if (event.target.closest('.km-return-box, [data-org-preview], #km-publication')) return;
    dirty = true;
    hint?.classList.add('is-visible');
  }
  const whatsappSame = form.querySelector('#id_whatsapp_same_as_phone');
  const whatsappSeparate = form.querySelector('[data-org-separate-whatsapp]');
  if (whatsappSame && whatsappSeparate) {
    const refreshWhatsApp = () => { whatsappSeparate.hidden = whatsappSame.checked; };
    whatsappSame.addEventListener('change', refreshWhatsApp);
    refreshWhatsApp();
  }
  const errorSummary = form.querySelector('[data-org-editor-errors]');
  if (errorSummary?.querySelector('a')) {
    errorSummary.focus();
  } else if (!errorSummary && form.querySelector('.km-orgc--add')) {
    form.querySelector('#id_name_az')?.focus({preventScroll: true});
  }
  form.addEventListener('input', markDirty);
  form.addEventListener('change', markDirty);
  form.addEventListener('submit', event => {
    if (event.submitter?.hasAttribute('data-org-preview-submit')) return;
    dirty = false;
    form.classList.add('is-submitting');
  });
  window.addEventListener('beforeunload', event => {
    if (dirty) {
      event.preventDefault();
      event.returnValue = '';
    }
  });

  function openBranchDetails() {
    if (location.hash === '#km-org-branches') {
      const details = document.getElementById('km-org-details');
      if (details) details.open = true;
    }
  }
  openBranchDetails();
  addEventListener('hashchange', openBranchDetails);
})();
