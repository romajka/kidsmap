(function () {
  'use strict';

  const button = document.querySelector('[data-copy-event-prompt]');
  if (!button) return;

  const text = document.getElementById('event-editor-prompt');
  const status = button.parentElement.querySelector('[role="status"]');
  button.addEventListener('click', async function () {
    try {
      await navigator.clipboard.writeText(text.value);
      status.textContent = button.dataset.success;
    } catch {
      text.focus();
      text.select();
      status.textContent = button.dataset.fallback;
    }
  });
})();
