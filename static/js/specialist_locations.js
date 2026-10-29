(function(){'use strict';
var form=document.querySelector('.km-specialist-owner-form');if(!form)return;
var editor=form.querySelector('[data-practice-editor]');if(!editor)return;
var rows=editor.querySelector('[data-practice-rows]'),total=editor.querySelector('[name="locations-TOTAL_FORMS"]'),tpl=editor.querySelector('template'),add=editor.querySelector('[data-practice-add]');
function number(){rows.querySelectorAll('[data-practice-row]').forEach(function(row,i){row.querySelector('[data-practice-number]').textContent=i+1;var button=row.querySelector('[data-practice-remove]');button.setAttribute('aria-label',button.dataset.label+' '+(i+1));});}
function append(){var i=Number(total.value);if(i>=30){editor.querySelector('[data-practice-status]').textContent=editor.querySelector('[data-practice-status]').dataset.limit;return null;}var holder=document.createElement('div');holder.innerHTML=tpl.innerHTML.replace(/__prefix__/g,String(i));var row=holder.firstElementChild;rows.appendChild(row);total.value=i+1;number();return row;}
editor.appendRecoveryRow=append;
add.hidden=false;add.addEventListener('click',function(){var row=append();if(row){row.querySelector('[name$="-address"]').focus();form.dispatchEvent(new Event('input',{bubbles:true}));}});
editor.addEventListener('click',function(event){var button=event.target.closest('[data-practice-remove]');if(!button)return;var row=button.closest('[data-practice-row]');row.querySelector('[name$="-is_active"]').checked=false;row.querySelector('[name$="-is_primary"]').checked=false;var id=row.querySelector('[name$="-id"]');if(!id||!id.value){row.querySelector('[name$="-DELETE"]').checked=true;row.hidden=true;add.focus();}else{row.querySelector('[name$="-is_active"]').focus();}form.dispatchEvent(new Event('input',{bubbles:true}));});number();
})();
