/* Event page media: the photo carousel ("Fotoqalereya") and the full-screen viewer.
   No libraries: pointer events + Web Animations API. Without JS the poster and
   photos stay ordinary links to the original files. */
(() => {
  'use strict';
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  const EASE = 'cubic-bezier(.2,.8,.2,1)';

  /* ─── Viewer ─────────────────────────────────────────────── */
  const dialog = document.querySelector('[data-km-lb]');
  const viewer = dialog && typeof dialog.showModal === 'function' ? createViewer(dialog) : null;

  function createViewer(root) {
    const img = root.querySelector('[data-km-lb-img]');
    const bg = root.querySelector('[data-km-lb-bg]');
    const cap = root.querySelector('[data-km-lb-cap]');
    const count = root.querySelector('[data-km-lb-count]');
    const stage = root.querySelector('[data-km-lb-stage]');
    const closeBtn = root.querySelector('[data-km-lb-close]');
    const items = Array.from(root.querySelectorAll('.km-lb__items > li')).map(li => ({
      src: li.dataset.src, srcset: li.dataset.srcset, thumb: li.dataset.thumb, original: li.dataset.original,
      w: +li.dataset.w || 0, h: +li.dataset.h || 0, alt: li.dataset.alt || '', caption: li.innerHTML,
    }));
    let index = 0, opener = null, busy = false, sourceFor = () => null;
    root.classList.toggle('is-single', items.length < 2);

    // Where the photo will sit: contained in 92% × 80% of the screen, never blown up past 1.5×.
    function finalBox(item) {
      const vw = window.innerWidth, vh = window.innerHeight;
      const ratio = item.w && item.h ? item.w / item.h : (img.naturalWidth && img.naturalHeight ? img.naturalWidth / img.naturalHeight : 0.75);
      let w = vw * 0.92, h = w / ratio;
      if (h > vh * 0.8) { h = vh * 0.8; w = h * ratio; }
      if (item.w && w > item.w * 1.5) { w = item.w * 1.5; h = w / ratio; }
      return { left: (vw - w) / 2, top: (vh - h) / 2 - Math.min(24, vh * 0.03), width: w, height: h };
    }
    // The visible picture inside a source frame (contain or cover), as a screen rect.
    function sourceRect(el, item) {
      if (!el || !el.isConnected) return null;
      const pic = el.querySelector('.km-fit__img') || el.querySelector('img') || el;
      const r = pic.getBoundingClientRect();
      if (!r.width || !r.height || r.bottom < 0 || r.top > window.innerHeight || r.right < 0 || r.left > window.innerWidth) return null;
      const contained = getComputedStyle(pic).objectFit === 'contain';
      if (!contained || !item.w || !item.h) return r;
      const ratio = item.w / item.h;
      let w = r.width, h = w / ratio;
      if (h > r.height) { h = r.height; w = h * ratio; }
      return { left: r.left + (r.width - w) / 2, top: r.top + (r.height - h) / 2, width: w, height: h };
    }
    function place(box) {
      Object.assign(img.style, { left: box.left + 'px', top: box.top + 'px', width: box.width + 'px', height: box.height + 'px' });
    }
    function delta(from, to) {
      return `translate(${from.left - to.left}px, ${from.top - to.top}px) scale(${from.width / to.width}, ${from.height / to.height})`;
    }
    function show(i) {
      index = (i + items.length) % items.length;
      const item = items[index];
      img.alt = item.alt;
      img.removeAttribute('srcset');
      if (item.srcset) { img.srcset = item.srcset; img.sizes = '92vw'; }
      img.src = item.src || item.original;
      bg.style.backgroundImage = `url("${item.thumb || item.src}")`;
      cap.innerHTML = item.caption;
      count.textContent = `${index + 1} / ${items.length}`;
      place(finalBox(item));
      return item;
    }
    function open(i, from, getSource) {
      if (busy || !items.length) return;
      opener = from || document.activeElement;
      sourceFor = getSource || (() => from);
      const item = show(i);
      root.showModal();
      closeBtn.focus({ preventScroll: true });
      requestAnimationFrame(() => root.classList.add('is-open'));
      const src = sourceRect(sourceFor(index), item);
      if (src && !reduce.matches) {
        busy = true;
        img.animate([{ transform: delta(src, finalBox(item)), borderRadius: '14px' }, { transform: 'none' }],
          { duration: 420, easing: EASE }).finished.finally(() => { busy = false; });
      }
    }
    function close() {
      if (!root.open || busy) return;
      const item = items[index];
      const src = sourceRect(sourceFor(index), item);
      root.classList.remove('is-open');
      const done = () => { root.close(); img.style.transform = ''; busy = false; };
      if (src && !reduce.matches) {
        busy = true;
        img.animate([{ transform: 'none' }, { transform: delta(src, finalBox(item)) }],
          { duration: 320, easing: EASE, fill: 'forwards' }).finished.then(done, done);
      } else if (!reduce.matches) {
        busy = true;
        img.animate([{ opacity: 1 }, { opacity: 0, transform: 'scale(.96)' }], { duration: 200, fill: 'forwards' }).finished.then(done, done);
      } else done();
    }
    function step(dir) {
      if (busy || items.length < 2) return;
      if (reduce.matches) { show(index + dir); return; }
      busy = true;
      img.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: `translateX(${-40 * dir}px)` }],
        { duration: 150, easing: 'ease-in', fill: 'forwards' }).finished.then(() => {
          show(index + dir);
          const anim = img.animate([{ opacity: 0, transform: `translateX(${40 * dir}px)` }, { opacity: 1, transform: 'none' }],
            { duration: 240, easing: EASE });
          anim.finished.finally(() => { busy = false; });
        });
    }
    root.addEventListener('close', () => {
      img.getAnimations().forEach(a => a.cancel());
      img.removeAttribute('src'); img.removeAttribute('srcset');
      root.classList.remove('is-open');
      if (opener && opener.isConnected) opener.focus({ preventScroll: true });
    });
    root.addEventListener('cancel', e => { e.preventDefault(); close(); });   // Esc
    closeBtn.addEventListener('click', close);
    root.querySelector('[data-km-lb-prev]').addEventListener('click', () => step(-1));
    root.querySelector('[data-km-lb-next]').addEventListener('click', () => step(1));
    root.addEventListener('keydown', e => {
      if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
      if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
    });
    // Click on the darkened background closes; a swipe flips.
    let sx = 0, sy = 0, tracking = false;
    stage.addEventListener('pointerdown', e => { sx = e.clientX; sy = e.clientY; tracking = true; });
    stage.addEventListener('pointerup', e => {
      if (!tracking) return; tracking = false;
      const dx = e.clientX - sx, dy = e.clientY - sy;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) { step(dx < 0 ? 1 : -1); return; }
      if (Math.abs(dx) < 8 && Math.abs(dy) < 8 && e.target !== img) close();
    });
    stage.addEventListener('pointercancel', () => { tracking = false; });
    window.addEventListener('resize', () => { if (root.open && !busy) place(finalBox(items[index])); });
    return { open, count: items.length };
  }

  const lbIndex = el => parseInt(el.getAttribute('data-km-lb-open'), 10) || 0;
  // The frame a photo flies from / back to. A carousel photo is first brought
  // to the middle (no animation), so closing the viewer lands it in its card.
  const sourceByIndex = i => {
    const el = document.querySelector(`[data-km-lb-open="${i}"]`);
    const car = el && el.closest('[data-km-car]');
    if (car && car.kmGoTo) car.kmGoTo(el.closest('[data-km-car-item]'), true);
    return el;
  };

  // Hero poster and carousel photos.
  document.querySelectorAll('[data-km-lb-open]').forEach(link => {
    link.addEventListener('click', e => {
      if (!viewer || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      viewer.open(lbIndex(link), link, sourceByIndex);
    });
  });

  /* ─── Hero poster tilt ───────────────────────────────────── */
  // Mouse only: the postcard leans toward the pointer and catches the light.
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)');
  document.querySelectorAll('.event-poster .event-cover').forEach(card => {
    if (!fine.matches || reduce.matches) return;
    card.classList.add('is-tiltable');
    let raf = 0, last = null;
    const paint = () => {
      raf = 0;
      if (!last) return;
      const r = card.getBoundingClientRect();
      const x = Math.max(0, Math.min(1, (last.clientX - r.left) / r.width));
      const y = Math.max(0, Math.min(1, (last.clientY - r.top) / r.height));
      card.style.setProperty('--ry', `${((x - .5) * 12).toFixed(2)}deg`);
      card.style.setProperty('--rx', `${((.5 - y) * 10).toFixed(2)}deg`);
      card.style.setProperty('--gx', `${(x * 100).toFixed(1)}%`);
      card.style.setProperty('--gy', `${(y * 100).toFixed(1)}%`);
    };
    card.addEventListener('pointerenter', e => { if (e.pointerType === 'mouse') card.classList.add('is-tilting'); });
    card.addEventListener('pointermove', e => {
      if (e.pointerType !== 'mouse') return;
      last = e;
      if (!raf) raf = requestAnimationFrame(paint);
    });
    card.addEventListener('pointerleave', () => {
      last = null;
      card.classList.remove('is-tilting');
      ['--rx', '--ry'].forEach(v => card.style.removeProperty(v));
    });
  });

  /* ─── Carousel ───────────────────────────────────────────── */
  document.querySelectorAll('[data-km-car]').forEach(car => {
    const track = car.querySelector('[data-km-car-track]');
    const items = Array.from(car.querySelectorAll('[data-km-car-item]'));
    const dots = Array.from(car.querySelectorAll('[data-km-car-dot]'));
    const counter = car.querySelector('[data-km-car-count]');
    const rings = Array.from(car.querySelectorAll('.km-nav--ring'));
    if (!track || !items.length) return;
    car.classList.add('is-ready');
    const many = items.length > 1;
    let active = -1;

    const center = it => it.offsetLeft - track.offsetLeft + it.offsetWidth / 2;
    function goTo(it, instant) {
      if (!it) return;
      track.scrollTo({ left: center(it) - track.clientWidth / 2, behavior: instant || reduce.matches ? 'instant' : 'smooth' });
    }
    car.kmGoTo = goTo;
    const step = dir => goTo(items[(Math.max(active, 0) + dir + items.length) % items.length]);

    // First and last photo can reach the middle: side padding = half the track minus half the photo.
    function pad() {
      const w = track.clientWidth;
      track.style.setProperty('--pad-l', `${Math.max(8, (w - items[0].offsetWidth) / 2)}px`);
      track.style.setProperty('--pad-r', `${Math.max(8, (w - items[items.length - 1].offsetWidth) / 2)}px`);
    }

    function setActive(i) {
      if (i === active) return;
      const first = active === -1;
      active = i;
      items.forEach((it, k) => it.classList.toggle('is-active', k === i));
      dots.forEach((d, k) => { if (k !== i) d.removeAttribute('aria-current'); else d.setAttribute('aria-current', 'true'); });
      restartRing();
      if (counter) {
        counter.innerHTML = `<b>${i + 1}</b> / ${items.length}`;
        if (!first && !reduce.matches) { counter.classList.remove('is-ticking'); void counter.offsetWidth; counter.classList.add('is-ticking'); }
      }
    }

    // Every scroll frame: how far each card is from the middle drives scale, turn and dimming.
    function update() {
      const mid = track.scrollLeft + track.clientWidth / 2;
      let best = 0, bestDist = Infinity;
      items.forEach((it, k) => {
        const dist = center(it) - mid;
        const unit = (it.offsetWidth + 20) || 1;
        const s = Math.max(-1, Math.min(1, dist / unit));
        it.style.setProperty('--s', s.toFixed(3));
        it.style.setProperty('--d', Math.abs(s).toFixed(3));
        if (Math.abs(dist) < bestDist) { bestDist = Math.abs(dist); best = k; }
      });
      setActive(best);
    }

    /* autoplay: runs on the dot's fill animation; stops for good once you touch the carousel */
    const canPlay = many && !reduce.matches;
    let stopped = !canPlay, inView = false, hovered = false, focused = false;
    const sync = () => {
      const held = !inView || hovered || focused || document.hidden;
      car.classList.toggle('is-playing', !stopped);
      car.classList.toggle('is-paused', held);
      rings.forEach(r => { r.classList.toggle('is-counting', !stopped); r.classList.toggle('is-held', held); });
    };
    // The ring round "next" counts down the same seconds as the bar under the photo.
    function restartRing() {
      if (stopped) return;
      rings.forEach(r => { r.classList.remove('is-counting'); void r.offsetWidth; r.classList.add('is-counting'); });
    }
    const stop = () => { if (!stopped) { stopped = true; sync(); } };
    car.addEventListener('animationend', e => {
      if (!stopped && e.animationName === 'km-car-fill') step(1);
    });
    car.addEventListener('pointerenter', e => { if (e.pointerType === 'mouse') { hovered = true; sync(); } });
    car.addEventListener('pointerleave', () => { hovered = false; sync(); });
    car.addEventListener('focusin', () => { focused = true; sync(); });
    car.addEventListener('focusout', e => { if (!car.contains(e.relatedTarget)) { focused = false; sync(); } });
    document.addEventListener('visibilitychange', sync);
    ['pointerdown', 'wheel', 'touchstart', 'keydown'].forEach(type => track.addEventListener(type, stop, { passive: true }));

    // Entrance when it comes into view; autoplay only runs while it is on screen.
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(entries => {
        entries.forEach(en => {
          inView = en.isIntersecting;
          if (inView) car.classList.add('is-inview');
          sync();
        });
      }, { rootMargin: '0px 0px -15% 0px' }).observe(car);
    } else { inView = true; car.classList.add('is-inview'); sync(); }

    car.querySelectorAll('[data-km-car-prev]').forEach(b => b.addEventListener('click', () => { stop(); step(-1); }));
    car.querySelectorAll('[data-km-car-next]').forEach(b => b.addEventListener('click', () => { stop(); step(1); }));
    dots.forEach((d, k) => d.addEventListener('click', () => { stop(); goTo(items[k]); }));

    // A tap on a side photo brings it to the middle; only the middle one opens full screen.
    track.addEventListener('click', e => {
      const it = e.target.closest('[data-km-car-item]');
      if (dragged) { e.preventDefault(); e.stopPropagation(); return; }
      if (it && many && items.indexOf(it) !== active && e.target.closest('[data-km-lb-open]')) {
        e.preventDefault(); e.stopPropagation(); stop(); goTo(it);
      }
    }, true);

    // ← → between photos while one of them has focus.
    track.addEventListener('keydown', e => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      const links = items.map(it => it.querySelector('[data-km-lb-open]'));
      const at = links.indexOf(document.activeElement);
      if (at < 0) return;
      e.preventDefault();
      const to = (at + (e.key === 'ArrowRight' ? 1 : -1) + items.length) % items.length;
      links[to].focus({ preventScroll: true });
      goTo(items[to]);
    });

    // Mouse: drag it like on a phone; the nearest photo snaps to the middle on release.
    let drag = null, dragged = false;
    track.addEventListener('pointerdown', e => {
      if (e.pointerType !== 'mouse' || e.button !== 0 || e.target.closest('details')) return;
      drag = { x: e.clientX, left: track.scrollLeft, id: e.pointerId, moved: false };
    });
    track.addEventListener('pointermove', e => {
      if (!drag || e.pointerId !== drag.id) return;
      const dx = e.clientX - drag.x;
      if (!drag.moved) {
        if (Math.abs(dx) < 6) return;
        drag.moved = true;
        track.classList.add('is-grabbing');
        track.setPointerCapture(e.pointerId);
      }
      track.scrollLeft = drag.left - dx;
    });
    const endDrag = e => {
      if (!drag || e.pointerId !== drag.id) return;
      dragged = drag.moved;
      drag = null;
      if (dragged) {
        track.classList.remove('is-grabbing');
        update();
        goTo(items[active]);
        setTimeout(() => { dragged = false; }, 0);
      }
    };
    track.addEventListener('pointerup', endDrag);
    track.addEventListener('pointercancel', endDrag);
    track.addEventListener('dragstart', e => e.preventDefault());

    let frame = 0;
    const schedule = () => { if (!frame) frame = requestAnimationFrame(() => { frame = 0; update(); }); };
    track.addEventListener('scroll', schedule, { passive: true });
    const relayout = () => { pad(); goTo(items[Math.max(active, 0)], true); update(); };
    if ('ResizeObserver' in window) new ResizeObserver(relayout).observe(track);
    else window.addEventListener('resize', relayout);
    pad();
    update();
    sync();
  });
})();
