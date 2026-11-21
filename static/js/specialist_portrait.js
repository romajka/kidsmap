(function () {
  'use strict';
  document.querySelectorAll('[data-portrait]').forEach(function (card) {
    const input = card.querySelector('input[type=file]');
    const clear = card.querySelector('[name="photo-clear"]');
    const preview = card.querySelector('[data-portrait-preview]');
    const savedUrl = preview.getAttribute('src');
    const filename = card.querySelector('[data-portrait-filename]');
    let previewUrl;
    function update() {
      const file = input.files[0];
      const saved = clear && clear.checked ? null : savedUrl;
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      previewUrl = file ? URL.createObjectURL(file) : null;
      const url = previewUrl || saved;
      preview.hidden = !url;
      if (url) preview.src = url;
      else preview.removeAttribute('src');
      filename.textContent = file ? file.name : '';
      card.querySelector('[data-portrait-choose]').hidden = Boolean(url);
      card.querySelector('[data-portrait-replace]').hidden = !url;
    }
    // Some browsers can upload HEIF but cannot show a local preview.
    preview.addEventListener('error', function () { preview.hidden = true; });
    input.addEventListener('change', function () {
      if (clear && input.files.length) clear.checked = false;
      update();
    });
    if (clear) clear.addEventListener('change', function () {
      if (clear.checked) input.value = '';
      update();
    });
    card.addEventListener('dragover', function (event) {
      event.preventDefault();
      card.classList.add('is-dragover');
    });
    card.addEventListener('dragleave', function () { card.classList.remove('is-dragover'); });
    card.addEventListener('drop', function (event) {
      event.preventDefault();
      card.classList.remove('is-dragover');
      if (event.dataTransfer.files.length === 1) {
        input.files = event.dataTransfer.files;
        input.dispatchEvent(new Event('change', {bubbles: true}));
      }
    });
    card.querySelector('.sp-portrait__action').hidden = false;
    card.classList.add('is-enhanced');
    update();
  });
})();
