(function () {
  'use strict';
  const copyNode = document.getElementById('km-private-draft-copy');
  if (!copyNode) return;
  const copy = JSON.parse(copyNode.textContent);
  document.addEventListener('click', async function (event) {
    const button = event.target.closest('[data-draft-delete]');
    if (!button || button.disabled) return;
    event.preventDefault();
    const confirmed = window.kmModal && window.kmModal.confirm
      ? await window.kmModal.confirm({ title: copy.delete, message: copy.confirm, tone: 'danger', confirmText: copy.delete, cancelText: copy.cancel })
      : window.confirm(copy.confirm);
    if (!confirmed) return;
    button.disabled = true;
    const error = document.querySelector('[data-private-draft-error]');
    if (error) error.hidden = true;
    try {
      const token = document.querySelector('[data-private-draft-csrf] input[name=csrfmiddlewaretoken]');
      const response = await fetch(button.dataset.draftDelete, { method: 'DELETE', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token ? token.value : '' },
        body: JSON.stringify({ expected_version: Number(button.dataset.draftVersion) }) });
      const result = await response.json();
      if (!response.ok || result.status !== 'deleted') throw new Error('delete_failed');
      window.location.reload();
    } catch (_) {
      button.disabled = false;
      if (error) { error.textContent = copy.error; error.hidden = false; error.scrollIntoView({ block: 'nearest' }); }
      if (window.kmToast) window.kmToast.error(copy.error);
    }
  });
})();
