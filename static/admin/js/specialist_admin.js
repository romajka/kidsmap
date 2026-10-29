/* KidsMap Specialist Admin Form Enhancement Script */
(function(){'use strict';
var page=document.querySelector('.km-specialist-form-page');if(!page)return;
var form=page.querySelector('form'),jump=page.querySelector('#specialist-section-jump'),status=page.querySelector('[data-specialist-save-status]');

function go(target){
  if(!target)return;
  target.scrollIntoView({behavior:'smooth',block:'start'});
  if(target.matches('section'))target=target.querySelector('h2')||target;
  if(target&&typeof target.focus==='function')target.focus({preventScroll:true});
}

// 1. Navigation items & Jump select
page.querySelectorAll('.km-nav-item').forEach(function(link){
  link.addEventListener('click',function(e){
    e.preventDefault();
    go(document.getElementById(link.dataset.section));
  });
});

if(jump)jump.addEventListener('change',function(){go(document.getElementById(jump.value));});

if('IntersectionObserver' in window){
  var observer=new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if(!entry.isIntersecting)return;
      page.querySelectorAll('.km-nav-item').forEach(function(a){
        var active=a.dataset.section===entry.target.id;
        a.classList.toggle('is-active',active);
        a.classList.toggle('km-nav-active',active);
        if(active)a.setAttribute('aria-current','location');
        else a.removeAttribute('aria-current');
      });
      if(jump)jump.value=entry.target.id;
    });
  },{rootMargin:'-80px 0px -70% 0px'});
  page.querySelectorAll('.km-specialist-section').forEach(function(s){observer.observe(s);});
}

var firstNav=page.querySelector('.km-nav-item');
if(firstNav&&!page.querySelector('.km-nav-item.is-active')){
  firstNav.classList.add('is-active','km-nav-active');
  firstNav.setAttribute('aria-current','location');
}

// 2. Error handling & focus jump
page.querySelectorAll('[data-specialist-errors] a').forEach(function(link){
  link.addEventListener('click',function(e){
    var target=document.getElementById(link.hash.slice(1));
    if(target){
      e.preventDefault();
      var details=target.closest('details');
      if(details)details.open=true;
      // If error is inside a hidden i18n pane, activate that tab!
      var pane=target.closest('[data-lang-pane]');
      if(pane&&pane.hasAttribute('hidden')){
        var group=pane.closest('[data-i18n-group]');
        if(group){
          var tab=group.querySelector('.km-spec-langtab[data-lang="'+pane.dataset.langPane+'"]');
          if(tab)tab.click();
        }
      }
      if(!target.matches('input,select,textarea,button,a[href]')){
        var control=Array.from(target.querySelectorAll('input:not([type=hidden]),select,textarea,button')).find(function(el){return !el.disabled&&el.getClientRects().length;});
        if(control)target=control;
        else target.setAttribute('tabindex','-1');
      }
      go(target);
    }
  });
});

page.querySelectorAll('.errorlist').forEach(function(errors,i){
  var wrapper=errors.closest('.km-field,.fieldBox,.form-row,.km-spec-pricing-item');
  if(!wrapper)return;
  errors.id=errors.id||'specialist-errors-'+i;
  wrapper.querySelectorAll('input:not([type=hidden]),select,textarea').forEach(function(field){
    field.setAttribute('aria-invalid','true');
    field.setAttribute('aria-describedby',errors.id);
  });
});

// 3. Multilingual Tab Switching (Bio & Education/Experience)
function initI18nGroup(group){
  var tabs=group.querySelectorAll('.km-spec-langtab');
  var panes=group.querySelectorAll('.km-spec-i18n-pane');

  function updateDots(){
    panes.forEach(function(pane){
      var lang=pane.dataset.langPane;
      var hasText=Array.from(pane.querySelectorAll('textarea,input')).some(function(inp){
        return inp.value&&inp.value.trim().length>0;
      });
      var dot=group.querySelector('.km-lang-dot[data-lang-dot$="'+lang+'"]');
      if(dot){
        dot.classList.toggle('is-filled',hasText);
      }
    });
  }

  tabs.forEach(function(tab){
    tab.addEventListener('click',function(){
      var lang=tab.dataset.lang;
      tabs.forEach(function(t){
        var active=t===tab;
        t.classList.toggle('is-active',active);
        t.setAttribute('aria-selected',active?'true':'false');
      });
      panes.forEach(function(pane){
        var match=pane.dataset.langPane===lang;
        pane.classList.toggle('is-hidden',!match);
        if(match)pane.removeAttribute('hidden');
        else pane.setAttribute('hidden','hidden');
      });
    });
  });

  group.addEventListener('input',updateDots);
  updateDots();
}
page.querySelectorAll('[data-i18n-group]').forEach(initI18nGroup);

