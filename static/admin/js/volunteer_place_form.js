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
  let interacted = false;
  let bypassNavigation = false;
  const hasPending = () => typeof form.kmDraftHasPending === 'function' ? form.kmDraftHasPending() : dirty;
  const copy = ({ru:{title:'Сохранить изменения перед выходом?',body:'Можно сохранить черновик и продолжить позже.',stay:'Продолжить заполнение',save:'Сохранить и выйти',discard:'Выйти без сохранения',error:'Не удалось сохранить. Проверьте данные и попробуйте ещё раз.',checking:'Проверяем изменения…'},az:{title:'Çıxmazdan əvvəl dəyişikliklər saxlanılsın?',body:'Qaralamanı saxlayıb sonra davam edə bilərsiniz.',stay:'Doldurmağa davam et',save:'Saxla və çıx',discard:'Saxlamadan çıx',error:'Saxlamaq mümkün olmadı. Məlumatları yoxlayıb yenidən cəhd edin.',checking:'Dəyişikliklər yoxlanılır…'},en:{title:'Save changes before leaving?',body:'Save a draft and continue later.',stay:'Keep editing',save:'Save and leave',discard:'Leave without saving',error:'Could not save. Check the entries and try again.',checking:'Checking changes…'}})[document.documentElement.lang?.split('-')[0]] || {title:'Save changes?',body:'Save a draft to continue later.',stay:'Keep editing',save:'Save and leave',discard:'Leave without saving',error:'Could not save. Try again.',checking:'Checking changes…'};
  const trackInteraction = event => { if (event.isTrusted) interacted = true; };
  form.addEventListener('pointerdown', trackInteraction, true);
  form.addEventListener('keydown', trackInteraction, true);
  const markDirty = event => {
    // Schedule/tariff widgets emit synthetic changes while initializing. A
    // freshly opened form must not warn that the user has unsaved edits.
    if (!event.isTrusted && !interacted) return;
    if (!event.target.name && !event.target.closest('[data-tariff-editor],[data-km-schedule-editor]')) return;
    dirty = typeof form.kmDraftHasPending === 'function' ? form.kmDraftHasPending() : true;
    if(dirty)form.querySelector('[data-editor-save-state]').textContent = form.dataset.dirtyLabel;
  };
  form.addEventListener('input', markDirty);
  form.addEventListener('change', markDirty);
  form.addEventListener('submit', event => {
    if(event.submitter?.matches('[data-km-preview]') || event.defaultPrevented)return;
    submitting=true;
    queueMicrotask(()=>{if(event.defaultPrevented)submitting=false;});
  });
  form.addEventListener('km:draft-saved', () => {dirty=false;submitting=false;const status=form.querySelector('[data-editor-save-state]');if(status)status.textContent=({ru:'Черновик сохранён',az:'Qaralama saxlanıldı',en:'Draft saved'})[document.documentElement.lang?.split('-')[0]]||'Draft saved';});
  window.addEventListener('beforeunload', event => { if (hasPending() && !submitting && !bypassNavigation) { event.preventDefault(); event.returnValue = ''; } });
  form.addEventListener('km:readiness', event => {
    const result=event.detail?.readiness || event.detail;if(!result)return;
    if(result.pending){form.querySelectorAll('[data-readiness-status]').forEach(node=>{node.textContent=copy.checking;});return;}
    if(!Array.isArray(result.items))return;
    const total=Number(result.required_count)||0,done=Number(result.completed_count)||0,pct=total?Math.round(done/total*100):0;
    form.querySelectorAll('[data-progress-pct]').forEach(node=>{node.textContent=pct+'%';});
    form.querySelectorAll('[data-progress-done]').forEach(node=>{node.textContent=done;});
    form.querySelectorAll('[data-progress-total]').forEach(node=>{node.textContent=total;});
    form.querySelectorAll('[data-progress-bar]').forEach(node=>{node.style.width=pct+'%';});
    const verify=form.querySelector('[data-volunteer-readiness]');
    if(verify){
      verify.querySelectorAll('.km-pf-verify-banner,.km-pf-issues__list').forEach(node=>{node.hidden=true;});
      const status=verify.querySelector('[data-readiness-status]');if(status){status.hidden=false;status.textContent=`${done} / ${total} · ${pct}%`;}
      const list=verify.querySelector('[data-readiness-items]');
      if(list){list.hidden=false;list.replaceChildren();result.items.forEach(item=>{const li=document.createElement('li'),link=document.createElement('a');link.href='#field='+encodeURIComponent(item.field);link.textContent=(item.complete?'✓ ':'○ ')+item.label;li.append(link);if(!item.complete&&item.message)li.append(document.createTextNode(' — '+item.message));list.append(li);});}
    }
    sections.forEach(section=>{
      const group=section.id==='verification'?result:result.sections?.find(item=>item.id===section.id);
      if(!group)return;
      const state=group.error_count?'error':(group.is_complete||group.is_ready)&&group.required_count?'done':group.completed_count?'partial':'empty';
      const nodes=[section,...form.querySelectorAll(`[data-pf-nav-for="${section.id}"]`)];
      nodes.forEach(node=>{['done','partial','empty','error'].forEach(value=>node.classList.toggle('is-'+value,state===value));node.querySelectorAll('[data-place-section-state-text],[data-pf-nav-sub]').forEach(text=>{text.textContent=group.required_count?`${group.completed_count} / ${group.required_count}`:'';});node.querySelectorAll('[data-place-section-state-icon],[data-pf-nav-icon]').forEach(icon=>icon.setAttribute('href','#kmi-'+({done:'check_circle',error:'error',partial:'radio_button_checked',empty:'radio_button_unchecked'})[state]));});
    });
  });
  document.addEventListener('click',event=>{
    const link=event.target.closest('a[href]');
    if(!link||!hasPending()||submitting||bypassNavigation||event.defaultPrevented||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||link.target==='_blank'||link.hasAttribute('download'))return;
    if(!/^https?:/.test(link.href)||link.getAttribute('href').startsWith('#')||link.href===location.href)return;
    event.preventDefault();
    const dialog=document.createElement('dialog');dialog.className='km-pf-dialog';dialog.setAttribute('aria-label',copy.title);
    const heading=document.createElement('h2');heading.textContent=copy.title;
    const note=document.createElement('p');note.textContent=copy.body;
    const error=document.createElement('p');error.className='km-pf-field__error';error.setAttribute('role','alert');error.hidden=true;
    dialog.append(heading,note,error);
    const stay=document.createElement('button'),save=document.createElement('button'),discard=document.createElement('button');
    [stay,save,discard].forEach(button=>{button.type='button';button.className='km-pf-btn';dialog.append(button);});
    stay.textContent=copy.stay;save.textContent=copy.save;discard.textContent=copy.discard;
    stay.addEventListener('click',()=>dialog.close());discard.addEventListener('click',()=>{bypassNavigation=true;location.assign(link.href);});
    save.addEventListener('click',async()=>{
      save.disabled=true;error.hidden=true;
      try {
        // The shared adapter owns serialization, media and retry/version handling.
        if(!form.kmDraftSave || !await form.kmDraftSave())throw new Error('Draft save failed');
        bypassNavigation=true;location.assign(link.href);
      }catch{error.textContent=copy.error;error.hidden=false;save.disabled=false;}
    });
    dialog.addEventListener('close',()=>{dialog.remove();link.focus({preventScroll:true});},{once:true});
    document.body.append(dialog);dialog.showModal();stay.focus();
  });
  const ageOpen = form.elements.namedItem('age_open_ended');
  const ageTo = form.elements.namedItem('age_to');
  const syncAge = () => { ageTo.disabled = ageOpen.checked; };
  ageOpen.addEventListener('change', syncAge); syncAge();
  const setupImagePreview = (inputName, previewSelector) => {
    const input = form.elements.namedItem(inputName);
    const preview = form.querySelector(previewSelector);
    if (!input || !preview) return;
    const wrap = preview.closest('.kv-photo-preview-wrap');
    let objectUrl;
    input.addEventListener('change', () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      if (input.files && input.files[0]) {
        objectUrl = URL.createObjectURL(input.files[0]);
        preview.src = objectUrl;
        preview.hidden = false;
        if (wrap) {
          wrap.classList.remove('is-empty');
          const placeholder = wrap.querySelector('.kv-photo-placeholder');
          if (placeholder) placeholder.hidden = true;
        }
      }
    });
  };
  setupImagePreview('photo', '[data-editor-photo-preview]');
  setupImagePreview('cover_photo', '[data-editor-cover-preview]');
  const errors = form.querySelector('[data-editor-errors]');
  if (errors) errors.focus();
})();
