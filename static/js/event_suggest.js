/* «Есть мероприятие?» — opens the request form in a dialog (bottom sheet on phones)
   and sends it without leaving the page. Links keep working without JS. */
(function () {
  'use strict';
  var dialog = document.querySelector('[data-event-suggest-dialog]');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function stamp(form) {
    var started = form.querySelector('[data-suggest-started]');
    if (started && !started.value) started.value = String(Math.floor(Date.now() / 1000));
  }

  function open(event) {
    if (!dialog || typeof dialog.showModal !== 'function') return; // plain link fallback
    event.preventDefault();
    var form = dialog.querySelector('[data-event-suggest-form]');
    var done = dialog.querySelector('[data-suggest-done]');
    form.hidden = false;
    done.hidden = true;
    stamp(form);
    dialog.showModal();
    dialog.classList.remove('is-closing');
    document.documentElement.classList.add('km-suggest-open');
    var first = form.querySelector('input[name="title"]');
    if (first && window.matchMedia('(pointer: fine)').matches) setTimeout(function () { first.focus(); }, 60);
  }

  function close() {
    if (!dialog || !dialog.open) return;
    if (reduce) { dialog.close(); return; }
    dialog.classList.add('is-closing');
    setTimeout(function () { dialog.classList.remove('is-closing'); dialog.close(); }, 220);
  }

  function showErrors(form, data) {
    form.querySelectorAll('.is-invalid').forEach(function (el) { el.classList.remove('is-invalid'); });
    var box = form.querySelector('[data-suggest-error]');
    var errors = (data && data.errors) || {};
    Object.keys(errors).forEach(function (name) {
      var input = form.elements.namedItem(name);
      if (input && input.closest) input.closest('.km-suggest__field').classList.add('is-invalid');
    });
    var text = (data && data.message) || (errors.__all__ && errors.__all__[0]) || box.dataset.fallback || '';
    if (!text && Object.keys(errors).length) text = box.dataset.checkFields || '';
    box.textContent = text;
    box.hidden = !text;
    if (!reduce) { form.classList.remove('is-shake'); void form.offsetWidth; form.classList.add('is-shake'); }
    var firstBad = form.querySelector('.is-invalid input, .is-invalid textarea');
    if (firstBad) firstBad.focus();
  }

  document.addEventListener('click', function (event) {
    var trigger = event.target.closest('[data-event-suggest]');
    if (trigger && !event.metaKey && !event.ctrlKey && !event.shiftKey) { open(event); return; }
    if (event.target.closest('[data-suggest-close]')) close();
    else if (dialog && event.target === dialog) close(); // backdrop
  });
  if (dialog) dialog.addEventListener('cancel', function (event) { event.preventDefault(); close(); });

  document.addEventListener('submit', function (event) {
    var form = event.target.closest('[data-event-suggest-form]');
    // Only the dialog sends in the background; the standalone page posts normally.
    if (!form || !window.fetch || !dialog || !dialog.contains(form)) return;
    event.preventDefault();
    stamp(form);
    var title = form.elements.namedItem('title');
    var name = form.elements.namedItem('name');
    var contact = form.elements.namedItem('contact');
    var email = form.elements.namedItem('email');
    var box = form.querySelector('[data-suggest-error]');
    box.dataset.checkFields = box.dataset.checkFields || (document.documentElement.lang === 'az' ? 'Sahələri yoxlayın.' : document.documentElement.lang === 'en' ? 'Please check the fields.' : 'Проверьте поля формы.');
    var local = {};
    if (!title.value.trim()) local.title = ['required'];
    if (!name.value.trim()) local.name = ['required'];
    if (!contact.value.trim() && !email.value.trim()) { local.contact = ['required']; local.email = ['required']; }
    if (Object.keys(local).length) { showErrors(form, { errors: local }); return; }

    var button = form.querySelector('[data-suggest-submit]');
    button.disabled = true;
    form.classList.add('is-sending');
    fetch(form.action, {
      method: 'POST', body: new FormData(form), credentials: 'same-origin',
      headers: { 'X-Requested-With': 'fetch', 'Accept': 'application/json' },
    }).then(function (response) {
      return response.json().catch(function () { return { ok: false }; });
    }).then(function (data) {
      if (!data.ok) { showErrors(form, data); return; }
      var done = dialog.querySelector('[data-suggest-done]');
      done.querySelector('[data-suggest-done-text]').textContent = data.message || '';
      form.hidden = true;
      done.hidden = false;
      form.reset();
      form.querySelector('[data-suggest-started]').value = '';
    }).catch(function () {
      // Network problem: keep what was typed and point to WhatsApp / e-mail below the form.
      showErrors(form, { message: form.dataset.offline || '' });
    }).then(function () {
      button.disabled = false;
      form.classList.remove('is-sending');
    });
  });

  // Standalone page: set the start stamp right away.
  document.querySelectorAll('[data-event-suggest-form]').forEach(function (form) {
    if (!dialog || !dialog.contains(form)) stamp(form);
  });
})();
