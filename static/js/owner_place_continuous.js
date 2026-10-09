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
  const localKey = `kidsmap:place:continuous:${form.dataset.accountId}:${form.dataset.draftKey}${currentDraftView ? ':current' : ''}`;
  const targetId = form.dataset.targetId ? Number(form.dataset.targetId) : null;
  const currentPhoto = form.querySelector('[data-pc-photo-current]')?.dataset.pcPhotoCurrent;
  const mainPhoto = form.querySelector('[data-photo-saved=main]');
  if (currentPhoto && mainPhoto) mainPhoto.dataset.photoPreview = currentPhoto;
  const photoEditor = window.KidsMapPhotoEditor?.mount(form);
  let draftId = form.dataset.fresh === '1' ? null : new URL(location.href).searchParams.get('draft_id'), draftVersion = 0, sourceVersion = Number(form.dataset.sourceVersion);
  let timer = null, saving = false, dirty = false, halted = false, submitting = false, restoring = false, userInteracted = false;
  let inFlight = null, photoDirty = false, editedAt = Date.now();
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
  const setStatus = (message, state) => {
    if (halted && state !== 'conflict') { message = ui.server_conflict; state = 'conflict'; }
    status.textContent = message; status.dataset.state = state;
    const actions = form.querySelector('[data-pc-conflict-actions]');
    actions.hidden = state !== 'conflict';
    const url = new URL(location.href);
    url.searchParams.set('draft_current', '1');
    if (draftId) url.searchParams.set('draft_id', draftId);
    actions.querySelector('a').href = url.href;
  };
  const localStore = () => {
    try { localStorage.setItem(localKey, JSON.stringify({fields: fields(), at: editedAt, draftId, draftVersion, sourceVersion, serverSaved: !dirty, photoPending: photoDirty, conflict: halted})); }
    catch { setStatus(ui.storage_error, 'error'); }
  };
  const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;
  function apply(saved) {
    if (!saved || !saved.fields || form.dataset.pwBound === '1') return;
    restoring = true;
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
    restoring = false; updatePreview();
  }
  async function restore() {
    if (form.dataset.pwBound === '1') return;
    let local = null;
    try { local = JSON.parse(localStorage.getItem(localKey) || 'null'); } catch {}
    if (form.dataset.fresh === '1' && !local) return;
    if (local) {
      draftId = local.draftId || null; draftVersion = Number(local.draftVersion) || 0;
      editedAt = local.at || Date.now();
      form.elements.namedItem('server_draft_id').value = draftId || ''; apply(local);
      setStatus(local.photoPending ? ui.restored : ui.browser_saved, 'browser');
      if (local.sourceVersion != null && local.sourceVersion !== sourceVersion) { halted = true; setStatus(ui.structure_conflict, 'conflict'); return; }
      if (local.conflict) { halted = true; setStatus(ui.server_conflict, 'conflict'); return; }
    }
    try {
      const response = await fetch(form.dataset.draftUrl, {credentials:'same-origin'});
      if (!response.ok) throw new Error('read');
      const rows = (await response.json()).drafts || [];
      if (local?.draftId && rows.some(item => item.draft_id === local.draftId && item.materialized_place_id)) {
        localStorage.removeItem(localKey);
        const url = new URL(location.href); url.searchParams.delete('draft_session'); url.searchParams.set('fresh', '1'); location.replace(url.href);
        return;
      }
      const list = rows.filter(item => !item.materialized_place_id);
      const selected = list.find(item => item.target_type === 'place' && item.target_id === targetId &&
        (draftId ? item.draft_id === draftId : targetId !== null));
      if (!selected || selected.materialized_place_id) return;
      const detailResponse = await fetch(`${form.dataset.draftUrl}${selected.draft_id}/`, {credentials:'same-origin'});
      if (!detailResponse.ok) throw new Error('detail');
      const detail = await detailResponse.json();
      if (local && !local.serverSaved && local.draftId === detail.draft_id && local.draftVersion !== detail.version) {
        halted = true; localStore(); setStatus(ui.server_conflict, 'conflict'); return;
      }
      draftId = detail.draft_id; draftVersion = detail.version; form.elements.namedItem('server_draft_id').value = draftId;
      if (targetId === null) root.querySelector('[data-pc-lifecycle]').textContent = ui.state_draft;
      if (userInteracted) { dirty = true; localStore(); schedule(); return; }
      if (!local || Date.parse(detail.saved_at) >= local.at) {
        apply(detail);
        setStatus(`${ui.server_saved} · ${new Date(detail.saved_at).toLocaleString()}${local?.photoPending ? ' · ' + ui.restored : ''}`, 'saved');
        localStore();
      } else { dirty = true; schedule(); setStatus(ui.browser_saved, 'browser'); }
    } catch { if (!local) setStatus(ui.save_failed, 'error'); }
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
  function fieldTarget(name, messages = '') {
    if (name === 'nested_pricing') {
      const path = String(messages);
      const ai = path.match(/activities[.\[]([0-9]+)/)?.[1];
      const gi = path.match(/groups[.\[]([0-9]+)/)?.[1];
      const pi = path.match(/pricing_plans[.\[]([0-9]+)/)?.[1];
      let scope = ai == null ? form.querySelector('[data-pc-offerings]') : form.querySelector(`[data-activity-index="${ai}"]`);
      if (gi != null) scope = scope?.querySelector(`[data-group-index="${gi}"]`);
      if (pi != null) scope = scope?.querySelector(`[data-plan-index="${pi}"]`);
      const key = path.match(/\.(age_from|age_to|price_min|price_max|price|name_az|category_id|subcategory_id)\b/)?.[1];
      return (key && scope?.querySelector(`[data-offering-key="${key}"]`)) || scope?.querySelector('input,select,textarea') || form.querySelector('[data-pc-add-activity]');
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
  function showErrors(errors) {
    const box = form.querySelector('[data-pc-errors]'); box.replaceChildren();
    if (!Object.keys(errors).length) { box.hidden = true; return; }
    box.hidden = false; const heading = document.createElement('strong'); heading.textContent = ui.errors_title; box.append(heading);
    const list = document.createElement('ul');
    Object.entries(errors).forEach(([name, messages]) => {
      const input = fieldTarget(name, messages), wrapper = input?.closest('[data-pw-field]');
      const item = document.createElement('li'), button = document.createElement('button');
      let message = Array.isArray(messages) ? messages.join(' ') : String(messages);
      if (message.includes('Candidate version conflict')) message = ui.server_conflict;
      const label = name === 'nested_pricing' ? ui.section_offer : wrapper?.querySelector('label')?.textContent?.trim() || input?.getAttribute('aria-label') || ui.errors_title;
      button.type = 'button'; button.textContent = `${label}: ${message}`;
      button.addEventListener('click', () => goTo(input));
      item.append(button); list.append(item);
      if (input) {
        input.setAttribute('aria-invalid','true');
        item.id = `pc-error-${list.children.length}`;
        input.setAttribute('aria-describedby', `${input.getAttribute('aria-describedby') || ''} ${item.id}`.trim());
      }
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
  ['km:pricing-change','km:schedule-change','km:map-change','km:photos-change','km:offerings-change'].forEach(name => form.addEventListener(name, () => { if (restoring || !userInteracted) return; dirty = true; editedAt = Date.now(); localStore(); schedule(); updatePreview(); updateMarkers(); setStatus(ui.unsaved, 'dirty'); form.querySelector('[data-pc-readiness-status]').textContent = ui.needs_check; if (name === 'km:photos-change') { photoDirty = true; localStore(); setStatus(ui.upload_pending, 'browser'); } }));
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
        if (!result.ok) { showErrors(result.errors || {}); setStatus(ui.save_failed, 'error'); return; }
        dirty = false; photoDirty = false;
        try { localStorage.removeItem(localKey); } catch {}
        location.assign(result.redirect);
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