// 4. Specializations custom dropdown, search, selection chips, and counter
var dropdown=page.querySelector('[data-spec-dropdown]');
var dropdownTrigger=page.querySelector('[data-dropdown-trigger]');
var dropdownPanel=page.querySelector('[data-dropdown-panel]');
var search=page.querySelector('[data-dropdown-search]');
var count=page.querySelector('[data-dropdown-found-pill]');
var clearAllBtn=page.querySelector('[data-dropdown-clear-all]');
var doneBtn=page.querySelector('[data-dropdown-done]');
var placeholder=page.querySelector('[data-dropdown-placeholder]');
var countBadge=page.querySelector('[data-dropdown-trigger-count]');
var tagsContainer=page.querySelector('[data-spec-selected-tags]');
var specOptions=Array.from(page.querySelectorAll('#id_specializations > div'));

function updateSpecTags(){
  if(!tagsContainer)return;
  tagsContainer.innerHTML='';
  var selectedCount=0;

  specOptions.forEach(function(row){
    var cb=row.querySelector('input[type=checkbox]');
    var lbl=row.querySelector('label')||row;
    if(!cb)return;
    if(cb.checked){
      selectedCount++;
      row.classList.add('is-checked');
      lbl.classList.add('is-selected');
      var chip=document.createElement('span');
      chip.className='km-spec-tag-chip';
      var textNode=document.createTextNode(lbl.textContent.trim()+' ');
      chip.appendChild(textNode);
      var removeBtn=document.createElement('button');
      removeBtn.type='button';
      removeBtn.className='km-spec-tag-remove';
      removeBtn.innerHTML='&times;';
      removeBtn.setAttribute('aria-label','Удалить '+lbl.textContent.trim());
      removeBtn.addEventListener('click',function(e){
        e.preventDefault();
        e.stopPropagation();
        cb.checked=false;
        row.classList.remove('is-checked');
        lbl.classList.remove('is-selected');
        updateSpecTags();
        filterSpecs();
        updateReadiness();
      });
      chip.appendChild(removeBtn);
      tagsContainer.appendChild(chip);
    } else {
      row.classList.remove('is-checked');
      lbl.classList.remove('is-selected');
    }
  });

  tagsContainer.style.display=selectedCount>0?'flex':'none';
  if(countBadge){
    countBadge.textContent=selectedCount;
    countBadge.hidden=selectedCount===0;
  }
  if(placeholder){
    if(selectedCount>0){
      placeholder.innerHTML='<strong>Выбрано направлений: '+selectedCount+'</strong> (нажмите, чтобы изменить)';
    } else {
      placeholder.textContent='Выберите направления (например: логопед, дефектолог)...';
    }
  }
  return selectedCount;
}

function filterSpecs(){
  var term=(search?search.value:'').toLocaleLowerCase().trim();
  var visible=0;
  specOptions.forEach(function(row){
    var cb=row.querySelector('input[type=checkbox]');
    if(!cb)return;
    var matches=!term||row.textContent.toLocaleLowerCase().includes(term);
    row.hidden=!matches;
    if(matches)visible++;
  });
  var selected=specOptions.filter(function(r){
    var c=r.querySelector('input[type=checkbox]');
    return c&&c.checked;
  }).length;
  if(count)count.textContent='Найдено '+visible+' · Выбрано '+selected;
}

if(dropdownTrigger&&dropdownPanel){
  dropdownTrigger.addEventListener('click',function(e){
    e.stopPropagation();
    var isOpen=!dropdownPanel.hidden;
    dropdownPanel.hidden=isOpen;
    dropdownTrigger.setAttribute('aria-expanded',!isOpen?'true':'false');
    dropdownTrigger.classList.toggle('is-open',!isOpen);
    if(dropdown)dropdown.classList.toggle('is-open',!isOpen);
    if(!isOpen&&search){
      setTimeout(function(){search.focus();},50);
    }
  });

  dropdownTrigger.addEventListener('keydown',function(e){
    if(e.key==='Enter'||e.key===' '){
      e.preventDefault();
      dropdownTrigger.click();
    }
  });

  document.addEventListener('click',function(e){
    if(dropdown&&!dropdown.contains(e.target)){
      dropdownPanel.hidden=true;
      dropdownTrigger.setAttribute('aria-expanded','false');
      dropdownTrigger.classList.remove('is-open');
      dropdown.classList.remove('is-open');
    }
  });

  if(doneBtn){
    doneBtn.addEventListener('click',function(e){
      e.stopPropagation();
      dropdownPanel.hidden=true;
      dropdownTrigger.setAttribute('aria-expanded','false');
      dropdownTrigger.classList.remove('is-open');
      if(dropdown)dropdown.classList.remove('is-open');
      dropdownTrigger.focus();
    });
  }

  if(clearAllBtn){
    clearAllBtn.addEventListener('click',function(e){
      e.stopPropagation();
      specOptions.forEach(function(row){
        var cb=row.querySelector('input[type=checkbox]');
        if(cb)cb.checked=false;
      });
      updateSpecTags();
      filterSpecs();
      updateReadiness();
    });
  }
}

