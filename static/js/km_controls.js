/*
 * KidsMap filter controls: dual range sliders and dropdown motion.
 *
 * Every [two native range inputs inside one track] gets a drawn layer on
 * top: rail with ticks, gradient fill and two "pebble" thumbs with a value
 * bubble. The native inputs stay in the DOM for keyboard, screen readers and
 * the form; this layer only drives them (sets value + dispatches input/change),
 * so every page's existing sync code keeps working untouched.
 *
 * Dragging follows the pointer 1:1 (no transition while dragging), a tap on
 * the rail jumps the nearest thumb there with a short spring.
 */
(function () {
  "use strict";

  var LANG = (document.documentElement.lang || "az").slice(0, 2);
  var AGE_SUFFIX = { az: " yaş", ru: "", en: "" };
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function plural(n) {
    if (LANG !== "ru") return "";
    var m10 = n % 10, m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return " год";
    if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return " года";
    return " лет";
  }

  function el(tag, cls, parent) {
    var node = document.createElement(tag);
    node.className = cls;
    if (parent) parent.appendChild(node);
    return node;
  }

  function enhanceRange(track) {
    if (track.dataset.kmrInit === "1") return;
    var from = track.querySelector("input[type=range].range-slider-from, input[type=range][data-range-from-range]");
    var to = track.querySelector("input[type=range].range-slider-to, input[type=range][data-range-to-range]");
    if (!from || !to) return;
    track.dataset.kmrInit = "1";

    var root = track.closest("[data-range]") || track.parentElement;
    var min = Number(from.min || 0);
    var max = Number(from.max || 100);
    var step = Number(from.step || 1) || 1;
    var unit = (root && root.dataset.unit) || "";
    var isPrice = !!(root && root.hasAttribute("data-price-range")) || unit === "₼";
    var isAge = !isPrice && max <= 21;

    track.classList.add("kmr-host");
    if (root) root.classList.add("kmr-root");

    var layer = el("div", "kmr", track);
    layer.setAttribute("aria-hidden", "true");
    var rail = el("div", "kmr__rail", layer);
    var ticks = el("div", "kmr__ticks", rail);
    var fill = el("div", "kmr__fill", rail);
    var thumbs = [el("div", "kmr__thumb kmr__thumb--from", layer), el("div", "kmr__thumb kmr__thumb--to", layer)];
    var bubbles = thumbs.map(function (t) { return el("span", "kmr__bubble", t); });
    var inputs = [from, to];

    // Ticks: one per year for age, ~6 even marks otherwise.
    var tickCount = isAge ? (max - min) : 6;
    if (tickCount > 0 && tickCount <= 30) {
      for (var i = 1; i < tickCount; i++) {
        var tk = el("i", "kmr__tick", ticks);
        tk.style.left = (i / tickCount) * 100 + "%";
        if (isAge && (min + i) % 6 === 0) tk.classList.add("is-major");
      }
    }

    var scale = el("div", "kmr__scale", track);
    scale.setAttribute("aria-hidden", "true");
    el("span", "", scale).textContent = format(min, false);
    el("span", "", scale).textContent = format(max, isPrice);

    function format(v, open) {
      if (isPrice) return v + (open ? "+" : "") + " " + (unit || "₼");
      if (isAge) return v + (LANG === "ru" ? plural(v) : (AGE_SUFFIX[LANG] || ""));
      return String(v) + (unit ? " " + unit : "");
    }

    function pct(v) {
      return max > min ? ((v - min) / (max - min)) * 100 : 0;
    }

    function render() {
      var a = Number(from.value), b = Number(to.value);
      var pa = pct(a), pb = pct(b);
      layer.style.setProperty("--kmr-a", pa + "%");
      layer.style.setProperty("--kmr-b", pb + "%");
      thumbs[0].style.left = pa + "%";
      thumbs[1].style.left = pb + "%";
      bubbles[0].textContent = format(a, false);
      bubbles[1].textContent = format(b, isPrice && b >= max);
      // When thumbs are close, merge the bubbles to avoid overlap.
      var close = Math.abs(pb - pa) < 18;
      layer.classList.toggle("is-close", close);
      if (close) bubbles[1].textContent = a === b ? format(a, isPrice && b >= max) : format(a, false) + " – " + format(b, isPrice && b >= max);
      layer.classList.toggle("is-full", a <= min && b >= max);
      // Keep the thumb that can still move on top when both sit at an edge.
      thumbs[0].style.zIndex = a >= max - step ? 4 : 2;
    }

    function valueAt(clientX) {
      var r = rail.getBoundingClientRect();
      var ratio = r.width ? (clientX - r.left) / r.width : 0;
      ratio = Math.min(1, Math.max(0, ratio));
      var raw = min + ratio * (max - min);
      return Math.min(max, Math.max(min, Math.round(raw / step) * step));
    }

    function setValue(idx, v, evt) {
      var a = Number(from.value), b = Number(to.value);
      if (idx === 0) v = Math.min(v, b); else v = Math.max(v, a);
      var input = inputs[idx];
      if (String(v) === String(input.value) && evt === "input") return;
      input.value = v;
      input.dispatchEvent(new Event(evt, { bubbles: true }));
      render();
    }

    var active = -1, pointerId = null, startVal = null;

    layer.addEventListener("pointerdown", function (e) {
      if (e.button !== undefined && e.button !== 0) return;
      var v = valueAt(e.clientX);
      var a = Number(from.value), b = Number(to.value);
      var onThumb = e.target.closest && e.target.closest(".kmr__thumb");
      if (onThumb) active = onThumb === thumbs[0] ? 0 : 1;
      else if (a === b) active = v < a ? 0 : 1;
      else active = Math.abs(v - a) <= Math.abs(v - b) ? 0 : 1;
      if (a === b && a >= max) active = 0;
      if (a === b && a <= min) active = 1;

      pointerId = e.pointerId;
      startVal = inputs[active].value;
      try { layer.setPointerCapture(pointerId); } catch (err) { /* noop */ }
      e.preventDefault();

      // Existing page code decides which side wins on cross-over by focus.
      try { inputs[active].focus({ preventScroll: true }); } catch (err) { /* noop */ }
      layer.classList.add("is-dragging");
      thumbs[active].classList.add("is-active");

      if (!onThumb && !reduceMotion) {
        // Tap on the rail: glide there.
        layer.classList.add("is-jumping");
        window.setTimeout(function () { layer.classList.remove("is-jumping"); }, 260);
      }
      setValue(active, v, "input");
    });

    layer.addEventListener("pointermove", function (e) {
      if (active < 0 || e.pointerId !== pointerId) return;
      setValue(active, valueAt(e.clientX), "input");
    });

    function end(e) {
      if (active < 0 || (e && e.pointerId !== pointerId)) return;
      var idx = active;
      active = -1;
      try { layer.releasePointerCapture(pointerId); } catch (err) { /* noop */ }
      layer.classList.remove("is-dragging");
      thumbs[idx].classList.remove("is-active");
      thumbs[idx].classList.add("is-settle");
      window.setTimeout(function () { thumbs[idx].classList.remove("is-settle"); }, 420);
      if (String(inputs[idx].value) !== String(startVal)) {
        inputs[idx].dispatchEvent(new Event("change", { bubbles: true }));
      }
    }
    layer.addEventListener("pointerup", end);
    layer.addEventListener("pointercancel", end);
    layer.addEventListener("lostpointercapture", end);

    inputs.forEach(function (input, idx) {
      input.addEventListener("input", render);
      input.addEventListener("change", render);
      input.addEventListener("focus", function () {
        if (input.matches(":focus-visible")) thumbs[idx].classList.add("is-focus");
      });
      input.addEventListener("keydown", function () { thumbs[idx].classList.add("is-focus"); });
      input.addEventListener("blur", function () { thumbs[idx].classList.remove("is-focus"); });
    });

    // Values may be restored by other scripts (reset button, ajax, history).
    var form = from.form;
    if (form) form.addEventListener("reset", function () { window.setTimeout(render, 0); });
    new MutationObserver(render).observe(from, { attributes: true, attributeFilter: ["value"] });
    new MutationObserver(render).observe(to, { attributes: true, attributeFilter: ["value"] });

    render();
    // Other scripts may sync values right after load.
    window.requestAnimationFrame(render);
    window.setTimeout(render, 300);
    track.kmrRender = render;
  }

  function enhanceAll(scope) {
    (scope || document).querySelectorAll(".range-filter-track, .km-age-slider-track, [data-kmr-track]").forEach(enhanceRange);
  }

  /* ---------- Dropdown option stagger index ---------- */
  var MENU_SEL = ".km-custom-select__menu, .km-sort-menu, .km-tree-dropdown, .mobile-quick-menu";
  var OPTION_SEL = ".km-custom-select__option, .km-sort-option, .km-tree-row, .mobile-quick-menu button, .mobile-quick-menu a";

  function indexMenu(menu) {
    var items = menu.querySelectorAll(OPTION_SEL);
    for (var i = 0; i < items.length; i++) {
      items[i].style.setProperty("--kmi", Math.min(i, 10));
    }
  }

  function watchMenus(scope) {
    (scope || document).querySelectorAll(MENU_SEL).forEach(function (menu) {
      if (menu.dataset.kmMenuInit === "1") return;
      menu.dataset.kmMenuInit = "1";
      menu.classList.add("km-pop");
      indexMenu(menu);
      new MutationObserver(function () { indexMenu(menu); }).observe(menu, { childList: true, subtree: true });
    });
  }


  /* ---------- Segmented controls: sliding selection pill ---------- */
  var SEG_SEL = ".event-type-filter, .results-view-mode";
  var SEG_ITEM = ".event-type-option, .results-view-btn";

  function enhanceSegment(group) {
    if (group.dataset.kmSegInit === "1") return;
    group.dataset.kmSegInit = "1";
    var ind = document.createElement("span");
    ind.className = "km-seg-ind no-anim";
    ind.setAttribute("aria-hidden", "true");
    group.insertBefore(ind, group.firstChild);
    group.classList.add("has-seg-ind");

    function activeItem() {
      var items = group.querySelectorAll(SEG_ITEM);
      for (var i = 0; i < items.length; i++) {
        var radio = items[i].querySelector("input[type=radio]");
        if (radio ? radio.checked : items[i].classList.contains("is-active")) return items[i];
      }
      return null;
    }

    function place() {
      var item = activeItem();
      group.querySelectorAll(SEG_ITEM).forEach(function (it) {
        var radio = it.querySelector("input[type=radio]");
        if (radio) it.classList.toggle("is-active", radio.checked);
      });
      if (!item || !item.offsetWidth) { ind.style.opacity = "0"; return; }
      ind.style.opacity = "1";
      ind.style.width = item.offsetWidth + "px";
      ind.style.transform = "translateX(" + item.offsetLeft + "px)";
    }

    group.addEventListener("change", place);
    group.addEventListener("click", function () { window.requestAnimationFrame(place); });
    new MutationObserver(place).observe(group, { subtree: true, attributes: true, attributeFilter: ["class"] });
    if (window.ResizeObserver) new ResizeObserver(place).observe(group);
    place();
    window.requestAnimationFrame(function () {
      place();
      window.requestAnimationFrame(function () { ind.classList.remove("no-anim"); });
    });
  }

  function init(scope) {
    enhanceAll(scope);
    watchMenus(scope);
    (scope || document).querySelectorAll(SEG_SEL).forEach(enhanceSegment);
  }

  window.kidsMapEnhanceControls = init;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { init(document); });
  } else {
    init(document);
  }

  // Catalog swaps fragments via ajax; pick up anything new (batched per frame).
  var pending = false;
  new MutationObserver(function () {
    if (pending) return;
    pending = true;
    window.requestAnimationFrame(function () { pending = false; init(document); });
  }).observe(document.body || document.documentElement, { childList: true, subtree: true });
})();
