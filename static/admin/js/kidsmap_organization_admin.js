/* Organization admin: live "how parents will see it" preview, unsaved-changes
   hint on the sticky save bar, client-side image checks, and a guided jump to
   the publication decision. Server-side validation stays authoritative. */
(() => {
  'use strict';
  const form = document.getElementById('organization_form');
  if (!form) return;
  const $ = sel => document.querySelector(sel);
  const preview = $('[data-org-preview]');
  const nameOut = $('[data-org-preview-name]');
  const descOut = $('[data-org-preview-desc]');
  const logoOut = $('[data-org-preview-logo]');
  const coverOut = $('[data-org-preview-cover]');
  const lang = (document.documentElement.lang || 'ru').slice(0, 2);
  const T = {
    ru: { small: 'Слишком маленькое изображение: нужно от {w}×{h} px.', type: 'Нужен JPG, PNG или WebP.', big: 'Файл больше {mb} МБ.' },
    az: { small: 'Şəkil çox kiçikdir: ən azı {w}×{h} px.', type: 'JPG, PNG və ya WebP lazımdır.', big: 'Fayl {mb} MB-dan böyükdür.' },
    en: { small: 'Image too small: needs {w}×{h} px or more.', type: 'Use JPG, PNG or WebP.', big: 'File is larger than {mb} MB.' },
  }[lang] || {};
  const fmt = (s, v) => String(s).replace(/\{(\w+)\}/g, (_, k) => v[k]);
  const pulse = el => { if (!el) return; el.classList.remove('is-updated'); void el.offsetWidth; el.classList.add('is-updated'); };

  const bindText = (id, out, fallback, limit) => {
    const input = document.getElementById(id);
    if (!input || !out) return;
    input.addEventListener('input', () => {
      const value = input.value.trim();
      out.textContent = value ? (limit && value.length > limit ? value.slice(0, limit - 1) + '…' : value) : fallback;
      pulse(preview);
      if (id === 'id_name_az' && logoOut && !logoOut.querySelector('img')) {
        const mono = logoOut.querySelector('span');
        if (mono) mono.textContent = (value[0] || 'K').toUpperCase();
      }
    });
  };
  bindText('id_name_az', nameOut, '—');
  bindText('id_description_az', descOut, '', 150);

  const RULES = { id_logo: [5, 120, 120], id_cover_photo: [8, 800, 300] };
  const showError = (input, text) => {
    let box = input.parentElement.querySelector('.km-org-file-error');
    if (!box) { box = document.createElement('p'); box.className = 'km-org-file-error'; box.setAttribute('role', 'alert'); input.parentElement.appendChild(box); }
    box.textContent = text || '';
    box.hidden = !text;
  };
  Object.keys(RULES).forEach(id => {
    const input = document.getElementById(id);
    if (!input) return;
    input.addEventListener('change', () => {
      const file = input.files && input.files[0];
      showError(input, '');
      if (!file) return;
      const [mb, w, h] = RULES[id];
      if (!/^image\/(jpeg|png|webp)$/.test(file.type)) { input.value = ''; return showError(input, T.type); }
      if (file.size > mb * 1024 * 1024) { input.value = ''; return showError(input, fmt(T.big, { mb })); }
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        if (img.naturalWidth < w || img.naturalHeight < h) { input.value = ''; URL.revokeObjectURL(url); return showError(input, fmt(T.small, { w, h })); }
        if (id === 'id_logo' && logoOut) { logoOut.innerHTML = ''; img.alt = ''; logoOut.appendChild(img); }
        if (id === 'id_cover_photo' && coverOut) coverOut.style.backgroundImage = `url("${url}")`;
        pulse(preview);
      };
      img.onerror = () => { input.value = ''; showError(input, T.type); };
      img.src = url;
    });
  });

  // Unsaved changes hint + leave guard.
  const hint = $('[data-org-dirty-hint]');
  let dirty = false;
  form.addEventListener('input', event => {
    if (event.target.closest('.km-return-box')) return;
    if (!dirty) { dirty = true; if (hint) hint.classList.add('is-visible'); }
  });
  form.addEventListener('change', event => {
    if (event.target.type === 'file' && !dirty) { dirty = true; if (hint) hint.classList.add('is-visible'); }
  });
  form.addEventListener('submit', () => { dirty = false; form.classList.add('is-submitting'); });
  window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });

  // Jump to the decision block and make it obvious.
  document.querySelectorAll('a[href="#km-publication"]').forEach(link => link.addEventListener('click', event => {
    const target = document.getElementById('km-publication');
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    target.classList.remove('is-spotlight'); void target.offsetWidth; target.classList.add('is-spotlight');
  }));
})();
