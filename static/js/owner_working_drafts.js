(() => {
  'use strict';
  const language = (document.documentElement.lang || 'az').slice(0, 2);
  const text = (ru, az, en) => ({ru, az, en}[language] || az);
  document.addEventListener('click', async event => {
    const button = event.target.closest('[data-working-draft-delete]');
    if (!button || button.disabled || !window.kmModal?.confirm) return;
    event.preventDefault();
    const card = button.closest('[data-working-draft-id]');
    const error = card?.querySelector('[data-working-draft-error]');
    const confirmed = await window.kmModal.confirm({
      title: text('Удалить этот черновик?', 'Bu qaralama silinsin?', 'Discard this draft?'),
      message: text('Удалится только эта сохранённая копия и её новые фотографии. Опубликованное место останется без изменений.', 'Yalnız bu saxlanılmış nüsxə və onun yeni şəkilləri silinəcək. Dərc olunmuş məkan dəyişməyəcək.', 'Only this saved copy and its new photos will be deleted. The published place will stay unchanged.'),
      confirmText: text('Удалить черновик', 'Qaralamanı sil', 'Discard draft'),
      cancelText: text('Оставить', 'Saxla', 'Keep draft')
    });
    if (!confirmed || button.disabled) return;
    button.disabled = true;
    if (error) error.hidden = true;
    try {
      const response = await fetch(button.dataset.url, {
        method: 'DELETE', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''},
        body: JSON.stringify({expected_version: Number(button.dataset.version)})
      });
      if (!response.ok) throw Object.assign(new Error('discard'), {status: response.status});
      location.reload();
    } catch (failure) {
      if (error) {
        error.textContent = failure.status === 409
          ? text('Черновик изменился. Обновите страницу и проверьте его перед удалением.', 'Qaralama dəyişib. Səhifəni yeniləyin və silməzdən əvvəl yoxlayın.', 'The draft changed. Refresh and review it before deleting.')
          : text('Не удалось удалить черновик. Он сохранён — попробуйте ещё раз.', 'Qaralamanı silmək alınmadı. O saxlanılıb — yenidən cəhd edin.', 'Could not discard the draft. It is still saved — please try again.');
        error.hidden = false;
      }
      button.disabled = false;
    }
  });
})();
