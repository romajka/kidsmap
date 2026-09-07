(() => {
  'use strict';
  const config = document.querySelector('[data-phone-config]');
  if (!config) return;

  const language = (document.documentElement.lang || 'az').split('-')[0];
  const copy = {
    ru: {
      show: 'Показать номер',
      loading: 'Загрузка…',
      error: 'Не удалось показать номер. Нажмите, чтобы повторить.',
      limit: 'Слишком много запросов. Попробуйте через минуту.',
      call: 'Позвонить',
      copy: 'Скопировать',
      copied: 'Скопировано!'
    },
    en: {
      show: 'Show number',
      loading: 'Loading…',
      error: 'Could not show number. Press to retry.',
      limit: 'Too many requests. Try again in a minute.',
      call: 'Call',
      copy: 'Copy',
      copied: 'Copied!'
    },
    az: {
      show: 'Nömrəni göstər',
      loading: 'Yüklənir…',
      error: 'Nömrə göstərilmədi. Yenidən cəhd edin.',
      limit: 'Çox sayda sorğu. Bir dəqiqə sonra cəhd edin.',
      call: 'Zəng et',
      copy: 'Kopyala',
      copied: 'Kopyalandı!'
    },
  }[language] || {
    show: 'Show number',
    loading: 'Loading…',
    error: 'Could not show number. Press to retry.',
    limit: 'Try again in a minute.',
    call: 'Call',
    copy: 'Copy',
    copied: 'Copied!'
  };

  const phoneSvg = '<svg viewBox="0 0 24 24" fill="none"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const whatsappSvg = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.301-.15-1.78-.878-2.056-.979-.275-.1-.476-.15-.677.15-.201.3-.777.979-.953 1.18-.175.2-.351.225-.652.075-.301-.15-1.272-.469-2.424-1.496-.895-.798-1.5-1.784-1.675-2.085-.175-.3-.019-.462.132-.612.136-.135.301-.35.451-.526.151-.176.201-.301.301-.501.101-.2.051-.376-.025-.526-.075-.15-.677-1.632-.927-2.235-.244-.588-.492-.508-.677-.518-.175-.008-.376-.01-.577-.01-.201 0-.526.075-.802.376-.276.301-1.053 1.028-1.053 2.507 0 1.479 1.078 2.908 1.229 3.109.15.2 2.122 3.24 5.141 4.544.718.31 1.279.495 1.716.634.721.229 1.377.197 1.896.12.578-.087 1.78-.727 2.031-1.429.251-.702.251-1.304.176-1.43-.076-.125-.276-.201-.577-.351zM12.004 21.996a9.94 9.94 0 0 1-5.074-1.39l-.364-.216-3.77.989 1.006-3.676-.237-.377a9.947 9.947 0 0 1-1.528-5.328c0-5.518 4.488-10.007 10.007-10.007 2.673 0 5.187 1.042 7.078 2.934 1.89 1.89 2.932 4.404 2.93 7.077-.002 5.52-4.49 10.004-10.048 10.004zm7.042-17.08A9.907 9.907 0 0 0 12.004.004C5.39.004.01 5.385.008 12c-.001 2.112.551 4.174 1.599 5.992L0 24l6.177-1.62a11.936 11.936 0 0 0 5.823 1.503h.005c6.612 0 11.993-5.381 11.995-11.997 0-3.205-1.248-6.218-3.514-8.484z"/></svg>';
  const copySvg = '<svg class="km-icon-copy" viewBox="0 0 24 24" fill="none"><rect x="9" y="9" width="13" height="13" rx="2" stroke="currentColor" stroke-width="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" stroke-width="2"/></svg>';
  const checkSvg = '<svg class="km-icon-check" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const spinnerSvg = '<svg class="km-icon-spinner" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2.5" stroke-dasharray="36" stroke-linecap="round"/></svg>';

  const loaded = new Map(), pending = new Map();
  let errorSequence = 0;

  function formatPhone(raw) {
    if (!raw) return '';
    const trimmed = String(raw).trim();
    if (/\s|-|\(|\)/.test(trimmed)) return trimmed;
    // Standard Azerbaijan +994XXXXXXXXX (13 chars)
    if (trimmed.startsWith('+994') && trimmed.length === 13) {
      return `+994 ${trimmed.slice(4, 6)} ${trimmed.slice(6, 9)} ${trimmed.slice(9, 11)} ${trimmed.slice(11, 13)}`;
    }
    // 994XXXXXXXXX (12 chars)
    if (trimmed.startsWith('994') && trimmed.length === 12) {
      return `+994 ${trimmed.slice(3, 5)} ${trimmed.slice(5, 8)} ${trimmed.slice(8, 10)} ${trimmed.slice(10, 12)}`;
    }
    // 0XXXXXXXXX (10 chars)
    if (trimmed.startsWith('0') && trimmed.length === 10) {
      return `${trimmed.slice(0, 3)} ${trimmed.slice(3, 6)} ${trimmed.slice(6, 8)} ${trimmed.slice(8, 10)}`;
    }
    return trimmed;
  }

  async function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch (_) {}
    }
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      ta.style.top = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand('copy');
      ta.remove();
      return ok;
    } catch (_) {
      return false;
    }
  }

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
    const isCard = className.includes('card-contact-toggle');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = (className + ' km-phone-control' + (isCard ? ' km-phone-control--card' : '')).trim();
    button.dataset.phoneReveal = String(id);
    if (isCard) button.dataset.phoneCard = '1';
    const text = isCard ? copy.call : copy.show;
    button.setAttribute('aria-label', text);
    button.setAttribute('title', text);
    button.innerHTML = `<span class="km-phone-icon km-phone-icon--phone" aria-hidden="true">${phoneSvg}</span><span class="km-phone-label">${text}</span>`;
    return button.outerHTML;
  };

  function reveal(id, data) {
    document.querySelectorAll('[data-phone-reveal]').forEach(button => {
      if (button.dataset.phoneReveal !== id) return;
      const whatsapp = button.dataset.phoneWhatsapp === '1';
      const isCard = button.classList.contains('card-contact-toggle') || button.dataset.phoneCard === '1';
      const focused = document.activeElement === button;
      clearError(button);

      if (whatsapp) {
        const link = document.createElement('a');
        link.className = button.className;
        link.classList.add('km-phone-control--revealed', 'km-phone-whatsapp-revealed');
        link.href = data.whatsapp;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.setAttribute('aria-label', 'WhatsApp');
        link.dataset.trackEvent = 'cta_whatsapp';
        link.dataset.trackPlaceId = id;
        link.dataset.trackSource = 'phone-reveal';
        link.innerHTML = `
          <span class="km-phone-icon km-phone-icon--whatsapp" aria-hidden="true">${whatsappSvg}</span>
          <span class="km-phone-label">WhatsApp</span>
        `;
        button.replaceWith(link);
        if (focused) link.focus({preventScroll: true});
        return;
      }

      const phone = data.phones[Number(button.dataset.phoneIndex || 0)];
      if (!phone) return;
      const formatted = formatPhone(phone.number);

      // On compact catalog cards: do not blow up dimensions into split number/copy pill.
      // Render as a direct tel: link with the call icon (and label if space permits), keeping card dimensions unchanged.
      if (isCard) {
        const link = document.createElement('a');
        link.className = button.className;
        link.classList.add('km-phone-control--revealed');
        link.href = phone.href;
        link.setAttribute('aria-label', copy.call + ': ' + formatted);
        link.setAttribute('title', copy.call + ': ' + formatted);
        link.dataset.trackEvent = 'cta_call';
        link.dataset.trackPlaceId = id;
        link.dataset.trackSource = 'card-cta-call';
        link.innerHTML = `
          <span class="km-phone-icon km-phone-icon--phone" aria-hidden="true">${phoneSvg}</span>
          <span class="km-phone-label">${copy.call}</span>
        `;
        button.replaceWith(link);
        if (focused) link.focus({preventScroll: true});
        return;
      }

      if (button.classList.contains('detail-contacts__secondary-link')) {
        const wrap = document.createElement('div');
        wrap.className = button.className + ' km-phone-group km-phone-group--secondary km-phone-group--revealed';
        wrap.innerHTML = `
          <a class="km-phone-call-btn" href="${phone.href}" aria-label="${copy.call}: ${formatted}" data-track-event="cta_call" data-track-place-id="${id}" data-track-source="phone-reveal">
            <span class="km-phone-number">${formatted}</span>
          </a>
          <button type="button" class="km-phone-copy-btn" aria-label="${copy.copy}: ${formatted}" title="${copy.copy}" data-copy="${phone.number}">
            <span class="km-phone-copy-icon" aria-hidden="true">${copySvg}${checkSvg}</span>
            <span class="km-phone-copy-tooltip" role="status" aria-live="polite">${copy.copied}</span>
          </button>
        `;
        button.replaceWith(wrap);
        if (focused) wrap.querySelector('.km-phone-call-btn')?.focus({preventScroll: true});
        return;
      }

      if (button.classList.contains('detail-contacts__row')) {
        const wrap = document.createElement('div');
        wrap.className = button.className + ' km-phone-group km-phone-group--contacts km-phone-group--revealed';
        wrap.innerHTML = `
          <a class="km-phone-call-btn" href="${phone.href}" aria-label="${copy.call}: ${formatted}" data-track-event="cta_call" data-track-place-id="${id}" data-track-source="phone-reveal">
            <span class="detail-contacts__icon detail-contacts__icon--phone km-phone-icon" aria-hidden="true">
              ${phoneSvg}
            </span>
            <span class="detail-contacts__body">
              <span class="detail-label">${copy.call}</span>
              <strong class="km-phone-number">${formatted}</strong>
            </span>
          </a>
          <button type="button" class="km-phone-copy-btn" aria-label="${copy.copy}: ${formatted}" title="${copy.copy}" data-copy="${phone.number}">
            <span class="km-phone-copy-icon" aria-hidden="true">${copySvg}${checkSvg}</span>
            <span class="km-phone-copy-tooltip" role="status" aria-live="polite">${copy.copied}</span>
          </button>
        `;
        button.replaceWith(wrap);
        if (focused) wrap.querySelector('.km-phone-call-btn')?.focus({preventScroll: true});
        return;
      }

      // Main CTAs on Place page (Hero CTA, Mobile sticky bar)
      const wrap = document.createElement('div');
      wrap.className = button.className + ' km-phone-group km-phone-group--revealed';
      wrap.innerHTML = `
        <a class="km-phone-call-btn" href="${phone.href}" aria-label="${copy.call}: ${formatted}" data-track-event="cta_call" data-track-place-id="${id}" data-track-source="phone-reveal">
          <span class="km-phone-icon km-phone-icon--phone" aria-hidden="true">${phoneSvg}</span>
          <span class="km-phone-number">${formatted}</span>
        </a>
        <button type="button" class="km-phone-copy-btn" aria-label="${copy.copy}: ${formatted}" title="${copy.copy}" data-copy="${phone.number}">
          <span class="km-phone-copy-icon" aria-hidden="true">${copySvg}${checkSvg}</span>
          <span class="km-phone-copy-tooltip" role="status" aria-live="polite">${copy.copied}</span>
        </button>
      `;
      button.replaceWith(wrap);
      if (focused) wrap.querySelector('.km-phone-call-btn')?.focus({preventScroll: true});
    });
  }

  // Handle copy buttons
  document.addEventListener('click', async event => {
    const copyBtn = event.target.closest('.km-phone-copy-btn');
    if (copyBtn) {
      event.preventDefault();
      event.stopPropagation();
      const num = copyBtn.dataset.copy;
      if (!num) return;
      const ok = await copyToClipboard(num);
      if (ok) {
        copyBtn.classList.add('is-copied');
        clearTimeout(copyBtn._copyTimer);
        copyBtn._copyTimer = setTimeout(() => {
          copyBtn.classList.remove('is-copied');
        }, 2000);
      }
      return;
    }

    const button = event.target.closest('[data-phone-reveal]');
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    const id = button.dataset.phoneReveal;
    const isCard = button.classList.contains('card-contact-toggle') || button.dataset.phoneCard === '1';
    clearError(button);

    if (loaded.has(id)) {
      const data = loaded.get(id);
      reveal(id, data);
      if (isCard) {
        const phone = data.phones[Number(button.dataset.phoneIndex || 0)];
        if (phone && phone.href) {
          window.location.href = phone.href;
        }
      }
      return;
    }

    button.disabled = true;
    button.setAttribute('aria-busy', 'true');

    const labelSpan = button.querySelector('.km-phone-label');
    if (labelSpan) {
      labelSpan.textContent = copy.loading;
    } else {
      button.textContent = copy.loading;
    }

    const iconSpan = button.querySelector('.km-phone-icon');
    if (iconSpan) {
      iconSpan.innerHTML = spinnerSvg;
      iconSpan.classList.add('km-phone-icon--spinning');
    }

    try {
      if (!pending.has(id)) {
        const token = config.querySelector('[name=csrfmiddlewaretoken]').value;
        pending.set(id, (async () => {
          const response = await fetch(config.dataset.phoneEndpoint.replace('/0/', '/' + encodeURIComponent(id) + '/'), {
            method: 'POST',
            credentials: 'same-origin',
            cache: 'no-store',
            headers: {'X-CSRFToken': token, 'Accept': 'application/json'},
            signal: AbortSignal.timeout(15000),
          });
          if (!response.ok) throw new Error(response.status === 429 ? copy.limit : copy.error);
          const data = await response.json();
          if (!Array.isArray(data.phones) || !data.phones.length) throw new Error(copy.error);
          loaded.set(id, data);
          return data;
        })());
      }
      const data = await pending.get(id);
      reveal(id, data);
      if (isCard) {
        const phone = data.phones[Number(button.dataset.phoneIndex || 0)];
        if (phone && phone.href) {
          window.location.href = phone.href;
        }
      }
    } catch (error) {
      button.disabled = false;
      const defaultText = isCard ? copy.call : (button.dataset.phoneWhatsapp === '1' ? 'WhatsApp' : copy.show);
      const labelSpan = button.querySelector('.km-phone-label');
      if (labelSpan) {
        labelSpan.textContent = defaultText;
      } else {
        button.textContent = defaultText;
      }
      const iconSpan = button.querySelector('.km-phone-icon');
      if (iconSpan) {
        iconSpan.classList.remove('km-phone-icon--spinning');
        iconSpan.innerHTML = button.dataset.phoneWhatsapp === '1' ? whatsappSvg : phoneSvg;
      }

      const message = document.createElement('span');
      message.id = 'phone-error-' + (++errorSequence);
      message.className = 'km-phone-error';
      message.setAttribute('role', 'status');
      message.textContent = error.message === copy.limit ? copy.limit : copy.error;
      button.dataset.phoneError = message.id;
      button.setAttribute('aria-describedby', [button.getAttribute('aria-describedby'), message.id].filter(Boolean).join(' '));
      button.after(message);
    } finally {
      pending.delete(id);
      button.removeAttribute('aria-busy');
    }
  }, true);
})();
