(() => {
  'use strict';
  const root = document.querySelector('[data-place-mode="continuous"]');
  const form = root?.querySelector('[data-permanent-place-form]');
  if (!form) return;
  const ui = JSON.parse(document.getElementById('pw-copy').textContent);
  const readiness = JSON.parse(document.getElementById('pc-readiness').textContent);
  root.classList.add('pc-enhanced');
  const allowed = new Set(JSON.parse(document.getElementById('pc-draft-fields').textContent));
  const status = form.querySelector('[data-pc-save-status]');
  const currentDraftView = new URL(location.href).searchParams.get('draft_current') === '1';
  const currentCandidateView = Boolean(form.dataset.targetId) && new URL(location.href).searchParams.get('candidate_current') === '1';
  const localKey = `kidsmap:place:continuous:${form.dataset.accountId}:${form.dataset.draftKey}${currentCandidateView ? ':candidate-current' : currentDraftView ? ':current' : ''}`;
  const targetId = form.dataset.targetId ? Number(form.dataset.targetId) : null;
  const currentPhoto = form.querySelector('[data-pc-photo-current]')?.dataset.pcPhotoCurrent;
  const mainPhoto = form.querySelector('[data-photo-saved=main]');
  if (currentPhoto && mainPhoto) mainPhoto.dataset.photoPreview = currentPhoto;
  const photoEditor = window.KidsMapPhotoEditor?.mount(form);
  let draftId = form.dataset.fresh === '1' ? null : new URL(location.href).searchParams.get('draft_id'), draftVersion = 0, sourceVersion = Number(form.dataset.sourceVersion);
  let timer = null, saving = false, dirty = false, halted = false, submitting = false, restoring = false, userInteracted = false;
  let inFlight = null, photoDirty = false, editedAt = Date.now();
  let candidateConflict = false;
  if (targetId === null) {
    const url = new URL(location.href);
    url.searchParams.delete('fresh');
    if (form.dataset.fresh === '1') url.searchParams.delete('draft_id');
    url.searchParams.set('draft_session', form.elements.namedItem('draft_client_key').value);
    history.replaceState(null, '', url);
  }
  const fields = () => {
    const result = {};
    for (const input of form.querySelectorAll('[name]')) {
      if (!allowed.has(input.name) || input.disabled || input.type === 'file') continue;
      if (input.type === 'radio' && !input.checked) continue;
      if (input.type === 'checkbox') result[input.name] = input.checked;
      else if (input.name === 'pricing_plans' || input.name === 'nested_pricing' || input.name === 'structured_schedule') {
        try { result[input.name] = JSON.parse(input.value || '[]'); } catch { result[input.name] = []; }
      } else result[input.name] = input.value;
    }
    return result;
  };
  const schemaVersion = Number(form.dataset.schemaVersion);
  const candidateVersion = (() => {
    // Some owner forms carry the candidate only in their signed source token.
    // This is a recovery hint; the server still validates its signature and CAS.
    const direct = form.elements.namedItem('candidate_version');
    if (direct && direct.value !== '') {
      const value = Number(direct.value);
      return Number.isSafeInteger(value) && value >= 0 ? value : null;
    }
    try {
      const encoded = (form.elements.namedItem('publication_token')?.value || '').split(':')[0]
        .replace(/-/g, '+').replace(/_/g, '/');
      const value = JSON.parse(atob(encoded + '='.repeat((4 - encoded.length % 4) % 4))).candidate;
      return Number.isSafeInteger(value) && value >= 0 ? value : null;
    } catch { return null; }
  })();
  const canonicalFields = fields();
  let recovery = null;
  let recoveryPreserved = true;
  const setStatus = (message, state) => {
    if (halted && state !== 'conflict') { message = ui.server_conflict; state = 'conflict'; }
    status.textContent = message; status.dataset.state = state;
    const actions = form.querySelector('[data-pc-conflict-actions]');
    actions.hidden = state !== 'conflict';
    const url = new URL(location.href);
    if (candidateConflict) {
      for (const key of ['draft_id', 'draft_current', 'draft_session']) url.searchParams.delete(key);
      url.searchParams.set('candidate_current', '1');
      url.hash = '';
    } else {
      url.searchParams.delete('candidate_current');
      url.searchParams.set('draft_current', '1');
      if (draftId) url.searchParams.set('draft_id', draftId);
    }
    actions.querySelector('a').href = url.href;
  };
  const localStore = () => {
    if (recovery && !recoveryPreserved) return;
    try { localStorage.setItem(localKey, JSON.stringify({fields: fields(), at: editedAt, draftId, draftVersion, sourceVersion, schemaVersion, candidateVersion, targetType:'place', targetId, serverSaved: !dirty, photoPending: photoDirty, conflict: halted, candidateConflict})); }
    catch { setStatus(ui.storage_error, 'error'); }
  };
  const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;
  function apply(saved) {
    if (!saved || !saved.fields || form.dataset.pwBound === '1') return;
    restoring = true;
    form.dispatchEvent(new CustomEvent('km:location-restore-start', {bubbles:true}));
    try {
    for (const [name, value] of Object.entries(saved.fields)) {
      if (!allowed.has(name)) continue;
      const controls = [...form.querySelectorAll('[name]')].filter(input => input.name === name);
      for (const input of controls) {
        if (input.type === 'radio') input.checked = String(input.value) === String(value);
        else if (input.type === 'checkbox') input.checked = Boolean(value);
        else input.value = typeof value === 'object' ? JSON.stringify(value) : String(value ?? '');
      }
      controls[0]?.dispatchEvent(new Event('change', {bubbles:true}));
    }
    if (openAge) { openAge.checked = form.elements.namedItem('age_open_ended').value === '1'; syncAge(); }
    } finally {
      restoring = false;
      form.dispatchEvent(new CustomEvent('km:location-restore-end', {bubbles:true}));
    }
    updatePreview();
  }
  function offerRecovery(saved, canRestore = true) {
    recoveryPreserved = false;
    try {
      const identifier = saved.draft_id || saved.draftId || saved.at || saved.saved_at || 'legacy';
      localStorage.setItem(`${localKey}:recovery:${identifier}`, JSON.stringify(saved));
      recoveryPreserved = true;
    } catch { /* Keep the original slot intact until preservation succeeds. */ }
    halted = true; candidateConflict = targetId !== null;
    clearTimeout(timer);
    setStatus(ui.working_copy_conflict, 'conflict');
    if (recovery) recovery.remove();
    recovery = document.createElement('div');
    recovery.dataset.pcRecovery = '';
    recovery.style.display = 'flex'; recovery.style.flexWrap = 'wrap'; recovery.style.gap = '8px';
    const current = document.createElement('a');
    current.className = 'pw-secondary'; current.textContent = ui.use_current_card;
    current.style.display = 'inline-flex'; current.style.alignItems = 'center';
    current.style.minHeight = '44px'; current.style.maxWidth = '100%'; current.style.padding = '6px 12px';
    current.style.boxSizing = 'border-box'; current.style.whiteSpace = 'normal';
    const url = new URL(location.href);
    for (const key of ['draft_id', 'draft_current', 'draft_session', 'fresh']) url.searchParams.delete(key);
    if (targetId !== null) url.searchParams.set('candidate_current', '1');
    else if (saved.materialized_place_id) {
      url.pathname = `/${document.documentElement.lang}/account/places/${saved.materialized_place_id}/edit/`;
      url.searchParams.set('candidate_current', '1');
    } else url.searchParams.set('fresh', '1');
    current.href = url.href; current.target = '_blank'; current.rel = 'noopener';
    const restoreButton = document.createElement('button');
    restoreButton.type = 'button'; restoreButton.className = 'pw-secondary';
    restoreButton.textContent = ui.restore_working_copy; restoreButton.dataset.pcRecoveryRestore = '';
    restoreButton.disabled = !canRestore;
    restoreButton.style.minHeight = '44px'; restoreButton.style.maxWidth = '100%'; restoreButton.style.whiteSpace = 'normal';
    restoreButton.addEventListener('click', () => {
      // Preserve the previous input before replacing its normal recovery slot.
      try {
        const identifier = saved.draft_id || saved.draftId || saved.at || saved.saved_at || 'legacy';
        localStorage.setItem(`${localKey}:recovery:${identifier}`, JSON.stringify(saved));
        recoveryPreserved = true;
      } catch { status.textContent = ui.storage_error; return; }
      halted = false; candidateConflict = false; draftId = null; draftVersion = 0;
      form.elements.namedItem('server_draft_id').value = '';
      apply(saved); userInteracted = true; dirty = true; editedAt = Date.now();
      recovery.remove(); recovery = null; localStore(); schedule();
      setStatus(ui.unsaved, 'dirty');
    });
    recovery.append(current, restoreButton); status.parentElement.append(recovery);
  }
  function validServerCopy(saved) {
    return saved.target_type === 'place' && saved.target_id === targetId &&
      saved.schema_version === schemaVersion && saved.source_version === sourceVersion && !saved.materialized_place_id;
  }
  async function restore() {
    if (form.dataset.pwBound === '1' || currentCandidateView) return;
    let local = null;
    try { local = JSON.parse(localStorage.getItem(localKey) || 'null'); } catch {}
    if (form.dataset.fresh === '1' && !local) return;
    if (local) {
      if (local.sourceVersion !== sourceVersion || local.schemaVersion !== schemaVersion ||
          candidateVersion === null || local.candidateVersion !== candidateVersion || local.targetType !== 'place' || local.targetId !== targetId || local.conflict) {
        const compatible = (local.targetType == null || local.targetType === 'place') &&
          (local.targetId === undefined || local.targetId === targetId) &&
          (local.schemaVersion == null || local.schemaVersion === schemaVersion);
        offerRecovery(local, compatible); return;
      }
      candidateConflict = local.candidateConflict === true;
      draftId = local.draftId || null; draftVersion = Number(local.draftVersion) || 0;
      editedAt = local.at || Date.now();
      // A cached server copy may have been consumed by another explicit-save session.
    }
    try {
      const response = await fetch(form.dataset.draftUrl, {credentials:'same-origin'});
      if (!response.ok) throw new Error('read');
      const rows = (await response.json()).drafts || [];
      const selected = rows.find(item => item.target_type === 'place' && item.target_id === targetId &&
        (draftId ? item.draft_id === draftId : targetId !== null && !item.materialized_place_id));
      if (selected) {
        const detailResponse = await fetch(`${form.dataset.draftUrl}${selected.draft_id}/`, {credentials:'same-origin'});
        if (!detailResponse.ok) throw new Error('detail');
        const detail = await detailResponse.json();
        if (detail.target_type !== 'place' || detail.target_id !== targetId || detail.schema_version !== schemaVersion) {
          offerRecovery(local || {fields:{}}, false); return;
        }
        if (!validServerCopy(detail)) { offerRecovery(local || detail); return; }
        if (local && !local.serverSaved && local.draftId === detail.draft_id && local.draftVersion !== detail.version) {
          offerRecovery(local); return;
        }
        if (userInteracted) return; // Late reads must never overwrite newer typing or attach an old draft ID.
        if (local && local.at > Date.parse(detail.saved_at)) {
          form.elements.namedItem('server_draft_id').value = draftId || ''; apply(local);
          dirty = true; localStore(); schedule(); setStatus(ui.browser_saved, 'browser'); return;
        }
        // Server copies have no persisted candidate-base token. Divergent data requires a choice.
        if (targetId !== null && !local && JSON.stringify(detail.fields) !== JSON.stringify(canonicalFields)) {
          offerRecovery(local || detail); return;
        }
        draftId = detail.draft_id; draftVersion = detail.version;
        form.elements.namedItem('server_draft_id').value = draftId;
        apply(detail); setStatus(`${ui.server_saved} · ${new Date(detail.saved_at).toLocaleString()}`, 'saved'); localStore();
      } else if (local && !userInteracted) {
        draftId = null; draftVersion = 0; form.elements.namedItem('server_draft_id').value = '';
        apply(local); dirty = true; localStore(); schedule(); setStatus(ui.browser_saved, 'browser');
      }
    } catch {
      if (local && !userInteracted) {
        form.elements.namedItem('server_draft_id').value = draftId || ''; apply(local);
        setStatus(ui.browser_saved, 'browser');
      } else if (!local) setStatus(ui.save_failed, 'error');
    }
  }
  async function save(force = false) {
    if (saving) return inFlight;
    if (halted || submitting || (!dirty && !force)) return false;
    if (!navigator.onLine) { localStore(); setStatus(ui.offline, 'browser'); return false; }
    saving = true; const submitted = fields(); let succeeded = false;
    setStatus(ui.server_saving, 'saving');
    inFlight = (async () => {
      try {
        const response = await fetch(form.dataset.draftUrl, {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json','X-CSRFToken':csrf}, body:JSON.stringify({draft_id:draftId, target_type:'place', target_id:targetId, schema_version:Number(form.dataset.schemaVersion), source_version:sourceVersion, expected_version:draftVersion, fields:submitted})});
        const result = await response.json();
        if (response.status === 409) { halted = true; localStore(); setStatus(result.error === 'structure_changed' ? ui.structure_conflict : ui.server_conflict, 'conflict'); return false; }
        if (!response.ok) throw new Error(result.status || 'save');
        draftId = result.draft_id; draftVersion = result.version; form.elements.namedItem('server_draft_id').value = draftId;
        if (targetId === null) root.querySelector('[data-pc-lifecycle]').textContent = ui.state_draft;
        dirty = JSON.stringify(fields()) !== JSON.stringify(submitted);
        succeeded = true; localStore();
        if (targetId === null) { const url = new URL(location.href); url.searchParams.set('draft_id', draftId); history.replaceState(null, '', url); }
        setStatus(dirty ? ui.unsaved : `${ui.server_saved} · ${new Date(result.saved_at).toLocaleString()}${photoDirty ? ' · ' + ui.upload_pending : ''}`, dirty ? 'dirty' : 'saved');
        return true;
      } catch { localStore(); setStatus(ui.save_failed, 'error'); return false; }
      finally { saving = false; if (succeeded && dirty && !halted && !submitting) schedule(); }
    })();
    return inFlight;
  }
  function schedule() { clearTimeout(timer); timer = setTimeout(() => save(), 900); }

  // Native focus scrolling does not account for the sticky editor surfaces.
  function visibleFocusTarget(input) {
    const rect = input.getBoundingClientRect();
    if (rect.width > 2 && rect.height > 2) return input;
    return input.closest('label') || input.labels?.[0] || input;
  }
  function keepFocusVisible() {
    const input = document.activeElement;
    if (!form.contains(input)) return;
    const target = visibleFocusTarget(input), rect = target.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    let top = 8, bottom = window.innerHeight - 8;
    for (const surface of document.querySelectorAll('#km-site-header, .pc-nav, .pc-savebar, .pc-actions')) {
      if (surface.contains(input)) continue;
      const box = surface.getBoundingClientRect();
      if (!box.height || box.bottom <= 0 || box.top >= innerHeight || box.right <= rect.left || box.left >= rect.right) continue;
      const css = getComputedStyle(surface);
      if (css.position !== 'sticky' && css.position !== 'fixed') continue;
      if (surface.matches('.pc-actions')) bottom = Math.min(bottom, box.top - 8);
      else if (box.top <= Math.max(parseFloat(css.top) || 0, 0) + 1) top = Math.max(top, box.bottom + 8);
    }
    root.style.setProperty('--pc-focus-top', `${top}px`);
    root.style.setProperty('--pc-focus-bottom', `${innerHeight - bottom}px`);
    // Oversized controls align their leading area without an alternating scroll loop.
    const delta = rect.height > bottom - top ? rect.top - top : rect.top < top ? rect.top - top : rect.bottom > bottom ? rect.bottom - bottom : 0;
    if (Math.abs(delta) > 1) window.scrollBy({top:delta, behavior:'instant'});
  }
  let focusFrame = null;
  function scheduleFocusVisibility() {
    if (focusFrame !== null) cancelAnimationFrame(focusFrame);
    focusFrame = requestAnimationFrame(() => { focusFrame = null; keepFocusVisible(); });
  }
  form.addEventListener('focusin', scheduleFocusVisibility);
  window.addEventListener('resize', scheduleFocusVisibility);
  if ('ResizeObserver' in window) {
    const focusSurfaces = new ResizeObserver(scheduleFocusVisibility);
    form.querySelectorAll('.pc-nav, .pc-savebar, .pc-actions').forEach(surface => focusSurfaces.observe(surface));
  }

  function updatePreview() {
    const language = form.querySelector('[data-pc-preview-language]')?.value || 'az';
    const translated = prefix => form.elements.namedItem(`${prefix}_${language}`)?.value || form.elements.namedItem(`${prefix}_az`)?.value || (prefix === 'name' ? form.elements.namedItem('name')?.value : '') || '';
    const name = translated('name') || ui.empty;
    root.querySelector('[data-pc-preview-description]').textContent = translated('description');
    const address = form.elements.namedItem('address')?.value || '';
    root.querySelector('[data-pc-preview-name]').textContent = name;
    root.querySelector('[data-pc-preview-address]').textContent = address;
    const directCount = form.querySelector('[data-tariff-list]')?.children.length || 0;
    let activities = [];
    try { activities = JSON.parse(form.elements.namedItem('nested_pricing')?.value || 'null')?.activities || []; } catch {}
    const groupCount = activities.reduce((total, activity) => total + (activity.groups || []).length, 0);
    const groupPlans = activities.reduce((total, activity) => total + (activity.groups || []).reduce((subtotal, group) => subtotal + (group.pricing_plans || []).length, 0), 0);
    const counted = (count, key) => {
      const last = count % 10, lastTwo = count % 100;
      const form = last === 1 && lastTwo !== 11 ? 'one' : last >= 2 && last <= 4 && (lastTwo < 12 || lastTwo > 14) ? 'few' : 'many';
      return `${count} ${ui[`${key}_${form}`] || ui[key]}`;
    };
    root.querySelector('[data-pc-preview-offerings]').textContent = activities.length ? `${counted(activities.length, 'activity_count')} · ${counted(groupCount, 'group_count')}` : '';
    const count = directCount + groupPlans;
    root.querySelector('[data-pc-preview-price]').textContent = count ? counted(count, 'plan_count') : ui.empty;
  }
  function fieldTarget(name, path = null) {
    if (name === 'nested_pricing') {
      const root = form.querySelector('[data-pc-offerings]');
      const fallback = () => root?.querySelector('input,select,textarea') || form.querySelector('[data-pc-add-activity]');
      if (!Array.isArray(path)) return fallback();
      const keys = new Set(['program_id', 'category_id', 'subcategory_id', 'name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'description_en', 'supplement_az', 'age_from', 'age_to', 'language', 'schedule_text', 'lesson_format', 'teachers_text', 'conditions_az', 'title_az', 'title_ru', 'title_en', 'product_type', 'price_kind', 'price', 'price_min', 'price_max', 'currency', 'charge_role', 'billing_mode', 'billing_interval', 'billing_interval_count', 'billing_cycles', 'quantity', 'quantity_unit', 'is_trial', 'is_required']);
      let scope = root, offset = 0;
      for (const [segment, attribute] of [['activities', 'activity'], ['groups', 'group'], ['pricing_plans', 'plan']]) {
        if (path[offset] !== segment) break;
        const index = path[offset + 1];
        if (!Number.isSafeInteger(index) || index < 0) return fallback();
        scope = scope?.querySelector(`[data-${attribute}-index="${index}"]`);
        if (!scope) return fallback();
        offset += 2;
      }
      if (offset === 0 || (path.length !== offset && path.length !== offset + 1)) return fallback();
      const key = path[offset];
      if (key !== undefined && !keys.has(key)) return scope.querySelector(':scope > summary') || fallback();
      const input = key === undefined ? scope.querySelector(':scope > summary') : scope.querySelector(`[data-offering-key="${key}"]`);
      // A billing input can intentionally be hidden after changing billing mode.
      return (input?.closest('[hidden]') ? scope.querySelector('[data-offering-key="billing_mode"]') : input) || scope.querySelector(':scope > summary') || fallback();
    }
    const input = [...form.querySelectorAll('[name]')].find(node => node.name === name);
    if (input?.type === 'hidden') return input.closest('[data-pw-field]')?.parentElement?.querySelector('input:not([type=hidden]),select,textarea,button') || input;
    return input;
  }
  function goTo(input) {
    if (!input) return;
    for (let parent = input.parentElement; parent; parent = parent.parentElement) if (parent.tagName === 'DETAILS') parent.open = true;
    input.scrollIntoView({block:'center', behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
    input.focus({preventScroll:true});
  }
  const summaryAttributes = new Map();
  function showErrors(errors, targets = {}) {
    for (const [input, attributes] of summaryAttributes) {
      for (const [name, value] of Object.entries(attributes)) {
        if (value === null) input.removeAttribute(name); else input.setAttribute(name, value);
      }
    }
    summaryAttributes.clear();
    const box = form.querySelector('[data-pc-errors]'); box.replaceChildren();
    if (!Object.keys(errors).length) { box.hidden = true; return; }
    box.hidden = false; const heading = document.createElement('strong'); heading.textContent = ui.errors_title; box.append(heading);
    const list = document.createElement('ul');
    Object.entries(errors).forEach(([name, messages]) => {
      (Array.isArray(messages) ? messages : [messages]).forEach((text, index) => {
        const input = fieldTarget(name, targets?.[name]?.[index]), wrapper = input?.closest('[data-pw-field]');
        const item = document.createElement('li'), button = document.createElement('button');
        let message = String(text);
        if (message.includes('Candidate version conflict')) message = ui.server_conflict;
        const label = name === 'nested_pricing' ? ui.section_offer : wrapper?.querySelector('label')?.textContent?.trim() || input?.getAttribute('aria-label') || ui.errors_title;
        button.type = 'button'; button.textContent = `${label}: ${message}`;
        button.addEventListener('click', () => goTo(input));
        item.append(button); list.append(item);
        if (input) {
          if (!summaryAttributes.has(input)) summaryAttributes.set(input, {'aria-invalid': input.getAttribute('aria-invalid'), 'aria-describedby': input.getAttribute('aria-describedby')});
          input.setAttribute('aria-invalid','true');
          item.id = `pc-error-${list.children.length}`;
          input.setAttribute('aria-describedby', `${input.getAttribute('aria-describedby') || ''} ${item.id}`.trim());
        }
      });
    });
    box.append(list); box.focus({preventScroll:true}); box.scrollIntoView({block:'center'});
  }
  for (const wrapper of form.querySelectorAll('[data-pw-field]')) {
    const input = wrapper.querySelector('input:not([type=hidden]),select,textarea');
    if (!input) continue;
    const ids = [...wrapper.querySelectorAll('.pw-help[id], [id$=_errors], .pw-client-error[id]')].map(node => node.id);
    if (ids.length) input.setAttribute('aria-describedby', `${input.getAttribute('aria-describedby') || ''} ${ids.join(' ')}`.trim());
    if (wrapper.querySelector('.pw-error')) input.setAttribute('aria-invalid','true');
  }
  function updateMarkers() {
    const required = new Set(readiness.items.filter(item => item.code !== 'phone').map(item => item.field));
    if (readiness.items.some(item => item.code === 'age') && form.elements.namedItem('age_open_ended')?.value !== '1') required.add('age_to');
    if (readiness.items.some(item => item.code === 'region')) { required.add('region'); if (form.elements.namedItem('region')?.value !== 'baku') required.delete('district'); }
    if (readiness.items.some(item => item.code === 'price')) required.add('price_mode');
    if (readiness.items.some(item => item.code === 'schedule')) required.add('schedule_mode');
    const contact = readiness.items.find(item => item.code === 'phone');
    const contactNeeded = contact && !contact.config.inherited && form.elements.namedItem('nature')?.value !== contact.config.optional_nature;
    form.querySelectorAll('[data-pw-required]').forEach(badge => {
      const name = badge.dataset.pwRequired;
      const oneContact = contact?.config.fields.includes(name) && contactNeeded;
      badge.textContent = oneContact ? ui.contact_choice : ui.required;
      badge.hidden = !required.has(name) && !oneContact;
      if (name === 'age_from' && form.elements.namedItem('age_open_ended')?.value === '1') badge.hidden = true;
    });
  }
  form.querySelectorAll('[data-pc-go-field]').forEach(button => button.addEventListener('click', () => goTo(fieldTarget(button.dataset.pcGoField))));
  const sectionSelect = form.querySelector('[data-pc-section-select]');
  const sectionLinks = [...form.querySelectorAll('.pc-nav a')];
  function selectSection(id, focus = false) {
    sectionLinks.forEach(link => { if (link.hash === `#${id}`) link.setAttribute('aria-current','location'); else link.removeAttribute('aria-current'); });
    sectionSelect.value = id;
    if (focus) goTo(document.getElementById(id)?.querySelector('h2'));
  }
  sectionSelect.addEventListener('change', () => selectSection(sectionSelect.value, true));
  sectionLinks.forEach(link => link.addEventListener('click', event => { event.preventDefault(); selectSection(link.hash.slice(1), true); }));
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => { const visible = entries.find(entry => entry.isIntersecting); if (visible) selectSection(visible.target.id); }, {rootMargin:'-15% 0px -60% 0px'});
    form.querySelectorAll('[data-place-section]').forEach(section => observer.observe(section));
  }
  const openAge = form.querySelector('[data-pc-open-age]');
  const ageEnd = form.querySelector('[name=age_to]')?.closest('[data-pw-field]');
  const syncAge = () => { form.elements.namedItem('age_open_ended').value = openAge.checked ? '1' : ''; if (ageEnd) ageEnd.hidden = openAge.checked; updateMarkers(); };
  if (openAge) { openAge.addEventListener('change', syncAge); syncAge(); }
  const firstError = form.querySelector('.pw-error');
  if (firstError) {
    const errors = {};
    form.querySelectorAll('[data-pw-field]').forEach(wrapper => { const messages = [...wrapper.querySelectorAll('.pw-error')].map(node => node.textContent.trim()); if (messages.length) errors[wrapper.dataset.pwField] = messages; });
    if (!Object.keys(errors).length) errors.__all__ = [firstError.textContent.trim()];
    showErrors(errors); setStatus(ui.saving_error, 'error');
  } else setStatus(targetId === null ? ui.not_saved : ui.saved_card, targetId === null ? 'idle' : 'saved');
  form.addEventListener('pointerdown', event => { if (event.isTrusted) userInteracted = true; });
  form.addEventListener('keydown', event => { if (event.isTrusted) userInteracted = true; });
  form.addEventListener('input', event => { if (event.target === sectionSelect || event.target?.matches('[data-pc-preview-language]')) { updatePreview(); return; } if (restoring || (!event.isTrusted && !userInteracted)) return; userInteracted = true; dirty = true; editedAt = Date.now(); localStore(); schedule(); updatePreview(); updateMarkers(); setStatus(ui.unsaved, 'dirty'); form.querySelector('[data-pc-readiness-status]').textContent = ui.needs_check; });
  form.addEventListener('change', event => {
    if (event.target === sectionSelect || event.target?.matches('[data-pc-preview-language]')) { updatePreview(); return; }
    if (restoring || (!event.isTrusted && !userInteracted)) return;
    userInteracted = true; dirty = true; editedAt = Date.now(); localStore(); schedule(); updatePreview(); updateMarkers(); setStatus(ui.unsaved, 'dirty'); form.querySelector('[data-pc-readiness-status]').textContent = ui.needs_check;
    if (event.target?.type === 'file') { photoDirty = true; localStore(); setStatus(ui.upload_pending, 'browser'); }
  });
  ['km:pricing-change','km:schedule-change','km:map-change','km:photos-change','km:offerings-change'].forEach(name => form.addEventListener(name, () => { if (restoring || (!userInteracted && !(name === 'km:photos-change' && photoEditor?.hasChanges()))) return; userInteracted = true; dirty = true; editedAt = Date.now(); localStore(); schedule(); updatePreview(); updateMarkers(); setStatus(ui.unsaved, 'dirty'); form.querySelector('[data-pc-readiness-status]').textContent = ui.needs_check; if (name === 'km:photos-change') { photoDirty = true; localStore(); setStatus(ui.upload_pending, 'browser'); } }));
  form.addEventListener('submit', async event => {
    if (halted) { event.preventDefault(); setStatus(ui.server_conflict, 'conflict'); return; }
    if (submitting) { event.preventDefault(); return; }
    const submitter = event.submitter;
    if (submitter?.matches('[data-pc-save-draft]') && !photoDirty) {
      event.preventDefault(); clearTimeout(timer); dirty = true; localStore();
      do { if (!await save(true)) break; } while (dirty && !halted);
      return;
    }
    if (!navigator.onLine) { event.preventDefault(); localStore(); setStatus(ui.offline, 'browser'); return; }
    if (photoEditor) {
      event.preventDefault(); submitting = true; clearTimeout(timer);
      if (saving) await inFlight;
      try {
        const result = await photoEditor.save(submitter);
        if (!result.ok) {
          if (result.conflict === 'candidate_version_conflict') {
            showErrors({__all__: [ui.server_conflict]});
            candidateConflict = true; halted = true; clearTimeout(timer); localStore();
            setStatus(ui.server_conflict, 'conflict');
          } else {
            showErrors(result.errors || {}, result.error_targets || {});
            setStatus(ui.save_failed, 'error');
          }
          return;
        }
        dirty = false; photoDirty = false;
        try { localStorage.removeItem(localKey); } catch {}
        if (currentCandidateView) {
          const redirect = new URL(result.redirect, location.href);
          redirect.searchParams.set('candidate_current', '1');
          location.assign(redirect.href);
        } else location.assign(result.redirect);
      } catch { setStatus(ui.save_failed, 'error'); }
      finally { submitting = false; }
    } else { submitting = true; clearTimeout(timer); }
  });
  window.addEventListener('online', () => { if (dirty) schedule(); });
  window.addEventListener('offline', () => setStatus(ui.offline, 'browser'));
  window.addEventListener('pageshow', () => { submitting = false; });
  window.addEventListener('beforeunload', event => { if ((dirty || photoDirty) && !submitting) { event.preventDefault(); event.returnValue = ''; } });
  updatePreview(); updateMarkers(); restore();
})();
