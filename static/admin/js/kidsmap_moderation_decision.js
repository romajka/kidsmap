/* KidsMap — moderation queue: "На доработку" / "Отклонить" always with a reason.
 * Row buttons and the bulk bar open one dialog; it posts the matching admin
 * action with the selected ids and the reason (moderation_comment). */
(function () {
  'use strict';

  var DECISIONS = { return_for_revision: true, mark_rejected: true };

  function init() {
    var tpl = document.getElementById('km-decision-template');
    if (tpl && tpl.content && !document.getElementById('km-decision-dialog')) {
      document.body.appendChild(tpl.content.cloneNode(true));
    }
    var dialog = document.getElementById('km-decision-dialog');
    var copyNode = document.getElementById('km-decision-copy');
    if (!dialog || !copyNode || typeof dialog.showModal !== 'function') return;
    var copy;
    try { copy = JSON.parse(copyNode.textContent); } catch (e) { return; }

    var form = dialog.querySelector('form');
    var ids = dialog.querySelector('[data-km-decision-ids]');
    var title = dialog.querySelector('#km-decision-title');
    var target = dialog.querySelector('[data-km-decision-target]');
    var hint = dialog.querySelector('[data-km-decision-hint]');
    var edits = dialog.querySelector('[data-km-decision-edits]');
    var presets = dialog.querySelector('[data-km-decision-presets]');
    var reason = dialog.querySelector('textarea[name="moderation_comment"]');
    var error = dialog.querySelector('#km-decision-error');
    var submit = dialog.querySelector('[data-km-decision-submit]');
    var opener = null;

    function addPreset(text) {
      var current = reason.value.trim();
      if (current.indexOf(text) !== -1) return;
      reason.value = current ? current + '\n' + text : text;
      error.hidden = true;
      reason.removeAttribute('aria-invalid');
      reason.focus();
    }

    function open(mode, placeIds, label, isEdits, trigger) {
      var modeCopy = copy.modes[mode];
      if (!modeCopy || !placeIds.length) return;
      opener = trigger || null;
      form.elements.action.value = mode;
      ids.innerHTML = '';
      placeIds.forEach(function (id) {
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = '_selected_action';
        input.value = id;
        ids.appendChild(input);
      });
      dialog.dataset.mode = mode;
      title.textContent = modeCopy.title;
      submit.textContent = modeCopy.submit;
      hint.textContent = modeCopy.hint;
      target.textContent = label || (copy.selected + ': ' + placeIds.length);
      edits.hidden = !isEdits;
      presets.innerHTML = '';
      (copy.presets[mode] || []).forEach(function (preset) {
        var chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'km-decision-dialog__chip';
        chip.textContent = preset.label;
        chip.title = preset.text;
        chip.addEventListener('click', function () { addPreset(preset.text); });
        presets.appendChild(chip);
      });
      reason.value = '';
      error.hidden = true;
      reason.removeAttribute('aria-invalid');
      dialog.showModal();
      reason.focus();
    }

    function close() {
      dialog.close();
    }

    dialog.addEventListener('close', function () {
      if (opener && typeof opener.focus === 'function') opener.focus();
    });
    dialog.querySelectorAll('[data-km-decision-cancel]').forEach(function (btn) {
      btn.addEventListener('click', close);
    });
    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) close();
    });
    reason.addEventListener('input', function () {
      if (reason.value.trim()) {
        error.hidden = true;
        reason.removeAttribute('aria-invalid');
      }
    });
    form.addEventListener('submit', function (event) {
      if (!reason.value.trim()) {
        event.preventDefault();
        error.hidden = false;
        reason.setAttribute('aria-invalid', 'true');
        reason.focus();
        return;
      }
      submit.disabled = true;
      submit.setAttribute('aria-busy', 'true');
    });

    // Row buttons.
    document.addEventListener('click', function (event) {
      var btn = event.target.closest('[data-km-decide]');
      if (!btn) return;
      event.preventDefault();
      open(btn.dataset.kmDecide, [btn.dataset.placeId], btn.dataset.placeName, btn.dataset.edits === '1', btn);
    });

    // Bulk bar: intercept before the generic handler submits without a reason.
    document.addEventListener('click', function (event) {
      var btn = event.target.closest('[data-bulk-submit]');
      if (!btn || !DECISIONS[btn.dataset.bulkSubmit]) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      var checked = Array.prototype.map.call(
        document.querySelectorAll('#changelist-form tbody input.action-select:checked'),
        function (box) { return box.value; });
      open(btn.dataset.bulkSubmit, checked, '', false, btn);
    }, true);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
