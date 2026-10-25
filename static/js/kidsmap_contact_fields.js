/* Contact choices never rewrite or truncate user input. */
(() => {
  'use strict';
  function mount() {
    document.querySelectorAll('[data-km-phone-list]').forEach(group=>{
      if(group.dataset.kmPhonesBound)return;group.dataset.kmPhonesBound='1';
      const form=group.closest('form'),slots=[...group.querySelectorAll('[data-km-phone-slot]')],add=group.querySelector('[data-km-phone-add]');
      const update=()=>{if(add)add.disabled=slots.every(slot=>!slot.hidden);};
      const show=slot=>{slot.hidden=false;update();};
      slots.forEach(slot=>{const field=slot.querySelector('input');if(!field)return;
        slot.hidden=!field.value.trim()&&!slot.querySelector('.pw-error,.km-pf-field__error,.errorlist,.km-editor-field-error');
        field.addEventListener('change',()=>{if(field.value.trim())show(slot);});
        slot.querySelector('[data-km-phone-remove]')?.addEventListener('click',()=>{field.value='';field.dispatchEvent(new Event('input',{bubbles:true}));field.dispatchEvent(new Event('change',{bubbles:true}));slot.hidden=true;update();add?.focus();});
      });
      add?.addEventListener('click',()=>{const next=slots.find(slot=>slot.hidden);if(next){show(next);next.querySelector('input')?.focus();}});
      form?.addEventListener('km:reveal-field',event=>{const slot=event.detail?.element?.closest('[data-km-phone-slot]');if(slots.includes(slot))show(slot);});
      form?.addEventListener('km:validation-change',()=>{slots.filter(slot=>slot.querySelector('[aria-invalid=true]')).forEach(show);});
      update();
    });
    document.querySelectorAll('input[type="hidden"][name="phone_country"][data-km-local-default]').forEach(country => {
      country.form?.querySelectorAll('[name="phone1"],[name="phone2"],[name="phone3"],[name="whatsapp_number"]').forEach(field => {
        field.addEventListener('input', event => {
          const value = field.value.trim();
          // Explicit international codes are self-contained. Imported values and
          // untouched legacy contacts retain their existing parsing context.
          if (event.isTrusted && value && !/^(\+|00)/.test(value)) country.value = country.dataset.kmLocalDefault;
        });
      });
    });
    document.querySelectorAll('select[name="whatsapp_mode"]').forEach(mode => {
      if (mode.dataset.kmContactsBound === '1') return;
      const form = mode.form;
      const number = form?.elements.namedItem('whatsapp_number');
      if (!number) return;
      const wrapper = number.closest('[data-pw-field], [data-pf-field], .form-row');
      if (!wrapper) return;
      mode.dataset.kmContactsBound = '1';
      function update() {
        const hasError = Boolean(wrapper.querySelector('.pw-error, .km-pf-field__error, .errorlist, .km-editor-field-error'));
        wrapper.hidden = mode.value !== 'separate' && !hasError;
        number.setAttribute('aria-required', mode.value === 'separate' ? 'true' : 'false');
        // Keep the value enabled: switching modes must not discard saved contacts.
      }
      mode.addEventListener('change', update);
      // Django/Jazzmin Select2 emits jQuery changes without a native event.
      const jqueryInstances = new Set([window.jQuery, window.django?.jQuery].filter(jquery => typeof jquery === 'function'));
      jqueryInstances.forEach(jquery => jquery(mode).on('change.kmContactFields', update));
      form.addEventListener('reset', () => setTimeout(update, 0));
      form.addEventListener('km:validation-change', update);
      update();
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
