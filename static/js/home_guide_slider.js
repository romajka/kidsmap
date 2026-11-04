/* Native swipe and links work without JavaScript; buttons enhance the guide row. */
(() => {
  'use strict';
  document.querySelectorAll('[data-guide-slider]').forEach(root => {
    const track = root.querySelector('[data-guide-track]');
    const controls = root.querySelector('[data-guide-controls]');
    const prev = root.querySelector('[data-guide-prev]');
    const next = root.querySelector('[data-guide-next]');
    const motion = root.querySelector('[data-guide-motion]');
    if (!track || !controls || !prev || !next) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const max = () => Math.max(0, track.scrollWidth - track.clientWidth);
    let paused = false;
    let visible = !('IntersectionObserver' in window);
    let touching = false;
    let scrolling = false;
    let scrollTimer;
    let autoTimer;
    let hasAdvanced = false;
    let hovered = false;
    function updateMotion() {
      const enabled = !!motion && !reduced.matches && max() > 2;
      const running = enabled && visible && !document.hidden && !paused && !touching && !scrolling;
      root.dataset.guideMotionState = running ? 'running' : 'paused';
      const keyboardFocused = root.contains(document.activeElement) && document.activeElement.matches(':focus-visible');
      if (!running || hovered || keyboardFocused) {
        clearTimeout(autoTimer); autoTimer = null;
      } else if (!autoTimer) {
        autoTimer = setTimeout(() => {
          autoTimer = null; hasAdvanced = true;
          if (track.scrollLeft >= max() - 2) scroll(0);
          else move(1);
        }, hasAdvanced ? 3600 : 1800);
      }
      if (!motion) return;
      motion.hidden = !enabled;
      motion.setAttribute('aria-pressed', String(paused));
      const label = paused ? motion.dataset.playLabel : motion.dataset.pauseLabel;
      motion.setAttribute('aria-label', label);
      motion.title = label;
      motion.querySelector('[data-guide-motion-icon]').textContent = paused ? '▷' : 'Ⅱ';
    }
    motion?.addEventListener('click', () => {
      paused = !paused;
      if (paused) track.scrollTo({left:track.scrollLeft, behavior:'auto'});
      updateMotion();
    });
    track.addEventListener('pointerenter', event => { if (event.pointerType === 'mouse') { hovered = true; updateMotion(); } });
    track.addEventListener('pointerleave', event => { if (event.pointerType === 'mouse') { hovered = false; updateMotion(); } });
    root.addEventListener('focusin', updateMotion);
    root.addEventListener('focusout', () => setTimeout(updateMotion, 0));
    track.addEventListener('pointerdown', () => { touching = true; updateMotion(); }, {passive:true});
    const release = () => { touching = false; updateMotion(); };
    window.addEventListener('pointerup', release, {passive:true});
    window.addEventListener('pointercancel', release, {passive:true});
    document.addEventListener('visibilitychange', () => { touching = false; updateMotion(); });
    reduced.addEventListener?.('change', updateMotion);
    if ('IntersectionObserver' in window) new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting; updateMotion();
    }, {threshold:.15}).observe(root);

    function update() {
      const limit = max();
      controls.hidden = limit < 2;
      prev.disabled = track.scrollLeft < 2;
      next.disabled = track.scrollLeft >= limit - 2;
      updateMotion();
    }
    function move(direction) {
      const left = track.scrollLeft;
      const origin = track.getBoundingClientRect().left + (parseFloat(getComputedStyle(track).paddingLeft) || 0);
      const stops = Array.from(track.children, card => card.getBoundingClientRect().left - origin + left);
      const target = direction > 0 ? stops.find(x => x > left + 2) ?? max() : stops.reverse().find(x => x < left - 2) ?? 0;
      scroll(target);
    }
    function scroll(left) {
      track.scrollTo({left:Math.min(max(), Math.max(0, left)), behavior:reduced.matches ? 'auto' : 'smooth'});
    }
    prev.addEventListener('click', () => { hasAdvanced = true; move(-1); });
    next.addEventListener('click', () => { hasAdvanced = true; move(1); });
    track.addEventListener('keydown', event => {
      if (event.target !== track || !['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
      event.preventDefault();
      if (event.key === 'Home') scroll(0);
      else if (event.key === 'End') scroll(max());
      else move(event.key === 'ArrowRight' ? 1 : -1);
    });
    track.addEventListener('focusin', event => {
      const card = event.target.closest('.home-parent-guide__destination, [data-guide-track] > a');
      if (!card || card.parentElement !== track) return;
      const box = card.getBoundingClientRect();
      const bounds = track.getBoundingClientRect();
      const inset = parseFloat(getComputedStyle(track).paddingLeft) || 0;
      if (box.left < bounds.left + inset - 1 || box.right > bounds.right - inset + 1) {
        track.scrollTo({left:Math.min(max(), Math.max(0, box.left - bounds.left + track.scrollLeft - inset)), behavior:'auto'});
      }
    });
    track.addEventListener('scroll', () => {
      scrolling = true; clearTimeout(scrollTimer); update();
      scrollTimer = setTimeout(() => { scrolling = false; updateMotion(); }, 180);
    }, {passive:true});
    window.addEventListener('resize', update, {passive:true});
    if ('ResizeObserver' in window) new ResizeObserver(update).observe(track);
    new MutationObserver(update).observe(track, {childList:true});
    update();
  });
})();