if(search){
  search.addEventListener('input',filterSpecs);
}

form.addEventListener('change',function(e){
  if(e.target&&e.target.name==='specializations'){
    updateSpecTags();
    filterSpecs();
    updateReadiness();
  }
});
updateSpecTags();
filterSpecs();

// 5. Open-ended Age Checkbox
var ageFrom=form.querySelector('#id_age_from');
var ageTo=form.querySelector('#id_age_to');
var ageOpenEnded=page.querySelector('#spec_age_open_ended');
var ageToContainer=page.querySelector('#km-spec-age-to-container');

if(ageOpenEnded&&ageTo){
  function syncAgeOpenEnded(){
    if(ageOpenEnded.checked){
      ageTo.dataset.prevVal=ageTo.value;
      ageTo.value='';
      ageTo.disabled=true;
      if(ageToContainer)ageToContainer.classList.add('is-disabled');
    } else {
      ageTo.disabled=false;
      if(ageToContainer)ageToContainer.classList.remove('is-disabled');
      if(ageTo.dataset.prevVal)ageTo.value=ageTo.dataset.prevVal;
    }
  }

  // Initial check: if ageFrom has value but ageTo is empty, mark open-ended
  if(ageFrom&&ageFrom.value&&(!ageTo.value||ageTo.value==='0')){
    ageOpenEnded.checked=true;
    syncAgeOpenEnded();
  }

  ageOpenEnded.addEventListener('change',function(){
    syncAgeOpenEnded();
    updateReadiness();
  });
}

// 6. Consultation Format Cards
var formatSelect=form.querySelector('#id_consultation_format');
var formatCards=page.querySelectorAll('[data-format-cards] .km-spec-format-card');
var locationBanner=page.querySelector('[data-location-banner]');

function syncFormatCards(val){
  formatCards.forEach(function(card){
    var match=card.dataset.formatVal===val;
    card.classList.toggle('is-active',match);
  });
  if(locationBanner){
    if(val==='online'){
      locationBanner.classList.add('is-optional');
    } else {
      locationBanner.classList.remove('is-optional');
    }
  }
}

if(formatSelect){
  syncFormatCards(formatSelect.value);
  formatCards.forEach(function(card){
    card.addEventListener('click',function(){
      var val=card.dataset.formatVal;
      formatSelect.value=val;
      syncFormatCards(val);
      formatSelect.dispatchEvent(new Event('change',{bubbles:true}));
      updateReadiness();
    });
  });
  formatSelect.addEventListener('change',function(){
    syncFormatCards(formatSelect.value);
    updateReadiness();
  });
}

// 7. Contacts Sync: Phone to WhatsApp & Smart Same-Number Toggle
var syncWaBtn=page.querySelector('[data-sync-wa]');
var sameWaCheckbox=page.querySelector('#spec_wa_same_as_phone');
var phoneInput=form.querySelector('#id_phone');
var waInput=form.querySelector('#id_whatsapp');

function syncWaFromPhone(){
  if(!phoneInput||!waInput)return;
  var val=phoneInput.value.trim();
  if(val){
    waInput.value=val;
    updateReadiness();
  }
}

if(sameWaCheckbox&&phoneInput&&waInput){
  // Check initially if values match and are non-empty
  if(phoneInput.value.trim()&&phoneInput.value.trim()===waInput.value.trim()){
    sameWaCheckbox.checked=true;
    waInput.readOnly=true;
    waInput.classList.add('is-synced-readonly');
  }

  sameWaCheckbox.addEventListener('change',function(){
    if(sameWaCheckbox.checked){
      syncWaFromPhone();
      waInput.readOnly=true;
      waInput.classList.add('is-synced-readonly');
    } else {
      waInput.readOnly=false;
      waInput.classList.remove('is-synced-readonly');
      waInput.focus();
    }
  });

  phoneInput.addEventListener('input',function(){
    if(sameWaCheckbox.checked){
      syncWaFromPhone();
    }
  });
}

