(function () {
  'use strict';
  const lang = (document.documentElement.lang || 'az').split('-')[0];
  const text = (ru, az, en) => lang === 'az' ? az : lang === 'en' ? en : ru;
  const actionForm = document.querySelector('[data-occurrence-form]');
  if (actionForm) {
    actionForm.addEventListener('submit', event => {
      if (actionForm.dataset.sending === '1') { event.preventDefault(); return; }
      actionForm.dataset.sending = '1';
      actionForm.setAttribute('aria-busy', 'true');
      actionForm.querySelector('[data-occurrence-status]').textContent = text('Действие выполняется…', 'Əməliyyat icra olunur…', 'Applying action…');
      // Do not disable the submitter before the browser reads its formaction.
      actionForm.querySelectorAll('button').forEach(button => button.setAttribute('aria-disabled', 'true'));
    });
    window.addEventListener('pageshow', () => { actionForm.dataset.sending = ''; actionForm.removeAttribute('aria-busy'); actionForm.querySelectorAll('button').forEach(button => button.removeAttribute('aria-disabled')); });
  }
  const form = document.querySelector('[data-event-form]');
  if (!form) return;
  const field = name => form.elements.namedItem(name);
  const value = name => field(name)?.value || '';
  const sections = Array.from(form.querySelectorAll('[data-owner-step]'));
  const stepButtons = Array.from(form.querySelectorAll('[data-owner-step-target]'));
  const formatRadios = Array.from(form.querySelectorAll('input[name="event_format"]'));
  const physical = Array.from(form.querySelectorAll('[data-event-physical]'));
  const organizerRadios = Array.from(form.querySelectorAll('[name="organizer_role_switch"]'));
  const venueRadios = Array.from(form.querySelectorAll('[name="venue_choice_switch"]'));
  const multiDay = form.querySelector('[data-toggle-multi-day]');
  const endContainer = form.querySelector('[data-multi-day-container]');
  const status = form.querySelector('[data-event-save-status]');
  const missingList = form.querySelector('[data-event-missing]');
  const requirements = JSON.parse(document.getElementById('event-requirements').textContent);
  let step = 0, sending = false, previewUrl = null;
  const online = () => value('event_format') === form.dataset.onlineFormat;
  const visibleControl = input => input?._flatpickr?.altInput || input;
  const photoInput = field('photo');

  function showStep(index, focus = false) {
    index = Math.max(0, Math.min(sections.length - 1, Number(index) || 0)); step = index;
    sections.forEach((section, i) => { section.hidden = i !== step; section.style.display = i === step ? '' : 'none'; });
    stepButtons.forEach((button, i) => {
      button.classList.toggle('is-active', i === step);
      button.classList.remove('is-completed'); // Visiting a step does not mean its data is ready.
      if (i === step) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current');
    });
    const progress = form.querySelector('[data-owner-progress-text]');
    if (progress) progress.textContent = progress.dataset.label.replace('{current}', step + 1).replace('{total}', sections.length).replace('{name}', sections[step].dataset.stepName);
    const bar = form.querySelector('[data-owner-progress-bar]'); if (bar) bar.style.width = ((step + 1) / sections.length * 100) + '%';
    form.querySelectorAll('[data-owner-prev]').forEach(button => button.disabled = step === 0);
    form.querySelectorAll('[data-owner-next]').forEach(button => button.disabled = step === sections.length - 1);
    if (focus) { const heading = sections[step].querySelector('h2'); heading.tabIndex = -1; heading.focus(); heading.scrollIntoView({block:'start'}); }
    updatePreview();
    form.dispatchEvent(new CustomEvent('km:event-step'));
    if (step === 1 && window.kidsMapRefreshOwnerMapPickers) window.kidsMapRefreshOwnerMapPickers();
  }
  function reveal(input) {
    if (!input) return;
    if (input.disabled && input.name.startsWith('organizer_')) input = Array.from(form.querySelectorAll('[name=organizer_organization],[name=organizer_specialist]')).find(node => !node.disabled) || input;
    const index = sections.findIndex(section => section.contains(input)); if (index >= 0) showStep(index);
    if (input.name === 'end_date' && multiDay) { multiDay.checked = true; syncEndDate(); }
    if (['address','region','district','metro','related_place'].includes(input.name) && !online()) {
      const choice = input.name === 'related_place' ? 'related' : 'custom';
      venueRadios.forEach(radio => radio.checked = radio.value === choice); syncVenue(false);
    }
    if (input.name === 'photo') input = form.querySelector('[data-choose-photo]');
    input = visibleControl(input); input.focus(); input.scrollIntoView({block:'center'});
  }
  stepButtons.forEach(button => button.addEventListener('click', () => showStep(button.dataset.ownerStepTarget, true)));
  form.querySelectorAll('[data-owner-next]').forEach(button => button.addEventListener('click', () => showStep(step + 1, true)));
  form.querySelectorAll('[data-owner-prev]').forEach(button => button.addEventListener('click', () => showStep(step - 1, true)));

  function syncOrganizer() {
    const selected = organizerRadios.find(radio => radio.checked)?.value || (value('organizer_specialist') ? 'specialist' : 'org');
    form.querySelectorAll('[data-organizer-block]').forEach(block => {
      const active = block.dataset.organizerBlock === selected; block.hidden = !active; block.style.display = active ? '' : 'none';
      block.querySelectorAll('select').forEach(select => select.disabled = !active);
    });
    organizerRadios.forEach(radio => radio.closest('label').classList.toggle('is-selected', radio.checked));
  }
  function syncFormat() {
    formatRadios.forEach(radio => radio.closest('[data-owner-format-card]').classList.toggle('is-selected', radio.checked));
    const notice = form.querySelector('[data-event-online-notice]'); notice.hidden = !online(); notice.style.display = online() ? '' : 'none';
    physical.forEach(block => {
      block.hidden = online(); block.style.display = online() ? 'none' : '';
      block.querySelectorAll('input,select,textarea,button').forEach(input => input.disabled = online());
    });
    if (!online()) syncVenue(false);
  }
  function syncEndDate() {
    if (!multiDay || !endContainer) return;
    endContainer.hidden = !multiDay.checked; endContainer.style.display = multiDay.checked ? '' : 'none';
    if (!multiDay.checked) setValue('end_date', value('event_date'));
    const end = field('end_date'); if (end?._flatpickr) end._flatpickr.set('minDate', value('event_date') || null);
  }
  function setValue(name, val) {
    const input = field(name); if (!input || input instanceof RadioNodeList) return;
    input.value = val;
    if (input._flatpickr) input._flatpickr.setDate(val, false);
  }
  function selectedVenue() { const select = field('related_place'); return select?.options?.[select.selectedIndex]; }
  function venueChoice() { return venueRadios.find(radio => radio.checked)?.value || 'custom'; }
  let customLocation = null;
  const locationFields = ['address','region','district','metro','lat','lng'];
  function syncVenue(change) {
    const related = venueChoice() === 'related';
    const block = form.querySelector('[data-venue-block="related"]'); block.hidden = !related; block.style.display = related ? '' : 'none';
    const place = field('related_place'); place.disabled = !related || online();
    venueRadios.forEach(radio => radio.closest('label').classList.toggle('is-selected', radio.checked));
    if (change && related) customLocation = Object.fromEntries(locationFields.map(name => [name, value(name)]));
    if (related && selectedVenue()?.value) {
      const option = selectedVenue();
      ['address','lat','lng','region'].forEach(name => setValue(name, option.dataset[name] || ''));
      field('region')?.dispatchEvent(new Event('change', {bubbles:true}));
      ['district','metro'].forEach(name => setValue(name, option.dataset[name] || ''));
      field('district')?.dispatchEvent(new Event('change', {bubbles:true}));
    } else if (change && !related && customLocation) locationFields.forEach(name => setValue(name, customLocation[name] || ''));
    // Never advertise a custom address as the selected venue snapshot.
    if (field('address')) field('address').readOnly = related;
    const map = form.querySelector('[data-venue-block="map"]'); if (map) { map.hidden = related; map.style.display = related ? 'none' : ''; }
    const venueStatus = form.querySelector('[data-venue-status]');
    if (venueStatus) venueStatus.textContent = related && !selectedVenue()?.value ? text('Выберите доступную площадку или собственный адрес.','Əlçatan məkan və ya öz ünvanınızı seçin.','Choose an available venue or your own address.') : '';
    const phoneButton = form.querySelector('[data-use-venue-phone]'); if (phoneButton) phoneButton.disabled = online() || !selectedVenue()?.dataset.phone;
  }
  organizerRadios.forEach(radio => radio.addEventListener('change', () => {syncOrganizer();updatePreview();}));
  formatRadios.forEach(radio => radio.addEventListener('change', () => {syncFormat();updatePreview();}));
  venueRadios.forEach(radio => radio.addEventListener('change', () => {syncVenue(true);updatePreview();}));
  field('related_place')?.addEventListener('change', () => {syncVenue(false);updatePreview();});
  multiDay?.addEventListener('change', () => {syncEndDate();updatePreview();});
  field('event_date')?.addEventListener('change', syncEndDate);
  form.querySelector('[data-use-venue-phone]')?.addEventListener('click', () => {
    setValue('phone',selectedVenue()?.dataset.phone || ''); field('phone').dispatchEvent(new Event('input',{bubbles:true})); reveal(field('phone'));
  });

  const put = (selector, val) => { const node=form.querySelector(selector); if(node) node.textContent=val; };
  function dateInterval() {
    const startDate=value('event_date'), endDate=value('end_date') || startDate;
    const start=startDate && value('start_time_input') ? new Date(startDate+'T'+value('start_time_input')+':00'+form.dataset.eventUtcOffset) : null;
    const end=endDate && value('end_time_input') ? new Date(endDate+'T'+value('end_time_input')+':00'+form.dataset.eventUtcOffset) : null;
    return {start,end,startDate,endDate};
  }
  function updatePreview() {
    const {start,end,startDate,endDate}=dateInterval();
    const dateText = startDate && value('start_time_input') ? startDate+' '+value('start_time_input')+' — '+endDate+' '+value('end_time_input')+' · Asia/Baku' : text('Дата и время не указаны','Tarix və vaxt göstərilməyib','Date and time not set');
    put('[data-preview-title]',value('name_az') || text('Название мероприятия (AZ)','Tədbirin adı (AZ)','Event title (AZ)'));
    const org=field('organizer_organization'),spec=field('organizer_specialist');
    const chosen=(org && !org.disabled && org.value ? org : spec && !spec.disabled && spec.value ? spec : null);
    put('[data-preview-organizer-text]',chosen?.options?.[chosen.selectedIndex]?.text || form.querySelector('[data-organizer-locked] strong')?.textContent || text('Организатор не выбран','Təşkilatçı seçilməyib','No organizer selected'));
    put('[data-preview-cat-tag]',field('category')?.selectedOptions?.[0]?.text || '');
    put('[data-preview-format-tag]',online()?text('Онлайн','Onlayn','Online'):text('Очно','Əyani','In person'));
    put('[data-preview-location-text]',online()?text('Физический адрес не требуется','Fiziki ünvan lazım deyil','No physical address required'):value('address') || text('Адрес не указан','Ünvan göstərilməyib','No address set'));
    put('[data-preview-datetime-text]',dateText);
    const ageFrom=value('age_from'),ageTo=value('age_to');
    put('[data-preview-age-text]',ageFrom !== '' && ageTo !== '' ? ageFrom+' – '+ageTo+' '+text('лет','yaş','years') : '—');
    put('[data-preview-price-text]',value('price_text') || '—'); put('[data-preview-phone-text]',value('phone') || '—');
    put('#event-description-counter',value('description_az').length);
    const duration=form.querySelector('[data-owner-event-datetime-summary]');
    if(duration){ const valid=start && end && end>start;duration.classList.toggle('is-error',Boolean(start&&end&&!valid));duration.textContent=valid?dateText+' · '+Math.round((end-start)/60000)+' '+text('мин.','dəq.','min'):start&&end?form.dataset.endBeforeStartMessage:duration.dataset.emptyLabel; }
    if(missingList){missingList.replaceChildren(); const missing=requirements.filter(rule=>!(rule.physical&&online()) && (rule.oneOf?!rule.oneOf.some(name=>field(name)&&!field(name).disabled&&value(name)):rule.field==='photo'?!(photoInput.files.length||form.dataset.hasPhoto==='1'):value(rule.field).trim()===''));
      missing.forEach(rule=>{const li=document.createElement('li'),link=document.createElement('a');link.href='#id_'+rule.field;link.textContent=rule.label;link.addEventListener('click',e=>{e.preventDefault();reveal(field(rule.field));});li.append(link);missingList.append(li);});
      if(!missing.length){const li=document.createElement('li');li.textContent=text('Поля заполнены. При отправке сервер проверит значения, даты и права.','Sahələr doldurulub. Server göndərmədə dəyərləri, tarixləri və hüquqları yoxlayacaq.','Fields are filled. The server checks values, dates and permissions on submission.');missingList.append(li);}
    }
  }

  form.querySelector('[data-choose-photo]')?.addEventListener('click',()=>photoInput.click());
  form.querySelector('[data-file-retry-btn]')?.addEventListener('click',()=>photoInput.click());
  photoInput.addEventListener('change',()=>{
    const file=photoInput.files[0],box=form.querySelector('[data-file-error-box]');if(!file)return;
    const supported=/\.(jpe?g|png|webp|heic|heif|hif)$/i.test(file.name);
    if(file.size>Number(form.dataset.photoSourceBytes)||!supported){photoInput.value='';box.style.display='block';put('[data-file-error-title]',text('Не удалось выбрать фото','Foto seçmək mümkün olmadı','Could not select photo'));put('[data-file-error-desc]',file.size>Number(form.dataset.photoSourceBytes)?text('Исходник превышает лимит сервера. Выберите меньший файл.','Mənbə fayl server limitini keçir. Kiçik fayl seçin.','The source exceeds the server limit. Choose a smaller file.'):text('Выберите JPG, PNG, WEBP или HEIC/HEIF.','JPG, PNG, WEBP və ya HEIC/HEIF seçin.','Choose JPG, PNG, WEBP or HEIC/HEIF.'));updatePreview();return;}
    box.style.display='none';if(previewUrl)URL.revokeObjectURL(previewUrl);previewUrl=URL.createObjectURL(file);
    ['[data-owner-photo-preview]','[data-preview-img-wrap]'].forEach(selector=>{const wrap=form.querySelector(selector),img=document.createElement('img');img.src=previewUrl;img.alt=text('Выбранное фото','Seçilmiş foto','Selected photo');img.onerror=()=>{wrap.replaceChildren(document.createTextNode(text('Предпросмотр недоступен; файл проверит сервер.','Önbaxış mümkün deyil; faylı server yoxlayacaq.','Preview unavailable; the server will validate the file.')));};wrap.replaceChildren(img);});updatePreview();
  });

  function setStatus(kind) {
    const messages={unsaved:text('Ещё не сохранено на сервере','Hələ serverdə saxlanılmayıb','Not saved on the server yet'),saved:text('Данные сохранены на сервере','Məlumatlar serverdə saxlanılıb','Data saved on the server'),loaded:text('Данные загружены с сервера','Məlumatlar serverdən yüklənib','Data loaded from the server'),dirty:text('Есть несохранённые изменения','Saxlanılmamış dəyişikliklər var','There are unsaved changes'),saving:text('Сохранение…','Saxlanılır…','Saving…'),error:text('Изменения не сохранены. Исправьте ошибки.','Dəyişikliklər saxlanılmayıb. Xətaları düzəldin.','Changes were not saved. Correct the errors.'),conflict:text('Конфликт версии. Изменения не сохранены.','Versiya ziddiyyəti. Dəyişikliklər saxlanılmayıb.','Version conflict. Changes were not saved.')};status.textContent=messages[kind];status.dataset.state=kind;
  }
  form.addEventListener('input',()=>{if(!sending)setStatus('dirty');updatePreview();});
  form.addEventListener('change',()=>{if(!sending)setStatus('dirty');updatePreview();});
  form.addEventListener('km:map-change',()=>{setStatus('dirty');updatePreview();});
  form.addEventListener('submit',event=>{
    if(sending){event.preventDefault();return;} sending=true;setStatus('saving');form.setAttribute('aria-busy','true');
    // Native submit values must survive disabling buttons; copy the chosen action first.
    const action=document.createElement('input');action.type='hidden';action.name='form_action';action.value=event.submitter?.value || 'submit';action.dataset.eventSubmitAction='';form.append(action);
    form.querySelectorAll('button[type=submit]').forEach(button=>button.disabled=true);
  });
  window.addEventListener('pageshow',()=>{if(sending){sending=false;form.removeAttribute('aria-busy');form.querySelectorAll('[data-event-submit-action]').forEach(node=>node.remove());form.querySelectorAll('button[type=submit]').forEach(button=>button.disabled=false);setStatus('dirty');}});
  // Server errors identify the real control, including visible flatpickr alt inputs.
  form.querySelectorAll('[data-error-field-ref]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();reveal(field(link.dataset.errorFieldRef));}));
  sections.forEach(section=>section.querySelectorAll('.auth-field-error').forEach(error=>{
    const group=error.closest('.km-field-group')||error.parentElement,input=group.querySelector('input:not([type=hidden]),select,textarea');
    if(input){if(!error.id)error.id='event-error-'+(input.name||'photo');visibleControl(input).setAttribute('aria-invalid','true');visibleControl(input).setAttribute('aria-describedby',error.id);}
  }));
  ['event_date','end_date','start_time_input','end_time_input'].forEach(name=>{const input=field(name),visible=visibleControl(input);if(visible&&visible!==input){visible.setAttribute('aria-label',input.closest('label')?.querySelector('.km-field-label')?.textContent || name);}});
  stepButtons.forEach((button,index)=>{const count=sections[index].querySelectorAll('.auth-field-error').length;button.classList.toggle('has-step-error',count>0);if(count){const badge=document.createElement('span');badge.className='km-step-error-badge';badge.textContent=count;badge.setAttribute('aria-label',text('Ошибок: ','Xətalar: ','Errors: ')+count);button.append(badge);}});
  form.querySelector('[data-map-search-input]')?.setAttribute('aria-label',form.dataset.mapSearchLabel);
  const summary=form.querySelector('[data-error-summary]');
  syncOrganizer();syncFormat();syncEndDate();showStep(0);updatePreview();
  if(summary){summary.focus();const first=summary.querySelector('[data-error-field-ref]');if(first){const input=field(first.dataset.errorFieldRef),index=sections.findIndex(section=>section.contains(input));if(index>=0)showStep(index);}}
  setStatus(form.dataset.errorCode==='stale_version'?'conflict':summary?'error':form.dataset.explicitSave==='1'?'saved':value('expected_updated_at')?'loaded':'unsaved');
  // Event-only timeout: a map outage does not erase an address or impose a map requirement.
  const mapRoot=form.querySelector('[data-event-optional-map]'),fallback=form.querySelector('[data-event-map-fallback]');
  if(mapRoot&&fallback){const check=()=>{if(typeof mapRoot._kidsMapRefreshMap!=='function'){fallback.hidden=false;mapRoot.querySelectorAll('[data-map-search],[data-map-locate]').forEach(button=>button.disabled=true);}else fallback.hidden=true;};if(mapRoot.dataset.mapProvider==='unavailable')check();else setTimeout(check,8000);}
  window.kidsMapOwnerEventEntry={getStep:()=>step,showStep,setValue,refresh:()=>{syncOrganizer();syncFormat();syncEndDate();updatePreview();},setStatus};
})();
