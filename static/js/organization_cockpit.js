/* Organization cockpit: animated counters, media drop zones with client-side
   checks that mirror the server rules, and focus-friendly anchor jumps. The
   server remains the authority; nothing here bypasses validation. */
(() => {
  'use strict';
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const lang = (document.documentElement.lang || 'ru').slice(0, 2);
  const T = {
    ru: { big: 'Файл больше {mb} МБ.', type: 'Загрузите JPG, PNG или WebP.', small: 'Нужно от {w}×{h} px, у файла {fw}×{fh}.', ok: 'Готово к отправке: {name}', removed: 'Изображение будет удалено после проверки.', read: 'Не удалось прочитать изображение.' },
    az: { big: 'Fayl {mb} MB-dan böyükdür.', type: 'JPG, PNG və ya WebP yükləyin.', small: 'Ən azı {w}×{h} px lazımdır, faylda {fw}×{fh}.', ok: 'Göndərməyə hazırdır: {name}', removed: 'Şəkil yoxlamadan sonra silinəcək.', read: 'Şəkli oxumaq alınmadı.' },
    en: { big: 'File is larger than {mb} MB.', type: 'Upload a JPG, PNG or WebP.', small: 'Needs {w}×{h} px or more, file is {fw}×{fh}.', ok: 'Ready to submit: {name}', removed: 'The image will be removed after review.', read: 'Could not read the image.' },
  }[lang] || {};
  const fmt = (s, v) => String(s || '').replace(/\{(\w+)\}/g, (_, k) => (v[k] ?? ''));

  // Count-up numbers in the overview cards.
  const counters = document.querySelectorAll('[data-count-to]');
  if (!reduce && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      io.unobserve(entry.target);
      const el = entry.target;
      const end = Number(el.dataset.countTo) || 0;
      if (!end) return;
      const start = performance.now();
      const dur = Math.min(900, 300 + end * 12);
      const tick = now => {
        const k = Math.min(1, (now - start) / dur);
        el.textContent = Math.round(end * (1 - Math.pow(1 - k, 4)));
        if (k < 1) requestAnimationFrame(tick);
      };
      el.textContent = '0';
      requestAnimationFrame(tick);
    }), { threshold: 0.4 });
    counters.forEach(el => io.observe(el));
  }

  // Media drop zones.
  document.querySelectorAll('[data-org-drop]').forEach(zone => {
    const input = zone.querySelector('[data-org-drop-input]');
    const preview = zone.querySelector('[data-org-drop-preview]');
    const msg = zone.querySelector('[data-org-drop-msg]');
    const clear = zone.querySelector('[data-org-drop-clear]');
    if (!input || !preview) return;
    const original = preview.innerHTML;
    const say = (text, cls) => { if (msg) { msg.textContent = text || ''; msg.className = 'orgx-drop__msg' + (cls ? ' ' + cls : ''); } };
    const reject = text => {
      input.value = '';
      preview.innerHTML = original;
      zone.classList.remove('is-invalid'); void zone.offsetWidth; zone.classList.add('is-invalid');
      say(text, 'is-error');
    };
    const check = file => new Promise(resolve => {
      const maxMb = Number(input.dataset.maxMb) || 5;
      if (!/^image\/(jpeg|png|webp)$/.test(file.type)) return resolve(T.type);
      if (file.size > maxMb * 1024 * 1024) return resolve(fmt(T.big, { mb: maxMb }));
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        const w = Number(input.dataset.minW) || 0, h = Number(input.dataset.minH) || 0;
        if (img.naturalWidth < w || img.naturalHeight < h) {
          URL.revokeObjectURL(url);
          return resolve(fmt(T.small, { w, h, fw: img.naturalWidth, fh: img.naturalHeight }));
        }
        preview.innerHTML = '';
        img.alt = '';
        preview.appendChild(img);
        resolve('');
      };
      img.onerror = () => { URL.revokeObjectURL(url); resolve(T.read); };
      img.src = url;
    });
    input.addEventListener('change', async () => {
      const file = input.files && input.files[0];
      if (!file) { preview.innerHTML = original; say(''); return; }
      const problem = await check(file);
      if (problem) return reject(problem);
      if (clear) clear.checked = false;
      zone.classList.add('has-file');
      say(fmt(T.ok, { name: file.name }), 'is-ok');
    });
    ['dragenter', 'dragover'].forEach(type => zone.addEventListener(type, e => { e.preventDefault(); zone.classList.add('is-dragover'); }));
    ['dragleave', 'drop'].forEach(type => zone.addEventListener(type, () => zone.classList.remove('is-dragover')));
    zone.addEventListener('drop', e => {
      e.preventDefault();
      const files = e.dataTransfer && e.dataTransfer.files;
      if (!files || !files.length) return;
      try { input.files = files; } catch (_) { return; }
      input.dispatchEvent(new Event('change', { bubbles: true }));
    });
    if (clear) clear.addEventListener('change', () => {
      if (clear.checked) {
        input.value = '';
        preview.style.opacity = '0.35';
        say(T.removed, 'is-error');
      } else {
        preview.style.opacity = '';
        say('');
      }
    });
  });

  // Checklist / stepper anchors: open the right tab-panel, scroll and focus.
  document.addEventListener('click', event => {
    const link = event.target.closest('.orgx-checklist a, .orgx-step a, .orgx-metric, .orgx-submit-cta, .orgx-banner a');
    if (!link) return;
    const id = (link.getAttribute('href') || '').replace(/^#/, '');
    const target = id && document.getElementById(id);
    if (!target) return;
    const panel = target.closest('[data-org-panel]') || target;
    const tab = panel.id && document.querySelector(`[data-org-tab="${panel.id}"]`);
    if (tab) tab.click();
    event.preventDefault();
    requestAnimationFrame(() => {
      target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
      target.focus({ preventScroll: true });
      if (history.replaceState) history.replaceState(null, '', '#' + id);
    });
  });
})();