if(syncWaBtn&&phoneInput&&waInput){
  syncWaBtn.addEventListener('click',function(e){
    e.preventDefault();
    if(phoneInput.value.trim()){
      waInput.value=phoneInput.value.trim();
      waInput.focus();
      syncWaBtn.classList.add('is-synced');
      setTimeout(function(){syncWaBtn.classList.remove('is-synced');},1500);
      updateReadiness();
    } else {
      phoneInput.focus();
    }
  });
}

// 8. Photo Interactive Dropzone & Instant Preview
var dropzone=page.querySelector('#spec_avatar_dropzone');
var photoInput=form.querySelector('#id_photo');
var avatarPreview=page.querySelector('[data-spec-avatar-preview]');
var deletePhotoBtn=page.querySelector('#spec_btn_delete_photo');
var avatarCtaTitle=page.querySelector('#spec_avatar_cta_title');
var objectUrl;

function showPhotoPreview(url){
  if(!avatarPreview)return;
  avatarPreview.innerHTML='';
  var img=document.createElement('img');
  img.id='spec_avatar_preview_img';
  img.className='km-spec-preview-img';
  img.src=url;
  avatarPreview.appendChild(img);
  if(dropzone)dropzone.classList.add('has-photo');
  if(avatarCtaTitle)avatarCtaTitle.innerHTML='<strong>Фото выбрано</strong>';
}

function clearPhotoPreview(){
  if(!avatarPreview)return;
  avatarPreview.innerHTML='<div class="km-spec-avatar-placeholder" id="spec_avatar_placeholder"><i class="fas fa-user-md" aria-hidden="true"></i><span>Нет фото</span></div>';
  if(dropzone)dropzone.classList.remove('has-photo');
  if(avatarCtaTitle)avatarCtaTitle.innerHTML='<strong>Нажмите или перетащите фото</strong>';
}

if(dropzone&&photoInput){
  // Click anywhere on dropzone to trigger file input
  dropzone.addEventListener('click',function(e){
    if(e.target.closest('#spec_btn_delete_photo')||e.target.closest('[data-avatar-delete]'))return;
    photoInput.click();
  });

  dropzone.addEventListener('keydown',function(e){
    if((e.key==='Enter'||e.key===' ')&&!e.target.closest('#spec_btn_delete_photo')){
      e.preventDefault();
      photoInput.click();
    }
  });

  // Drag and drop handlers
  dropzone.addEventListener('dragover',function(e){
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add('is-dragover');
  });

  dropzone.addEventListener('dragleave',function(e){
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('is-dragover');
  });

  dropzone.addEventListener('drop',function(e){
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('is-dragover');
    if(e.dataTransfer&&e.dataTransfer.files&&e.dataTransfer.files.length){
      var file=e.dataTransfer.files[0];
      if(file.type.startsWith('image/')){
        photoInput.files=e.dataTransfer.files;
        if(objectUrl)URL.revokeObjectURL(objectUrl);
        objectUrl=URL.createObjectURL(file);
        showPhotoPreview(objectUrl);
        updateReadiness();
      }
    }
  });

  photoInput.addEventListener('change',function(){
    if(objectUrl)URL.revokeObjectURL(objectUrl);
    var file=photoInput.files&&photoInput.files[0];
    if(file&&file.type.startsWith('image/')){
      objectUrl=URL.createObjectURL(file);
      showPhotoPreview(objectUrl);
    }
    updateReadiness();
  });

  if(deletePhotoBtn){
    deletePhotoBtn.addEventListener('click',function(e){
      e.preventDefault();
      e.stopPropagation();
      var clearCb=form.querySelector('#photo-clear_id');
      if(clearCb)clearCb.checked=true;
      photoInput.value='';
      clearPhotoPreview();
      updateReadiness();
    });
  }
}

// 9. Real-time Readiness Score & Checklist
var readinessBar=page.querySelector('[data-spec-readiness]');
var readinessPct=page.querySelector('[data-readiness-pct]');
var readinessFill=page.querySelector('[data-readiness-fill]');
var readinessSummary=page.querySelector('[data-readiness-summary]');
var readinessMissing=page.querySelector('[data-readiness-missing]');

