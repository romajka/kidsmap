/* Documents keep their original bytes; the server validates content and access. */
(function () {
  'use strict';
  function init() {
    document.querySelectorAll('[data-specialist-documents]').forEach(function (widget) {
      if (widget.dataset.initialized) return;
      widget.dataset.initialized = 'true';
      const input = widget.querySelector('input[type="file"]');
      const list = widget.querySelector('[data-document-files]');
      const status = widget.querySelector('[data-document-status]');
      const error = widget.querySelector('[data-document-error]');
      let selected = Array.from(input.files || []);
      const canEdit = typeof DataTransfer === 'function';
      function sync() {
        if (!canEdit) return;
        const transfer = new DataTransfer();
        selected.forEach(function (file) { transfer.items.add(file); });
        input.files = transfer.files;
      }
      function render() {
        list.replaceChildren();
        status.textContent = selected.length ? widget.dataset.selectedLabel + ' ' + selected.length : '';
        selected.forEach(function (file, index) {
          const row = document.createElement('li');
          const name = document.createElement('span');
          name.textContent = file.name;
          row.append(name);
          if (canEdit) {
            const remove = document.createElement('button');
            remove.type = 'button';
            remove.textContent = widget.dataset.removeLabel;
            remove.setAttribute('aria-label', widget.dataset.removeLabel + ': ' + file.name);
            remove.addEventListener('click', function () {
              selected.splice(index, 1); sync(); render(); input.focus();
              input.dispatchEvent(new Event('input', {bubbles: true}));
            });
            row.append(remove);
          }
          list.append(row);
        });
      }
      input.addEventListener('change', function () {
        const incoming = Array.from(input.files || []);
        if (!canEdit) { selected = incoming; render(); return; }
        const rejected = [];
        incoming.forEach(function (file) {
          if (!/\.(pdf|png|jpe?g)$/i.test(file.name) || file.size < 1 || file.size > 10 * 1024 * 1024) {
            rejected.push(file.name); return;
          }
          if (!selected.some(function (old) { return old.name === file.name && old.size === file.size && old.lastModified === file.lastModified; })) selected.push(file);
        });
        error.textContent = rejected.length ? widget.dataset.invalidLabel + ' ' + rejected.join(', ') : '';
        sync(); render();
      });
      render();
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
