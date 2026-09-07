(() => {
  'use strict';
  const form = document.querySelector('[data-permanent-place-form]');
  if (!form) return;
  const ui = JSON.parse(document.getElementById('pw-copy').textContent);
  const rules = JSON.parse(document.getElementById('pw-rules').textContent);
  const volunteer = form.dataset.pwVolunteer === '1';
  const steps = [...form.querySelectorAll('[data-pw-step]')];
  const el = name => form.elements.namedItem(name);
  const value = name => (el(name)?.value || '').trim();
  const box = name => form.querySelector(`[data-pw-field="${name}"]`) || el(name)?.closest('[data-pw-field]');
  const parse = (text, fallback = []) => { try { return JSON.parse(text); } catch { return fallback; } };
  const text = (selector, content) => { const node = form.querySelector(selector); if (node) node.textContent = content; };
  let current = 1, dirty = false, submitting = false, restoring = false, initialized = false;
  let ageMode = value('age_open_ended') ? (value('age_from') === '0' ? 'all' : 'open') : 'range';
  const draftKey = `kidsmap:permanent:v1:${form.dataset.draftKey}`;
  try {
    if (sessionStorage.getItem('kidsmap:submitted-draft') === draftKey) {
      if (!volunteer && form.dataset.pwBound !== '1') localStorage.removeItem(draftKey);
      sessionStorage.removeItem('kidsmap:submitted-draft');
    }
  } catch {}
  const initialAddress = value('address');
  const savedMain = form.querySelector('[data-photo-saved=main]')?.dataset.photoPreview || '';
  const photoEditor = window.KidsMapPhotoEditor?.mount(form);
  const allDistricts = [...(el('district')?.options || [])].map(option => option.cloneNode(true));
  function label(name) {
    return (box(name)?.querySelector('[data-pw-label]') || box(name)?.querySelector('label'))?.textContent.replace('*', '').trim() ||
      ({pricing_plans: steps[2].querySelector('h2').textContent, structured_schedule: steps[4].querySelector('h2').textContent})[name] || name;
  }
  function fieldStep(name) { return Number(box(name)?.closest('[data-pw-step]')?.dataset.pwStep || 1); }
  function reveal(name) {
    go(fieldStep(name));
    let parent = box(name)?.parentElement;
    while (parent && parent !== form) { if (parent.tagName === 'DETAILS') parent.open = true; parent = parent.parentElement; }
    const target = el(name);
    if (name === 'category') form.querySelector('[data-pw-category]')?.focus();
    else if (target?.type !== 'hidden' && target?.focus) target.focus();
    else box(name)?.querySelector('button,input:not([type=hidden]),select')?.focus();
  }
  function requiredNames() {
    if (volunteer) return [];
    const names = [...rules.required];
    if (ageMode === 'range') names.push('age_to');
    if (value('region') === 'baku') names.push('district');
    return names;
  }
  function filled(name) {
    if (name === 'photo') return photoEditor ? photoEditor.hasMain() : !!el(name)?.files?.length || (!!savedMain && !el('photo-clear')?.checked);
    return value(name) !== '';
  }
  function issues() {
    const result = new Map();
    if (volunteer) return result;
    if (photoEditor?.validationMessage()) result.set('gallery_images', photoEditor.validationMessage());
    requiredNames().forEach(name => { if (!filled(name)) result.set(name, ui.required); });
    if (!rules.names.some(name => value(name))) result.set('name_az', ui.required);
    if (Math.max(...rules.descriptions.map(name => value(name).length)) < rules.description_min) result.set('description_az', `${ui.invalid}: ${rules.description_min}`);
    if (value('age_from') && value('age_to') && Number(value('age_from')) > Number(value('age_to'))) result.set('age_to', ui.invalid);
    for (const [name, limit] of [['lat', 90], ['lng', 180]]) {
      if (filled(name) && (!Number.isFinite(Number(value(name))) || Math.abs(Number(value(name))) > limit)) result.set(name, ui.invalid);
    }
    const plans = parse(value('pricing_plans'));
    const hasPrimary = plans.some(p => p.is_active !== false && (p.charge_role || 'primary') === 'primary' && (
      ['free', 'on_request'].includes(p.price_kind) ||
      (p.price_kind === 'from' && Number(p.price_min) > 0) ||
      (p.price_kind === 'range' && p.price_min !== '' && p.price_min != null && p.price_max !== '' && p.price_max != null && Number(p.price_min) >= 0 && Number(p.price_max) >= Number(p.price_min)) ||
      ((!p.price_kind || p.price_kind === 'exact') && Number(p.price) > 0)));
    if ((!hasPrimary && !(rules.legacy_price && !plans.length)) || plans.length > rules.max_plans) result.set('pricing_plans', ui.required);
    for (const p of plans) {
      if (!p.product_type || (p.billing_mode === 'recurring' && (!p.billing_interval || !(Number(p.billing_interval_count) > 0))) ||
          (p.billing_mode === 'installment' && !(Number(p.billing_cycles) > 0)) ||
          (p.price_kind === 'exact' && !(Number(p.price) > 0)) ||
          (p.price_kind === 'range' && (p.price_min == null || p.price_min === '' || p.price_max == null || p.price_max === '' || Number(p.price_max) < Number(p.price_min)))) result.set('pricing_plans', ui.invalid);
    }
    if (value('schedule_mode') === 'regular' && !value('schedule')) {
      const days = parse(value('structured_schedule'));
      if (!days.some(day => !day.is_closed && (day.is_24_hours || day.intervals?.some(interval => interval.start && interval.end)))) result.set('structured_schedule', ui.required);
    }
    const savedGallery = form.querySelectorAll('input[name=delete_gallery_ids]').length;
    const removed = form.querySelectorAll('input[name=delete_gallery_ids]:checked').length;
    if (savedGallery - removed + (el('gallery_images')?.files?.length || 0) > rules.max_gallery) result.set('gallery_images', `${ui.invalid}: ${rules.max_gallery}`);
    for (const input of form.querySelectorAll('input,select,textarea')) {
      if (input.type === 'hidden' || input.hidden || input.closest('.pw-field')?.hidden || input.closest('.owner-tariff-field')?.hidden || input.disabled) continue;
      if (input.validity && !input.validity.valid && input.value !== '') result.set(input.name || 'pricing_plans', input.validationMessage);
    }
    return result;
  }
  function displayIssues(result) {
    form.querySelectorAll('.pw-client-error').forEach(node => node.textContent = '');
    form.querySelectorAll('[aria-invalid=true]').forEach(node => node.removeAttribute('aria-invalid'));
    const summary = form.querySelector('[data-pw-errors]');
    summary.replaceChildren(); summary.hidden = result.size === 0;
    if (!result.size) return;
    const title = document.createElement('strong'); title.textContent = ui.missing; summary.append(title);
    const list = document.createElement('ul');
    result.forEach((message, name) => {
      const entry = document.createElement('li'), button = document.createElement('button');
      button.type = 'button'; button.textContent = `${label(name)}: ${message}`;
      button.addEventListener('click', () => reveal(name)); entry.append(button); list.append(entry);
      const error = box(name)?.querySelector('.pw-client-error'); if (error) error.textContent = message;
      const input = el(name); if (input?.setAttribute) input.setAttribute('aria-invalid', 'true');
    });
    summary.append(list);
  }
  function go(number, focus = true) {
    current = Math.max(1, Math.min(7, number));
    steps.forEach(step => { step.hidden = Number(step.dataset.pwStep) !== current; });
    form.querySelectorAll('[data-pw-go]').forEach(button => { button.setAttribute('aria-current', Number(button.dataset.pwGo) === current ? 'step' : 'false'); });
    form.querySelector('[data-pw-prev]').hidden = current === 1;
    form.querySelector('[data-pw-next]').hidden = current === 7;
    form.querySelector('[data-pw-submit]').hidden = current !== 7;
    text('[data-pw-progress-label]', `${ui.step} ${current} ${ui.of} 7`);
    text('[data-pw-progress-title]', steps[current - 1].querySelector('h2').textContent);
    const progress = form.querySelector('[data-pw-progress-bar]');
    progress.style.width = `${current / 7 * 100}%`;
    progress.parentElement.setAttribute('aria-valuenow', current);
    if (focus) {
      steps[current - 1].querySelector('h2').focus({preventScroll: true});
      const workspace = form.querySelector('.pw-workspace');
      if (workspace.getBoundingClientRect().top < 70) workspace.scrollIntoView({block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
      const activeNav = form.querySelector('[aria-current=step]');
      if (innerWidth <= 850) activeNav.parentElement.scrollTo({left: activeNav.offsetLeft - activeNav.parentElement.offsetLeft - 12, behavior: 'smooth'});
    }
    if (current === 4) { window.dispatchEvent(new Event('resize')); window.kidsMapRefreshOwnerMapPickers?.(); }
    if (current === 7) review();
    updateRequirements();
  }
  function setAge(mode, userAction = false) {
    ageMode = mode;
    el('age_open_ended').value = mode === 'range' ? '' : '1';
    if (userAction && mode !== 'range') el('age_to').value = '';
    if (mode === 'all') el('age_from').value = '0';
    el('age_from').readOnly = mode === 'all';
    box('age_to').hidden = mode !== 'range';
    form.querySelectorAll('[data-pw-age]').forEach(button => button.setAttribute('aria-pressed', button.dataset.pwAge === mode ? 'true' : 'false'));
  }
  function regionChanged(userAction = false) {
    if (!el('region')) return;
    const baku = value('region') === 'baku';
    box('district').hidden = !baku; box('metro').hidden = !baku;
    if (userAction && !baku) { el('district').value = ''; el('metro').value = ''; }
    if (baku && el('district').options.length < 2) el('district').replaceChildren(...allDistricts.map(option => option.cloneNode(true)));
  }
  function markRequired() {
    if (volunteer) return;
    const required = requiredNames();
    form.querySelectorAll('[data-pw-required]').forEach(node => {
      const name = node.dataset.pwRequired;
      const groupedName = rules.names.includes(name);
      const mandatory = required.includes(name);
      node.hidden = false;
      node.textContent = groupedName ? ui.one_name : mandatory ? ui.required_badge : ui.optional_badge;
      node.dataset.kind = groupedName ? 'group' : mandatory ? 'required' : 'optional';
      box(name)?.classList.toggle('pw-field--required', mandatory || groupedName);
      if (el(name)?.setAttribute) el(name).setAttribute('aria-required', String(mandatory));
    });
    updateRequirements();
  }
  function updateRequirements() {
    if (volunteer) return;
    const errors = issues();
    const entries = requiredNames().filter(name => name !== 'lng').map(name => ({
      name, title: name === 'lat' ? ui.point_requirement : label(name),
      ready: !errors.has(name) && (name !== 'lat' || !errors.has('lng')),
    }));
    entries.unshift({name: 'name_az', title: ui.name_requirement, ready: rules.names.some(name => value(name))});
    entries.push({name: 'pricing_plans', title: ui.price_requirement, ready: !errors.has('pricing_plans')});
    if (value('schedule_mode') === 'regular') entries.push({name: 'structured_schedule', title: ui.schedule_requirement, ready: !errors.has('structured_schedule')});
    form.querySelectorAll('[data-pw-requirements]').forEach(panel => {
      const number = Number(panel.dataset.pwRequirements);
      const items = entries.filter(entry => fieldStep(entry.name) === number);
      const list = panel.querySelector('[data-pw-requirements-list]'); list.replaceChildren();
      const complete = items.filter(item => item.ready).length;
      panel.querySelector('[data-pw-requirements-count]').textContent = `${ui.fields_ready} ${complete} / ${items.length}`;
      items.forEach(item => {
        const button = document.createElement('button'), icon = document.createElement('span'), caption = document.createElement('span');
        button.type = 'button'; button.dataset.pwRequirement = item.name; button.dataset.ready = String(item.ready);
        icon.textContent = item.ready ? '✓' : '○'; icon.setAttribute('aria-hidden', 'true');
        caption.textContent = item.title; button.append(icon, caption);
        button.setAttribute('aria-label', `${item.title}: ${item.ready ? ui.fields_ready : ui.required_badge}`);
        button.addEventListener('click', () => reveal(item.name)); list.append(button);
      });
      panel.dataset.complete = String(complete === items.length);
      const status = form.querySelector(`[data-pw-step-status="${number}"]`);
      status.textContent = complete === items.length ? '✓' : `${complete}/${items.length}`;
      status.setAttribute('title', `${ui.fields_ready} ${complete} / ${items.length}`);
    });
    const finalStatus = form.querySelector('[data-pw-step-status="7"]');
    finalStatus.textContent = errors.size ? '' : '✓';
  }
  function saveBrowser() {
    if (restoring) return;
    if (volunteer) { text('[data-pw-draft-status]', ui.browser_saved); return; }
    const data = {};
    for (const input of form.querySelectorAll('input[name],select[name],textarea[name]')) {
      if (['csrfmiddlewaretoken', 'form_action', 'gallery_order', 'photo-clear'].includes(input.name) || input.type === 'file' || input.name === 'delete_gallery_ids') continue;
      if (input.type === 'radio' && !input.checked) continue;
      data[input.name] = input.type === 'checkbox' ? input.checked : input.value;
    }
    try {
      localStorage.setItem(draftKey, JSON.stringify({data, ageMode, step: current, at: Date.now()}));
      text('[data-pw-draft-status]', navigator.onLine ? ui.browser_saved : ui.offline);
    } catch { text('[data-pw-draft-status]', ui.storage_error); }
  }
  function changed(event) {
    if (restoring || !initialized) return;
    dirty = true;
    if (event?.target?.name === 'region') regionChanged(true);
    if (event?.target?.name === 'address' && value('address') !== initialAddress && value('lat')) form.querySelector('[data-pw-map-changed]').hidden = false;
    if (event?.target?.name === 'age_from' && ageMode === 'all' && value('age_from') !== '0') setAge('open');
    markRequired(); saveBrowser();
    if (current === 7) review();
  }
  function planText(p) {
    const currency = p.currency || 'AZN';
    if (p.price_kind === 'free') return ui.free;
    if (p.price_kind === 'on_request') return ui.request;
    if (p.price_kind === 'range') return `${p.price_min}–${p.price_max} ${currency}`;
    if (p.price_kind === 'from') return `${ui.from_price} ${p.price_min} ${currency}`;
    return `${p.price || '—'} ${currency}`;
  }
  function headline(plans) {
    if (rules.custom_price || (!plans.length && rules.legacy_price)) return rules.existing_price_label;
    const primary = plans.filter(p => p.is_active !== false && (p.charge_role || 'primary') === 'primary' && (p.currency || 'AZN') === 'AZN');
    const free = primary.some(p => p.price_kind === 'free'), request = primary.some(p => p.price_kind === 'on_request');
    const paid = primary.filter(p => !['free','on_request'].includes(p.price_kind)).map(p => ({
      lo: Number(p.price_kind === 'from' || p.price_kind === 'range' ? p.price_min : p.price),
      hi: Number(p.price_kind === 'range' ? p.price_max : p.price_kind === 'from' ? p.price_min : p.price), kind: p.price_kind,
    })).filter(p => p.lo > 0 && Number.isFinite(p.hi));
    if (free && !paid.length && !request) return ui.free;
    if (paid.length) {
      const lo = free ? 0 : Math.min(...paid.map(p => p.lo)), hi = Math.max(...paid.map(p => p.hi));
      if (lo !== hi) return `${lo}–${hi} ₼`;
      if (paid.some(p => p.kind === 'from')) return document.documentElement.lang === 'az' ? `${lo} ₼-dən` : `${ui.from_price} ${lo} ₼`;
      return `${lo} ₼`;
    }
    return ui.request;
  }
  function review() {
    const result = issues();
    text('[data-pw-preview-name]', value('name_az') || value('name_ru') || value('name_en') || ui.empty);
    text('[data-pw-preview-category]', el('category')?.selectedOptions?.[0]?.textContent || '');
    text('[data-pw-preview-address]', value('address'));
    text('[data-pw-preview-age]', ageMode === 'all' ? ui.all_ages : ageMode === 'open' ? `${value('age_from')}+` : `${value('age_from')}–${value('age_to')}`);
    const plans = parse(value('pricing_plans'));
    const primary = plans.filter(p => p.is_active !== false && (p.charge_role || 'primary') === 'primary');
    text('[data-pw-preview-price]', headline(plans));
    const photo = form.querySelector('[data-pw-preview-image]'); photo.replaceChildren();
    const src = photoEditor ? photoEditor.preview() : (el('photo-clear')?.checked ? '' : savedMain);
    if (src) { const img = document.createElement('img'); img.src = src; img.alt = ''; photo.append(img); }
    const overview = form.querySelector('[data-pw-review]'); overview.replaceChildren();
    steps.slice(0, 6).forEach(step => {
      const section = document.createElement('section'), button = document.createElement('button');
      button.type = 'button'; button.textContent = `${step.querySelector('h2').textContent} ↗`; button.addEventListener('click', () => go(Number(step.dataset.pwStep))); section.append(button);
      const dl = document.createElement('dl');
      for (const field of step.querySelectorAll('[data-pw-field]')) {
        const name = field.dataset.pwField;
        if (name === 'pricing_plans') {
          plans.forEach((p, index) => {
            const row = form.querySelector('[data-tariff-list]')?.children[index];
            const dt = document.createElement('dt'), dd = document.createElement('dd');
            dt.textContent = p.title_az || p.title_ru || row?.querySelector('[data-tariff-key=editor_kind]')?.selectedOptions?.[0]?.textContent || ui.empty;
            const details = [];
            row?.querySelectorAll('[data-tariff-key]').forEach(input => {
              if (input.hidden || input.closest('.owner-tariff-field')?.hidden || input.dataset.tariffKey === 'verified_at' || !input.value || (input.type === 'checkbox' && !input.checked)) return;
              details.push(`${input.closest('label')?.querySelector('span')?.textContent || ''}: ${input.selectedOptions?.[0]?.textContent || (input.type === 'checkbox' ? '✓' : input.value)}`);
            });
            dd.textContent = `${planText(p)}\n${details.join('\n')}`; dl.append(dt, dd);
          }); continue;
        }
        if (name === 'structured_schedule') {
          const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = label(name);
          const schedule = value('schedule_mode') === 'regular' ? (value('schedule') || form.querySelector('[data-km-schedule-preview]')?.textContent || '') : '';
          dd.textContent = [el('schedule_mode')?.selectedOptions?.[0]?.textContent, schedule, ...['az','ru','en'].map(lang => value(`schedule_note_${lang}`))].filter(Boolean).join('\n'); dl.append(dt, dd); continue;
        }
        if (name === 'photo' || name === 'gallery_images') {
          const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = label(name);
          dd.textContent = name === 'photo' ? (el(name).files[0]?.name || (savedMain ? '✓' : ui.empty)) : String(form.querySelectorAll('input[name=delete_gallery_ids]:not(:checked)').length + el(name).files.length);
          dl.append(dt,dd); continue;
        }
        if (!value(name) || el(name)?.type === 'file' || field.hidden) continue;
        const dt = document.createElement('dt'), dd = document.createElement('dd');
        dt.textContent = label(name); dd.textContent = el(name)?.selectedOptions?.[0]?.textContent || form.querySelector(`input[name="${name}"]:checked`)?.closest('label')?.textContent || value(name); dl.append(dt, dd);
      }
      section.append(dl); overview.append(section);
    });
    text('[data-pw-readiness]', result.size ? ui.missing : ui.ready);
    updateRequirements();
  }
  // Restore before tariff and schedule editors are initialized. Bound server errors win.
  if (!volunteer && form.dataset.pwBound !== '1') {
    try {
      const saved = parse(localStorage.getItem(draftKey), null);
      if (saved?.data && Date.now() - saved.at < 7 * 86400000) {
        restoring = true;
        for (const input of form.querySelectorAll('input[name],select[name],textarea[name]')) {
          if (!(input.name in saved.data) || input.type === 'file' || ['gallery_order','photo-clear','delete_gallery_ids'].includes(input.name)) continue;
          if (input.type === 'checkbox') input.checked = !!saved.data[input.name];
          else if (input.type === 'radio') input.checked = input.value === saved.data[input.name];
          else input.value = saved.data[input.name];
        }
        ageMode = saved.ageMode; current = saved.step; text('[data-pw-draft-status]', ui.restored); restoring = false;
      }
    } catch { /* A blocked storage API does not prevent server-side saving. */ }
  }
  form.querySelectorAll('[data-pw-go]').forEach(button => button.addEventListener('click', () => go(Number(button.dataset.pwGo))));
  form.querySelectorAll('[data-pw-age]').forEach(button => button.addEventListener('click', () => { setAge(button.dataset.pwAge, true); changed(); }));
  form.querySelector('[data-pw-prev]').addEventListener('click', () => go(current - 1));
  form.querySelector('[data-pw-next]').addEventListener('click', () => {
    const errors = new Map([...issues()].filter(([name]) => fieldStep(name) === current));
    displayIssues(errors); if (!errors.size) go(current + 1); else reveal(errors.keys().next().value);
  });
  ['input', 'change', 'km:schedule-change', 'km:map-change', 'km:pricing-change', 'km:photos-change'].forEach(name => form.addEventListener(name, changed));
  form.querySelector('[data-pw-confirm-point]').addEventListener('click', () => { form.querySelector('[data-pw-map-changed]').hidden = true; });
  form.addEventListener('submit', async event => {
    if (submitting) { event.preventDefault(); return; }
    if (event.submitter?.value !== 'save_draft') {
      const errors = issues(); displayIssues(errors);
      if (errors.size) { event.preventDefault(); reveal(errors.keys().next().value); return; }
    }
    if (!navigator.onLine) { event.preventDefault(); text('[data-pw-draft-status]', ui.offline); return; }
    submitting = true;
    if (photoEditor) {
      event.preventDefault();
      const result = await photoEditor.save(event.submitter);
      if (result.ok) {
        try { localStorage.removeItem(draftKey); } catch {}
        location.assign(result.redirect);
      } else {
        submitting = false;
        const errors = new Map(Object.entries(result.errors || {}).map(([name, messages]) => [name, messages.join(' ')]));
        displayIssues(errors);
        const first = errors.keys().next().value;
        if (box(first)) reveal(first); else go(6);
      }
      return;
    }
    // Retain browser recovery until the next GET proves that saving succeeded.
    try { if (!volunteer) sessionStorage.setItem('kidsmap:submitted-draft', draftKey); } catch {}
  });
  window.addEventListener('beforeunload', event => { if (dirty && !submitting) { event.preventDefault(); event.returnValue = ui.unsaved; } });
  window.addEventListener('offline', () => text('[data-pw-draft-status]', ui.offline));
  window.addEventListener('online', () => text('[data-pw-draft-status]', ui.browser_saved));
  document.querySelector('[data-pw-delete]')?.addEventListener('submit', event => { if (!window.confirm(ui.delete_confirm)) event.preventDefault(); else submitting = true; });
  // Enhance real controls, retaining their original names and server validation.
  const category = el('category');
  const categoryChoices = form.querySelector('.pw-category-choices');
  categoryChoices.hidden = false;
  categoryChoices.querySelectorAll('[data-pw-category]').forEach(button => {
    button.addEventListener('click', () => {
      category.value = button.dataset.pwCategory;
      category.dispatchEvent(new Event('change', {bubbles: true}));
    });
  });
  function syncCategory() { categoryChoices.querySelectorAll('button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.pwCategory === category.value))); }
  category.classList.add('pw-native-category'); category.tabIndex = -1;
  category.addEventListener('change', syncCategory); syncCategory();
  const description = el('description_az'), counter = document.createElement('small');
  counter.className = 'pw-description-count'; description.after(counter);
  function countDescription() { counter.textContent = `${description.value.length} / ${rules.description_min}`; counter.classList.toggle('is-ready', description.value.length >= rules.description_min); }
  if (!volunteer) { description.addEventListener('input', countDescription); countDescription(); }
  setAge(ageMode); regionChanged(); markRequired();
  const firstError = form.querySelector('.pw-error')?.closest('[data-pw-step]');
  const fieldAnchor = new URLSearchParams(location.hash.slice(1)).get('field');
  go(firstError ? Number(firstError.dataset.pwStep) : fieldAnchor ? fieldStep(fieldAnchor) : location.hash === '#photos' ? 6 : current, false);
  if (fieldAnchor) reveal(fieldAnchor);
  document.addEventListener('DOMContentLoaded', () => { initialized = true; markRequired(); });
  window.addEventListener('pageshow', () => { submitting = false; });
  window.addEventListener('hashchange', () => { const name = new URLSearchParams(location.hash.slice(1)).get('field'); if (name) reveal(name); });
})();
