// Freeze only decorative infinite CSS effects. CSS still owns hover/paused states and finite entrances.
(function () {
  'use strict';
  if (!document.getAnimations || !window.CSSAnimation || !window.IntersectionObserver) return;

  var targets = new Map();
  var savedRates = new WeakMap();
  var pending = 0;
  var rescan = false;

  function queue(discover) {
    if (discover === true) rescan = true;
    if (!pending && (rescan || targets.size)) pending = requestAnimationFrame(refresh);
  }

  var viewport = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      var record = targets.get(entry.target);
      if (record) record.near = entry.isIntersecting;
    });
    queue();
  }, { rootMargin: '80px' });

  // Watch the actual ancestors, not all class/style mutations or every scroll event on the page.
  var visibility = new MutationObserver(function () { queue(); });

  function discoverEffects() {
    var next = new Map();
    document.getAnimations().forEach(function (animation) {
      if (!(animation instanceof CSSAnimation) || !animation.effect ||
          animation.effect.getTiming().iterations !== Infinity) return;
      var el = animation.effect.target;
      if (!el || el.nodeType !== 1) return;
      if (!next.has(el)) next.set(el, []);
      next.get(el).push(animation);
    });
    targets.forEach(function (record, el) {
      record.effects.forEach(function (a) {
        if (!next.has(el) || !next.get(el).includes(a)) restore(a);
      });
      if (!next.has(el)) { viewport.unobserve(el); targets.delete(el); }
    });
    visibility.disconnect();
    var ancestors = new Set();
    next.forEach(function (effects, el) {
      if (!targets.has(el)) {
        targets.set(el, { near: false, effects: [] });
        viewport.observe(el);
      }
      targets.get(el).effects = effects;
      for (var n = el; n && !ancestors.has(n); n = n.parentElement) ancestors.add(n);
    });
    ancestors.forEach(function (n) {
      visibility.observe(n, { attributes: true, attributeFilter: ['class', 'style', 'hidden', 'aria-hidden'] });
    });
  }

  function restore(a) {
    if (!savedRates.has(a)) return;
    if (a.playbackRate === 0) a.playbackRate = savedRates.get(a);
    savedRates.delete(a);
  }

  function transparent(n) {
    if (getComputedStyle(n).opacity !== '0') return false;
    // A loop may start with a transparent keyframe. It must be allowed to advance on screen.
    return !n.getAnimations().some(function (a) {
      return a.effect && !a.effect.pseudoElement && a.effect.getKeyframes().some(function (key) { return 'opacity' in key; });
    });
  }

  function refresh() {
    pending = 0;
    if (rescan) { rescan = false; discoverEffects(); }
    var opacity = new Map();
    targets.forEach(function (record, el) {
      if (!el.isConnected) { queue(true); return; }
      var show = record.near && getComputedStyle(el).visibility === 'visible';
      for (var n = el; show && n; n = n.parentElement) {
        if (!opacity.has(n)) opacity.set(n, transparent(n));
        show = !opacity.get(n);
      }
      record.effects.forEach(function (a) {
        if (show) restore(a);
        else if (!savedRates.has(a) && a.playbackRate !== 0) {
          savedRates.set(a, a.playbackRate);
          a.playbackRate = 0;
        }
      });
    });
  }

  document.addEventListener('animationstart', function (event) {
    var style = getComputedStyle(event.target, event.pseudoElement || null);
    if (style.animationIterationCount.includes('infinite')) queue(true);
  }, true);
  document.addEventListener('animationcancel', function (event) {
    if (targets.has(event.target)) queue(true);
  }, true);
  document.addEventListener('transitionend', function (event) {
    if (event.propertyName === 'opacity' || event.propertyName === 'visibility') queue();
  }, true);
  document.addEventListener('animationend', function () { queue(); }, true);
  window.addEventListener('pageshow', function () { queue(true); });
  // Removing an already offscreen subtree does not necessarily generate another viewport callback.
  new MutationObserver(function (changes) {
    if (!targets.size || !changes.some(function (change) { return change.removedNodes.length; })) return;
    for (var el of targets.keys()) { if (!el.isConnected) { queue(true); break; } }
  }).observe(document.documentElement, { subtree: true, childList: true });
  queue(true);
})();
