/* Mappy 3D: turns every [data-mappy3d] box into the live 3D bear once it is on screen and the page is idle.
   A still of the current bear ([data-mappy-fallback]) stays until the bear is ready, and stays for good
   without WebGL, on data-saver connections, or in boxes too small for 3D (data-min-size, default 90px). */
(() => {
  'use strict';
  const me = document.currentScript;
  const MODULE = me && me.dataset.module, MODEL = me && me.dataset.model;
  if (!MODULE || !MODEL || !('IntersectionObserver' in window)) return;
  const net = navigator.connection;
  if (net && (net.saveData || /(^|-)2g$/.test(net.effectiveType || ''))) return;
  const hasGL = () => { try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); } catch (_) { return false; } };
  const lang = (document.documentElement.lang || 'az').slice(0, 2);
  const sleepCopy = {
    ru: ['Маппи спит. Нажмите, чтобы разбудить.', 'Разбудить Маппи', 'Я проснулся! Поиграем?'],
    az: ['Mappy yatır. Oyatmaq üçün toxunun.', 'Mappini oyat', 'Oyandım! Oynayaq?'],
    en: ['Mappy is asleep. Tap to wake him.', 'Wake Mappy', 'I’m awake! Shall we play?'],
  }[lang] || ['Mappy is asleep. Tap to wake him.', 'Wake Mappy', 'I’m awake! Shall we play?'];
  const idle = (fn) => ('requestIdleCallback' in window ? requestIdleCallback(fn, { timeout: 2000 }) : setTimeout(fn, 600));
  const bleedOf = (v) => { const n = (v || '').trim().split(/\s+/).map(Number); return n.length === 4 && n.every(Number.isFinite) ? { top: n[0], right: n[1], bottom: n[2], left: n[3] } : undefined; };
  let lib = null;

  function mount(el) {
    if (el.dataset.mappy3dState) return;
    const box = el.getBoundingClientRect();
    if (box.width < (Number(el.dataset.minSize) || 90)) return;          // too small: keep the picture
    el.dataset.mappy3dState = 'loading';
    (lib ||= import(MODULE)).then(({ mountMappy }) => {
      const helper = el.closest('[data-mappy-helper]');
      const context = el.closest('[data-mappy-context]');
      const mappy = mountMappy(el, {
        src: MODEL, lang, mood: el.dataset.mappy3d || 'idle', bleed: bleedOf(el.dataset.bleed),
        label: el.dataset.label || 'Mappy', sleepAfter: context ? Infinity : (Number(el.dataset.sleep) || 45), bubble: !helper && !context,
      });
      el.mappy = mappy;
      mappy.on('ready', () => { el.dataset.mappy3dState = 'ready'; });
      mappy.on('error', () => { el.dataset.mappy3dState = 'error'; });
      if (helper) {
        // on the home page he speaks through the existing tip bubble
        const text = helper.querySelector('[data-mappy-text]'), content = helper.querySelector('[data-mappy-content]');
        const bubble = helper.querySelector('.mappy-bubble');
        const live = helper.querySelector('[data-mappy-live]');
        const awakeLabel = el.dataset.label || 'Mappy';
        const tipLabel = bubble?.getAttribute('aria-label');
        mappy.on('sleep', () => {
          helper.dataset.mappyState = 'sleeping';
          helper.dispatchEvent(new Event('mappy:sleep'));
          if (text) text.textContent = sleepCopy[0];
          if (live) live.textContent = '';
          el.setAttribute('aria-label', sleepCopy[1]);
          bubble?.setAttribute('aria-label', sleepCopy[1]);
        });
        mappy.on('wake', () => {
          delete helper.dataset.mappyState;
          helper.dispatchEvent(new Event('mappy:wake'));
          if (text) text.textContent = sleepCopy[2];
          if (live) live.textContent = sleepCopy[2];
          el.setAttribute('aria-label', awakeLabel);
          if (tipLabel) bubble?.setAttribute('aria-label', tipLabel);
        });
        mappy.on('say', (t) => {
          if (!text || !t || t.startsWith('Zzz')) return;
          helper.dispatchEvent(new Event('mappy:say'));
          // the same word-by-word entrance as the 3D speech cloud
          text.textContent = '';
          t.split(/(\s+)/).forEach((w, i) => {
            if (!w) return;
            if (/^\s+$/.test(w)) { text.appendChild(document.createTextNode(' ')); return; }
            const sp = document.createElement('span'); sp.className = 'mappy-say__w'; sp.style.setProperty('--i', String(i >> 1)); sp.textContent = w;
            text.appendChild(sp);
          });
          if (content) { content.classList.remove('mappy-react'); void content.offsetWidth; content.classList.add('mappy-react'); }
        });
        bubble?.addEventListener('click', () => {
          if (!mappy.ready) return;
          if (helper.dataset.mappyState === 'sleeping') mappy.touch('belly');
          else { mappy.play('earflick', 0.15); mappy.express('happy', 1.2); }
        });
      }
    }).catch(() => { el.dataset.mappy3dState = 'error'; });
  }

  function start() {
    const boxes = document.querySelectorAll('[data-mappy3d]');
    if (!boxes.length || !hasGL()) return;
    const io = new IntersectionObserver((entries) => entries.forEach((e) => {
      if (e.isIntersecting) { io.unobserve(e.target); idle(() => mount(e.target)); }
    }), { rootMargin: '200px 0px' });
    boxes.forEach((el) => {
      // The hero is already visible: do not wait for page idle before starting its model.
      if (el.closest('[data-mappy-helper]')) mount(el);
      else io.observe(el);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
