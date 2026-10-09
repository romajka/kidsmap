/* Event's server checklist; live filling is an estimate, validation stays server-side. */
document.addEventListener('DOMContentLoaded', function () {
  var form = document.querySelector('[data-event-readiness]');
  var config = document.getElementById('km-admin-progress-config');
  if (!form || !config) return;
  var items = JSON.parse(config.textContent);
  var dirty = false;
  var serverReady = form.dataset.serverReady === 'true';
  function snapshot() {
    return JSON.stringify(Array.from(form.elements).filter(function (el) {
      return el.name && !el.name.startsWith('gallery-') && el.type !== 'submit' && el.type !== 'button' && el.name !== 'csrfmiddlewaretoken';
    }).map(function (el) {
      return [el.name, el.type === 'checkbox' ? el.checked : el.value];
    }));
  }
  var initialSnapshot = snapshot();
  function value(id) {
    var input = document.getElementById(id);
    return input ? String(input.value || '').trim() : '';
  }
  function filled(item) {
    if (item.input_ids) return item.input_ids.filter(function (id) { return !!value(id); }).length === 1;
    if (item.field_name === 'photo') {
      var file = document.getElementById(item.input_id);
      var clear = document.getElementById('id_photo-clear');
      return !!(file && file.files.length) || (!!item.stored_photo && !(clear && clear.checked));
    }
    return !!value(item.input_id);
  }
  function update() {
    var active = items.filter(function (item) { return !item.physical_only || value('id_event_format') !== 'online'; });
    var missing = active.filter(function (item) { return !filled(item); });
    var done = active.length - missing.length;
    var ready = !dirty && serverReady;
    var pct = Math.round(done / active.length * 100);
    if (!ready) pct = Math.min(pct, 99);
    form.querySelectorAll('[data-progress-total]').forEach(function (node) { node.textContent = active.length; });
    form.querySelectorAll('[data-progress-done]').forEach(function (node) { node.textContent = done; });
    form.querySelectorAll('[data-progress-pct]').forEach(function (node) { node.textContent = pct + '%'; });
    form.querySelectorAll('[data-progress-bar]').forEach(function (node) { node.style.width = pct + '%'; });
    form.querySelector('[data-progress-ring]').style.setProperty('--km-place-progress', pct);
    var badge = form.querySelector('[data-progress-readiness]');
    badge.textContent = ready ? form.dataset.progressCompleteLabel : (!dirty || missing.length ? form.dataset.progressIncompleteLabel : form.dataset.progressReviewLabel);
    badge.className = 'km-place-sidebar-badge km-place-sidebar-badge--' + (ready ? 'good' : 'warn');
    var list = form.querySelector('[data-progress-missing-list]');
    list.replaceChildren();
    missing.forEach(function (item) {
      var li = document.createElement('li');
      var link = document.createElement('a');
      link.href = '#' + item.input_id;
      link.className = 'km-place-sidebar-missing-link';
      link.textContent = item.label;
      li.appendChild(link); list.appendChild(li);
    });
    list.hidden = !missing.length;
    var empty = form.querySelector('[data-progress-empty]');
    empty.hidden = !!missing.length;
    empty.textContent = ready ? form.dataset.progressEmptyText : (dirty ? form.dataset.progressReviewLabel : form.dataset.progressIncompleteLabel);
    ['km-publish-btn', 'km-publish-mobile-btn'].forEach(function (id) {
      var button = document.getElementById(id);
      if (button) button.disabled = !!missing.length;
    });
    var errors = form.querySelector('[data-event-server-errors]');
    if (errors) errors.hidden = dirty;
  }
  function changed(event) {
    if (!event.target.matches('input, select, textarea')) return;
    dirty = snapshot() !== initialSnapshot; update();
  }
  form.addEventListener('input', changed);
  form.addEventListener('change', changed);
  if (window.django && django.jQuery) django.jQuery(form).on('change', 'select', changed);
  update();
});
