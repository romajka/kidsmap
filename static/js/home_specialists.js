/* Home: hand-picked specialists (section.home-spx).
   - filter tabs with a sliding pill; cards leave and the rest slide into place (FLIP);
   - cards tilt toward the pointer with a soft glare (mouse and pen only);
   - on phones one whole card per view, dots under the row, a short nudge hints at swiping;
   - arrows and a progress line follow the row; numbers count up once.
   Everything is driven by events and requestAnimationFrame; nothing runs on a timer. */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  var phone = window.matchMedia ? window.matchMedia("(max-width: 860px)") : { matches: false };

  function each(list, fn) { Array.prototype.forEach.call(list, fn); }

  function init(section) {
    if (section.hasAttribute("data-spx-ready")) return;
    section.setAttribute("data-spx-ready", "");
    var track = section.querySelector(".home-spx__track");
    if (!track) return;
    var cards = Array.prototype.slice.call(track.querySelectorAll(".home-spx-card"));
    var arrows = section.querySelectorAll("[data-spx-step]");
    var bar = section.querySelector(".home-spx__progress i");

    /* ---------- Row state: arrows, progress, centre card ---------- */
    var frame = 0;
    function paint() {
      frame = 0;
      var max = track.scrollWidth - track.clientWidth;
      var x = track.scrollLeft;
      each(arrows, function (btn) {
        var dir = parseInt(btn.getAttribute("data-spx-step"), 10);
        btn.disabled = dir < 0 ? x <= 2 : x >= max - 2;
      });
      if (bar) {
        var size = track.scrollWidth ? Math.min(1, track.clientWidth / track.scrollWidth) : 1;
        var start = max > 0 ? (x / max) * (1 - size) / size : 0;
        bar.style.setProperty("--size", size.toFixed(3));
        bar.style.setProperty("--start", start.toFixed(3));
      }
      paintDots();
    }
    function schedule() { if (!frame) frame = requestAnimationFrame(paint); }
    track.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", function () { buildDots(); schedule(); });
    if (phone.addEventListener) phone.addEventListener("change", schedule);
    schedule();

    each(arrows, function (btn) {
      btn.addEventListener("click", function () {
        var dir = parseInt(btn.getAttribute("data-spx-step"), 10) || 1;
        var first = cards.filter(function (c) { return !c.hidden; })[0];
        var stepWidth = first ? first.getBoundingClientRect().width + 18 : 290;
        var count = Math.max(1, Math.floor(track.clientWidth / stepWidth));
        track.scrollBy({ left: dir * count * stepWidth, behavior: reduce ? "auto" : "smooth" });
      });
    });

    /* ---------- Dots (phones): one per visible card ---------- */
    var dotsBox = section.querySelector(".home-spx__dots");
    var dotLabel = dotsBox ? (dotsBox.getAttribute("data-label") || "") : "";
    function visibleCards() { return cards.filter(function (c) { return !c.hidden; }); }
    // Dots count pages: as many cards as fit whole in the row make one page.
    var perView = 1;
    function measure() {
      var shown = visibleCards();
      var style = getComputedStyle(track);
      var gap = parseFloat(style.columnGap) || 0;
      var room = track.clientWidth - (parseFloat(style.paddingLeft) || 0) - (parseFloat(style.paddingRight) || 0);
      var width = shown[0] ? shown[0].getBoundingClientRect().width : room;
      perView = Math.max(1, Math.round((room + gap) / (width + gap)));
      return { shown: shown, step: width + gap };
    }
    function buildDots() {
      var m = measure();
      cards.forEach(function (c) { c.classList.remove("is-page-start"); });
      m.shown.forEach(function (c, i) { if (i % perView === 0) c.classList.add("is-page-start"); });
      track.classList.toggle("has-pages", perView > 1);
      if (!dotsBox) return;
      dotsBox.textContent = "";
      var pages = Math.ceil(m.shown.length / perView);
      if (pages < 2) return;
      for (var p = 0; p < pages; p++) {
        (function (page) {
          var dot = document.createElement("button");
          dot.type = "button";
          dot.className = "home-spx__dot";
          dot.setAttribute("aria-label", dotLabel + " " + (page + 1));
          dot.addEventListener("click", function () {
            var target = visibleCards()[page * perView];
            if (!target) return;
            track.scrollTo({ left: target.offsetLeft - (parseFloat(getComputedStyle(track).paddingLeft) || 0), behavior: reduce ? "auto" : "smooth" });
          });
          dotsBox.appendChild(dot);
        })(p);
      }
    }
    function paintDots() {
      if (!dotsBox || !dotsBox.children.length) return;
      var m = measure();
      var max = track.scrollWidth - track.clientWidth;
      var pages = dotsBox.children.length;
      var index = track.scrollLeft >= max - 2 ? pages - 1 : Math.round(track.scrollLeft / (m.step * perView || 1));
      index = Math.max(0, Math.min(pages - 1, index));
      Array.prototype.forEach.call(dotsBox.children, function (dot, i) {
        dot.setAttribute("aria-current", i === index ? "true" : "false");
      });
    }
    buildDots();

    /* A short nudge when the row first shows on a phone: the next card peeks in and slides back */
    function nudge() {
      if (reduce || !phone.matches || !track.animate || track.scrollLeft > 4 || track.scrollWidth <= track.clientWidth + 4) return;
      visibleCards().slice(0, 2).forEach(function (card) {
        card.animate(
          [{ transform: "none" }, { transform: "translateX(-46px)", offset: .45 }, { transform: "none" }],
          { duration: 1100, delay: 900, easing: "cubic-bezier(.45, 0, .2, 1)" }
        );
      });
    }

    /* ---------- Filter tabs ---------- */
    var tabs = section.querySelector(".home-spx__tabs");
    if (tabs) {
      var pill = tabs.querySelector(".home-spx__tab-pill");
      var buttons = tabs.querySelectorAll("[data-spx-tab]");
      var placePill = function () {
        var active = tabs.querySelector('[aria-pressed="true"]');
        if (!active || !pill) return;
        pill.style.setProperty("--pw", active.offsetWidth + "px");
        pill.style.setProperty("--ph", active.offsetHeight + "px");
        pill.style.setProperty("--px", active.offsetLeft + "px");
        pill.style.setProperty("--py", active.offsetTop + "px");
        tabs.classList.add("is-ready");
      };
      placePill();
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(placePill);
      window.addEventListener("resize", placePill);

      each(buttons, function (btn) {
        btn.addEventListener("click", function () {
          if (btn.getAttribute("aria-pressed") === "true") return;
          each(buttons, function (b) { b.setAttribute("aria-pressed", b === btn ? "true" : "false"); });
          placePill();
          if (btn.scrollIntoView && phone.matches) btn.scrollIntoView({ block: "nearest", inline: "center", behavior: reduce ? "auto" : "smooth" });
          filter(btn.getAttribute("data-spx-tab") || "");
        });
      });
    }

    function matches(card, code) {
      if (!code || card.classList.contains("home-spx-card--all")) return true;
      return (" " + (card.getAttribute("data-spx-codes") || "") + " ").indexOf(" " + code + " ") !== -1;
    }

    var filterRun = 0;
    function filter(code) {
      var run = ++filterRun;
      var leaving = cards.filter(function (c) { return !c.hidden && !matches(c, code); });
      var entering = cards.filter(function (c) { return c.hidden && matches(c, code); });
      if (reduce) {
        cards.forEach(function (c) { c.hidden = !matches(c, code); });
        track.scrollLeft = 0;
        buildDots();
        schedule();
        return;
      }
      leaving.forEach(function (c) { c.classList.add("is-leaving"); });
      setTimeout(function () {
        if (run !== filterRun) return;
        // FLIP: remember where the staying cards are, change the set, slide them from there
        var staying = cards.filter(function (c) { return !c.hidden && matches(c, code); });
        var before = staying.map(function (c) { return c.getBoundingClientRect().left; });
        leaving.forEach(function (c) { c.hidden = true; c.classList.remove("is-leaving"); });
        entering.forEach(function (c) { c.hidden = false; });
        track.scrollLeft = 0;
        buildDots();
        staying.forEach(function (c, i) {
          var dx = before[i] - c.getBoundingClientRect().left;
          if (!dx) return;
          c.animate([{ transform: "translateX(" + dx + "px)" }, { transform: "none" }],
                    { duration: 420, easing: "cubic-bezier(.22, 1, .36, 1)" });
        });
        entering.forEach(function (c, i) {
          c.animate([{ transform: "translateY(24px) scale(.92)", opacity: 0 }, { transform: "none", opacity: 1 }],
                    { duration: 460, delay: 60 * i, easing: "cubic-bezier(.34, 1.3, .64, 1)", fill: "backwards" });
        });
        schedule();
      }, leaving.length ? 180 : 0);
    }

    /* ---------- Tilt and glare (mouse and pen) ---------- */
    if (finePointer && !reduce) {
      cards.forEach(function (card) {
        if (card.classList.contains("home-spx-card--all")) return;
        var inner = card.querySelector(".home-spx-card__in");
        var pending = null;
        var raf = 0;
        function apply() {
          raf = 0;
          if (!pending) return;
          var r = inner.getBoundingClientRect();
          var px = (pending.x - r.left) / r.width;
          var py = (pending.y - r.top) / r.height;
          inner.style.setProperty("--ry", ((px - 0.5) * 10).toFixed(2) + "deg");
          inner.style.setProperty("--rx", ((0.5 - py) * 8).toFixed(2) + "deg");
          inner.style.setProperty("--gx", (px * 100).toFixed(1) + "%");
          inner.style.setProperty("--gy", (py * 100).toFixed(1) + "%");
        }
        inner.addEventListener("pointerenter", function () { card.classList.add("is-tilting"); });
        inner.addEventListener("pointermove", function (e) {
          pending = { x: e.clientX, y: e.clientY };
          if (!raf) raf = requestAnimationFrame(apply);
        });
        inner.addEventListener("pointerleave", function () {
          pending = null;
          card.classList.remove("is-tilting");
          inner.style.setProperty("--rx", "0deg");
          inner.style.setProperty("--ry", "0deg");
        });
      });
    }

    /* ---------- Count up once the section arrives ---------- */
    var counters = section.querySelectorAll("[data-spx-count]");
    function countUp() {
      if (reduce) return;
      each(counters, function (el) {
        var target = parseInt(el.getAttribute("data-spx-count"), 10) || 0;
        if (target < 2) return;
        var t0 = performance.now();
        el.textContent = "0";
        (function step(now) {
          var k = Math.min(1, (now - t0) / 900);
          el.textContent = String(Math.round(target * (1 - Math.pow(1 - k, 3))));
          if (k < 1) requestAnimationFrame(step);
        })(t0);
      });
    }
    if ("IntersectionObserver" in window && section.getBoundingClientRect().top > window.innerHeight * 0.9) {
      var io = new IntersectionObserver(function (entries) {
        if (!entries[0].isIntersecting) return;
        io.disconnect();
        countUp();
      }, { threshold: 0.3 });
      io.observe(section);
    }
    if ("IntersectionObserver" in window) {
      var seen = new IntersectionObserver(function (entries) {
        if (!entries[0].isIntersecting) return;
        seen.disconnect();
        nudge();
      }, { threshold: 0.6 });
      seen.observe(track);
    }
  }

  function start() { each(document.querySelectorAll("[data-spx]"), init); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
