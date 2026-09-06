(() => {
  'use strict';
  const config = document.querySelector('[data-phone-config]');
  if (!config) return;
  const language = (document.documentElement.lang || 'az').split('-')[0];
  const copy = {
    ru: {show: 'Показать номер', loading: 'Загрузка…', error: 'Не удалось показать номер. Нажмите, чтобы повторить.', limit: 'Слишком много запросов. Попробуйте через минуту.', call: 'Позвонить'},
    en: {show: 'Show number', loading: 'Loading…', error: 'Could not show number. Press to retry.', limit: 'Too many requests. Try again in a minute.', call: 'Call'},
    az: {show: 'Nömrəni göstər', loading: 'Yüklənir…', error: 'Nömrə göstərilmədi. Yenidən cəhd edin.', limit: 'Çox sayda sorğu. Bir dəqiqə sonra cəhd edin.', call: 'Zəng et'},
  }[language] || {show: 'Show number', loading: 'Loading…', error: 'Could not show number. Press to retry.', limit: 'Try again in a minute.', call: 'Call'};
  const loaded = new Map(), pending = new Map();
  let errorSequence = 0;
  function clearError(button) {
    const errorId = button.dataset.phoneError;
    if (!errorId) return;
    document.getElementById(errorId)?.remove();
    const descriptions = (button.getAttribute('aria-describedby') || '').split(' ').filter(id => id && id !== errorId);
    if (descriptions.length) button.setAttribute('aria-describedby', descriptions.join(' '));
    else button.removeAttribute('aria-describedby');
    delete button.dataset.phoneError;
  }
  // Map popups use this factory too; only the ID is present in their payload.
  window.kidsMapPhoneButton = (id, className = '') => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = className + ' km-phone-control';
    button.dataset.phoneReveal = String(id); button.textContent = copy.show;
    return button.outerHTML;
  };
  function reveal(id, data) {
    document.querySelectorAll('[data-phone-reveal]').forEach(button => {
      if (button.dataset.phoneReveal !== id) return;
      const phone = data.phones[Number(button.dataset.phoneIndex || 0)];
      if (!phone) return;
      const link = document.createElement('a');
      const whatsapp = button.dataset.phoneWhatsapp === '1';
      link.className = button.className;
      link.classList.add('km-phone-control--revealed');
      link.href = whatsapp ? data.whatsapp : phone.href;
      link.textContent = whatsapp ? 'WhatsApp' : phone.number;
      link.setAttribute('aria-label', (whatsapp ? 'WhatsApp' : copy.call) + ': ' + phone.number);
      link.dataset.trackEvent = whatsapp ? 'cta_whatsapp' : 'cta_call';
      link.dataset.trackPlaceId = id; link.dataset.trackSource = 'phone-reveal';
      if (whatsapp) { link.target = '_blank'; link.rel = 'noopener noreferrer'; }
      const focused = document.activeElement === button;
      clearError(button);
      button.replaceWith(link);
      if (focused) link.focus({preventScroll: true});
    });
  }
  document.addEventListener('click', async event => {
    const button = event.target.closest('[data-phone-reveal]');
    if (!button) return;
    event.preventDefault(); event.stopPropagation();
    const id = button.dataset.phoneReveal;
    clearError(button);
    if (loaded.has(id)) { reveal(id, loaded.get(id)); return; }
    button.disabled = true; button.setAttribute('aria-busy', 'true');
    button.textContent = copy.loading;
    try {
      if (!pending.has(id)) {
        const token = config.querySelector('[name=csrfmiddlewaretoken]').value;
        pending.set(id, (async () => {
          const response = await fetch(config.dataset.phoneEndpoint.replace('/0/', '/' + encodeURIComponent(id) + '/'), {
            method: 'POST', credentials: 'same-origin', cache: 'no-store',
            headers: {'X-CSRFToken': token, 'Accept': 'application/json'},
            signal: AbortSignal.timeout(15000),
          });
          if (!response.ok) throw new Error(response.status === 429 ? copy.limit : copy.error);
          const data = await response.json();
          if (!Array.isArray(data.phones) || !data.phones.length) throw new Error(copy.error);
          loaded.set(id, data); return data;
        })());
      }
      reveal(id, await pending.get(id));
    } catch (error) {
      button.disabled = false; button.textContent = copy.show;
      const message = document.createElement('span');
      message.id = 'phone-error-' + (++errorSequence);
      message.className = 'km-phone-error';
      message.setAttribute('role', 'status');
      message.textContent = error.message === copy.limit ? copy.limit : copy.error;
      button.dataset.phoneError = message.id;
      button.setAttribute('aria-describedby', [button.getAttribute('aria-describedby'), message.id].filter(Boolean).join(' '));
      button.after(message);
    } finally {
      pending.delete(id); button.removeAttribute('aria-busy');
    }
  }, true);
})();
