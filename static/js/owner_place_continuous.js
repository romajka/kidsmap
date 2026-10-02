(() => {
  'use strict';
  const root = document.querySelector('[data-place-mode="continuous"]');
  const form = root?.querySelector('[data-permanent-place-form]');
  if (!form) return;
  const ui = JSON.parse(document.getElementById('pw-copy').textContent);
  const allowed = new Set(JSON.parse(document.getElementById('pc-draft-fields').textContent));
  const status = form.querySelector('[data-pc-save-status]');
  const localKey = `kidsmap:place:continuous:${form.dataset.accountId}:${form.dataset.draftKey}`;
  const targetId = form.dataset.targetId ? Number(form.dataset.targetId) : null;
  const photoEditor = window.KidsMapPhotoEditor?.mount(form);
  let draftId = null, draftVersion = 0, sourceVersion = Number(form.dataset.sourceVersion);
  let timer = null, saving = false, dirty = false, halted = false, submitting = false, restoring = false, userInteracted = false;
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
  const setStatus = (message, state) => { status.textContent = message; status.dataset.state = state; };
  const localStore = () => {
    try { localStorage.setItem(localKey, JSON.stringify({fields: fields(), at: Date.now(), draftId, draftVersion})); }
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
    if (local) { draftId = local.draftId || null; draftVersion = Number(local.draftVersion) || 0; form.elements.namedItem('server_draft_id').value = draftId || ''; apply(local); setStatus(ui.browser_saved, 'browser'); }
    try {
      const response = await fetch(form.dataset.draftUrl, {credentials:'same-origin'});
      if (!response.ok) throw new Error('read');
      const rows = (await response.json()).drafts || [];
      if (local?.draftId && rows.some(item => item.draft_id === local.draftId && item.materialized_place_id)) {
        localStorage.removeItem(localKey);
        const url = new URL(location.href); url.searchParams.set('fresh', '1'); location.replace(url.href);
        return;
      }
      const list = rows.filter(item => !item.materialized_place_id);
      const selected = list.find(item => item.target_type === 'place' && item.target_id === targetId && (!draftId || item.draft_id === draftId)) ||
        (!draftId && list.find(item => item.target_type === 'place' && item.target_id === targetId));
      if (!selected || selected.materialized_place_id) return;
      const detailResponse = await fetch(`${form.dataset.draftUrl}${selected.draft_id}/`, {credentials:'same-origin'});
      if (!detailResponse.ok) throw new Error('detail');
      const detail = await detailResponse.json();
      draftId = detail.draft_id; draftVersion = detail.version; form.elements.namedItem('server_draft_id').value = draftId;
      if (userInteracted) { dirty = true; localStore(); schedule(); return; }
      if (!local || Date.parse(detail.saved_at) >= local.at) {
        apply(detail);
        setStatus(`${ui.server_saved} · ${new Date(detail.saved_at).toLocaleString()}`, 'saved');
      } else { dirty = true; schedule(); setStatus(ui.browser_saved, 'browser'); }
    } catch { if (!local) setStatus(ui.save_failed, 'error'); }
  }
  async function save(force = false) {
    if (saving || halted || submitting || (!dirty && !force)) return;
    if (!navigator.onLine) { localStore(); setStatus(ui.offline, 'browser'); return; }
    saving = true; const submitted = fields();
    setStatus(ui.server_saving, 'saving');
    try {
      const response = await fetch(form.dataset.draftUrl, {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json','X-CSRFToken':csrf}, body:JSON.stringify({draft_id:draftId, target_type:'place', target_id:targetId, schema_version:Number(form.dataset.schemaVersion), source_version:sourceVersion, expected_version:draftVersion, fields:submitted})});
      const result = await response.json();
      if (response.status === 409) { halted = true; localStore(); setStatus(ui.server_conflict, 'conflict'); return; }
      if (!response.ok) throw new Error(result.status || 'save');
      draftId = result.draft_id; draftVersion = result.version; form.elements.namedItem('server_draft_id').value = draftId;
      if (JSON.stringify(fields()) === JSON.stringify(submitted)) {
        dirty = false;
        try { localStorage.removeItem(localKey); } catch {}
      } else { localStore(); }
      const pendingPhoto = [...form.querySelectorAll('input[type=file]')].some(input => input.files.length);
      setStatus(`${ui.server_saved} · ${new Date(result.saved_at).toLocaleString()}${pendingPhoto ? ' · ' + ui.upload_pending : ''}`, 'saved');
    } catch { localStore(); setStatus(ui.save_failed, 'error'); }
    finally { saving = false; }
  }
  function schedule() { clearTimeout(timer); timer = setTimeout(() => save(), 900); }
  form.querySelector('[data-pc-save-draft]')?.addEventListener('click', () => { clearTimeout(timer); dirty = true; localStore(); save(true); });
  function updatePreview() {
    const name = form.elements.namedItem('name_az')?.value || form.elements.namedItem('name_ru')?.value || ui.empty;
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
  function showErrors(errors) {
    const box = form.querySelector('[data-pc-errors]'); box.replaceChildren();
    if (!Object.keys(errors).length) { box.hidden = true; return; }
    box.hidden = false; const list = document.createElement('ul');
    Object.entries(errors).forEach(([name, messages]) => {
      const input = name === 'nested_pricing' ? (form.querySelector('.pc-activity-card input') || form.querySelector('[data-pc-add-activity]')) : [...form.querySelectorAll('[name]')].find(node => node.name === name);
      const item = document.createElement('li'); const button = document.createElement('button');
      button.type = 'button'; button.textContent = `${name === 'nested_pricing' ? ui.section_offer : input?.closest('[data-pw-field]')?.querySelector('label')?.textContent?.trim() || name}: ${Array.isArray(messages) ? messages.join(' ') : messages}`;
      button.addEventListener('click', () => { input?.closest('details')?.setAttribute('open', ''); input?.scrollIntoView({block:'center'}); input?.focus(); });
      item.append(button); list.append(item); input?.setAttribute('aria-invalid','true');
    });
    box.append(list);
  }
  for (const error of form.querySelectorAll('.pw-error')) {
    const input = error.closest('[data-pw-field]')?.querySelector('input,select,textarea');
    if (input) input.setAttribute('aria-invalid','true');
  }
  const openAge = form.querySelector('[data-pc-open-age]');
  const ageEnd = form.querySelector('[name=age_to]')?.closest('[data-pw-field]');
  const syncAge = () => { form.elements.namedItem('age_open_ended').value = openAge.checked ? '1' : ''; if (ageEnd) ageEnd.hidden = openAge.checked; };
  if (openAge) { openAge.addEventListener('change', syncAge); syncAge(); }
  const firstError = form.querySelector('.pw-error');
  if (firstError) { firstError.closest('details')?.setAttribute('open',''); firstError.closest('[data-place-section]')?.scrollIntoView({block:'start'}); }
  form.addEventListener('pointerdown', event => { if (event.isTrusted) userInteracted = true; });
  form.addEventListener('keydown', event => { if (event.isTrusted) userInteracted = true; });
  form.addEventListener('input', event => { if (restoring || (!event.isTrusted && !userInteracted)) return; userInteracted = true; dirty = true; localStore(); schedule(); updatePreview(); });
  form.addEventListener('change', event => {
    if (restoring || (!event.isTrusted && !userInteracted)) return;
    userInteracted = true; dirty = true; localStore(); schedule(); updatePreview();
    if (event.target?.type === 'file') setStatus(ui.upload_pending, 'browser');
  });
  ['km:pricing-change','km:schedule-change','km:map-change','km:photos-change','km:offerings-change'].forEach(name => form.addEventListener(name, () => { if (restoring || !userInteracted) return; dirty = true; localStore(); schedule(); updatePreview(); if (name === 'km:photos-change') setStatus(ui.upload_pending, 'browser'); }));
  form.addEventListener('submit', async event => {
    if (submitting) { event.preventDefault(); return; }
    const submitter = event.submitter;
    if (submitter?.value === 'save_and_publish') {
      const invalid = [...form.querySelectorAll('input,select,textarea')].find(input => !input.disabled && !input.checkValidity());
      if (invalid) { event.preventDefault(); showErrors({[invalid.name]: invalid.validationMessage}); return; }
    }
    if (!navigator.onLine) { event.preventDefault(); localStore(); setStatus(ui.offline, 'browser'); return; }
    if (photoEditor) {
      event.preventDefault(); submitting = true; clearTimeout(timer);
      try {
        const result = await photoEditor.save(submitter);
        if (!result.ok) { showErrors(result.errors || {}); setStatus(ui.save_failed, 'error'); return; }
        try { localStorage.removeItem(localKey); } catch {}
        location.assign(result.redirect);
      } catch { setStatus(ui.save_failed, 'error'); }
      finally { submitting = false; }
    } else { submitting = true; clearTimeout(timer); }
  });
  window.addEventListener('online', () => { if (dirty) schedule(); });
  window.addEventListener('offline', () => setStatus(ui.offline, 'browser'));
  window.addEventListener('pageshow', () => { submitting = false; });
  updatePreview(); restore();
})();
