/* Home hero photo stage.
   Slides sit on top of each other; the active one reveals its three photos in turn and
   slowly settles its zoom. The active dot fills like a timeline and its animation drives
   autoplay, so the bar and the change always agree. Hover, focus or a hidden tab pause it.
   Arrows, dots, swipe and the keyboard (← →) change slides by hand. */
(function () {
  "use strict";
  var SLIDE_MS = 6500;
  var SWIPE_MIN = 40;

  function mountHeroSlider(slider) {
    var viewport = slider.querySelector("[data-home-hero-slider-viewport]");
    var track = slider.querySelector("[data-home-hero-slider-track]");
    var slides = Array.prototype.slice.call(slider.querySelectorAll("[data-home-hero-slide]"));
    var dots = Array.prototype.slice.call(slider.querySelectorAll("[data-home-hero-slider-dot]"));
    var prev = slider.querySelector("[data-home-hero-slider-prev]");
    var next = slider.querySelector("[data-home-hero-slider-next]");
    if (!viewport || !track || slides.length < 2) return;

    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var current = 0;
    var paused = false;

    slider.classList.add("is-stage");
    slider.style.setProperty("--stage-ms", SLIDE_MS + "ms");
    slider.setAttribute("aria-roledescription", "carousel");
    viewport.setAttribute("tabindex", "0");
    viewport.setAttribute("aria-live", "off");

    function setPaused(value) {
      paused = value;
      slider.classList.toggle("is-paused", value);
    }

    function show(index, direction) {
      var target = (index + slides.length) % slides.length;
      if (target === current && slides[target].classList.contains("is-active")) return;
      var leaving = slides[current];
      slides.forEach(function (slide, i) {
        var on = i === target;
        slide.classList.toggle("is-active", on);
        slide.classList.remove("is-leaving");
        slide.setAttribute("aria-hidden", on ? "false" : "true");
        Array.prototype.forEach.call(slide.querySelectorAll("img"), function (img) {
          if (on) img.removeAttribute("loading");
        });
      });
      if (leaving && leaving !== slides[target]) leaving.classList.add("is-leaving");
      slider.setAttribute("data-dir", direction < 0 ? "back" : "forward");
      dots.forEach(function (dot, i) {
        var on = i === target;
        dot.classList.toggle("is-active", on);
        dot.setAttribute("aria-current", on ? "true" : "false");
        if (on) {
          // restart the timeline fill
          dot.classList.remove("is-running");
          void dot.offsetWidth;
          dot.classList.add("is-running");
        } else {
          dot.classList.remove("is-running");
        }
      });
      current = target;
    }

    // the active dot's fill animation is the autoplay clock
    dots.forEach(function (dot) {
      dot.addEventListener("animationend", function (event) {
        if (event.animationName === "km-stage-fill" && dot.classList.contains("is-active") && !paused) show(current + 1, 1);
      });
      dot.addEventListener("click", function () {
        var i = Number(dot.getAttribute("data-slide-index") || 0);
        show(i, i < current ? -1 : 1);
      });
    });
    if (prev) prev.addEventListener("click", function () { show(current - 1, -1); });
    if (next) next.addEventListener("click", function () { show(current + 1, 1); });

    // pause while the visitor looks at or works with the photos
    slider.addEventListener("pointerenter", function (e) { if (e.pointerType === "mouse") setPaused(true); });
    slider.addEventListener("pointerleave", function (e) { if (e.pointerType === "mouse") setPaused(slider.contains(document.activeElement)); });
    slider.addEventListener("focusin", function () { setPaused(true); });
    slider.addEventListener("focusout", function () {
      setTimeout(function () { if (!slider.contains(document.activeElement) && !slider.matches(":hover")) setPaused(false); }, 0);
    });
    document.addEventListener("visibilitychange", function () { slider.classList.toggle("is-hidden-tab", document.hidden); });

    viewport.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); show(current - 1, -1); }
      if (e.key === "ArrowRight") { e.preventDefault(); show(current + 1, 1); }
    });

    // swipe / drag
    var startX = null, startY = 0, pointerId = null;
    viewport.addEventListener("pointerdown", function (e) {
      if (e.button !== undefined && e.button !== 0) return;
      startX = e.clientX; startY = e.clientY; pointerId = e.pointerId;
    });
    function endSwipe(e) {
      if (startX === null || (pointerId !== null && e.pointerId !== pointerId)) return;
      var dx = e.clientX - startX, dy = e.clientY - startY;
      startX = null; pointerId = null;
      if (Math.abs(dx) >= SWIPE_MIN && Math.abs(dx) > Math.abs(dy)) show(current + (dx < 0 ? 1 : -1), dx < 0 ? 1 : -1);
    }
    viewport.addEventListener("pointerup", endSwipe);
    viewport.addEventListener("pointercancel", function () { startX = null; pointerId = null; });
    viewport.addEventListener("dragstart", function (e) { e.preventDefault(); });

    if (reduce) slider.classList.add("is-still");
    // first slide: reveal once the photos can be seen
    show(0, 1);
  }

  function mountSingle(slider) {
    slider.classList.add("is-stage");
    var slide = slider.querySelector(".home-hero-slide");
    if (slide) slide.classList.add("is-active");
  }

  function boot() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-home-hero-slider]"), mountHeroSlider);
    Array.prototype.forEach.call(document.querySelectorAll("[data-home-hero-slider-single]"), mountSingle);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
