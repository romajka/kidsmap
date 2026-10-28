/* Event-only editor. Backend-provided mappings select relevant controls. */
(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    var form = document.querySelector('[data-event-editor]');
    if (!form) return;
    var config = JSON.parse(document.getElementById('km-event-ui-config').textContent);
    var field = function (name) { return form.elements.namedItem(name); };
    var value = function (name) { return field(name) ? field(name).value : ''; };
    var state = form.querySelector('[data-event-save-state]');
    var physical = form.querySelector('[data-event-physical]');
    var type = form.querySelector('[data-event-organizer-type]');
    var initialLabel = state.textContent;
    var initialSnapshot = null;
    function snapshot() {
      return JSON.stringify(Array.from(form.elements).filter(function (input) { return input.name && input.name !== 'csrfmiddlewaretoken' && !['submit','button'].includes(input.type); }).map(function (input) { return [input.name, input.type === 'checkbox' ? input.checked : input.value]; }));
    }
    var venueFacts = null;
    var venueRequest = 0;
    function syncChoices(key, mappings) {
      var active = mappings[value(key)] || [];
      var names = new Set(Object.values(mappings).flat());
      names.forEach(function (name) {
        var input = field(name), row = form.querySelector('[data-event-field="' + name + '"]');
        var visible = name === 'price_text' || active.includes(name);
        if (row) row.hidden = !visible;
        if (input) input.disabled = !visible;
      });
    }
    function sync() {
      syncChoices('price_mode', config.priceFields);
      syncChoices('registration_method', config.registrationFields);
      var online = value('event_format') === 'online';
      physical.hidden = online;
      physical.querySelectorAll('input,select,textarea,button').forEach(function (input) { input.disabled = online; });
      form.querySelectorAll('[data-event-organizer]').forEach(function (row) {
        var active = row.dataset.eventOrganizer === type.value;
        row.hidden = !active;
        row.querySelectorAll('select').forEach(function (input) { input.disabled = !active; });
      });
      form.querySelector('[data-event-copy-phone]').hidden = value('registration_method') !== 'phone' || online;
    }
    function changed() { if (initialSnapshot !== null) state.textContent = snapshot() === initialSnapshot ? initialLabel : form.dataset.unsavedLabel + ' · ' + form.dataset.checkLabel; }
    form.addEventListener('input', function (event) { if (event.isTrusted) changed(); });
    form.addEventListener('change', function (event) { sync(); if (event.isTrusted) changed(); });
    type.addEventListener('change', function () {
      form.querySelectorAll('[data-event-organizer]').forEach(function (row) {
        if (row.dataset.eventOrganizer !== type.value) {
          row.querySelectorAll('select').forEach(function (select) { select.value = ''; });
        }
      });
      sync();
    });
    var customVenue = null;
    async function loadVenue() {
      var select = field('related_place');
      var id = ++venueRequest;
      venueFacts = null;
      if (!select.value) {
        if (customVenue) Object.entries(customVenue).forEach(function (entry) { var input = field(entry[0]); if (input) input.value = entry[1]; });
        field('address').readOnly = false;
        return;
      }
      if (value('event_format') === 'online') return;
      if (!customVenue) customVenue = Object.fromEntries(['address','region','district','metro','lat','lng'].map(function (name) { return [name, value(name)]; }));
      try {
        var response = await fetch(form.dataset.venueUrl + '?id=' + encodeURIComponent(select.value), {credentials: 'same-origin'});
        if (!response.ok) return;
        var facts = await response.json();
        if (id !== venueRequest) return;
        venueFacts = facts;
        field('address').readOnly = true;
        ['address','region','district','metro','lat','lng'].forEach(function (name) {
          var input = field(name);
          if (!input) return;
          {
            input.value = facts[name] || '';
            input.dispatchEvent(new Event('change', {bubbles: true}));
          }
        });
      } catch (_) { /* Manual address input remains available. */ }
    }
    field('related_place').addEventListener('change', loadVenue);
    if (window.django && django.jQuery) {
      django.jQuery(field('related_place')).on('change', loadVenue);
      django.jQuery(form).on('change', 'select', sync);
      django.jQuery(form).on('select2:select select2:clear', 'select', function () { sync(); changed(); });
    }
    form.querySelector('[data-event-copy-phone]').addEventListener('click', async function () {
      if (!venueFacts) await loadVenue();
      if (venueFacts && venueFacts.phone) {
        field('phone').value = venueFacts.phone;
        field('phone').dispatchEvent(new Event('input', {bubbles: true}));
        changed();
      } else form.querySelector('[data-event-venue-status]').textContent = form.dataset.phoneMissing;
    });
    form.addEventListener('click', function (event) {
      if (event.target.closest('[data-main-photo-clear]')) changed();
      var link = event.target.closest('a[href^="#id_"]');
      if (!link) return;
      var input = document.getElementById(link.getAttribute('href').slice(1));
      if (!input) return;
      for (var parent = input.parentElement; parent; parent = parent.parentElement) if (parent.tagName === 'DETAILS') parent.open = true;
      if (input.type === 'file') input = form.querySelector('[data-main-photo-pick]');
      if (input && input._flatpickr) input = input._flatpickr.altInput || input;
      if (input) { input.scrollIntoView({block: 'center'}); input.focus({preventScroll: true}); }
    });
    sync();
    initialSnapshot = snapshot();
    field('address').readOnly = !!value('related_place');
    if (form.querySelector('[data-event-errors]')) form.querySelector('[data-event-errors]').focus();

    window.addEventListener('keydown', function (event) {
      if ((event.ctrlKey || event.metaKey) && (event.key === 's' || event.key === 'S' || event.keyCode === 83)) {
        if (!event.altKey && !event.shiftKey) {
          event.preventDefault();
          var primaryBtn = form.querySelector('button[name="_continue"]');
          if (primaryBtn && !primaryBtn.disabled) {
            primaryBtn.click();
          }
        }
      }
    });
  });
})();
