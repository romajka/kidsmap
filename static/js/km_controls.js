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

    // The layer may already be rendered by the server (no flash); otherwise draw it.
    var layer = track.querySelector(":scope > .kmr");
    var steps = isAge ? (max - min) : 6;
    if (!layer) {
      layer = el("div", "kmr", track);
      layer.setAttribute("aria-hidden", "true");
      var railNew = el("div", "kmr__rail", layer);
      el("div", "kmr__ticks", railNew);
      el("div", "kmr__fill", railNew);
      el("span", "kmr__bubble", el("div", "kmr__thumb kmr__thumb--from", layer));
      el("span", "kmr__bubble", el("div", "kmr__thumb kmr__thumb--to", layer));
      layer.style.setProperty("--kmr-steps", steps > 0 && steps <= 30 ? steps : 6);
    }
    var rail = layer.querySelector(".kmr__rail");
    var thumbs = [layer.querySelector(".kmr__thumb--from"), layer.querySelector(".kmr__thumb--to")];
    var bubbles = thumbs.map(function (t) { return t.querySelector(".kmr__bubble"); });
    var inputs = [from, to];

    var scale = track.querySelector(":scope > .kmr__scale");
    if (!scale) {
      scale = el("div", "kmr__scale", track);
      scale.setAttribute("aria-hidden", "true");
      el("span", "", scale);
      el("span", "", scale);
    }
    scale.children[0].textContent = format(min);
    scale.children[1].textContent = format(max);

    function format(v) {
      if (isPrice) return v + " " + (unit || "₼");
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
      bubbles[0].textContent = format(a);
      bubbles[1].textContent = format(b);
      // When thumbs are close, merge the bubbles to avoid overlap.
      var close = Math.abs(pb - pa) < 18;
      layer.classList.toggle("is-close", close);
      if (close) bubbles[1].textContent = a === b ? format(a) : format(a) + " – " + format(b);
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
    (scope || document).querySelectorAll(".range-filter-track, [data-kmr-track]").forEach(enhanceRange);
  }

  /* ---------- Dropdown option stagger index ---------- */
  var MENU_SEL = ".km-custom-select__menu, .km-sort-menu, .km-tree-dropdown, .mobile-quick-menu";
  var OPTION_SEL = ".km-custom-select__option, .km-sort-option, .km-tree-row, .mobile-quick-menu button, .mobile-quick-menu a";

  function indexMenu(menu) {
    var items = menu.querySelectorAll(OPTION_SEL);
    for (var i = 0; i < items.length; i++) {
      items[i].style.setProperty("--kmi", Math.min(i, 8));
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


  /* ---------- Catalog sidebar: category list, applied chips, head reset ---------- */
  function syncCatalogSidebar() {
    var list = document.querySelector("[data-km-cat-list]");
    if (list && list.dataset.kmInit !== "1") {
      list.dataset.kmInit = "1";
      var more = list.querySelector("[data-km-cat-more]");
      function setExpanded(on) {
        list.classList.toggle("is-expanded", on);
        if (!more) return;
        more.setAttribute("aria-expanded", on ? "true" : "false");
        var m = more.querySelector("[data-more-label]"), l = more.querySelector("[data-less-label]");
        if (m) m.hidden = on;
        if (l) l.hidden = !on;
      }
      if (more) more.addEventListener("click", function () { setExpanded(!list.classList.contains("is-expanded")); });
      // A chosen category further down the list stays visible.
      if (list.querySelector(".km-cat-item.is-extra.is-active")) setExpanded(true);
      list.addEventListener("click", function (e) {
        var item = e.target.closest && e.target.closest(".km-cat-item");
        if (!item) return;
        // Instant feedback; the page script confirms the same state.
        list.querySelectorAll(".km-cat-item").forEach(function (it) {
          var on = it === item;
          it.classList.toggle("is-active", on);
          it.setAttribute("aria-checked", on ? "true" : "false");
        });
      });
    }
    if (list) {
      list.querySelectorAll(".km-cat-item").forEach(function (it) {
        var on = it.classList.contains("is-active");
        if (it.getAttribute("aria-checked") !== (on ? "true" : "false")) it.setAttribute("aria-checked", on ? "true" : "false");
      });
    }

    // Applied filters: the results header owns them (it is refreshed on every filter change);
    // on desktop they are shown in the sidebar instead.
    var slot = document.querySelector("[data-km-side-chips]");
    if (slot) {
      var bar = document.querySelector(".catalog-top-stack .active-filter-chips");
      var html = bar ? bar.innerHTML.trim() : "";
      if (slot.dataset.kmHtml !== html) {
        slot.dataset.kmHtml = html;
        slot.innerHTML = html;
        slot.hidden = !html;
      }
      var headReset = document.querySelector("[data-km-head-reset]");
      if (headReset) headReset.hidden = !html;
    }
  }


  /* ---------- Place page: sticky column, phone bar, today in the week ---------- */
  function initPlaceDetail() {
    if (!document.body || !document.body.classList.contains("page-place_detail")) return;
    if (document.body.dataset.kdInit === "1") return;
    document.body.dataset.kdInit = "1";

    // Tall right column: let it scroll with the page, then stick with its bottom in view.
    var side = document.querySelector(".detail-side");
    if (side) {
      var placeSide = function () {
        var top = Math.min(96, window.innerHeight - side.offsetHeight - 16);
        side.style.setProperty("--kd-side-top", top + "px");
      };
      placeSide();
      window.addEventListener("resize", placeSide);
      if (window.ResizeObserver) new ResizeObserver(placeSide).observe(side);
    }

    // Phone bar hides while the card's own call button is on screen (no double buttons).
    var bar = document.querySelector(".detail-mobile-bar");
    var cta = document.querySelector(".detail-decision__cta");
    if (bar && cta && window.IntersectionObserver) {
      new IntersectionObserver(function (entries) {
        bar.classList.toggle("is-tucked", entries[0].isIntersecting);
      }, { threshold: 0.2 }).observe(cta);
    }

    // Week row on phones starts at today.
    var week = document.querySelector(".detail-week");
    var today = week && week.querySelector(".detail-week__day--today");
    if (week && today && week.scrollWidth > week.clientWidth) {
      week.scrollLeft = Math.max(0, today.offsetLeft - week.offsetLeft - 16);
    }
  }


  /* ---------- Specialist page: phone contact bar hides while the contact card is visible ---------- */
  function initSpecialistDetail() {
    var bar = document.querySelector(".sp-mobile-contact");
    var card = document.querySelector(".sp-contacts .sp-contact-actions");
    if (!bar || !card || bar.dataset.kspInit === "1" || !window.IntersectionObserver) return;
    bar.dataset.kspInit = "1";
    new IntersectionObserver(function (entries) {
      bar.classList.toggle("is-tucked", entries[0].isIntersecting);
    }, { threshold: 0.2 }).observe(card);
  }

  // Server lists form errors in field-declaration order; show them in the
  // order the fields appear on the page, so the list reads top to bottom.
  function orderErrorSummaries() {
    document.querySelectorAll("[data-error-summary] ul:not([data-km-ordered])").forEach(function (list) {
      list.setAttribute("data-km-ordered", "");
      var items = Array.prototype.slice.call(list.children);
      var target = function (li) {
        var a = li.querySelector("a[href^='#']");
        if (!a) return null;
        var el = null;
        try { el = document.querySelector(a.getAttribute("href")); } catch (e) { el = null; }
        var ref = a.getAttribute("data-error-field-ref");
        if (!el && ref) el = document.querySelector("[name='" + ref.replace(/'/g, "") + "']");
        return el;
      };
      var keyed = items.map(function (li, i) { return { li: li, el: target(li), i: i }; });
      keyed.sort(function (a, b) {
        if (!a.el || !b.el) return (a.el ? 1 : 0) - (b.el ? 1 : 0) || a.i - b.i;
        if (a.el === b.el) return a.i - b.i;
        return a.el.compareDocumentPosition(b.el) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
      });
      keyed.forEach(function (k) { list.appendChild(k.li); });
    });
  }

  // Home: the specialists' band and card row play their entrance once, when they
  // first scroll into view. Already visible on load: no animation.
  function initRevealFaces() {
    if (!("IntersectionObserver" in window)) return;
    if (reducedMotionOn()) return;
    document.querySelectorAll("[data-km-reveal-once]:not([data-km-revealed])").forEach(function (el) {
      el.setAttribute("data-km-revealed", "");
      if (el.getBoundingClientRect().top < window.innerHeight * 0.9) { el.classList.add("is-arrived"); return; }
      el.classList.add("is-waiting");
      var io = new IntersectionObserver(function (entries) {
        if (!entries[0].isIntersecting) return;
        el.classList.remove("is-waiting");
        el.classList.add("is-arrived");
        io.disconnect();
      }, { threshold: 0.3 });
      io.observe(el);
    });
  }

  // Home: arrows next to the specialists row scroll it by about one screen of cards.
  function initSpecialistRail() {
    document.querySelectorAll(".home-specialists--rail:not([data-km-rail])").forEach(function (section) {
      section.setAttribute("data-km-rail", "");
      var row = section.querySelector(".home-sp-row");
      if (!row) return;
      section.querySelectorAll("[data-sp-scroll]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var dir = parseInt(btn.getAttribute("data-sp-scroll"), 10) || 1;
          row.scrollBy({ left: dir * Math.max(240, row.clientWidth * 0.8), behavior: reducedMotionOn() ? "auto" : "smooth" });
        });
      });
    });
  }
  function reducedMotionOn() { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); }

  function init(scope) {
    orderErrorSummaries();
    initRevealFaces();
    initSpecialistRail();
    enhanceAll(scope);
    watchMenus(scope);
    (scope || document).querySelectorAll(SEG_SEL).forEach(enhanceSegment);
    syncCatalogSidebar();
    initPlaceDetail();
    initSpecialistDetail();
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
