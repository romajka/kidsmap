(function(){'use strict';
var form=document.querySelector('.km-specialist-owner-form');if(!form)return;
var editor=form.querySelector('[data-practice-editor]');if(!editor)return;
var rows=editor.querySelector('[data-practice-rows]'),total=editor.querySelector('[name="locations-TOTAL_FORMS"]'),tpl=editor.querySelector('template'),add=editor.querySelector('[data-practice-add]');

function number(){
  rows.querySelectorAll('[data-practice-row]').forEach(function(row,i){
    row.querySelector('[data-practice-number]').textContent=i+1;
    var button=row.querySelector('[data-practice-remove]');
    if(button) button.setAttribute('aria-label',button.dataset.label+' '+(i+1));
  });
}

function syncCustomSelects(target){
  if(!target) return;
  target.querySelectorAll('.km-custom-select-wrap select').forEach(function(sel){
    function update(){
      var wrap=sel.closest('.km-custom-select-wrap');
      var hasVal=sel.value && sel.value !== '';
      if(wrap) wrap.classList.toggle('has-value', !!hasVal);
      sel.classList.toggle('is-selected', !!hasVal);
    }
    sel.addEventListener('change', update);
    sel.addEventListener('input', update);
    update();
  });
}

function initPracticeRow(row){
  if(!row || row.dataset.typeSelectorBound === '1') return;
  row.dataset.typeSelectorBound = '1';
  var selector = row.querySelector('[data-location-type-selector]');
  if(!selector) return;
  var btnPlace = selector.querySelector('[data-type-target="place"]');
  var btnCustom = selector.querySelector('[data-type-target="custom"]');
  var panelPlace = row.querySelector('[data-location-panel="place"]');
  var panelCustom = row.querySelector('[data-location-panel="custom"]');
  var placeInput = row.querySelector('[name$="-place"]');
  var addressInput = row.querySelector('[name$="-address"]');
  var latInput = row.querySelector('[name$="-lat"]');
  var lngInput = row.querySelector('[name$="-lng"]');

  function setMode(mode){
    if(mode === 'place'){
      if(btnPlace) { btnPlace.classList.add('is-active'); btnPlace.setAttribute('aria-checked', 'true'); }
      if(btnCustom) { btnCustom.classList.remove('is-active'); btnCustom.setAttribute('aria-checked', 'false'); }
      if(panelPlace) panelPlace.hidden = false;
      if(panelCustom) panelCustom.hidden = true;
    } else {
      if(btnCustom) { btnCustom.classList.add('is-active'); btnCustom.setAttribute('aria-checked', 'true'); }
      if(btnPlace) { btnPlace.classList.remove('is-active'); btnPlace.setAttribute('aria-checked', 'false'); }
      if(panelCustom) panelCustom.hidden = false;
      if(panelPlace) panelPlace.hidden = true;
      setTimeout(function(){
        if(typeof window.kidsMapRefreshOwnerMapPickers === 'function'){
          window.kidsMapRefreshOwnerMapPickers();
        }
      }, 60);
    }
  }

  var initialMode = 'place';
  if(placeInput && placeInput.value){
    initialMode = 'place';
  } else if((addressInput && addressInput.value) || (latInput && latInput.value && latInput.value !== '0')){
    initialMode = 'custom';
  }
  setMode(initialMode);

  if(btnPlace){
    btnPlace.addEventListener('click', function(){
      setMode('place');
      form.dispatchEvent(new Event('input', {bubbles: true}));
    });
  }
  if(btnCustom){
    btnCustom.addEventListener('click', function(){
      if(placeInput) placeInput.value = '';
      setMode('custom');
      form.dispatchEvent(new Event('input', {bubbles: true}));
    });
  }

  syncCustomSelects(row);
}

function initAllRows(){
  rows.querySelectorAll('[data-practice-row]').forEach(initPracticeRow);
  syncCustomSelects(rows);
  if(typeof window.kidsMapInitOwnerMapPickers === 'function'){
    window.kidsMapInitOwnerMapPickers();
  }
}

function append(){
  var i=Number(total.value);
  if(i>=30){
    editor.querySelector('[data-practice-status]').textContent=editor.querySelector('[data-practice-status]').dataset.limit;
    return null;
  }
  var holder=document.createElement('div');
  holder.innerHTML=tpl.innerHTML.replace(/__prefix__/g,String(i));
  var row=holder.firstElementChild;
  rows.appendChild(row);
  total.value=i+1;
  number();
  initPracticeRow(row);
  if(typeof window.kidsMapInitOwnerMapPickers === 'function'){
    window.kidsMapInitOwnerMapPickers();
  }
  return row;
}

editor.appendRecoveryRow=append;
add.hidden=false;
add.addEventListener('click',function(){
  var row=append();
  if(row){
    var targetInput = row.querySelector('[name$="-place"]') || row.querySelector('[name$="-address"]');
    if(targetInput) targetInput.focus();
    form.dispatchEvent(new Event('input',{bubbles:true}));
  }
});

editor.addEventListener('click',function(event){
  var button=event.target.closest('[data-practice-remove]');
  if(!button)return;
  var row=button.closest('[data-practice-row]');
  row.querySelector('[name$="-is_active"]').checked=false;
  row.querySelector('[name$="-is_primary"]').checked=false;
  var id=row.querySelector('[name$="-id"]');
  if(!id||!id.value){
    row.querySelector('[name$="-DELETE"]').checked=true;
    row.hidden=true;
    add.focus();
  }else{
    row.querySelector('[name$="-is_active"]').focus();
  }
  form.dispatchEvent(new Event('input',{bubbles:true}));
});

initAllRows();
number();
})();
