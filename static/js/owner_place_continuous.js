(() => {
  'use strict';
  const root = document.querySelector('[data-place-mode="continuous"]');
  const form = root?.querySelector('[data-permanent-place-form]');
  if (!form) return;
  const ui = JSON.parse(document.getElementById('pw-copy').textContent);
  let readiness = JSON.parse(document.getElementById('pc-readiness').textContent);
  const language = (document.documentElement.lang || 'az').slice(0, 2);
  const text = (ru, az, en) => ({ru, az, en}[language] || az);
  const mascotController = window.KidsMapOwnerMappy?.mount(root.querySelector('[data-pc-mappy]'));
  const setText = (node, value) => { if (node && node.textContent !== value) node.textContent = value; };
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
  form.photoEditor = photoEditor;
  const draftMedia = window.KidsMapDraftMedia?.mount(form, photoEditor);
  let draftId = form.dataset.fresh === '1' ? null : (new URL(location.href).searchParams.get('draft_id') || form.elements.namedItem('server_draft_id')?.value || null), draftVersion = Number(form.elements.namedItem('server_draft_version')?.value) || 0, sourceVersion = Number(form.dataset.sourceVersion);
  let timer = null, saving = false, dirty = false, halted = false, submitting = false, restoring = false, userInteracted = false;
  let inFlight = null, photoDirty = false, editedAt = Date.now();
  let candidateConflict = false, restoreFailed = false, restorePromise = null, pendingText = null, mediaResume = null;
  if (targetId === null) {
    const url = new URL(location.href);
    url.searchParams.delete('fresh');
    if (form.dataset.fresh === '1') url.searchParams.delete('draft_id');
    url.searchParams.set('draft_session', form.elements.namedItem('draft_client_key').value);
    history.replaceState(null, '', url);
  }
  const fields = () => {
    const result = {};
    if (photoEditor?.snapshotMedia) result._draft_media_selection = photoEditor.snapshotMedia().map(({id,role,order})=>({id,role,order}));
    if (form.dataset.baseSignature) result._editor_base_signature = form.dataset.baseSignature;
    if (allowed.has('delete_gallery_ids')) result.delete_gallery_ids = [];
    for (const input of form.querySelectorAll('[name]')) {
      if (!allowed.has(input.name) || input.disabled || input.type === 'file') continue;
      if (input.type === 'radio' && !input.checked) continue;
      if (input.name === 'delete_gallery_ids') { if (input.checked) (result[input.name] ||= []).push(input.value); }
      else if (input.type === 'checkbox') result[input.name] = input.checked;
      else if (['pricing_plans','nested_pricing','structured_schedule','public_links','gallery_order'].includes(input.name)) {
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
  const formatTime = iso => {
    try {
      const d = new Date(iso);
      if (isNaN(d.getTime())) return '';
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    } catch { return ''; }
  };
  const setStatus = (message, state) => {
    if (halted && state !== 'conflict') { message = ui.server_conflict; state = 'conflict'; }
    status.textContent = message; status.dataset.state = state;
    const savedLink = form.querySelector('[data-pc-saved-link]');
    if (savedLink) savedLink.hidden = !draftId || ['error', 'browser', 'conflict'].includes(state);
    const retry = form.querySelector('[data-pc-save-retry]');
    if (retry) retry.hidden = !['error', 'browser'].includes(state);
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
    let versionInput=form.elements.namedItem('server_draft_version');
    if(!versionInput){versionInput=document.createElement('input');versionInput.type='hidden';versionInput.name='server_draft_version';form.append(versionInput);}
    versionInput.value=String(draftVersion);
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
        else if (input.name === 'delete_gallery_ids') input.checked = Array.isArray(value) && value.includes(input.value);
        else if (input.type === 'checkbox') input.checked = Boolean(value);
        else input.value = typeof value === 'object' ? JSON.stringify(value) : String(value ?? '');
      }
      controls[0]?.dispatchEvent(new Event('input', {bubbles:true}));
      controls[0]?.dispatchEvent(new Event('change', {bubbles:true}));
    }
    if (saved.fields.structured_schedule !== undefined) form.elements.namedItem('structured_schedule')?.dispatchEvent(new CustomEvent('km:schedule-import', {bubbles:true}));
    if (openAge) { openAge.checked = form.elements.namedItem('age_open_ended').value === '1'; syncAge(); }
    } finally {
      restoring = false;
      form.dispatchEvent(new CustomEvent('km:location-restore-end', {bubbles:true}));
    }
    updatePreview(); scheduleReadiness();
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
      let selected = draftId ? {draft_id:draftId} : null;
      if (!selected && targetId !== null) {
        const response = await fetch(form.dataset.draftUrl, {credentials:'same-origin'});
        if (!response.ok) throw new Error('read');
        const rows = (await response.json()).drafts || [];
        selected = rows.find(item => item.target_type === 'place' && item.target_id === targetId && !item.materialized_place_id);
      }
      if (selected) {
        const detailResponse = await fetch(`${form.dataset.draftUrl}${selected.draft_id}/`, {credentials:'same-origin'});
        if (detailResponse.status === 409) { halted=true;candidateConflict=targetId!==null;setStatus(ui.server_conflict,'conflict');return; }
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
          draftId=detail.draft_id;draftVersion=detail.version;
          form.elements.namedItem('server_draft_id').value = draftId || ''; apply(local);
          if (draftMedia) { restoring=true;try {await draftMedia.restore(detail);} finally {restoring=false;} }
          restoreFailed=false;
          dirty = true; localStore(); schedule(); setStatus(ui.browser_saved, 'browser'); return;
        }
        // Server copies have no persisted candidate-base token. Divergent data requires a choice.
        if (targetId !== null && !local && !(form.dataset.baseSignature && detail.fields?._editor_base_signature === form.dataset.baseSignature) && JSON.stringify(detail.fields) !== JSON.stringify(canonicalFields)) {
          offerRecovery(local || detail); return;
        }
        draftId = detail.draft_id; draftVersion = detail.version;
        form.elements.namedItem('server_draft_id').value = draftId;
        const timeStr = formatTime(detail.saved_at);
        apply(detail);
        if (draftMedia) {
          restoring = true;
          try { await draftMedia.restore(detail); photoDirty = draftMedia.hasPending(); }
          finally { restoring = false; }
        }
        restoreFailed=false;
        if(photoDirty){dirty=true;schedule();}
        setStatus(dirty ? ui.unsaved : `${text('Сохранено в черновиках', 'Qaralamalarda saxlanıldı', 'Saved in drafts')}${timeStr ? ' · ' + timeStr : ''}`, dirty ? 'dirty' : 'saved'); localStore(); scheduleReadiness();
      } else if (local && !userInteracted) {
        draftId = null; draftVersion = 0; form.elements.namedItem('server_draft_id').value = '';
        apply(local); dirty = true; localStore(); schedule(); setStatus(ui.browser_saved, 'browser');
      }
    } catch {
      restoreFailed=Boolean(draftId);dirty=dirty || Boolean(local && !local.serverSaved);
      if (local && !userInteracted) {
        form.elements.namedItem('server_draft_id').value = draftId || ''; apply(local);
        setStatus(ui.save_failed, 'error');
      } else if (!local) setStatus(ui.save_failed, 'error');
    }
  }
  let lastSaveError=null;
  async function save(force = false) {
    if (restorePromise) await restorePromise;
    if (saving) return inFlight;
    if (restoreFailed || halted || submitting || (!dirty && !force)) return false;
    if (!navigator.onLine) { lastSaveError={kind:'network'};localStore(); setStatus(ui.offline, 'browser'); return false; }
    lastSaveError=null;saving = true; let succeeded = false;
    setStatus(ui.server_saving, 'saving');
    inFlight = (async () => {
      try {
        const adopt = updated => {draftId=updated.draft_id;draftVersion=updated.version;form.elements.namedItem('server_draft_id').value=draftId;localStore();};
        // Resolve a possibly committed media request before advancing the text
        // version; the transport replays the exact failed request once.
        if(mediaResume){mediaResume=await draftMedia.save(mediaResume,updated=>{mediaResume=updated;adopt(updated);});adopt(mediaResume);mediaResume=null;}
        if(!draftId)draftId=crypto.randomUUID();
        if(!pendingText)pendingText={draft_id:draftId,target_type:'place',target_id:targetId,schema_version:schemaVersion,source_version:sourceVersion,expected_version:draftVersion,fields:fields()};
        const submitted=pendingText.fields;
        const response = await fetch(form.dataset.draftUrl, {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json','X-CSRFToken':csrf}, body:JSON.stringify(pendingText)});
        let result;try{result=await response.json();}catch{throw Object.assign(new Error('invalid_response'),{status:response.status,kind:'server'});}
        if (response.status === 409) { lastSaveError={status:409};pendingText=null;halted = true; localStore(); setStatus(result.error === 'structure_changed' ? ui.structure_conflict : ui.server_conflict, 'conflict'); return false; }
        if (!response.ok) throw Object.assign(new Error(result.status || 'save'),{status:response.status});
        if(typeof result.draft_id!=='string'||!Number.isInteger(result.version)||result.version<1)throw Object.assign(new Error('invalid_response'),{kind:'server'});
        pendingText=null;
        draftId = result.draft_id; draftVersion = result.version; form.elements.namedItem('server_draft_id').value = draftId;
        if (draftMedia) {
          mediaResume=result;
          const mediaResult = await draftMedia.save(result, updated => { mediaResume=updated;adopt(updated); });
          mediaResume=null;
          if (mediaResult?.version) draftVersion = mediaResult.version;
          photoDirty = draftMedia.hasPending();
        }
        if (targetId === null) root.querySelector('[data-pc-lifecycle]').textContent = ui.state_draft;
        dirty = photoDirty || JSON.stringify(fields()) !== JSON.stringify(submitted);
        succeeded = true; localStore();
        if (targetId === null) { const url = new URL(location.href); url.searchParams.set('draft_id', draftId); history.replaceState(null, '', url); }
        const saveTime = formatTime(result.saved_at);
        setStatus(dirty ? ui.unsaved : `${text('Сохранено в черновиках', 'Qaralamalarda saxlanıldı', 'Saved in drafts')}${saveTime ? ' · ' + saveTime : ''}${photoDirty ? ' · ' + ui.upload_pending : ''}`, dirty || photoDirty ? 'dirty' : 'saved');
        return true;
      } catch (error) { lastSaveError=error;if(error?.status&&error.status<500)pendingText=null;if (error?.status === 409 || error?.conflict) halted = true; localStore(); setStatus(halted ? ui.server_conflict : ui.save_failed, halted ? 'conflict' : 'error'); return false; }
      finally { saving = false; if (succeeded && dirty && !halted && !submitting) schedule(); }
    })();
    return inFlight;
  }
  function schedule() { clearTimeout(timer); timer = setTimeout(() => save(), 900); scheduleReadiness(); }

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
    if (!rect.width || !rect.height || rect.bottom <= 0 || rect.top >= innerHeight) return;
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
    if (focusAdjustment && Math.abs(delta) > 1) window.scrollBy({top:delta, behavior:'instant'});
  }
  let focusFrame = null, focusAdjustment = false, pointerFocusTarget = null, tabFocusAt = -Infinity;
  function scheduleFocusVisibility(adjust = false) {
    focusAdjustment ||= adjust;
    if (focusFrame !== null) cancelAnimationFrame(focusFrame);
    focusFrame = requestAnimationFrame(() => { focusFrame = null; keepFocusVisible(); focusAdjustment = false; });
  }
  form.addEventListener('pointerdown', event => { pointerFocusTarget = event.target.closest('input,textarea,select,button,summary,[role=combobox]'); }, true);
  form.addEventListener('keydown', event => { if (event.key === 'Tab') tabFocusAt = performance.now(); }, true);
  form.addEventListener('focusin', event => {
    const direct = event.target === pointerFocusTarget || performance.now() - tabFocusAt < 150;
    pointerFocusTarget = null; tabFocusAt = -Infinity;
    scheduleFocusVisibility(direct);
  });
  window.addEventListener('resize', () => scheduleFocusVisibility());
  if ('ResizeObserver' in window) {
    // Background save/layout changes update offsets, never the user's scroll.
    const focusSurfaces = new ResizeObserver(() => scheduleFocusVisibility());
    form.querySelectorAll('.pc-nav, .pc-savebar, .pc-actions').forEach(surface => focusSurfaces.observe(surface));
  }

  function updatePreview() {
    const language = form.querySelector('[data-pc-preview-language]')?.value || 'az';
    const translated = prefix => form.elements.namedItem(`${prefix}_${language}`)?.value || form.elements.namedItem(`${prefix}_az`)?.value || (prefix === 'name' ? form.elements.namedItem('name')?.value : '') || '';
    const name = translated('name') || ui.empty;
    setText(root.querySelector('[data-pc-preview-description]'), translated('description'));
    const address = form.elements.namedItem('address')?.value || '';
    setText(root.querySelector('[data-pc-preview-name]'), name);
    setText(root.querySelector('[data-pc-preview-address]'), address);
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
    setText(root.querySelector('[data-pc-preview-offerings]'), activities.length ? `${counted(activities.length, 'activity_count')} · ${counted(groupCount, 'group_count')}` : '');
    const count = directCount + groupPlans;
    setText(root.querySelector('[data-pc-preview-price]'), count ? counted(count, 'plan_count') : ui.empty);
  }
  function fieldTarget(name, path = null) {
    if (['photo','gallery_images','gallery_uploads'].includes(name)) return form.querySelector('[data-place-photos-picker]');
    if (['age_from','age_to'].includes(name) && form.querySelector(`#id_${name}_range`)) return form.querySelector(`#id_${name}_range`);
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
    if(window.KidsMapEditorUX){window.KidsMapEditorUX.focus(input);return;}
    for (let parent = input.parentElement; parent; parent = parent.parentElement) if (parent.tagName === 'DETAILS') parent.open = true;
    input.scrollIntoView({block:'center', behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
    input.focus({preventScroll:true});
  }
  const summaryAttributes = new Map();
  function showErrors(errors, targets = {}) {
    if (window.KidsMapEditorUX) {
      window.KidsMapEditorUX.setErrors(form,errors,{paths:targets,formatMessage:message=>String(message).includes('Candidate version conflict')?ui.server_conflict:String(message),resolveTarget:(name,index)=>name==='nested_pricing'?fieldTarget(name,targets?.[name]?.[index]):null});
      return;
    }
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
  function contactOptional(config) {
    const category = String(form.elements.namedItem('category')?.value || '');
    const subcategory = String(form.elements.namedItem('subcategory')?.value || '');
    return Boolean(config?.optional_pairs?.[category]?.includes(subcategory) ||
      (config?.optional && category === config.original_category && subcategory === config.original_subcategory));
  }
  function filledContact(name) {
    if (name === 'whatsapp_number' && form.elements.namedItem('whatsapp_mode')?.value !== 'separate') return false;
    return Boolean(form.elements.namedItem(name)?.value?.trim());
  }
  function contactInherited(config) {
    const mode = form.elements.namedItem('whatsapp_mode')?.value || 'legacy';
    return Boolean(config?.inherited_by_mode ? config.inherited_by_mode[mode] : config?.inherited);
  }
  function contactNeeded() {
    const contact = readiness.items.find(item => item.code === 'phone');
    return Boolean(contact && !contactInherited(contact.config) && !contactOptional(contact.config));
  }
  let markerSignature = null;
  function updateMarkers() {
    const required = new Set(readiness.items.filter(item => item.code !== 'phone').map(item => item.field));
    if (readiness.items.some(item => item.code === 'age') && form.elements.namedItem('age_open_ended')?.value !== '1') required.add('age_to');
    if (readiness.items.some(item => item.code === 'region')) { required.add('region'); if (form.elements.namedItem('region')?.value !== 'baku') required.delete('district'); }
    if (readiness.items.some(item => item.code === 'price')) required.add('price_mode');
    if (readiness.items.some(item => item.code === 'schedule')) required.add('schedule_mode');
    const contact = readiness.items.find(item => item.code === 'phone');
    const needsContact = contactNeeded();
    const signature = JSON.stringify([[...required].sort(), needsContact, contactInherited(contact?.config)]);
    if (signature === markerSignature) return;
    markerSignature = signature;
    const hint = form.querySelector('[data-pc-contact-hint]');
    if (hint) hint.textContent = contactInherited(contact?.config) ? ui.contact_inherited : needsContact ? ui.contact_required : ui.contact_optional;
    form.querySelectorAll('[data-pw-required]').forEach(badge => {
      const name = badge.dataset.pwRequired;
      const oneContact = name === 'contact_group' && needsContact;
      badge.textContent = oneContact ? ui.contact_choice : ui.required;
      badge.hidden = !required.has(name) && !oneContact;
      const field = badge.closest('[data-pw-field]');
      if(field){field.dataset.kmRequired=String(required.has(name));const control=field.querySelector(`[name="${name}"]:not([type=hidden])`)||field.querySelector(`#id_${name}_range`);control?.setAttribute('aria-required',String(required.has(name)));field.querySelectorAll('.select2-selection,.km-pf-picker-btn').forEach(proxy=>proxy.setAttribute('aria-required',String(required.has(name))));}
    });
  }
  form.querySelectorAll('[data-pc-go-field]').forEach(button => button.addEventListener('click', () => goTo(fieldTarget(button.dataset.pcGoField))));
  const sectionSelect = form.querySelector('[data-pc-section-select]');
  const sectionLinks = [...form.querySelectorAll('.pc-nav a')];
  let readinessTimer = null, readinessRevision = 0, readinessController = null;
  let readinessPending = false;
  let renderedReadiness = null, renderedPending = null, requirementsSignature = null;
  function updateStepProgress() {
    if (renderedReadiness === readiness && renderedPending === readinessPending) return;
    renderedReadiness = readiness; renderedPending = readinessPending;
    const groups = readiness.sections || [1,2,3,4].map(id => {
      const items = readiness.items.filter(item => Number(fieldTarget(item.field)?.closest('[data-place-section]')?.dataset.placeSection) === id);
      return {id, required_count:items.length, completed_count:items.filter(item=>item.complete).length, is_complete:items.every(item=>item.complete), error_count:0};
    });
    groups.forEach(group => {
      const badge = form.querySelector(`[data-pc-step-badge="${group.id}"]`);
      const tag = form.querySelector(`[data-pc-section-tag="${group.id}"]`);
      const state = readinessPending ? 'pending' : group.error_count ? 'error' : group.required_count && group.is_complete ? 'complete' : group.completed_count ? 'partial' : 'empty';
      const count = group.required_count ? `${group.completed_count}/${group.required_count}` : '—';
      for (const node of [badge,tag]) if (node) {
        node.dataset.status = state; node.dataset.tag = state; node.textContent = count;
        node.title = readinessPending ? text('Проверяем изменения…','Dəyişikliklər yoxlanılır…','Checking changes…') : group.error_count ? text('Исправьте отмеченные поля','İşarələnmiş sahələri düzəldin','Check the highlighted fields') : group.required_count ? count : text('Необязательно','İstəyə görə','Optional');
        node.setAttribute('aria-label',node.title);
      }
    });
    const total = Number(readiness.required_count) || 0, done = Number(readiness.completed_count) || 0;
    const percent = total ? Math.round(done / total * 100) : 0;
    const fill = root.querySelector('[data-pc-progress-fill]');
    if (fill) fill.style.width = `${percent}%`;
    const pct = root.querySelector('[data-pc-progress-pct]'); if (pct) pct.textContent = `${percent}%`;
    const bar = root.querySelector('[data-pc-progress-bar]'); if (bar) {bar.setAttribute('aria-valuenow',String(percent));bar.setAttribute('aria-valuetext',`${done}/${total}`);}
    const count = form.querySelector('[data-pc-ready-count]'); if (count) count.textContent = String(done);
    const required = form.querySelector('[data-pc-required-count]'); if (required) required.textContent = String(total);
    const summary = root.querySelector('[data-pc-progress-summary]');
    const message = readinessPending ? text('Проверяем изменения…','Dəyişikliklər yoxlanılır…','Checking changes…') : readiness.is_ready ? text('Можно отправлять на проверку','Yoxlamaya göndərə bilərsiniz','Ready to send for review') : readiness.error_count ? text('Исправьте отмеченные поля','İşarələnmiş sahələri düzəldin','Check the highlighted fields') : `${text('Заполнено','Doldurulub','Completed')} ${done}/${total} · ${text('Осталось','Qalıb','Remaining')} ${Math.max(0,total-done)}`;
    if (summary) summary.textContent = message;
    const mascot = root.querySelector('[data-pc-mappy]');
    if (mascotController) mascotController.update(readiness, readinessPending);
    else if (mascot) {
      const happy = !readinessPending && readiness.is_ready;
      mascot.dataset.state=happy?'ready':'help';
      const image=mascot.querySelector('img');
      if(image){
        image.onerror=()=>{if(image.getAttribute('src')!==mascot.dataset.welcome){mascot.dataset.success=mascot.dataset.welcome;image.src=mascot.dataset.welcome;}};
        const source=happy?mascot.dataset.success:mascot.dataset.welcome;
        if(image.getAttribute('src')!==source)image.src=source;
      }
      const caption=mascot.querySelector('p');if(caption)caption.textContent=message;
    }
    const list=form.querySelector('[data-pc-requirements-list]');
    const signature = JSON.stringify(readiness.items.map(item => [item.code,item.field,item.label,item.complete,item.message]));
    if(list && signature !== requirementsSignature){requirementsSignature=signature;list.replaceChildren();readiness.items.forEach(item=>{const row=document.createElement('li'),button=document.createElement('button');button.type='button';button.textContent=item.label;button.addEventListener('click',()=>goTo(fieldTarget(item.field)));row.append(button,document.createTextNode(' — '+(item.complete?text('Готово','Hazırdır','Ready'):item.message)));row.dataset.complete=String(item.complete);list.append(row);});}
  }
  function setReadiness(result) {
    if (!result || !Array.isArray(result.items) || !Array.isArray(result.sections)) return;
    readiness=result;readinessPending=false;updateStepProgress();updateMarkers();
  }
  async function checkReadiness() {
    const preview=form.querySelector('[data-km-preview]'); if(!preview||submitting) return;
    const revision=readinessRevision;
    if(readinessController)readinessController.abort();readinessController=new AbortController();
    try {
      const body=new FormData(form);body.set('_km_check_required','1');
      // Readiness does not need to upload the same files after every keystroke.
      // Photo format/queue errors stay with the photo editor; explicit check/save
      // validates actual bytes. Photos are not a publication requirement.
      for(const input of form.querySelectorAll('input[type=file][name]'))body.delete(input.name);
      body.delete('gallery_order');
      const values=Object.fromEntries([...body].filter(([,value])=>typeof value==='string'));
      const response=await fetch(preview.formAction,{method:'POST',body,credentials:'same-origin',signal:readinessController.signal,headers:{'X-CSRFToken':csrf}});
      if(!response.ok&&response.status!==422)throw Error('readiness');
      const result=await response.json();if(revision!==readinessRevision)return;
      if(result.readiness)setReadiness(result.readiness);
      if(result.errors&&typeof result.errors==='object'&&!Array.isArray(result.errors))form.dispatchEvent(new CustomEvent('km:server-validation',{detail:{errors:result.errors,error_targets:result.error_targets||{},values}}));
    } catch(error) {if(error.name==='AbortError'||revision!==readinessRevision)return;const label=root.querySelector('[data-pc-progress-summary]');if(label)label.textContent=text('Не удалось проверить заполнение. Попробуем снова после изменения.','Doldurulmanı yoxlamaq alınmadı. Dəyişiklikdən sonra yenidən yoxlayacağıq.','Could not check completion. We will retry after your next change.');}
  }
  function scheduleReadiness() {
    readinessRevision++;readinessPending=true;clearTimeout(readinessTimer);
    readinessTimer=setTimeout(checkReadiness,500);updateStepProgress();
  }
  form.addEventListener('km:validation-request',scheduleReadiness);

  let isNavigatingStep = false;
  function selectSection(id, focus = false) {
    sectionLinks.forEach(link => { if (link.hash === `#${id}`) link.setAttribute('aria-current','location'); else link.removeAttribute('aria-current'); });
    sectionSelect.value = id;
    const match = id.match(/\d+/);
    if (match) {
      const stepNum = match[0];
      const sectionEl = document.getElementById(id);
      const title = sectionEl?.querySelector('h2')?.textContent || '';
      const progressText = root.querySelector('[data-pc-progress-text]');
      if (progressText) progressText.textContent = `${ui.step || 'Шаг'} ${stepNum} ${ui.of || 'из'} 4 · ${title}`;
    }
    if (focus) {
      isNavigatingStep = true;
      setTimeout(() => { isNavigatingStep = false; }, 900);
      const sectionEl = document.getElementById(id);
      if (sectionEl) {
        sectionEl.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
        sectionEl.querySelector('h2')?.focus({ preventScroll: true });
      }
    }
  }
  sectionSelect.addEventListener('change', () => selectSection(sectionSelect.value, true));
  sectionLinks.forEach(link => link.addEventListener('click', event => { event.preventDefault(); selectSection(link.hash.slice(1), true); }));
  form.querySelectorAll('[data-pc-goto-step]').forEach(btn => {
    btn.addEventListener('click', () => {
      const stepNum = btn.dataset.pcGotoStep;
      selectSection(`pc-section-${stepNum}`, true);
    });
  });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      if (isNavigatingStep) return;
      const visibleEntries = entries.filter(entry => entry.isIntersecting);
      if (visibleEntries.length > 0) {
        visibleEntries.sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        selectSection(visibleEntries[0].target.id);
      }
    }, { threshold: [0.1, 0.25, 0.5, 0.75], rootMargin: '-70px 0px -40% 0px' });
    form.querySelectorAll('[data-place-section]').forEach(section => observer.observe(section));
  }
  const openAge = form.querySelector('[data-pc-open-age]');
  const ageEnd = form.querySelector('[name=age_to]')?.closest('[data-pw-field]');
  const syncAge = () => {
    if (openAge) form.elements.namedItem('age_open_ended').value = openAge.checked ? '1' : '';
    if (ageEnd && !form.querySelector('.km-age-range-field')) ageEnd.hidden = openAge.checked;
    form.querySelector('.km-age-range-field')?._syncFromInputs?.();
    updateMarkers();
    updateStepProgress();
  };
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
  form.addEventListener('input', event => { if (event.target === sectionSelect || event.target?.matches('[data-pc-preview-language]')) { updatePreview(); return; } if ((restoring && !event.isTrusted) || (!event.isTrusted && !userInteracted)) return; userInteracted = true; dirty = true; editedAt = Date.now(); localStore(); schedule(); updatePreview(); updateMarkers(); updateStepProgress(); setStatus(ui.unsaved, 'dirty'); form.querySelector('[data-pc-readiness-status]').textContent = ''; });
  form.addEventListener('change', event => {
    if (event.target === sectionSelect || event.target?.matches('[data-pc-preview-language]')) { updatePreview(); return; }
    if ((restoring && !event.isTrusted) || (!event.isTrusted && !userInteracted)) return;
    userInteracted = true; dirty = true; editedAt = Date.now(); localStore(); schedule(); updatePreview(); updateMarkers(); updateStepProgress(); setStatus(ui.unsaved, 'dirty'); form.querySelector('[data-pc-readiness-status]').textContent = '';
    if (event.target?.type === 'file') { photoDirty = true; localStore(); setStatus(ui.upload_pending, 'browser'); }
  });
  ['km:pricing-change','km:schedule-change','km:map-change','km:photos-change','km:offerings-change'].forEach(name => form.addEventListener(name, () => { if (restoring || (!userInteracted && !(name === 'km:photos-change' && photoEditor?.hasChanges()))) return; userInteracted = true; dirty = true; editedAt = Date.now(); localStore(); schedule(); updatePreview(); updateMarkers(); updateStepProgress(); setStatus(ui.unsaved, 'dirty'); form.querySelector('[data-pc-readiness-status]').textContent = ''; if (name === 'km:photos-change') { photoDirty = true; localStore(); setStatus(ui.upload_pending, 'browser'); } }));
  form.addEventListener('submit', async event => {
    if (event.submitter?.matches('[data-km-preview]')) return;
    if (halted) { event.preventDefault(); setStatus(ui.server_conflict, 'conflict');window.KidsMapEditorFeedback?.report(form,{action:event.submitter?.matches('[data-pc-save-draft]')?'draft':'moderation',outcome:'conflict'}); return; }
    if (submitting) { event.preventDefault(); return; }
    const submitter = event.submitter;
    if (submitter?.matches('[data-pc-save-draft]') && targetId === null &&
        (!form.elements.namedItem('name_az')?.value.trim() || !form.elements.namedItem('category')?.value)) {
      event.preventDefault(); clearTimeout(timer); dirty = true; localStore();
      await manualSave();
      return;
    }
    const feedbackAction=submitter?.matches('[data-pc-save-draft]')?'draft':'moderation';
    const failed=error=>window.KidsMapEditorFeedback?.report(form,{action:feedbackAction,outcome:window.KidsMapEditorFeedback.classify(error)});
    if (!navigator.onLine) { event.preventDefault(); localStore(); setStatus(ui.offline, 'browser');failed({kind:'network'}); return; }
    if (photoEditor) {
      event.preventDefault(); clearTimeout(timer);
      submitting = true;
      try {
        if(restorePromise)await restorePromise;
        if(restoreFailed||draftMedia?.blocking?.()){setStatus(ui.save_failed,'error');failed({kind:'pending'});return;}
        if (saving) await inFlight;
        if (halted) { setStatus(ui.server_conflict,'conflict');failed({status:409});return; }
        const result = await photoEditor.save(submitter);
        if (!result.ok) {
          failed({status:result.status,kind:result.kind,conflict:result.conflict});
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
        const redirect = new URL(result.redirect, location.href);
        if (currentCandidateView) redirect.searchParams.set('candidate_current', '1');
        const sameDocument = redirect.origin === location.origin &&
          redirect.pathname === location.pathname && redirect.search === location.search;
        if (sameDocument) {
          // A fragment-only assignment does not reload the form or its version token.
          location.replace(redirect.href);
          location.reload();
        } else location.assign(redirect.href);
      } catch(error) { setStatus(ui.save_failed, 'error');failed(error); }
      finally { submitting = false; }
    } else { submitting = true; clearTimeout(timer); }
  });
  window.addEventListener('online', () => { if (dirty) schedule(); });
  window.addEventListener('offline', () => setStatus(ui.offline, 'browser'));
  window.addEventListener('pageshow', () => { submitting = false; });
  window.addEventListener('beforeunload', event => { if ((dirty || photoDirty) && !submitting) { event.preventDefault(); event.returnValue = ''; } });
  async function flushDraft() {
    if (halted) {lastSaveError={status:409};return false;}
    if (restoreFailed) {
      // Retry the authorized detail before touching media. Otherwise an empty
      // editor could replace a gallery that was saved but not downloaded yet.
      try {
        const response=await fetch(`${form.dataset.draftUrl}${draftId}/`,{credentials:'same-origin'});
        if(response.status===409){lastSaveError={status:409};halted=true;candidateConflict=targetId!==null;setStatus(ui.server_conflict,'conflict');return false;}
        if(!response.ok)throw Object.assign(Error('restore'),{status:response.status});
        const detail=await response.json();if(!validServerCopy(detail))throw Error('restore');
        draftVersion=detail.version;
        if(draftMedia){restoring=true;try{await draftMedia.restore(detail);}finally{restoring=false;}}
        restoreFailed=false;
      }catch(error){lastSaveError=error;setStatus(ui.save_failed,'error');return false;}
    }
    clearTimeout(timer);
    dirty = true;
    do { if (!await save(true)) return false; } while (dirty || (draftMedia && draftMedia.hasPending()));
    return !photoDirty;
  }
  function manualSave(){const operation=async()=>({ok:await flushDraft(),error:lastSaveError||{kind:'pending'}});return window.KidsMapEditorFeedback?window.KidsMapEditorFeedback.run(form,'draft',operation):operation().then(result=>result.ok);}
  window.KidsMapOwnerWorkflow = {save:manualSave,setReadiness,checkReadiness,invalidateReadiness:scheduleReadiness,
    hasPending:()=>dirty||photoDirty||saving,
    draft:()=>({draft_id:draftId,version:draftVersion}),
    photoEditor};
  form.addEventListener('km:readiness',event=>{if(event.detail)setReadiness(event.detail);});
  form.querySelector('[data-pc-save-retry]')?.addEventListener('click',manualSave);
  document.addEventListener('click',event=>{
    if (!(dirty || photoDirty || saving) || submitting || event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const link=event.target.closest('a[href]');
    if(!link || link.target==='_blank' || link.hasAttribute('download'))return;
    const href=link.getAttribute('href');
    if(!href || href.startsWith('#') || /^(mailto:|tel:|javascript:)/i.test(href))return;
    const url=new URL(link.href,location.href);
    if(url.href===location.href)return;
    // Refresh/tab close remains the browser's native prompt. This dialog covers
    // only an intentional in-site link and never turns save into moderation.
    if(!window.kmModal?.unsavedChanges)return;
    event.preventDefault();
    window.kmModal.unsavedChanges({
      title:text('Сохранить изменения перед выходом?','Çıxmazdan əvvəl dəyişikliklər saxlanılsın?','Save changes before leaving?'),
      message:text('Сохраним текст и фотографии в ваших черновиках. Место не будет отправлено на проверку.','Mətn və şəkillər qaralamalarda saxlanılacaq. Məkan yoxlamaya göndərilməyəcək.','Save text and photos in your drafts. This will not send the place for review.'),
      stayText:text('Продолжить заполнение','Doldurmağa davam et','Keep editing'),
      saveText:text('Сохранить и выйти','Saxla və çıx','Save and leave'),
      discardText:text('Выйти без новых изменений','Yeni dəyişikliklərsiz çıx','Leave without new changes'),
      onSaveAndExit:async()=>{if(await manualSave()){submitting=true;location.assign(url.href);}},
      onExitWithoutSaving:()=>{clearTimeout(timer);submitting=true;location.assign(url.href);}
    });
  });
  function initKidsMapCustomSelects(root) {
    const lang = (document.documentElement.lang || 'ru').slice(0, 2);
    const searchPlaceholder = lang === 'az' ? 'Axtarış...' : lang === 'en' ? 'Search...' : 'Поиск...';
    const noResultsText = lang === 'az' ? 'Nəticə tapılmadı' : lang === 'en' ? 'No results found' : 'Ничего не найдено';

    function enhance(select) {
      if (!select || select.dataset.kmEnhanced === '1') return;
      select.dataset.kmEnhanced = '1';

      const wrapper = document.createElement('div');
      wrapper.className = 'km-custom-select';
      if (select.disabled) wrapper.classList.add('is-disabled');
      if (select.name) wrapper.dataset.kmSelectName = select.name;

      const trigger = document.createElement('button');
      trigger.type = 'button';
      trigger.className = 'km-custom-select__trigger';
      trigger.setAttribute('aria-haspopup', 'listbox');
      trigger.setAttribute('aria-expanded', 'false');
      if (select.disabled) trigger.disabled = true;

      const valueSpan = document.createElement('span');
      valueSpan.className = 'km-custom-select__value';

      const arrowSpan = document.createElement('span');
      arrowSpan.className = 'km-custom-select__arrow';
      arrowSpan.setAttribute('aria-hidden', 'true');
      arrowSpan.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>';

      trigger.appendChild(valueSpan);
      trigger.appendChild(arrowSpan);

      const menu = document.createElement('div');
      menu.className = 'km-custom-select__menu';
      menu.setAttribute('role', 'listbox');
      menu.tabIndex = -1;

      const searchBox = document.createElement('div');
      searchBox.className = 'km-custom-select__search-box';
      searchBox.innerHTML = `
        <svg class="km-custom-select__search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>
        <input type="text" class="km-custom-select__search-input" placeholder="${searchPlaceholder}" autocomplete="off" spellcheck="false">
      `;
      const searchInput = searchBox.querySelector('input');

      const list = document.createElement('div');
      list.className = 'km-custom-select__list';

      const emptyMsg = document.createElement('div');
      emptyMsg.className = 'km-custom-select__no-results';
      emptyMsg.textContent = noResultsText;
      emptyMsg.hidden = true;

      menu.appendChild(searchBox);
      menu.appendChild(list);
      menu.appendChild(emptyMsg);

      select.parentNode.insertBefore(wrapper, select);
      wrapper.appendChild(select);
      wrapper.appendChild(trigger);
      wrapper.appendChild(menu);

      function renderOptions() {
        list.innerHTML = '';
        const options = Array.from(select.options);
        searchBox.hidden = options.length <= 6;

        let selectedText = '';
        let hasValue = false;

        options.forEach(opt => {
          const optDiv = document.createElement('div');
          optDiv.className = 'km-custom-select__option';
          optDiv.setAttribute('role', 'option');
          optDiv.dataset.value = opt.value;
          optDiv.tabIndex = 0;
          const isSelected = opt.selected || (!select.value && !opt.value);
          if (isSelected) {
            optDiv.classList.add('is-selected');
            optDiv.setAttribute('aria-selected', 'true');
            selectedText = opt.text;
            hasValue = Boolean(opt.value);
          } else {
            optDiv.setAttribute('aria-selected', 'false');
          }

          const textSpan = document.createElement('span');
          textSpan.className = 'km-custom-select__opt-text';
          textSpan.textContent = opt.text;

          const checkSpan = document.createElement('span');
          checkSpan.className = 'km-custom-select__opt-check';
          checkSpan.setAttribute('aria-hidden', 'true');
          checkSpan.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

          optDiv.appendChild(textSpan);
          optDiv.appendChild(checkSpan);

          function chooseOption() {
            if (select.value !== opt.value) {
              select.value = opt.value;
              select.dispatchEvent(new Event('change', { bubbles: true }));
              select.dispatchEvent(new Event('input', { bubbles: true }));
            }
            updateSelection();
            close();
            trigger.focus();
          }

          optDiv.addEventListener('click', (e) => {
            e.stopPropagation();
            chooseOption();
          });

          optDiv.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              chooseOption();
            }
          });

          list.appendChild(optDiv);
        });

        if (!selectedText && select.selectedIndex >= 0) {
          selectedText = select.options[select.selectedIndex]?.text || '';
          hasValue = Boolean(select.value);
        }

        valueSpan.textContent = selectedText || '—';
        valueSpan.classList.toggle('is-placeholder', !hasValue);
      }

      function updateSelection() {
        const curVal = select.value;
        let selectedText = '';
        let hasValue = false;

        list.querySelectorAll('.km-custom-select__option').forEach(optDiv => {
          const match = optDiv.dataset.value === curVal;
          optDiv.classList.toggle('is-selected', match);
          optDiv.setAttribute('aria-selected', match ? 'true' : 'false');
          if (match) {
            selectedText = optDiv.querySelector('.km-custom-select__opt-text')?.textContent || '';
            hasValue = Boolean(curVal);
          }
        });

        if (!selectedText && select.selectedIndex >= 0) {
          selectedText = select.options[select.selectedIndex]?.text || '';
          hasValue = Boolean(curVal);
        }

        valueSpan.textContent = selectedText || '—';
        valueSpan.classList.toggle('is-placeholder', !hasValue);
      }

      function open() {
        if (select.disabled || wrapper.classList.contains('is-disabled')) return;
        document.querySelectorAll('.km-custom-select.is-open').forEach(other => {
          if (other !== wrapper) {
            other.classList.remove('is-open');
            other.querySelector('.km-custom-select__trigger')?.setAttribute('aria-expanded', 'false');
          }
        });

        const rect = trigger.getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom;
        const openUpwards = spaceBelow < 280 && rect.top > 280;
        wrapper.classList.toggle('opens-up', openUpwards);

        wrapper.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');

        searchInput.value = '';
        filterOptions('');
        if (!searchBox.hidden) {
          setTimeout(() => searchInput.focus(), 50);
        }

        const selectedOpt = list.querySelector('.km-custom-select__option.is-selected');
        if (selectedOpt) {
          selectedOpt.scrollIntoView({ block: 'nearest' });
        }
      }

      function close() {
        wrapper.classList.remove('is-open');
        trigger.setAttribute('aria-expanded', 'false');
      }

      function filterOptions(query) {
        const q = query.trim().toLowerCase();
        let matchCount = 0;
        list.querySelectorAll('.km-custom-select__option').forEach(optDiv => {
          const txt = (optDiv.querySelector('.km-custom-select__opt-text')?.textContent || '').toLowerCase();
          const match = !q || txt.includes(q);
          optDiv.hidden = !match;
          if (match) matchCount++;
        });
        emptyMsg.hidden = matchCount > 0;
      }

      searchInput.addEventListener('input', () => {
        filterOptions(searchInput.value);
      });

      trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        if (wrapper.classList.contains('is-open')) close();
        else open();
      });

      trigger.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          open();
        } else if (e.key === 'Escape') {
          close();
        }
      });

      menu.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          close();
          trigger.focus();
        } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
          e.preventDefault();
          const visible = Array.from(list.querySelectorAll('.km-custom-select__option:not([hidden])'));
          if (!visible.length) return;
          const focused = document.activeElement;
          let idx = visible.indexOf(focused);
          if (e.key === 'ArrowDown') {
            idx = idx < visible.length - 1 ? idx + 1 : 0;
          } else {
            idx = idx > 0 ? idx - 1 : visible.length - 1;
          }
          visible[idx].focus();
        }
      });

      select.addEventListener('change', updateSelection);
      select.addEventListener('input', updateSelection);
      select.addEventListener('km:subcategory-rebuilt', () => {
        renderOptions();
        wrapper.classList.toggle('is-disabled', select.disabled);
        trigger.disabled = select.disabled;
      });

      const observer = new MutationObserver(() => {
        const dis = select.disabled;
        wrapper.classList.toggle('is-disabled', dis);
        trigger.disabled = dis;
        renderOptions();
      });
      observer.observe(select, { attributes: true, attributeFilter: ['disabled'], childList: true });

      renderOptions();
    }

    const selectElements = root.querySelectorAll('select:not([data-pc-section-select])');
    selectElements.forEach(enhance);

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.km-custom-select')) {
        document.querySelectorAll('.km-custom-select.is-open').forEach(w => {
          w.classList.remove('is-open');
          w.querySelector('.km-custom-select__trigger')?.setAttribute('aria-expanded', 'false');
        });
      }
    });
  }

  function initKidsMapAgeSlider(rootForm) {
    const ageRoot = rootForm.querySelector('.km-age-range-field');
    if (!ageRoot) return;

    const min = Number(ageRoot.dataset.min || 0);
    const max = Number(ageRoot.dataset.max || 18);
    const fromInput = ageRoot.querySelector('[data-range-from-input]');
    const toInput = ageRoot.querySelector('[data-range-to-input]');
    const fromRange = ageRoot.querySelector('[data-range-from-range]');
    const toRange = ageRoot.querySelector('[data-range-to-range]');
    const caption = ageRoot.querySelector('[data-range-caption]');
    const openAgeCheckbox = ageRoot.querySelector('[data-pc-open-age]');
    const openAgeHidden = rootForm.elements.namedItem('age_open_ended');

    const lang = document.documentElement.lang || 'ru';
    const yearsUnit = lang === 'az' ? 'yaş' : lang === 'en' ? 'years' : 'лет';
    const fromPrefix = lang === 'az' ? '' : lang === 'en' ? 'from ' : 'от ';
    const fromSuffix = lang === 'az' ? ' yaşdan' : '';

    let lastExplicitTo = 18;

    function clamp(val, fallback) {
      if (val === '' || val === null || val === undefined) return fallback;
      const n = Number(val);
      if (!Number.isFinite(n)) return fallback;
      return Math.min(max, Math.max(min, Math.round(n)));
    }

    if (toInput && toInput.value !== '') {
      lastExplicitTo = clamp(toInput.value, 18);
    }

    function updateVisuals(a, b, isOpen) {
      if (isOpen) {
        ageRoot.classList.add('is-open-ended');
        if (caption) {
          caption.textContent = lang === 'az'
            ? `${a}+${fromSuffix}`
            : `${fromPrefix}${a} ${yearsUnit}`;
        }
        const fromPct = max > min ? ((a - min) / (max - min)) * 100 : 0;
        ageRoot.style.setProperty('--from-pct', `${fromPct}%`);
        ageRoot.style.setProperty('--to-pct', '100%');
      } else {
        ageRoot.classList.remove('is-open-ended');
        if (caption) {
          caption.textContent = `${a}–${b} ${yearsUnit}`;
        }
        const fromPct = max > min ? ((a - min) / (max - min)) * 100 : 0;
        const toPct = max > min ? ((b - min) / (max - min)) * 100 : 100;
        ageRoot.style.setProperty('--from-pct', `${fromPct}%`);
        ageRoot.style.setProperty('--to-pct', `${toPct}%`);
      }
    }

    function syncFromSliders(source) {
      let a = clamp(fromRange.value, 0);
      let b = clamp(toRange.value, 18);

      if (source === 'to') {
        lastExplicitTo = b;
      } else if (source === 'toggle' && openAgeCheckbox && !openAgeCheckbox.checked) {
        b = Math.max(a, lastExplicitTo);
        toRange.value = b;
      }

      // Enforce: 'a' can never exceed 'b'
      if (a > b) {
        if (source === 'from') {
          b = a;
          toRange.value = b;
          lastExplicitTo = b;
        } else {
          a = b;
          fromRange.value = a;
        }
      }

      const isOpen = Boolean(openAgeCheckbox && openAgeCheckbox.checked);
      fromInput.value = String(a);
      toInput.value = isOpen ? '' : String(b);
      if (openAgeHidden) openAgeHidden.value = isOpen ? '1' : '';

      updateVisuals(a, b, isOpen);

      fromInput.dispatchEvent(new Event('input', { bubbles: true }));
      toInput.dispatchEvent(new Event('input', { bubbles: true }));
      updateMarkers();
      updateStepProgress();
    }

    function syncFromInputs() {
      const isOpen = Boolean((openAgeHidden && openAgeHidden.value === '1') || (openAgeCheckbox && openAgeCheckbox.checked));
      if (openAgeCheckbox) openAgeCheckbox.checked = isOpen;
      if (openAgeHidden) openAgeHidden.value = isOpen ? '1' : '';

      let a = clamp(fromInput.value, 0);
      let b = isOpen ? 18 : clamp(toInput.value, 18);
      if (a > b && !isOpen) b = a;

      fromRange.value = a;
      toRange.value = b;
      fromInput.value = String(a);
      if (!isOpen) toInput.value = String(b);

      updateVisuals(a, b, isOpen);
    }

    ['input', 'change'].forEach(evt => {
      fromRange.addEventListener(evt, () => syncFromSliders('from'));
      toRange.addEventListener(evt, () => syncFromSliders('to'));
    });

    if (openAgeCheckbox) {
      openAgeCheckbox.addEventListener('change', () => {
        syncFromSliders('toggle');
        fromInput.dispatchEvent(new Event('change', { bubbles: true }));
      });
    }

    fromInput.addEventListener('change', syncFromInputs);
    toInput.addEventListener('change', syncFromInputs);

    ageRoot._syncFromInputs = syncFromInputs;
    syncFromInputs();
  }

  function initAudienceChoices(rootForm) {
    const container = rootForm.querySelector('.km-audience-options');
    if (!container) return;

    const options = container.querySelectorAll('.km-audience-option');
    const radios = container.querySelectorAll('input[type="radio"]');

    function syncActive() {
      options.forEach(opt => {
        const radio = opt.querySelector('input[type="radio"]');
        opt.classList.toggle('is-checked', Boolean(radio && radio.checked));
      });
    }

    radios.forEach(radio => {
      radio.addEventListener('change', syncActive);
    });

    options.forEach(opt => {
      opt.addEventListener('click', () => {
        const radio = opt.querySelector('input[type="radio"]');
        if (radio && !radio.checked) {
          radio.checked = true;
          syncActive();
          radio.dispatchEvent(new Event('input', { bubbles: true }));
          radio.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });
    });

    syncActive();
  }

  updatePreview(); updateMarkers(); updateStepProgress(); restorePromise=restore();
  initKidsMapCustomSelects(form);
  initKidsMapAgeSlider(form);
  initAudienceChoices(form);
})();
