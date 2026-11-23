/* Motion budget: endless CSS animations run only where someone can see them.
   An element whose endless animation is off screen, or inside something fully transparent
   or hidden, is paused (data-km-motion="off") and resumes from the same frame when it is
   visible again. Nothing is restyled: the attribute only sets animation-play-state.
   Finite animations (reveals, hovers, clicks) are never touched. */
(function () {
  'use strict';
  if (typeof document.getAnimations !== 'function' || typeof CSSAnimation === 'undefined') return;

  var ATTR = 'data-km-motion';
  var MARGIN = 80;                   // start a little before the element scrolls in
  var tracked = new Set();

  function endless(animation) {
    try {
      return animation instanceof CSSAnimation && animation.effect
        && animation.effect.getTiming().iterations === Infinity;
    } catch (e) { return false; }
  }

  function visible(el) {
    if (!el.isConnected) return false;
    var r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return false;
    if (r.bottom < -MARGIN || r.top > innerHeight + MARGIN || r.right < -MARGIN || r.left > innerWidth + MARGIN) return false;
    for (var n = el; n && n.nodeType === 1; n = n.parentElement) {
      var s = getComputedStyle(n);
      if (s.display === 'none' || s.visibility === 'hidden' || s.opacity === '0') return false;
    }
    return true;
  }

  function update() {
    tracked.forEach(function (el) {
      if (!el.isConnected) { tracked.delete(el); return; }
      if (visible(el)) { if (el.hasAttribute(ATTR)) el.removeAttribute(ATTR); }
      else if (el.getAttribute(ATTR) !== 'off') el.setAttribute(ATTR, 'off');
    });
  }

  // Find elements with endless CSS animations (their ::before/::after count as the element).
  function scan() {
    document.getAnimations().forEach(function (animation) {
      if (!endless(animation)) return;
      var el = animation.effect.target;
      if (el && el.nodeType === 1) tracked.add(el);
    });
    update();
  }

  var queued = false;
  function soon() {                  // coalesce bursts of scroll/animation events into one check
    if (queued) return;
    queued = true;
    setTimeout(function () { queued = false; update(); }, 100);
  }

  var scanQueued = false, lastScan = 0;
  function queueScan() {
    if (scanQueued) return;
    scanQueued = true;
    setTimeout(function () {
      var run = function () { scanQueued = false; lastScan = Date.now(); scan(); };
      if ('requestIdleCallback' in window) requestIdleCallback(run, { timeout: 1500 }); else run();
    }, Math.max(0, 1500 - (Date.now() - lastScan)));   // at most one scan every 1.5 s
  }

  function boot() {
    lastScan = Date.now();
    scan();
    // New content (map popups, filters, reveals) may bring new endless animations.
    new MutationObserver(queueScan).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
    window.addEventListener('scroll', soon, { passive: true });
    window.addEventListener('resize', soon);
    document.addEventListener('animationend', soon, true);
    document.addEventListener('transitionend', soon, true);
    window.addEventListener('load', queueScan);
    // Safety net for anything that moves without an event (carousels, reveals): a light re-check each second.
    setInterval(function () { if (!document.hidden) update(); }, 1000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
