/* Home hero photo stack: turns the top photo by itself every few seconds,
 * only while it is on screen and untouched. Any touch, hover, key or focus
 * stops it for good (the visitor is in charge). Off under reduced motion. */
(function () {
  "use strict";
  var root = document.querySelector(".home-hero-stack .km-pstack");
  if (!root || (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
  var next = root.querySelector("[data-km-pstack-next]");
  if (!next) return;
  var GAP = 4600, timer = null, visible = false, stopped = false;
  root.style.setProperty("--hh-gap", GAP + "ms");
  function stop() { stopped = true; clear(); root.classList.remove("is-auto"); }
  function clear() { if (timer) { clearTimeout(timer); timer = null; } }
  function schedule() {
    clear();
    if (stopped || !visible || document.hidden) { root.classList.remove("is-auto"); return; }
    root.classList.remove("is-auto"); void root.offsetWidth; root.classList.add("is-auto");
    timer = setTimeout(function () { next.click(); schedule(); }, GAP);
  }
  ["pointerdown", "pointerenter", "focusin", "keydown", "touchstart"].forEach(function (ev) { root.addEventListener(ev, stop, { passive: true }); });
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (es) { visible = es[0].isIntersecting; schedule(); }, { threshold: 0.55 }).observe(root);
  } else { visible = true; schedule(); }
  document.addEventListener("visibilitychange", schedule);
})();
