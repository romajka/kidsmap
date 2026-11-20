(function () {
  'use strict';

  function releasePreview(image) {
    if (image.dataset.objectUrl) {
      URL.revokeObjectURL(image.dataset.objectUrl);
      delete image.dataset.objectUrl;
    }
  }

  function showFile(row, file) {
    const size = file.size;
    const divisor = size < 1024 ? 1 : size < 1048576 ? 1024 : 1048576;
    const unit = divisor === 1 ? 'byte' : divisor === 1024 ? 'kilobyte' : 'megabyte';
    const amount = new Intl.NumberFormat(document.documentElement.lang || undefined, {
      style: 'unit', unit, maximumFractionDigits: 1,
    }).format(size / divisor);
    const meta = row.querySelector('[data-qual-meta]');
    meta.textContent = file.name.split('.').pop().toUpperCase() + ' · ' + amount;
    meta.hidden = false;

    const image = row.querySelector('[data-qual-preview]');
    releasePreview(image);
    image.hidden = true;
    image.removeAttribute('src');
    if (!['image/jpeg', 'image/png'].includes(file.type) || !URL.createObjectURL) return;
    image.onload = () => { image.hidden = false; releasePreview(image); };
    image.onerror = () => { image.hidden = true; releasePreview(image); };
    image.dataset.objectUrl = URL.createObjectURL(file);
    image.src = image.dataset.objectUrl;
  }

  function enhance(editor) {
    const pickerBox = editor.querySelector('[data-qual-picker]');
    const picker = pickerBox.querySelector('input');
    const rows = editor.querySelector('[data-qual-rows]');
    const total = editor.querySelector('[name="qual-TOTAL_FORMS"]');
    const template = editor.querySelector('template');
    const message = editor.querySelector('[data-qual-message]');
    if (!total || typeof window.DataTransfer !== 'function') return;
    try {
      const probe = document.createElement('input');
      probe.type = 'file';
      probe.files = new DataTransfer().files;
    } catch (_) {
      return;
    }

    const limits = {
      files: Number(editor.dataset.maxFiles),
      single: Number(editor.dataset.maxBytes),
      batch: Number(editor.dataset.batchBytes),
    };
    const field = (row, suffix) => row.querySelector('[name$="-' + suffix + '"]');
    const getRows = () => Array.from(rows.querySelectorAll('[data-qual-row]'));
    function isOccupied(row) {
      return row.hasAttribute('data-saved') || row.hasAttribute('data-bound-row') ||
        Boolean(field(row, 'file')?.files.length);
    }
    function updateRow(row) {
      const saved = row.hasAttribute('data-saved');
      const checked = field(row, 'DELETE').checked;
      const file = field(row, 'file')?.files[0];
      row.hidden = !isOccupied(row);
      row.dataset.selected = file ? 'true' : 'false';
      row.querySelector('[data-qual-body]').hidden = checked;
      if (!saved && file) row.querySelector('[data-qual-heading]').textContent = file.name;
    }
    function makeRow(index) {
      const fragment = document.createElement('template');
      fragment.innerHTML = template.innerHTML.replaceAll('__prefix__', String(index));
      return fragment.content.firstElementChild;
    }
    function availableRow() {
      const empty = getRows().find(row => !isOccupied(row));
      if (empty) {
        field(empty, 'DELETE').checked = false;
        return empty;
      }
      const row = makeRow(Number(total.value));
      total.value = String(Number(total.value) + 1);
      rows.append(row);
      return row;
    }
    function activeRows() {
      return getRows().filter(row => isOccupied(row) && !field(row, 'DELETE').checked);
    }

    function selectedCount() {
      const label = editor.dataset.countLabel || editor.dataset.added;
      return label ? label + ': ' + activeRows().length + '.' : String(activeRows().length);
    }

    getRows().forEach(updateRow);
    pickerBox.hidden = false;
    const fallback = editor.querySelector('[data-qual-fallback]');
    if (fallback) fallback.hidden = true;

    picker.addEventListener('change', () => {
      const active = activeRows();
      let count = active.length;
      let bytes = active.reduce((sum, row) => sum + (field(row, 'file')?.files[0]?.size || 0), 0);
      let added = 0;
      const errors = [];
      for (const file of picker.files) {
        let error;
        if (!/\.(?:pdf|png|jpe?g)$/i.test(file.name)) error = editor.dataset.formatError;
        else if (!file.size || file.size > limits.single) error = editor.dataset.sizeError;
        else if (count >= limits.files) error = editor.dataset.countError;
        else if (bytes + file.size > limits.batch) error = editor.dataset.batchError;
        if (error) {
          errors.push(file.name + ' — ' + error + '.');
          continue;
        }

        const row = availableRow();
        const transfer = new DataTransfer();
        transfer.items.add(file);
        field(row, 'file').files = transfer.files;
        field(row, 'name').value = file.name.replace(/\.[^.]+$/, '').slice(0, 255);
        updateRow(row);
        showFile(row, file);
        bytes += file.size;
        added++;
        count++;
      }
      picker.value = '';
      message.dataset.error = String(errors.length > 0);
      message.textContent = [added ? selectedCount() : '', ...errors].filter(Boolean).join(' ');
    });

    rows.addEventListener('change', event => {
      const row = event.target.closest('[data-qual-row]');
      if (!row) return;
      const remove = field(row, 'DELETE');
      if (event.target === remove && remove.checked && !row.hasAttribute('data-saved')) {
        releasePreview(row.querySelector('[data-qual-preview]'));
        const index = Number(remove.name.split('-')[1]);
        const empty = makeRow(index);
        // Django counts submitted indexes towards the formset limit unless they are deleted.
        field(empty, 'DELETE').checked = true;
        row.replaceWith(empty);
        updateRow(empty);
        message.dataset.error = 'false';
        message.textContent = selectedCount();
        picker.focus();
      } else if (event.target === remove && !remove.checked && activeRows().length > limits.files) {
        remove.checked = true;
        message.dataset.error = 'true';
        message.textContent = editor.dataset.countError;
        updateRow(row);
      } else {
        updateRow(row);
        if (event.target === field(row, 'file') && event.target.files[0]) showFile(row, event.target.files[0]);
        if (event.target === remove) {
          message.dataset.error = 'false';
          message.textContent = selectedCount();
        }
      }
    });
  }

  const init = () => document.querySelectorAll('[data-qualification-editor]').forEach(enhance);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once: true});
  else init();
})();
