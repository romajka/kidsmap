/* Opt-in editor interaction contract. Business validation remains on the server. */
(() => {
  'use strict';
  const lang=(document.documentElement.lang||'az').split('-')[0];
  const copy={ru:{phone:'В телефоне используйте цифры, пробелы, скобки, дефис и + в начале.',title:'Проверьте отмеченные поля',chars:'символов',lines:'строк',required:'Заполните это поле.',invalid:'Проверьте формат значения.',long:'Сократите текст до указанного ограничения.'},az:{phone:'Telefon üçün rəqəmlər, boşluq, mötərizə, defis və əvvəlində + istifadə edin.',title:'İşarələnmiş sahələri yoxlayın',chars:'simvol',lines:'sətir',required:'Bu sahəni doldurun.',invalid:'Dəyərin formatını yoxlayın.',long:'Mətni göstərilən həddə qədər qısaldın.'},en:{phone:'Use digits, spaces, parentheses, hyphens and one leading + in a phone number.',title:'Check the highlighted fields',chars:'characters',lines:'lines',required:'Complete this field.',invalid:'Check the value format.',long:'Shorten the text to the stated limit.'}}[lang]||{};
  const text={...{phone:'Use digits and an international +code.',title:'Check the highlighted fields',chars:'characters',lines:'lines',required:'Complete this field.',invalid:'Check the value format.',long:'Shorten the text to the stated limit.'},...copy};
  const states=new WeakMap(),attentionTimers=new WeakMap();let nextId=0;
  const checkCopy={ru:{busy:'Проверяем данные…',ready:'Обязательные данные заполнены. Откройте предпросмотр перед отправкой.',changed:'Данные изменились во время проверки. Проверьте заполнение ещё раз.',failed:'Проверка не завершилась. Введённые данные остались в форме. Повторите попытку.'},az:{busy:'Məlumatlar yoxlanılır…',ready:'Məcburi məlumatlar doldurulub. Göndərməzdən əvvəl ön baxışı açın.',changed:'Yoxlama zamanı məlumatlar dəyişib. Yenidən yoxlayın.',failed:'Yoxlama tamamlanmadı. Daxil etdiyiniz məlumatlar formadadır. Yenidən cəhd edin.'},en:{busy:'Checking entries…',ready:'Required entries are complete. Open the preview before submitting.',changed:'Entries changed during the check. Check the form again.',failed:'The check did not finish. Your entries remain in the form. Try again.'}}[lang]||{busy:'Checking…',ready:'Required entries are complete.',changed:'Check again after editing.',failed:'Try the check again.'};
  const wrapper=input=>input?.closest('[data-km-editor-field],[data-pw-field],[data-pf-field],.owner-tariff-field,[data-tariff-editor]')||input?.parentElement;
  function target(form,name,path) {
    if(name==='structured_schedule'){
      const message=form.querySelector('[data-km-schedule-validation]'),mode=form.elements.namedItem('schedule_mode');
      if(message)return mode&&!mode.value?mode:message;
    }
    if(name==='pricing_plans'&&Array.isArray(path)&&path[0]==='pricing_plans'&&Number.isSafeInteger(path[1])&&path[1]>=0){
      const row=form.querySelectorAll('[data-tariff-list] > [data-tariff-row]')[path[1]];
      if(row&&typeof path[2]==='string'&&/^[a-z_]+$/.test(path[2])){
        const field=row.querySelector(`[data-tariff-key="${path[2]}"]`);
        if(path[2]==='price_kind')return row.querySelector('[data-price-kind][aria-pressed=true]')||field;
        if(field&&!field.closest('[hidden]'))return field;
      }
      if(row)return row.querySelector('[data-tariff-key=editor_kind]');
    }
    if(name==='public_links'&&Array.isArray(path)&&path[0]==='public_links'&&Number.isSafeInteger(path[1])&&path[1]>=0&&['label','url'].includes(path[2])){
      const row=form.querySelectorAll('[data-public-link-row]')[path[1]];
      if(row)return row.querySelector(`[data-public-link-key="${path[2]}"]`);
    }
    if(name==='pricing_plans')return form.querySelector('[data-tariff-list] [data-tariff-key=editor_kind],[data-tariff-add]');
    if(['photo','gallery_images','gallery_uploads'].includes(name))return form.querySelector('[data-place-photos-picker]');
    if(['age_from','age_to'].includes(name)&&form.querySelector(`#id_${name}_range`))return form.querySelector(`#id_${name}_range`);
    const input=[...form.querySelectorAll('[name]')].find(node=>node.name===name);
    if(input?.type==='hidden')return wrapper(input)?.querySelector('button,input:not([type=hidden]),select,textarea')||input;
    return input;
  }
  function focus(input) {
    if(!input)return;
    const panel=input.closest('[data-km-language-panel]');
    panel?.closest('[data-km-language-group]')?.querySelector(`[data-km-language="${panel.dataset.kmLanguagePanel}"]`)?.click();
    input.closest('form')?.dispatchEvent(new CustomEvent('km:reveal-field',{bubbles:true,detail:{element:input}}));
    for(let p=input.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
    const row=wrapper(input),proxy=row?.querySelector('.select2-selection,.km-pf-picker-btn,[data-price-policy]');
    const control=(input.type==='hidden'||input.classList.contains('select2-hidden-accessible')||input.closest('.km-pf-native-select'))?proxy||input:input;
    control.scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});control.focus({preventScroll:true});
    if(row){clearTimeout(attentionTimers.get(row));row.classList.remove('km-editor-attention');void row.offsetWidth;row.classList.add('km-editor-attention');attentionTimers.set(row,setTimeout(()=>row.classList.remove('km-editor-attention'),4200));}
  }
  function clear(form,input) {
    const state=states.get(form),entry=state?.errors.get(input);if(!entry)return;
    entry.node.remove();input.removeAttribute('aria-invalid');
    entry.proxies?.forEach(proxy=>{proxy.removeAttribute('aria-invalid');const ids=(proxy.getAttribute('aria-describedby')||'').split(/\s+/).filter(id=>id&&id!==entry.id);if(ids.length)proxy.setAttribute('aria-describedby',ids.join(' '));else proxy.removeAttribute('aria-describedby');});
    entry.originalErrors?.forEach(error=>error.remove());
    const tokens=(input.getAttribute('aria-describedby')||'').split(/\s+/).filter(token=>token&&token!==entry.id);
    if(tokens.length)input.setAttribute('aria-describedby',tokens.join(' '));else input.removeAttribute('aria-describedby');
    state.errors.delete(input);
    if(![...state.errors.keys()].some(other=>wrapper(other)===wrapper(input)))wrapper(input)?.classList.remove('km-editor-invalid','is-error');
    entry.item?.remove();if(!state.summary.querySelector('li,[data-km-error-note]'))state.summary.hidden=true;
    form.dispatchEvent(new Event('km:validation-change'));
  }
  function mark(form,input,messages,options={}) {
    if(!input)return null;const existing=states.get(form)?.errors.get(input);
    if(options.live&&existing){existing.node.textContent=messages.join(' ');existing.value=input.value;input.dataset.kmValidation='invalid';return existing;}
    clear(form,input);const state=states.get(form),row=wrapper(input),node=document.createElement('p');
    const id=`km-editor-error-${++nextId}`;node.id=id;node.className='km-editor-field-error';node.textContent=messages.join(' ');node.setAttribute('aria-live','polite');row?.append(node);
    row?.classList.add('km-editor-invalid');input.setAttribute('aria-invalid','true');
    input.setAttribute('aria-describedby',`${input.getAttribute('aria-describedby')||''} ${id}`.trim());
    const originalErrors=[...row?.querySelectorAll('.pw-error,.km-pf-field__error,.errorlist')||[]];originalErrors.forEach(error=>error.hidden=true);
    const proxies=[...row?.querySelectorAll('.select2-selection,.km-pf-picker-btn,.km-custom-select__trigger')||[]].filter(proxy=>proxy!==input);
    proxies.forEach(proxy=>{proxy.setAttribute('aria-invalid','true');proxy.setAttribute('aria-describedby',`${proxy.getAttribute('aria-describedby')||''} ${id}`.trim());});
    const entry={id,node,originalErrors,proxies,value:input.value};state.errors.set(input,entry);form.dispatchEvent(new Event('km:validation-change'));return entry;
  }
  function setErrors(form,errors,options={}) {
    mount(form);const state=states.get(form);state.submitted=true;for(const input of [...state.errors.keys()])clear(form,input);
    const summary=state.summary,notes=[...summary.querySelectorAll('[data-km-error-note]')].map(note=>note.cloneNode(true));summary.replaceChildren();const heading=document.createElement('strong');heading.textContent=text.title;summary.append(heading);const list=document.createElement('ul');summary.append(list);summary.append(...notes);
    for(const [name,raw]of Object.entries(errors))for(const [index,message]of(Array.isArray(raw)?raw:[raw]).entries()) {
      const path=options.paths?.[name]?.[index];
      const input=options.resolveTarget?.(name,index)||target(form,name,path),item=document.createElement('li'),button=document.createElement('button');
      const row=wrapper(input);
      const label=row?.querySelector('[data-pw-label]')?.textContent?.trim()||row?.querySelector('.owner-tariff-label,label,strong')?.textContent?.trim()||row?.querySelector(':scope > span')?.textContent?.trim()||input?.getAttribute('aria-label')||'';
      const fieldKey=Array.isArray(path)?path.at(-1):null;
      const translated=String(options.formatMessage?options.formatMessage(message):message);
      const display=typeof fieldKey==='string'&&label&&/^[a-z_]+$/.test(fieldKey)?translated.replaceAll(fieldKey,label):translated;
      button.type='button';button.textContent=`${label?label+': ':''}${display}`;button.addEventListener('click',()=>focus(input));if(input)item.append(button);else item.textContent=display;list.append(item);
      const existing=state.errors.get(input);if(existing){existing.node.textContent+=' '+display;}else{const entry=mark(form,input,[display]);if(entry)entry.item=item;}
    }
    summary.hidden=!list.children.length;
    if(!summary.hidden&&options.focus!==false){summary.focus({preventScroll:true});summary.scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});}
  }
  function phoneAllowed(input,value) {
    value=value.trim();
    if(!value)return true;
    if(input.name==='whatsapp_number'&&'https://wa.me/'.startsWith(value))return true;
    if(input.name==='whatsapp_number'&&value.startsWith('https://'))return /^https:\/\/wa\.me\/[0-9]*\/?$/.test(value);
    return /^\+?[0-9 ()-]*$/.test(value);
  }
  function validationName(input) {
    if(input?.dataset.kmValidationName)return input.dataset.kmValidationName;
    if(input?.matches('[data-public-link-key]'))return 'public_links';
    if(input?.matches('[data-tariff-key],[data-price-kind]'))return 'pricing_plans';
    if(input?.id==='id_age_from_range')return 'age_from';
    if(input?.id==='id_age_to_range')return 'age_to';
    return input?.name||'';
  }
  function nativeMessage(input) {
    if(!input||input.disabled||!input.validity)return '';
    if(input.matches('[data-km-phone]')&&!phoneAllowed(input,input.value))return text.phone;
    const validity=input.validity;
    // Required publication fields are authoritative on the server; partial drafts are allowed.
    if(validity.badInput||(!validity.valid&&!validity.valueMissing))return validity.tooLong?text.long:text.invalid;
    return '';
  }
  function meaningful(input) {
    if(input.type==='checkbox'||input.type==='radio')return input.checked;
    return typeof input.value==='string'&&input.value.trim()!==''&&input.value!=='[]'&&input.value!=='{}';
  }
  function entered(input) {
    if(input.tagName==='SELECT'){
      const initial=[...input.options].find(option=>option.defaultSelected)||input.options[0];
      return meaningful(input)&&input.value!==(initial?.value||'');
    }
    return meaningful(input);
  }
  function liveValidation(form,detail) {
    const state=states.get(form),values=detail?.values;
    if(!values||typeof values!=='object'||Array.isArray(values))return;
    const current=Object.fromEntries([...new FormData(form)].filter(([,value])=>typeof value==='string'));
    // Cross-field dependencies (country, price policy, category) invalidate stale answers too.
    for(const [name,value]of Object.entries(values)) {
      if(!form.elements.namedItem(name))continue;
      if(typeof value!=='string'||(current[name]??'')!==value)return;
    }
    const affected=new Map(),errors=detail.errors||{},paths=detail.error_targets||{};
    for(const [name,raw]of Object.entries(errors)) {
      if(!Object.hasOwn(values,name))continue;
      for(const [index,message]of(Array.isArray(raw)?raw:[raw]).entries()) {
        const input=target(form,name,paths[name]?.[index]);if(!input)continue;
        const messages=affected.get(input)||[];messages.push(String(message));affected.set(input,messages);
      }
    }
    const controls=[...form.querySelectorAll('input,select,textarea')];
    const activeGroups=new Set(controls.filter(input=>input.type!=='hidden'&&(state.touched.has(input)||meaningful(input))).map(validationName).filter(name=>['pricing_plans','public_links'].includes(name)));
    const candidates=new Set([...affected.keys(),...state.errors.keys(),...controls]);
    for(const input of candidates) {
      if(!form.contains(input)||input.disabled||input.type==='hidden')continue;
      const name=validationName(input);if(!Object.hasOwn(values,name))continue;
      const eligible=state.submitted||state.errors.has(input)||state.touched.has(input)||entered(input)||activeGroups.has(name);
      if(!eligible)continue;
      const local=nativeMessage(input),messages=affected.get(input)||(local?[local]:[]);
      if(messages.length){mark(form,input,messages,{live:true});input.dataset.kmValidation='invalid';}
      else {clear(form,input);input.dataset.kmValidation='checked';}
    }
  }
  function mountLiveValidation(form) {
    const state=states.get(form);
    const handle=(event,reason)=>{
      const input=event.target;
      if(!(input instanceof HTMLElement)||!input.matches('input,select,textarea')||input.type==='hidden'||input.disabled||event.isComposing)return;
      if(input.closest('[data-km-schedule-editor]')&&(reason==='blur'||event.isTrusted||entered(input))){
        const message=form.querySelector('[data-km-schedule-validation]'),mode=form.elements.namedItem('schedule_mode');
        if(message){if(input!==mode)state.touched.add(message);}else if(mode)state.touched.add(mode);
      }
      const name=validationName(input);if(!name)return;
      const wasInvalid=state.errors.has(input);
      if(reason!=='change'||entered(input)||state.touched.has(input)||document.activeElement===input)state.touched.add(input);
      if(reason==='blur')state.blurred.add(input);
      input.dataset.kmValidation='pending';
      const message=nativeMessage(input);
      if(message&&(reason!=='input'||state.blurred.has(input)||wasInvalid||input.type==='number')){
        mark(form,input,[message],{live:true});input.dataset.kmValidation='invalid';
      }
      if(reason!=='input')form.dispatchEvent(new CustomEvent('km:validation-request',{bubbles:true,detail:{field:name,reason}}));
    };
    form.addEventListener('input',event=>handle(event,'input'));
    form.addEventListener('change',event=>handle(event,'change'));
    form.addEventListener('focusout',event=>handle(event,'blur'));
    form.addEventListener('km:server-validation',event=>liveValidation(form,event.detail));
  }
  async function check(form) {
    const state=states.get(form);if(state.checking)return;
    if(form.photoEditor?.blocking()){setErrors(form,{gallery_images:[form.photoEditor.validationMessage()]});return;}
    const button=form.querySelector('[data-km-check]'),status=form.querySelector('[data-km-check-status]');
    const version=state.version,body=new FormData(form);body.set('_km_check_required','1');
    const url=form.querySelector('[data-km-preview]')?.formAction;if(!url)return;
    state.checking=true;button.disabled=true;status.hidden=false;status.textContent=checkCopy.busy;status.dataset.state='checking';
    try {
      const response=await fetch(url,{method:'POST',body,credentials:'same-origin',headers:{Accept:'application/json'},signal:AbortSignal.timeout(20000)});
      if(![200,422].includes(response.status))throw new Error('Check unavailable');const result=await response.json();
      if(state.version!==version){status.textContent=checkCopy.changed;status.dataset.state='changed';return;}
      if(result.readiness)form.dispatchEvent(new CustomEvent('km:readiness',{detail:result.readiness}));
      setErrors(form,result.errors||{},{paths:result.error_targets||{}});status.dataset.state=result.ok?'ready':'error';status.textContent=result.ok?checkCopy.ready:text.title;
    }catch{status.textContent=checkCopy.failed;status.dataset.state='error';}
    finally{state.checking=false;button.disabled=false;}
  }
  function mount(form) {
    if(states.has(form))return;
    let summary=form.querySelector('[data-km-errors],[data-pc-errors],[data-place-error-summary]');if(!summary){summary=document.createElement('div');form.prepend(summary);}
    summary.dataset.kmErrors='';summary.classList.add('km-editor-errors');summary.setAttribute('role','alert');summary.tabIndex=-1;summary.hidden=!summary.textContent.trim();
    states.set(form,{summary,errors:new Map(),version:0,touched:new WeakSet(),blurred:new WeakSet(),submitted:false});form.classList.add('km-editor');
    form.querySelectorAll('[data-public-links]').forEach(root=>{
      const input=root.querySelector('[data-public-links-input]'),list=root.querySelector('[data-public-links-list]'),add=root.querySelector('[data-public-links-add]');
      if(!input||!list||!add)return;let rows=[],writing=false;
      const sync=()=>{writing=true;input.value=JSON.stringify(rows);input.dispatchEvent(new Event('change',{bubbles:true}));writing=false;};
      const render=()=>{list.replaceChildren();rows.forEach((row,index)=>{
        const box=document.createElement('div');box.dataset.publicLinkRow='';box.className='km-public-links-row';
        ['label','url'].forEach(key=>{const label=document.createElement('label'),caption=document.createElement('span'),field=document.createElement('input');label.dataset.kmEditorField='public-link-'+key;caption.textContent=(key==='label'?root.dataset.linkName:root.dataset.linkUrl)+' '+(index+1);field.type=key==='url'?'url':'text';field.dataset.publicLinkKey=key;field.maxLength=key==='url'?500:80;field.value=row[key]||'';field.placeholder=key==='url'?'https://example.com/':'';field.addEventListener('input',()=>{row[key]=field.value;sync();});label.append(caption,field);box.append(label);});
        const remove=document.createElement('button');remove.type='button';remove.textContent=root.dataset.linkRemove;remove.setAttribute('aria-label',`${root.dataset.linkRemove} ${index+1}`);remove.addEventListener('click',()=>{rows.splice(index,1);render();sync();add.focus();});box.append(remove);list.append(box);
      });add.disabled=rows.length>=5;};
      const restore=()=>{if(writing)return;try{const parsed=JSON.parse(input.value||'[]');if(Array.isArray(parsed))rows=parsed.map(row=>({...row}));}catch{rows=[];}render();};
      input.addEventListener('change',restore);input.addEventListener('input',restore);add.addEventListener('click',()=>{if(rows.length>=5)return;rows.push({label:'',url:''});render();sync();list.lastElementChild?.querySelector('input')?.focus();});restore();
    });
    form.querySelector('[data-km-check]')?.addEventListener('click',()=>check(form));
    ['input','change','km:pricing-change','km:photos-change','km:schedule-change'].forEach(name=>form.addEventListener(name,()=>{const state=states.get(form);state.version++;const status=form.querySelector('[data-km-check-status]');if(status&&!state.checking){status.hidden=true;status.removeAttribute('data-state');}}));
    form.querySelectorAll('input[data-km-phone]').forEach(input=>{
      let previous=input.value,selection=[0,0],composing=false;
      const remember=()=>{previous=input.value;selection=[input.selectionStart,input.selectionEnd];};
      const rejected=()=>mark(form,input,[text.phone]);
      const proposal=data=>input.value.slice(0,input.selectionStart??input.value.length)+(data||'')+input.value.slice(input.selectionEnd??input.value.length);
      input.addEventListener('focus',remember);
      input.addEventListener('beforeinput',event=>{remember();if(event.isComposing||event.inputType?.startsWith('delete'))return;if(event.data!==null&&event.data!==undefined&&!phoneAllowed(input,proposal(event.data))){event.preventDefault();rejected();}});
      input.addEventListener('paste',event=>{remember();const value=event.clipboardData?.getData('text/plain')??event.clipboardData?.getData('text');if(value!==undefined&&!phoneAllowed(input,proposal(value))){event.preventDefault();rejected();}});
      input.addEventListener('compositionstart',()=>{remember();composing=true;});input.addEventListener('compositionend',()=>{composing=false;if(!phoneAllowed(input,input.value)){input.value=previous;input.setSelectionRange(...selection);rejected();}else remember();});
      input.addEventListener('input',event=>{if(composing)return;if(event.isTrusted&&!phoneAllowed(input,input.value)){input.value=previous;input.setSelectionRange(...selection);rejected();event.stopPropagation();}else remember();});
    });
    const languageGroups=new WeakSet();
    const mountLanguages=()=>form.querySelectorAll('[data-km-language-group]').forEach(group=>{
      if(languageGroups.has(group))return;languageGroups.add(group);
      const buttons=[...group.querySelectorAll('[data-km-language]')],panels=[...group.querySelectorAll('[data-km-language-panel]')];
      const select=language=>{buttons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.kmLanguage===language)));panels.forEach(panel=>panel.hidden=panel.dataset.kmLanguagePanel!==language);};
      buttons.forEach(button=>button.addEventListener('click',()=>select(button.dataset.kmLanguage)));select(buttons[0]?.dataset.kmLanguage);
    });mountLanguages();
    const countedInputs=new WeakSet();
    const counters=()=>form.querySelectorAll('input[type=text][maxlength],input:not([type])[maxlength],textarea').forEach(input=>{
      if(input.closest('[data-km-schedule-editor],[data-pw-field=structured_schedule]')||input.hidden||input.matches('[data-km-phone]'))return;
      if(countedInputs.has(input))return;countedInputs.add(input);
      const counter=document.createElement('small');counter.dataset.kmCounter='';counter.className='km-editor-counter';const id=`km-editor-counter-${++nextId}`;counter.id=id;wrapper(input)?.append(counter);
      input.setAttribute('aria-describedby',`${input.getAttribute('aria-describedby')||''} ${id}`.trim());
      const update=()=>{const count=Array.from(input.value).length,max=input.getAttribute('maxlength');counter.textContent=max?`${count} / ${max} ${text.chars}`:`${count} ${text.chars}`;counter.dataset.nearLimit=max&&count>=Number(max)*.9?'true':'false';};input.addEventListener('input',update);input.addEventListener('change',update);update();
    });
    counters();new MutationObserver(()=>{if(!window.document||!form.isConnected)return;counters();mountLanguages();}).observe(form,{childList:true,subtree:true});
    const clearChanged=input=>{const entry=states.get(form).errors.get(input);if(entry&&input.value!==entry.value)clear(form,input);};
    form.addEventListener('input',event=>{if(!event.isComposing&&(!event.target.matches('[data-km-phone]')||phoneAllowed(event.target,event.target.value)))clearChanged(event.target);});form.addEventListener('change',event=>clearChanged(event.target));
    mountLiveValidation(form);
    let initialErrors={};const originalErrors=[];
    try{const parsed=JSON.parse(document.getElementById('km-editor-errors')?.textContent||'{}');if(parsed&&typeof parsed==='object'&&!Array.isArray(parsed))initialErrors=parsed;}catch{}
    form.querySelectorAll('[data-pw-field],[data-pf-field]').forEach(row=>{const messages=[...row.querySelectorAll('.pw-error,.km-pf-field__error,.errorlist')].filter(error=>error.textContent.trim());if(messages.length){const name=row.dataset.pwField||row.dataset.pfField;if(!initialErrors[name])initialErrors[name]=messages.map(error=>error.textContent.trim());originalErrors.push(...messages);}});
    if(Object.keys(initialErrors).length){let paths={};try{paths=JSON.parse(document.getElementById('km-editor-error-targets')?.textContent||'{}');}catch{}setErrors(form,initialErrors,{focus:false,paths});originalErrors.forEach(error=>error.hidden=true);}
    document.addEventListener('submit',event=>{
      if(event.target!==form||event.defaultPrevented)return;const errors={},targets=new Map();
      if(event.submitter?.hasAttribute('data-km-preview')){
        if(form.photoEditor?.blocking()){event.preventDefault();event.stopImmediatePropagation();setErrors(form,{gallery_images:[form.photoEditor.validationMessage()]});form.dispatchEvent(new CustomEvent('km:submit-invalid',{bubbles:true,detail:{submitter:event.submitter,outcome:'pending'}}));return;}
        let language=form.querySelector('[name=_km_preview_language]');if(!language){language=document.createElement('input');language.type='hidden';language.name='_km_preview_language';form.append(language);}
        language.value=form.querySelector('[data-pc-preview-language],[data-pf-preview-language]')?.value||lang;
      }
      let index=0;
      for(const input of form.querySelectorAll('input,textarea,select')) {
        if(input.disabled||input.type==='hidden'||(!input.name&&!input.dataset.tariffKey&&!input.dataset.publicLinkKey))continue;
        const key=input.name||`tariff-${index++}-${input.dataset.tariffKey}`;targets.set(key,input);
        // Partial drafts and previews do not impose publication completeness.
        const validity=input.validity;
        if(validity&&!validity.valid&&!validity.valueMissing)errors[key]=[validity.tooLong?text.long:text.invalid];
        if(input.matches('[data-km-phone]')&&!phoneAllowed(input,input.value)&&input.value!==input.defaultValue)errors[key]=[text.phone];
      }
      if(Object.keys(errors).length){event.preventDefault();event.stopImmediatePropagation();setErrors(form,errors,{resolveTarget:key=>targets.get(key)});form.dispatchEvent(new CustomEvent('km:submit-invalid',{bubbles:true,detail:{submitter:event.submitter,outcome:'validation'}}));}
    },true);
  }
  window.KidsMapEditorUX={mount,setErrors,clear,focus,phoneAllowed,check};
  const init=()=>document.querySelectorAll('form[data-km-editor]').forEach(mount);
  if(document.readyState!=='complete')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
