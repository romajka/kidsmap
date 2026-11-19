/* Hero live line: shows one topic word at a time under the headline.
   Every word is already a link in the HTML; this only takes turns showing them.
   On desktop the matching popular chip under the search lights up with each word. */
(function () {
  "use strict";
  var STEP_MS = 2600;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var desktop = window.matchMedia && window.matchMedia("(min-width: 768px)").matches;

  function splitLetters(word, lowerFirst, lang) {
    if (word.getAttribute("data-split")) return;
    var text = word.textContent;
    word.setAttribute("aria-label", text);
    // "Bakıda uşaqlar üçün cüdo": the word ends the phrase, so it starts in lower case
    var shown = lowerFirst ? text.charAt(0).toLocaleLowerCase(lang || undefined) + text.slice(1) : text;
    word.textContent = "";
    Array.prototype.forEach.call(shown, function (ch, i) {
      var s = document.createElement("span");
      s.className = "km-rot__ch";
      s.setAttribute("aria-hidden", "true");
      s.style.setProperty("--d", i);
      s.textContent = ch;
      word.appendChild(s);
    });
    word.setAttribute("data-split", "1");
  }

  function restart(el, cls) {
    el.classList.remove(cls);
    void el.offsetWidth;
    el.classList.add(cls);
  }

  function findChip(word) {
    var key = word.getAttribute("data-rot-chip");
    if (!key) return null;
    var hero = document.querySelector(".home-hero");
    if (!hero) return null;
    var chips = hero.querySelectorAll(".home-search-popular-chip");
    for (var i = 0; i < chips.length; i++) {
      var chip = chips[i];
      if (chip.getAttribute("data-popular-category") === key) return chip;
      var href = chip.getAttribute("href") || "";
      if (href.indexOf("specialization=" + encodeURIComponent(key)) !== -1) return chip;
    }
    return null;
  }

  function init(root) {
    var line = root.querySelector(".km-rot__line");
    var box = root.querySelector(".km-rot__words");
    var words = Array.prototype.slice.call(root.querySelectorAll(".km-rot__word"));
    var ink = root.querySelector(".km-rot__ink");
    var pin = root.querySelector(".km-rot__pin");
    if (!line || !box || !words.length || !root.offsetParent) return;
    var lang = root.getAttribute("data-rot-lang") || "";
    var lowerFirst = desktop && root.hasAttribute("data-rot-lower-desktop");

    root.classList.add("is-live");
    words.forEach(function (w) { splitLetters(w, lowerFirst, lang); });

    // Fit: the longest word plus the rest of the phrase must stay on one line.
    function fit() {
      root.style.setProperty("--rot-fit", "1");
      var widest = 0;
      words.forEach(function (w) { widest = Math.max(widest, w.scrollWidth); });
      var others = 0;
      Array.prototype.forEach.call(line.children, function (el) {
        if (el !== box && getComputedStyle(el).display !== "none") others += el.getBoundingClientRect().width;
      });
      var gaps = parseFloat(getComputedStyle(line).columnGap) || 0;
      var needed = widest + others + gaps * (line.children.length - 1) + 4;
      var room = line.clientWidth;
      if (needed > room && room > 0) root.style.setProperty("--rot-fit", String(Math.max(0.6, room / needed).toFixed(3)));
    }
    fit();
    // web fonts change word widths; measure again once they are in
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () {
        fit();
        if (started) root.style.setProperty("--ink-w", words[current].scrollWidth + "px");
      });
    }

    var chips = words.map(findChip);
    var current = 0;
    function show(next, first) {
      var prev = words[current];
      var word = words[next];
      if (!first && prev !== word) {
        prev.classList.remove("is-on", "is-in");
        prev.setAttribute("tabindex", "-1");
        restart(prev, "is-out");
      }
      word.classList.remove("is-out");
      word.classList.add("is-on");
      word.removeAttribute("tabindex");
      if (!reduce) restart(word, "is-in");
      root.setAttribute("data-kind", word.classList.contains("km-rot__word--person") ? "specialist" : "place");
      root.style.setProperty("--ink-w", word.scrollWidth + "px");
      if (ink && !reduce) restart(ink, "is-draw");
      if (pin && !reduce) restart(pin, "is-drop");
      chips.forEach(function (chip, i) { if (chip) chip.classList.toggle("km-echo", i === next); });
      current = next;
    }
    words.forEach(function (w, i) { if (i || !reduce) w.classList.remove("is-on"); if (i) w.setAttribute("tabindex", "-1"); });

    var timer = null, visible = true, held = false, started = false;
    function tick() { show((current + 1) % words.length); }
    function sync() {
      // with reduced motion the words still take turns, just as a quiet fade and a little slower
      var run = started && visible && !held && !document.hidden && words.length > 1;
      if (run && !timer) timer = setInterval(tick, reduce ? 4000 : STEP_MS);
      if (!run && timer) { clearInterval(timer); timer = null; }
    }
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) { visible = entries[0].isIntersecting; sync(); }).observe(root);
    }
    document.addEventListener("visibilitychange", sync);
    // hold the word still while a pointer or keyboard is on it, so it can be clicked
    var release = null;
    function holdFor(type) {
      root.addEventListener(type, function () { clearTimeout(release); held = true; sync(); });
    }
    holdFor("pointerdown");
    if (desktop) holdFor("pointerenter");
    ["pointerup", "pointercancel", "pointerleave"].forEach(function (type) {
      root.addEventListener(type, function () {
        clearTimeout(release);
        release = setTimeout(function () { held = root.contains(document.activeElement); sync(); }, type === "pointerleave" ? 400 : 1500);
      });
    });
    root.addEventListener("focusin", function () { held = true; sync(); });
    root.addEventListener("focusout", function () { held = false; sync(); });
    var resizeTimer = null;
    window.addEventListener("resize", function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () { fit(); root.style.setProperty("--ink-w", words[current].scrollWidth + "px"); }, 150);
    });
    // the first word comes in right away (the line itself rises with the headline);
    // the clock starts from there
    show(0, true);
    root.classList.add("is-started");
    started = true;
    sync();
  }

  function boot() { Array.prototype.forEach.call(document.querySelectorAll("[data-km-rot]"), init); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