function updateReadiness(){
  if(!readinessBar)return;

  var nameVal=(form.querySelector('#id_name')?form.querySelector('#id_name').value:'').trim();
  var hasName=nameVal.length>0;

  var checkedSpecs=form.querySelectorAll('#id_specializations input[type=checkbox]:checked').length;
  var hasSpecs=checkedSpecs>0;

  var hasFormat=Boolean(formatSelect&&formatSelect.value);

  var langAz=form.querySelector('#id_language_az');
  var langRu=form.querySelector('#id_language_ru');
  var langEn=form.querySelector('#id_language_en');
  var hasLang=(langAz&&langAz.checked)||(langRu&&langRu.checked)||(langEn&&langEn.checked);

  var phoneVal=(phoneInput?phoneInput.value:'').trim();
  var waVal=(waInput?waInput.value:'').trim();
  var hasContact=phoneVal.length>0||waVal.length>0;

  var bioRu=(form.querySelector('#id_bio_ru')?form.querySelector('#id_bio_ru').value:'').trim();
  var bioAz=(form.querySelector('#id_bio_az')?form.querySelector('#id_bio_az').value:'').trim();
  var bioEn=(form.querySelector('#id_bio_en')?form.querySelector('#id_bio_en').value:'').trim();
  var hasBio=bioRu.length>0||bioAz.length>0||bioEn.length>0;

  var rules=[
    {id:'name',label:'Имя и фамилия',section:'#km-sec-1',done:hasName},
    {id:'specializations',label:'Специализация',section:'#km-sec-3',done:hasSpecs},
    {id:'format',label:'Формат приёма',section:'#km-sec-6',done:hasFormat},
    {id:'languages',label:'Язык консультации',section:'#km-sec-5',done:hasLang},
    {id:'contacts',label:'Телефон или WhatsApp',section:'#km-sec-11',done:hasContact},
    {id:'bio',label:'Описание о себе',section:'#km-sec-2',done:hasBio}
  ];

  var completed=rules.filter(function(r){return r.done;}).length;
  var total=rules.length;
  var pct=Math.round((completed/total)*100);

  if(readinessPct)readinessPct.textContent=pct+'%';
  if(readinessFill)readinessFill.style.width=pct+'%';
  if(readinessSummary)readinessSummary.textContent='Заполнено '+completed+' из '+total+' обязательных пунктов';

  // Nav checkmarks
  page.querySelectorAll('.km-nav-check').forEach(function(check){
    var secId=check.dataset.navCheck;
    var isDone=false;
    if(secId==='km-sec-1')isDone=hasName;
    else if(secId==='km-sec-2')isDone=hasBio;
    else if(secId==='km-sec-3')isDone=hasSpecs;
    else if(secId==='km-sec-5')isDone=hasLang;
    else if(secId==='km-sec-6')isDone=hasFormat;
    else if(secId==='km-sec-11')isDone=hasContact;
    check.classList.toggle('is-done',isDone);
  });

  if(readinessMissing){
    readinessMissing.innerHTML='';
    var missing=rules.filter(function(r){return !r.done;});
    if(missing.length===0){
      readinessMissing.innerHTML='<span class="km-readiness-all-done"><i class="fas fa-check-circle"></i> Все обязательные пункты заполнены! Анкета готова.</span>';
    } else {
      var prefix=document.createElement('span');
      prefix.className='km-missing-label';
      prefix.textContent='Не заполнено: ';
      readinessMissing.appendChild(prefix);
      missing.forEach(function(m){
        var pill=document.createElement('a');
        pill.href=m.section;
        pill.className='km-missing-item-link';
        pill.textContent=m.label;
        pill.addEventListener('click',function(e){
          e.preventDefault();
          go(document.querySelector(m.section));
        });
        readinessMissing.appendChild(pill);
      });
    }
  }
}

form.addEventListener('input',updateReadiness);
form.addEventListener('change',updateReadiness);
updateReadiness();

// 10. Form dirty state & submit status
if(form.dataset.hasErrors==='true'&&status)status.textContent=status.dataset.error;
['input','change'].forEach(function(type){
  form.addEventListener(type,function(){
    if(status)status.textContent=status.dataset.dirty;
  });
});
form.addEventListener('submit',function(){if(status)status.textContent=status.dataset.saving;});

var doc=page.querySelector('#documents-group-wrapper');
if(doc)doc.addEventListener('focusin',function(){
  var target=document.activeElement;
  if(doc.contains(target))target.scrollIntoView({block:'nearest',inline:'nearest'});
});
})();
