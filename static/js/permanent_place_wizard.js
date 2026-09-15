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
    const stepNum = fieldStep(name);
    go(stepNum);
    let parent = box(name)?.parentElement;
    while (parent && parent !== form) { if (parent.tagName === 'DETAILS') parent.open = true; parent = parent.parentElement; }
    let target = null;
    if (name === 'category') target = form.querySelector('[data-pw-category][aria-pressed="true"]') || form.querySelector('[data-pw-category]');
    else if (name === 'subcategory') target = form.querySelector('.pw-subcategory-trigger') || form.querySelector('[data-pw-field="subcategory"]');
    else if (name === 'photo') target = form.querySelector('.pw-upload') || box('photo');
    else if (name === 'lat' || name === 'lng') target = form.querySelector('.owner-map-picker') || box('address');
    else if (name === 'pricing_plans') target = form.querySelector('[data-tariff-add]') || box('pricing_plans');
    else if (name === 'structured_schedule') target = form.querySelector('.km-schedule-editor') || box('structured_schedule');
    else {
      target = el(name);
      if (!target || target.type === 'hidden') target = box(name)?.querySelector('input:not([type=hidden]),textarea,select,button');
    }

    const scrollTarget = box(name) || target;
    if (scrollTarget) {
      scrollTarget.scrollIntoView({ behavior: 'smooth', block: 'center' });
      scrollTarget.classList.remove('pw-field--pulse');
      void scrollTarget.offsetWidth;
      scrollTarget.classList.add('pw-field--pulse');
      setTimeout(() => scrollTarget.classList.remove('pw-field--pulse'), 1800);
    }
    if (target?.focus && target.type !== 'hidden') {
      try { target.focus({ preventScroll: true }); } catch (e) { target.focus(); }
    }
  }
  function requiredNames() {
    if (volunteer) return [];
    const names = [...rules.required];
    if (ageMode === 'range') names.push('age_to');
    if (value('region') === 'baku') names.push('district');
    return names;
  }
  function isNumericString(str) {
    return typeof str === 'string' && /^\d+$/.test(str.trim());
  }
  function isValidPhone(val) {
    if (!val) return true;
    const trimmed = val.trim();
    if (!trimmed) return true;
    if (/[a-zA-Zа-яА-ЯёЁüöğışəÜÖĞİŞƏ]/.test(trimmed)) return false;
    if (!/^[0-9+\s()\-]+$/.test(trimmed)) return false;
    const digits = trimmed.replace(/\D/g, '');
    return digits.length >= 7 && digits.length <= 15;
  }
  function isValidUrl(val) {
    if (!val) return true;
    const trimmed = val.trim();
    if (!trimmed) return true;
    try {
      const url = new URL(trimmed.includes('://') ? trimmed : `https://${trimmed}`);
      return Boolean(url.hostname && url.hostname.includes('.'));
    } catch {
      return false;
    }
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

    const ageFromStr = value('age_from');
    const ageToStr = value('age_to');
    if (ageMode !== 'all') {
      if (ageFromStr !== '') {
        if (!isNumericString(ageFromStr) || Number(ageFromStr) < 0 || Number(ageFromStr) > 18) {
          result.set('age_from', ui.age_invalid || ui.invalid);
        }
      } else if (requiredNames().includes('age_from')) {
        result.set('age_from', ui.required);
      }

      if (ageMode === 'range') {
        if (ageToStr !== '') {
          if (!isNumericString(ageToStr) || Number(ageToStr) < 0 || Number(ageToStr) > 18) {
            result.set('age_to', ui.age_invalid || ui.invalid);
          } else if (isNumericString(ageFromStr) && Number(ageToStr) < Number(ageFromStr)) {
            result.set('age_to', ui.age_range_invalid || ui.invalid);
          }
        } else if (requiredNames().includes('age_to')) {
          result.set('age_to', ui.required);
        }
      } else if (ageToStr !== '') {
        if (!isNumericString(ageToStr) || Number(ageToStr) < 0 || Number(ageToStr) > 18) {
          result.set('age_to', ui.age_invalid || ui.invalid);
        } else if (isNumericString(ageFromStr) && Number(ageToStr) < Number(ageFromStr)) {
          result.set('age_to', ui.age_range_invalid || ui.invalid);
        }
      }
    }

    const duration = value('lesson_duration_minutes');
    if (duration !== '') {
      if (!isNumericString(duration) || Number(duration) < 5 || Number(duration) > 1440) {
        result.set('lesson_duration_minutes', ui.number_invalid || ui.invalid);
      }
    }
    const lessonsWeek = value('lessons_per_week');
    if (lessonsWeek !== '') {
      if (!isNumericString(lessonsWeek) || Number(lessonsWeek) < 1 || Number(lessonsWeek) > 50) {
        result.set('lessons_per_week', ui.number_invalid || ui.invalid);
      }
    }
    const lessonsMonth = value('lessons_per_month');
    if (lessonsMonth !== '') {
      if (!isNumericString(lessonsMonth) || Number(lessonsMonth) < 1 || Number(lessonsMonth) > 200) {
        result.set('lessons_per_month', ui.number_invalid || ui.invalid);
      }
    }

    for (const [name, limit] of [['lat', 90], ['lng', 180]]) {
      if (filled(name) && (!Number.isFinite(Number(value(name))) || Math.abs(Number(value(name))) > limit)) result.set(name, ui.invalid);
    }

    ['phone1', 'phone2', 'phone3'].forEach(phoneName => {
      const pVal = value(phoneName);
      if (pVal !== '') {
        if (!isValidPhone(pVal)) {
          result.set(phoneName, ui.phone_invalid || ui.invalid);
        }
      } else if (requiredNames().includes(phoneName)) {
        result.set(phoneName, ui.required);
      }
    });

    const webVal = value('website');
    if (webVal !== '') {
      if (!isValidUrl(webVal)) {
        result.set('website', ui.url_invalid || ui.invalid);
      }
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
      if (input.validity && !input.validity.valid && input.value !== '') {
        if (!result.has(input.name)) {
          result.set(input.name || 'pricing_plans', input.validationMessage || ui.invalid);
        }
      }
    }
    return result;
  }
  function displayIssues(result) {
    form.querySelectorAll('.pw-client-error').forEach(node => node.textContent = '');
    form.querySelectorAll('[aria-invalid=true]').forEach(node => node.removeAttribute('aria-invalid'));
    form.querySelectorAll('.pw-field--invalid').forEach(node => node.classList.remove('pw-field--invalid'));
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
      const b = box(name); if (b) b.classList.add('pw-field--invalid');
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
    const errors = issues();
    form.querySelectorAll('[data-pw-required]').forEach(node => {
      const name = node.dataset.pwRequired;
      const groupedName = rules.names.includes(name);
      const isDesc = rules.descriptions.includes(name);
      const mandatory = required.includes(name);
      const b = box(name);
      const input = el(name);
      const hasError = errors.has(name);
      const rawVal = value(name);
      const hasContent = rawVal.length > 0;

      let isFilled = false;
      let isPartial = false;
      let isInvalid = false;

      if (hasError && !isDesc && (hasContent || (name === 'lat' && errors.has('lat')))) {
        isInvalid = true;
      } else if (!hasError) {
        if (groupedName) {
          isFilled = rules.names.some(n => filled(n) && !errors.has(n));
        } else if (isDesc) {
          const len = rawVal.length;
          if (len >= rules.description_min) {
            isFilled = true;
          } else if (len > 0) {
            isPartial = true;
          }
        } else {
          isFilled = filled(name);
        }
      } else if (isDesc) {
        const len = rawVal.length;
        if (len >= rules.description_min) {
          isFilled = true;
        } else if (len > 0) {
          isPartial = true;
        }
      }

      node.hidden = false;
      if (isInvalid) {
        node.textContent = ui.invalid;
        node.dataset.filled = 'invalid';
      } else if (isDesc && isPartial) {
        node.textContent = `${rawVal.length} / ${rules.description_min}`;
        node.dataset.filled = 'partial';
      } else {
        node.textContent = groupedName ? ui.one_name : mandatory ? (isFilled ? ui.fields_ready : ui.required_badge) : (isFilled ? ui.fields_ready : ui.optional_badge);
        node.dataset.filled = String(isFilled);
      }
      node.dataset.kind = isInvalid ? 'invalid' : groupedName ? 'group' : mandatory ? 'required' : 'optional';

      if (b) {
        b.classList.toggle('pw-field--required', mandatory || groupedName);
        b.classList.toggle('pw-field--filled', isFilled && !isInvalid);
        b.classList.toggle('pw-field--partial', isPartial && !isInvalid);
        b.classList.toggle('pw-field--invalid', isInvalid);
        b.classList.toggle('pw-field--empty', !isFilled && !isPartial && !isInvalid);

        const errSpan = b.querySelector('.pw-client-error');
        if (errSpan) {
          errSpan.textContent = isInvalid ? (errors.get(name) || ui.invalid) : '';
        }
      }
      if (input?.setAttribute) {
        input.setAttribute('aria-required', String(mandatory));
        if (isInvalid) {
          input.setAttribute('aria-invalid', 'true');
        } else {
          input.removeAttribute('aria-invalid');
        }
      }
    });
    updateRequirements();
  }
  function updateRequirements() {
    if (volunteer) return;
    const errors = issues();
    const entries = requiredNames().filter(name => name !== 'lng' && !rules.names.includes(name)).map(name => {
      let title = name === 'lat' ? ui.point_requirement : label(name);
      const isReady = !errors.has(name) && (name !== 'lat' || !errors.has('lng'));
      if (rules.descriptions.includes(name)) {
        const descLen = Math.max(0, ...rules.descriptions.map(dn => value(dn).trim().length));
        if (!isReady && descLen > 0) {
          title = `${title} (${descLen}/${rules.description_min})`;
        }
      }
      return { name, title, ready: isReady };
    });
    entries.unshift({name: 'name_az', title: ui.name_requirement, ready: rules.names.some(name => value(name).trim().length > 0)});
    entries.push({name: 'pricing_plans', title: ui.price_requirement, ready: !errors.has('pricing_plans')});
    if (value('schedule_mode') === 'regular') entries.push({name: 'structured_schedule', title: ui.schedule_requirement, ready: !errors.has('structured_schedule')});
    form.querySelectorAll('[data-pw-requirements]').forEach(panel => {
      const number = Number(panel.dataset.pwRequirements);
      const items = entries.filter(entry => fieldStep(entry.name) === number);
      const list = panel.querySelector('[data-pw-requirements-list]'); list.replaceChildren();
      const complete = items.filter(item => item.ready).length;
      const total = items.length;
      const percent = total > 0 ? Math.round((complete / total) * 100) : 100;
      const isComplete = complete === total && total > 0;
      const isEmpty = complete === 0;
      const state = isComplete ? 'complete' : isEmpty ? 'empty' : 'partial';

      panel.querySelector('[data-pw-requirements-count]').textContent = `${ui.fields_ready} ${complete} / ${total}`;
      items.forEach(item => {
        const button = document.createElement('button'), icon = document.createElement('span'), caption = document.createElement('span');
        button.type = 'button'; button.dataset.pwRequirement = item.name; button.dataset.ready = String(item.ready);
        icon.textContent = item.ready ? '✓' : '○'; icon.setAttribute('aria-hidden', 'true');
        caption.textContent = item.title; button.append(icon, caption);
        button.setAttribute('aria-label', `${item.title}: ${item.ready ? ui.fields_ready : ui.required_badge}`);
        button.addEventListener('click', (e) => { e.preventDefault(); reveal(item.name); });
        list.append(button);
      });
      panel.dataset.complete = String(isComplete);

      const status = form.querySelector(`[data-pw-step-status="${number}"]`);
      if (status) {
        status.dataset.state = state;
        status.dataset.complete = String(isComplete);
        status.dataset.percent = String(percent);
        status.setAttribute('title', `${ui.fields_ready} ${complete} / ${total} (${percent}%)`);

        const circumference = 50.26;
        const offset = isComplete ? 0 : Math.max(0, circumference - (circumference * percent / 100));
        status.innerHTML =
          '<svg class="pw-nav-ring" viewBox="0 0 22 22" aria-hidden="true">' +
            '<circle cx="11" cy="11" r="8" class="pw-nav-ring-bg"></circle>' +
            '<circle cx="11" cy="11" r="8" class="pw-nav-ring-fill" stroke-dasharray="' + circumference + '" stroke-dashoffset="' + offset.toFixed(2) + '"></circle>' +
          '</svg>' +
          '<span class="pw-nav-status-text">' + (isComplete ? '✓' : complete + '/' + total) + '</span>';
      }

      const bar = form.querySelector(`[data-pw-step-bar="${number}"]`);
      if (bar) {
        bar.style.width = percent + '%';
        bar.dataset.state = state;
      }

      const navBtn = form.querySelector(`[data-pw-go="${number}"]`);
      if (navBtn) {
        navBtn.classList.toggle('pw-nav--complete', isComplete);
        navBtn.classList.toggle('pw-nav--pending', !isComplete);
        navBtn.dataset.state = state;
      }
    });

    const finalStatus = form.querySelector('[data-pw-step-status="7"]');
    const allStepsComplete = errors.size === 0;
    const finalBar = form.querySelector('[data-pw-step-bar="7"]');
    const finalNavBtn = form.querySelector('[data-pw-go="7"]');
    if (finalStatus) {
      const finalState = allStepsComplete ? 'complete' : 'partial';
      finalStatus.dataset.state = finalState;
      finalStatus.dataset.complete = String(allStepsComplete);
      if (allStepsComplete) {
        finalStatus.innerHTML =
          '<svg class="pw-nav-ring" viewBox="0 0 22 22" aria-hidden="true">' +
            '<circle cx="11" cy="11" r="8" class="pw-nav-ring-bg"></circle>' +
            '<circle cx="11" cy="11" r="8" class="pw-nav-ring-fill" stroke-dasharray="50.26" stroke-dashoffset="0"></circle>' +
          '</svg>' +
          '<span class="pw-nav-status-text">✓</span>';
      } else {
        finalStatus.innerHTML =
          '<svg class="pw-nav-ring" viewBox="0 0 22 22" aria-hidden="true">' +
            '<circle cx="11" cy="11" r="8" class="pw-nav-ring-bg"></circle>' +
            '<circle cx="11" cy="11" r="8" class="pw-nav-ring-fill" stroke-dasharray="50.26" stroke-dashoffset="50.26"></circle>' +
          '</svg>' +
          '<span class="pw-nav-status-text">!</span>';
      }
    }
    if (finalBar) {
      finalBar.style.width = allStepsComplete ? '100%' : '0%';
      finalBar.dataset.state = allStepsComplete ? 'complete' : 'empty';
    }
    if (finalNavBtn) {
      finalNavBtn.classList.toggle('pw-nav--complete', allStepsComplete);
      finalNavBtn.classList.toggle('pw-nav--pending', !allStepsComplete);
      finalNavBtn.dataset.state = allStepsComplete ? 'complete' : 'partial';
    }
  }
  function saveBrowser() {
    if (restoring) return;
    if (volunteer) { text('[data-pw-draft-status]', ui.unsaved); return; }
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
    const target = event?.target;
    if (target && target.name) {
      if (['age_from', 'age_to', 'lesson_duration_minutes', 'lessons_per_week', 'lessons_per_month', 'price_from', 'price_to', 'price_per_lesson', 'price_per_month', 'price_per_8_lessons'].includes(target.name)) {
        const sanitized = target.value.replace(/[^\d]/g, '');
        if (sanitized !== target.value) {
          target.value = sanitized;
        }
      } else if (['phone1', 'phone2', 'phone3'].includes(target.name)) {
        const sanitized = target.value.replace(/[^\d+\s()\-\.]/g, '');
        if (sanitized !== target.value) {
          target.value = sanitized;
        }
      }
    }
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
    const draftAction = volunteer ? 'draft' : 'save_draft';
    if (event.submitter?.value !== draftAction) {
      const errors = issues(); displayIssues(errors);
      if (errors.size) { event.preventDefault(); reveal(errors.keys().next().value); return; }
    } else {
      saveBrowser();
    }
    if (!navigator.onLine) { event.preventDefault(); saveDestination = null; text('[data-pw-draft-status]', ui.offline); return; }
    submitting = true;
    if (photoEditor) {
      event.preventDefault();
      let result;
      try {
        result = await photoEditor.save(event.submitter);
      } catch {
        submitting = false;
        saveDestination = null;
        text('[data-pw-draft-status]', ui.save_failed);
        return;
      }
      if (result.ok) {
        try { localStorage.removeItem(draftKey); } catch {}
        location.assign(saveDestination || result.redirect);
      } else {
        submitting = false;
        saveDestination = null;
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
  const leaveModal = document.getElementById('pw-leave-modal');
  let pendingNavigationUrl = null;
  let saveDestination = null;

  function saveAndLeave(destination) {
    if (!destination || submitting) return;
    const draftButton = form.querySelector(volunteer
      ? 'button[name="action"][value="draft"]'
      : 'button[name="form_action"][value="save_draft"]');
    if (!draftButton || draftButton.disabled || typeof form.requestSubmit !== 'function') {
      closeLeaveModal();
      text('[data-pw-draft-status]', ui.save_failed);
      return;
    }
    saveDestination = destination;
    closeLeaveModal();
    // Submit the actual form so text, files and photo-editor changes are persisted.
    // Only a confirmed AJAX save may navigate here; native POST owns its redirect.
    form.requestSubmit(draftButton);
  }

  function hasUnsavedData() {
    if (dirty) return true;
    const plansVal = value('pricing_plans');
    return Boolean(
      value('name_az') || value('name_ru') || value('name_en') ||
      value('address') || value('category') ||
      (plansVal && plansVal !== '[]' && plansVal !== '') ||
      value('phone1') || value('website') ||
      value('description_az') || value('description_ru') || value('description_en') ||
      (photoEditor && photoEditor.hasMain && photoEditor.hasMain())
    );
  }

  function showLeaveModal(targetUrl, isLanguageSwitch = false) {
    if (!leaveModal) {
      if (window.confirm(isLanguageSwitch ? (ui.leave_modal_desc_lang || ui.unsaved) : ui.unsaved)) {
        saveAndLeave(targetUrl);
      }
      return;
    }
    pendingNavigationUrl = targetUrl;
    const descEl = leaveModal.querySelector('[data-pw-leave-desc]');
    if (descEl) {
      descEl.textContent = isLanguageSwitch ? (ui.leave_modal_desc_lang || ui.unsaved) : (ui.leave_modal_desc_nav || ui.unsaved);
    }
    if (typeof leaveModal.showModal === 'function') {
      try {
        leaveModal.showModal();
      } catch (e) {
        leaveModal.setAttribute('open', '');
      }
    } else {
      leaveModal.setAttribute('open', '');
    }
  }

  function closeLeaveModal() {
    if (!leaveModal) return;
    if (typeof leaveModal.close === 'function') {
      try {
        leaveModal.close();
      } catch (e) {
        leaveModal.removeAttribute('open');
      }
    } else {
      leaveModal.removeAttribute('open');
    }
    pendingNavigationUrl = null;
  }

  if (leaveModal) {
    leaveModal.querySelector('[data-pw-leave-save]')?.addEventListener('click', () => {
      saveAndLeave(pendingNavigationUrl);
    });

    leaveModal.querySelector('[data-pw-leave-stay]')?.addEventListener('click', () => {
      closeLeaveModal();
    });

    leaveModal.querySelector('[data-pw-leave-discard]')?.addEventListener('click', () => {
      const dest = pendingNavigationUrl;
      dirty = false;
      closeLeaveModal();
      if (!dest) return;
      submitting = true;
      window.location.assign(dest);
    });

    leaveModal.addEventListener('click', (event) => {
      if (event.target === leaveModal) {
        closeLeaveModal();
      }
    });

    leaveModal.addEventListener('cancel', () => {
      pendingNavigationUrl = null;
    });
  }

  document.addEventListener('click', (event) => {
    if (submitting) return;
    const link = event.target.closest('a');
    if (!link || !link.href) return;
    if (link.target === '_blank' || link.hasAttribute('download') || link.href.startsWith('javascript:') || link.href.startsWith('tel:') || link.href.startsWith('mailto:')) return;

    try {
      const url = new URL(link.href, window.location.origin);
      if (url.origin === window.location.origin && url.pathname === window.location.pathname && url.search === window.location.search && url.hash) {
        return;
      }

      const isLangSwitch = Boolean(
        link.closest('.km-lang-wrapper') ||
        link.closest('.km-drawer-lang-section') ||
        link.classList.contains('km-lang-option') ||
        link.classList.contains('km-drawer-lang-btn') ||
        link.hasAttribute('hreflang')
      );

      if (hasUnsavedData()) {
        event.preventDefault();
        event.stopPropagation();
        showLeaveModal(link.href, isLangSwitch);
      } else if (isLangSwitch) {
        if (url.pathname.includes('/account/places/create/')) {
          url.searchParams.set('type', 'permanent');
          if (form.dataset.draftKey) {
            url.searchParams.set('draft_session', form.dataset.draftKey);
          }
          if (url.href !== link.href) {
            event.preventDefault();
            event.stopPropagation();
            window.location.assign(url.href);
          }
        }
      }
    } catch (err) {}
  }, true);

  window.addEventListener('beforeunload', event => {
    if (dirty && !submitting) {
      saveBrowser();
      event.preventDefault();
      event.returnValue = ui.unsaved;
    }
  });
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

  // Custom enhanced dropdown for subcategory
  const subcategory = el('subcategory');
  if (subcategory) {
    const picker = document.createElement('div');
    picker.className = 'pw-subcategory-picker';

    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'pw-subcategory-trigger';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');

    const triggerContent = document.createElement('div');
    triggerContent.className = 'pw-subcategory-trigger__content';

    const triggerIcon = document.createElement('span');
    triggerIcon.className = 'pw-subcategory-trigger__icon';
    triggerIcon.setAttribute('aria-hidden', 'true');
    triggerIcon.innerHTML = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>';

    const triggerText = document.createElement('span');
    triggerText.className = 'pw-subcategory-trigger__label';

    triggerContent.append(triggerIcon, triggerText);

    const triggerRight = document.createElement('div');
    triggerRight.className = 'pw-subcategory-trigger__right';

    const triggerBadge = document.createElement('span');
    triggerBadge.className = 'pw-subcategory-trigger__badge';

    const clearBtn = document.createElement('span');
    clearBtn.className = 'pw-subcategory-trigger__clear';
    clearBtn.setAttribute('title', ui.clear_selection || 'Очистить');
    clearBtn.setAttribute('aria-label', ui.clear_selection || 'Очистить');
    clearBtn.setAttribute('role', 'button');
    clearBtn.innerHTML = '✕';
    clearBtn.hidden = true;

    const chevron = document.createElement('span');
    chevron.className = 'pw-subcategory-trigger__chevron';
    chevron.setAttribute('aria-hidden', 'true');
    chevron.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>';

    triggerRight.append(triggerBadge, clearBtn, chevron);
    trigger.append(triggerContent, triggerRight);

    const menu = document.createElement('div');
    menu.className = 'pw-subcategory-menu';
    menu.setAttribute('role', 'listbox');
    menu.hidden = true;

    const searchWrap = document.createElement('div');
    searchWrap.className = 'pw-subcategory-search';
    searchWrap.innerHTML =
      '<span class="pw-subcategory-search__icon" aria-hidden="true">' +
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>' +
      '</span>' +
      '<input type="text" class="pw-subcategory-search__input" placeholder="' + (ui.search_subcategory || 'Поиск подкатегории...') + '" autocomplete="off" />' +
      '<button type="button" class="pw-subcategory-search__clear" hidden aria-label="Clear">✕</button>';

    const searchInput = searchWrap.querySelector('.pw-subcategory-search__input');
    const searchClear = searchWrap.querySelector('.pw-subcategory-search__clear');

    const list = document.createElement('div');
    list.className = 'pw-subcategory-list';

    const emptyMsg = document.createElement('div');
    emptyMsg.className = 'pw-subcategory-empty';
    emptyMsg.textContent = ui.empty || 'Ничего не найдено';
    emptyMsg.hidden = true;

    menu.append(searchWrap, list, emptyMsg);
    picker.append(trigger, menu);

    subcategory.classList.add('pw-native-subcategory');
    subcategory.tabIndex = -1;
    subcategory.after(picker);

    function getValidOptions() {
      return [...subcategory.options].filter(o => o.value !== '');
    }

    function renderTrigger() {
      const selectedCat = category.value;
      const validOptions = getValidOptions();
      const currentVal = subcategory.value;

      if (!selectedCat) {
        trigger.disabled = true;
        trigger.classList.add('is-disabled');
        triggerText.textContent = ui.select_category_first || 'Сначала выберите категорию';
        triggerBadge.hidden = true;
        clearBtn.hidden = true;
        picker.classList.remove('has-value');
        closeMenu();
        return;
      }

      if (!validOptions.length) {
        trigger.disabled = true;
        trigger.classList.add('is-disabled');
        triggerText.textContent = ui.no_subcategories || 'Для этой категории нет подкатегорий';
        triggerBadge.hidden = true;
        clearBtn.hidden = true;
        picker.classList.remove('has-value');
        closeMenu();
        return;
      }

      trigger.disabled = false;
      trigger.classList.remove('is-disabled');

      const selectedOption = validOptions.find(o => o.value === currentVal);
      if (selectedOption) {
        triggerText.textContent = selectedOption.text;
        picker.classList.add('has-value');
        triggerBadge.hidden = true;
        clearBtn.hidden = false;
      } else {
        triggerText.textContent = ui.select_subcategory || 'Выберите подкатегорию';
        picker.classList.remove('has-value');
        triggerBadge.textContent = `${validOptions.length} ${ui.options_count || ''}`.trim();
        triggerBadge.hidden = false;
        clearBtn.hidden = true;
      }
    }

    function renderOptions(query = '') {
      const validOptions = getValidOptions();
      searchWrap.hidden = validOptions.length < 5;

      const q = query.trim().toLowerCase();
      const filtered = validOptions.filter(o => !q || o.text.toLowerCase().includes(q));

      list.innerHTML = '';
      if (!filtered.length) {
        emptyMsg.hidden = false;
        return;
      }
      emptyMsg.hidden = true;

      filtered.forEach(option => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'pw-subcategory-item';
        item.dataset.value = option.value;
        const isSelected = option.value === subcategory.value;
        if (isSelected) item.classList.add('is-selected');
        item.setAttribute('role', 'option');
        item.setAttribute('aria-selected', String(isSelected));

        const itemLeft = document.createElement('span');
        itemLeft.className = 'pw-subcategory-item__left';

        const dot = document.createElement('span');
        dot.className = 'pw-subcategory-item__dot';
        dot.setAttribute('aria-hidden', 'true');

        const labelSpan = document.createElement('span');
        labelSpan.className = 'pw-subcategory-item__label';
        labelSpan.textContent = option.text;

        itemLeft.append(dot, labelSpan);
        item.append(itemLeft);

        if (isSelected) {
          const check = document.createElement('span');
          check.className = 'pw-subcategory-item__check';
          check.setAttribute('aria-hidden', 'true');
          check.innerHTML = '✓';
          item.append(check);
        }

        item.addEventListener('click', (e) => {
          e.preventDefault();
          subcategory.value = option.value;
          subcategory.dispatchEvent(new Event('change', { bubbles: true }));
          closeMenu();
          trigger.focus();
        });

        list.append(item);
      });
    }

    function openMenu() {
      if (trigger.disabled) return;
      menu.hidden = false;
      picker.classList.add('is-open');
      trigger.setAttribute('aria-expanded', 'true');
      renderOptions('');
      if (!searchWrap.hidden) {
        searchInput.value = '';
        searchClear.hidden = true;
        setTimeout(() => searchInput.focus(), 50);
      }
    }

    function closeMenu() {
      menu.hidden = true;
      picker.classList.remove('is-open');
      trigger.setAttribute('aria-expanded', 'false');
    }

    function toggleMenu() {
      if (menu.hidden) openMenu();
      else closeMenu();
    }

    trigger.addEventListener('click', toggleMenu);

    clearBtn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      subcategory.value = '';
      subcategory.dispatchEvent(new Event('change', { bubbles: true }));
      renderTrigger();
      closeMenu();
      trigger.focus();
    });

    searchInput.addEventListener('input', () => {
      searchClear.hidden = !searchInput.value;
      renderOptions(searchInput.value);
    });

    searchClear.addEventListener('click', () => {
      searchInput.value = '';
      searchClear.hidden = true;
      renderOptions('');
      searchInput.focus();
    });

    document.addEventListener('click', (e) => {
      if (!picker.contains(e.target)) {
        closeMenu();
      }
    });

    picker.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeMenu();
        trigger.focus();
      }
    });

    category.addEventListener('change', () => {
      window.setTimeout(() => {
        renderTrigger();
        if (!menu.hidden) renderOptions();
      }, 0);
    });

    subcategory.addEventListener('change', () => {
      renderTrigger();
      if (!menu.hidden) renderOptions();
    });

    subcategory.addEventListener('km:subcategory-rebuilt', () => {
      renderTrigger();
      if (!menu.hidden) renderOptions();
    });

    try {
      const observer = new MutationObserver(() => {
        renderTrigger();
        if (!menu.hidden) renderOptions();
      });
      observer.observe(subcategory, { childList: true });
    } catch (e) {}

    renderTrigger();
  }

  const description = el('description_az'), counter = document.createElement('small');
  counter.className = 'pw-description-count';
  if (description) {
    description.after(counter);
    function countDescription() {
      const len = description.value.trim().length;
      const min = rules.description_min;
      if (len >= min) {
        counter.textContent = `✓ ${len} / ${min} simvol (kifayətdir)`;
        counter.classList.add('is-ready');
        counter.classList.remove('is-partial');
      } else if (len > 0) {
        counter.textContent = `${len} / ${min} simvol (tamamlamaq üçün daha ${min - len} simvol yazın)`;
        counter.classList.remove('is-ready');
        counter.classList.add('is-partial');
      } else {
        counter.textContent = `0 / ${min} simvol (ən azı ${min} simvol tələb olunur)`;
        counter.classList.remove('is-ready', 'is-partial');
      }
    }
    if (!volunteer) {
      description.addEventListener('input', () => { countDescription(); markRequired(); });
      countDescription();
    }
  }
  setAge(ageMode); regionChanged(); markRequired();
  function targetStepFromHash() {
    const raw = (location.hash || '').replace(/^#/, '');
    if (!raw) return null;
    if (raw === 'photos') return 6;
    const params = new URLSearchParams(raw);
    const stepVal = params.get('step');
    if (stepVal) {
      const num = Number(stepVal);
      if (num >= 1 && num <= 7) return num;
    }
    const fieldAnchor = params.get('field');
    if (fieldAnchor) return fieldStep(fieldAnchor);
    return null;
  }

  const firstError = form.querySelector('.pw-error')?.closest('[data-pw-step]');
  const hashStep = targetStepFromHash();
  go(firstError ? Number(firstError.dataset.pwStep) : hashStep || current, false);
  const initialField = new URLSearchParams((location.hash || '').replace(/^#/, '')).get('field');
  if (initialField) reveal(initialField);
  document.addEventListener('DOMContentLoaded', () => { initialized = true; markRequired(); });
  window.addEventListener('pageshow', () => { submitting = false; });
  window.addEventListener('hashchange', () => {
    const hs = targetStepFromHash();
    if (hs) go(hs, false);
    const name = new URLSearchParams((location.hash || '').replace(/^#/, '')).get('field');
    if (name) reveal(name);
  });
})();
