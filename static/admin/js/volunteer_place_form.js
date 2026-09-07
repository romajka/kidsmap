/* Presentation only. All saves use the restricted proposal endpoint. */
(() => {
  const form = document.querySelector('[data-volunteer-admin-form]');
  if (!form) return;
  const sections = [...form.querySelectorAll('[data-place-section]')];
  const setOpen = (section, open) => {
    section.querySelector('[data-place-section-toggle]').setAttribute('aria-expanded', String(open));
    section.querySelector('.km-pf-section__body').hidden = !open;
    if (open) window.dispatchEvent(new Event('resize'));
  };
  sections.forEach(section => section.querySelector('[data-place-section-toggle]').addEventListener('click', () => setOpen(section, section.querySelector('.km-pf-section__body').hidden)));
  form.querySelector('[data-editor-collapse]').addEventListener('click', () => sections.forEach(s => setOpen(s, false)));
  form.querySelector('[data-editor-expand]').addEventListener('click', () => sections.forEach(s => setOpen(s, true)));
  const tabs = [...form.querySelectorAll('[data-pf-langtab]')];
  const selectLanguage = (code, focus = false) => {
    tabs.forEach(tab => {
      const active = tab.dataset.pfLangtab === code;
      tab.classList.toggle('is-active', active);
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
      if (active && focus) tab.focus();
    });
    form.querySelectorAll('[data-pf-langpane]').forEach(pane => {
      pane.hidden = pane.dataset.pfLangpane !== code;
      pane.classList.toggle('is-hidden', pane.hidden);
    });
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectLanguage(tab.dataset.pfLangtab));
    tab.addEventListener('keydown', event => {
      if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      selectLanguage(tabs[next].dataset.pfLangtab, true);
    });
  });
  selectLanguage('az');
  const navigate = () => {
    let hash;
    try { hash = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    let target;
    if (hash.startsWith('field=')) {
      const name = hash.slice(6);
      target = form.elements.namedItem(name === 'region' ? 'district' : name);
      if (!target || !target.closest) return;
      const pane = target.closest('[data-pf-langpane]');
      if (pane) selectLanguage(pane.dataset.pfLangpane);
      let parent = target.parentElement;
      while (parent && parent !== form) { if (parent.tagName === 'DETAILS') parent.open = true; parent = parent.parentElement; }
      if (target.type === 'hidden') target = target.closest('[data-tariff-editor],[data-pf-field],[data-km-schedule-editor]') || target;
    } else target = sections.find(section => section.id === hash);
    if (!target) return;
    const section = target.closest('[data-place-section]');
    if (section) setOpen(section, true);
    target.scrollIntoView({block:'center'});
    if (target.type !== 'hidden') { if (!target.matches('input,select,textarea,button,a')) target.tabIndex = -1; target.focus({preventScroll:true}); }
    form.querySelectorAll('[data-place-step-link]').forEach(link => link.classList.toggle('is-active', link.hash === '#' + section?.id));
  };
  window.addEventListener('hashchange', navigate);
  form.querySelectorAll('a[href^="#"]').forEach(link => link.addEventListener('click', () => { if (link.hash === location.hash) navigate(); }));
  if (location.hash) navigate();
  const guide = form.querySelector('[data-volunteer-guide]');
  form.querySelector('[data-guide-open]').addEventListener('click', () => guide.showModal());
  form.querySelector('[data-guide-close]').addEventListener('click', () => guide.close());
  let dirty = false;
  let submitting = false;
  const markDirty = event => {
    if (!event.target.name && !event.target.closest('[data-tariff-editor],[data-km-schedule-editor]')) return;
    dirty = true;
    form.querySelector('[data-editor-save-state]').textContent = form.dataset.dirtyLabel;
  };
  form.addEventListener('input', markDirty);
  form.addEventListener('change', markDirty);
  form.addEventListener('submit', () => { submitting = true; });
  window.addEventListener('beforeunload', event => { if (dirty && !submitting) { event.preventDefault(); event.returnValue = ''; } });
  const ageOpen = form.elements.namedItem('age_open_ended');
  const ageTo = form.elements.namedItem('age_to');
  const syncAge = () => { ageTo.disabled = ageOpen.checked; };
  ageOpen.addEventListener('change', syncAge); syncAge();
  const photo = form.elements.namedItem('photo');
  const preview = form.querySelector('[data-editor-photo-preview]');
  let photoUrl;
  photo.addEventListener('change', () => {
    if (photoUrl) URL.revokeObjectURL(photoUrl);
    if (photo.files[0]) { photoUrl = URL.createObjectURL(photo.files[0]); preview.src = photoUrl; preview.hidden = false; }
  });
  const errors = form.querySelector('[data-editor-errors]');
  if (errors) errors.focus();
})();
