/* Event page media: the photo stack ("Fotoqalereya") and the full-screen viewer.
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
      if (!r.width || !r.height || r.bottom < 0 || r.top > window.innerHeight) return null;
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
      opener = (from && from.closest('[data-km-stack-deck]')) || from || document.activeElement;
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
  const sourceByIndex = i => document.querySelector(`[data-km-lb-open="${i}"]`)?.closest('.km-stack__card[data-pos]:not([data-pos="0"])')
    ? null : document.querySelector(`[data-km-lb-open="${i}"]`);

  // Hero poster (and any other plain opener outside the stack).
  document.querySelectorAll('[data-km-lb-open]').forEach(link => {
    if (link.closest('[data-km-stack]')) return;
    link.addEventListener('click', e => {
      if (!viewer || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      viewer.open(lbIndex(link), link, sourceByIndex);
    });
  });

  /* ─── Stack ──────────────────────────────────────────────── */
  document.querySelectorAll('[data-km-stack]').forEach(stack => {
    const deck = stack.querySelector('[data-km-stack-deck]');
    const cards = Array.from(stack.querySelectorAll('[data-km-stack-card]'));
    const counter = stack.querySelector('[data-km-stack-count]');
    const captionSlot = stack.querySelector('[data-km-stack-caption]');
    if (!deck || !cards.length) return;
    let order = cards.map((_, i) => i);   // order[0] is the top card
    let animating = false;
    stack.classList.add('is-ready');

    function layout() {
      order.forEach((cardIndex, pos) => {
        const card = cards[cardIndex];
        const sign = pos % 2 ? -1 : 1;
        card.dataset.pos = pos;
        card.style.zIndex = String(cards.length - pos);
        card.style.opacity = pos > 3 ? '0' : '1';
        card.style.transform = pos === 0 ? 'none'
          : `translateY(${pos * 13}px) scale(${1 - pos * 0.05}) rotate(${sign * (2 + pos * 1.5)}deg)`;
        card.setAttribute('aria-hidden', pos === 0 ? 'false' : 'true');
        card.querySelectorAll('a, summary').forEach(el => { el.tabIndex = pos === 0 && el.tagName === 'SUMMARY' ? 0 : -1; });
      });
      if (counter) counter.textContent = `${order[0] + 1} / ${cards.length}`;
      if (captionSlot) {
        const source = cards[order[0]].querySelector('figcaption');
        captionSlot.innerHTML = source ? source.innerHTML : '';
      }
    }
    function flyOut(dir) {
      if (animating || cards.length < 2) return;
      const top = cards[order[0]];
      const finish = () => {
        order.push(order.shift());
        top.classList.add('is-dragging');      // jump to the back without a visible trip
        top.style.opacity = '0';
        layout();
        top.style.opacity = '0';
        requestAnimationFrame(() => { top.classList.remove('is-dragging'); top.style.opacity = order.indexOf(cards.indexOf(top)) > 3 ? '0' : '1'; animating = false; });
      };
      if (reduce.matches) { animating = true; finish(); return; }
      animating = true;
      top.style.transform = `translateX(${dir * 130}%) rotate(${dir * 20}deg)`;
      top.style.opacity = '0';
      setTimeout(finish, 450);
    }
    function bringBack() {
      if (animating || cards.length < 2) return;
      animating = true;
      const last = order.pop();
      order.unshift(last);
      const card = cards[last];
      card.classList.add('is-dragging');
      card.style.transform = 'translateX(-130%) rotate(-20deg)';
      card.style.opacity = '0';
      card.style.zIndex = String(cards.length + 1);
      requestAnimationFrame(() => requestAnimationFrame(() => {
        card.classList.remove('is-dragging');
        layout();
        setTimeout(() => { animating = false; }, reduce.matches ? 0 : 450);
      }));
    }
    const openTop = () => {
      const link = cards[order[0]].querySelector('[data-km-lb-open]');
      if (!viewer || !link) { if (link) window.location.href = link.href; return; }
      viewer.open(lbIndex(link), link, i => {
        const el = document.querySelector(`[data-km-lb-open="${i}"]`);
        const card = el && el.closest('[data-km-stack-card]');
        return card && card.dataset.pos !== '0' ? null : el;
      });
    };

    // Drag the top card; a short tap opens the viewer.
    let drag = null;
    deck.addEventListener('pointerdown', e => {
      const card = e.target.closest('[data-km-stack-card]');
      if (animating || !card || card.dataset.pos !== '0' || e.target.closest('details') || e.button > 0) return;
      drag = { card, x: e.clientX, y: e.clientY, t: performance.now(), dx: 0, moved: false, id: e.pointerId };
    });
    deck.addEventListener('pointermove', e => {
      if (!drag || e.pointerId !== drag.id) return;
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (!drag.moved) {
        if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
        if (Math.abs(dy) > Math.abs(dx)) { drag = null; return; }   // vertical: let the page scroll
        drag.moved = true;
        drag.card.classList.add('is-dragging');
        deck.setPointerCapture(e.pointerId);
      }
      drag.dx = dx;
      drag.card.style.transform = `translateX(${dx}px) rotate(${dx / 18}deg)`;
    });
    const end = e => {
      if (!drag || e.pointerId !== drag.id) return;
      const { card, dx, moved, t } = drag;
      drag = null;
      card.classList.remove('is-dragging');
      if (!moved) {
        if (e.type === 'pointerup' && performance.now() - t < 400) { e.preventDefault(); openTop(); }
        return;
      }
      if (Math.abs(dx) > 90) flyOut(dx > 0 ? 1 : -1);
      else layout();
    };
    deck.addEventListener('dragstart', e => e.preventDefault());   // links/images must not start a native drag
    deck.addEventListener('pointerup', end);
    deck.addEventListener('pointercancel', end);
    deck.addEventListener('click', e => { if (e.target.closest('[data-km-lb-open]')) e.preventDefault(); });
    deck.addEventListener('keydown', e => {
      if (e.target !== deck) return;
      if (e.key === 'ArrowRight') { e.preventDefault(); flyOut(-1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); bringBack(); }
      if (e.key === 'Enter') { e.preventDefault(); openTop(); }
    });
    stack.querySelector('[data-km-stack-next]')?.addEventListener('click', () => flyOut(-1));
    stack.querySelector('[data-km-stack-prev]')?.addEventListener('click', bringBack);
    layout();
  });
})();
