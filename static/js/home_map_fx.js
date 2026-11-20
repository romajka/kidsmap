/* KidsMap · Home map explorer motion layer.
 * Adds scroll reveal, staggered cards, count-up, pointer spotlight, a
 * loading veil over the map and an animated full-screen mode.
 * It only decorates the DOM that home_map.js renders; data, filters,
 * selection and paging stay in home_map.js. */
(function () {
  "use strict";

  const root = document.querySelector("[data-home-map-explorer]");
  if (!root || root.dataset.kmfxReady) return;
  root.dataset.kmfxReady = "1";

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  const lang = (document.documentElement.lang || "az").slice(0, 2);
  const FALLBACK = {
    az: {expand: "Tam ekran", close: "Bağla", loading: "Xəritə yüklənir…", map: "Xəritə", list: "Siyahı"},
    ru: {expand: "На весь экран", close: "Закрыть", loading: "Загружаем карту…", map: "Карта", list: "Список"},
    en: {expand: "Full screen", close: "Close", loading: "Loading map…", map: "Map", list: "List"},
  };
  const fallback = FALLBACK[lang] || FALLBACK.az;
  const label = (key) => root.dataset["fx" + key.charAt(0).toUpperCase() + key.slice(1)] || fallback[key];

  const workspace = root.querySelector(".home-explorer-workspace");
  const container = root.querySelector(".home-map-container");
  const mapEl = document.getElementById("home-map");
  const list = root.querySelector("[data-home-map-list]");
  const tabs = Array.from(root.querySelectorAll("[data-home-explorer-tab]"));
  const mobile = window.matchMedia("(max-width: 767px)");

  const icon = {
    expand: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 3h6v6"/><path d="M9 21H3v-6"/><path d="M21 3l-7 7"/><path d="M3 21l7-7"/></svg>',
    close: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
  };

  root.classList.add("kmfx");

  /* ── 1. Scroll reveal ─────────────────────────────────────────────── */
  const revealTargets = [
    ".home-map-eyebrow-row", ".home-map-head h2", ".home-map-subtitle", ".home-map-head-action",
    ".home-hero-search-area", ".home-map-result-status", ".home-explorer-tabs",
    ".home-explorer-list-panel", ".home-explorer-map-panel", ".home-map-pagination",
  ];
  let order = 0;
  revealTargets.forEach((selector) => {
    root.querySelectorAll(":scope " + selector).forEach((el) => {
      if (el.closest(".kmfx-bar")) return;
      el.classList.add("kmfx-reveal");
      el.style.setProperty("--kmfx-i", String(order++));
    });
  });

  function revealNow() {
    if (root.classList.contains("kmfx-in")) return;
    root.classList.add("kmfx-in");
    countUpInitial();
    window.setTimeout(() => root.classList.add("kmfx-settled"), 1700);
  }
  if (reduced.matches || typeof IntersectionObserver !== "function") {
    root.classList.add("kmfx-in", "kmfx-settled");
  } else {
    root.classList.add("kmfx-armed");
    const io = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) { io.disconnect(); revealNow(); }
    }, {threshold: 0.12, rootMargin: "0px 0px -8% 0px"});
    io.observe(root);
    // Deep links (#home-map-section) and very tall phones: never leave it hidden.
    window.setTimeout(() => { if (root.getBoundingClientRect().top < window.innerHeight) revealNow(); }, 1200);
  }

  /* ── 2. Count-up for the live counter ─────────────────────────────── */
  const counters = Array.from(root.querySelectorAll("[data-home-map-live-count]"));
  const tween = new WeakMap();
  function runCount(el, from, to, duration) {
    if (reduced.matches || from === to || !Number.isFinite(from) || !Number.isFinite(to)) {
      el.dataset.kmfxValue = String(to);
      el.textContent = String(to);
      return;
    }
    const start = performance.now();
    const token = {};
    tween.set(el, token);
    const step = (now) => {
      if (tween.get(el) !== token) return;
      const t = Math.min(1, (now - start) / duration);
      const eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
      const value = Math.round(from + (to - from) * eased);
      el.dataset.kmfxValue = String(value);
      el.textContent = String(value);
      if (t < 1) window.requestAnimationFrame(step);
    };
    window.requestAnimationFrame(step);
    const pill = el.closest(".home-map-live-pill");
    if (pill) { pill.classList.remove("kmfx-bump"); void pill.offsetWidth; pill.classList.add("kmfx-bump"); }
  }
  function countUpInitial() {
    counters.forEach((el) => {
      const target = parseInt(el.textContent, 10);
      if (Number.isFinite(target)) runCount(el, 0, target, 1300);
    });
  }
  if (typeof MutationObserver === "function") {
    counters.forEach((el) => {
      new MutationObserver(() => {
        const shown = el.textContent.trim();
        if (shown === el.dataset.kmfxValue) return; // our own frame
        const next = parseInt(shown, 10);
        const previous = parseInt(el.dataset.kmfxValue || "0", 10);
        if (Number.isFinite(next)) runCount(el, previous, next, 650);
      }).observe(el, {childList: true, characterData: true, subtree: true});
    });
  }

  /* ── 3. Staggered result cards ────────────────────────────────────── */
  let renderedIds = new Set();
  function rowId(row) { return row.querySelector("[data-home-map-member-id]")?.dataset.homeMapMemberId || ""; }
  function decorateRows() {
    if (!list) return;
    const rows = Array.from(list.children);
    const nextIds = new Set();
    let n = 0;
    rows.forEach((row) => {
      const id = rowId(row);
      nextIds.add(id);
      if (row.dataset.kmfxCard) return;
      row.dataset.kmfxCard = "1";
      if (!renderedIds.has(id) && !reduced.matches) {
        row.style.setProperty("--kmfx-card", String(Math.min(n++, 9)));
        row.classList.add("kmfx-card-in");
        row.addEventListener("animationend", () => row.classList.remove("kmfx-card-in"), {once: true});
      }
    });
    renderedIds = nextIds;
  }
  if (list && typeof MutationObserver === "function") {
    new MutationObserver(decorateRows).observe(list, {childList: true});
    decorateRows();
  }

  // Pointer spotlight on cards (desktop only, one listener for the list).
  if (list) {
    list.addEventListener("pointermove", (event) => {
      if (!finePointer.matches) return;
      const card = event.target.closest?.(".home-explorer-card");
      if (!card) return;
      const box = card.getBoundingClientRect();
      card.style.setProperty("--kmfx-mx", (event.clientX - box.left) + "px");
      card.style.setProperty("--kmfx-my", (event.clientY - box.top) + "px");
    }, {passive: true});
  }

  /* ── 4. Mobile panels: animate the view that becomes visible ──────── */
  root.querySelectorAll("[data-home-explorer-list], [data-home-explorer-map]").forEach((panel) => {
    if (typeof MutationObserver !== "function") return;
    new MutationObserver(() => {
      if (panel.hidden || reduced.matches) return;
      panel.classList.remove("kmfx-panel-in"); void panel.offsetWidth; panel.classList.add("kmfx-panel-in");
    }).observe(panel, {attributes: true, attributeFilter: ["hidden"]});
    panel.addEventListener("animationend", (e) => { if (e.target === panel) panel.classList.remove("kmfx-panel-in"); });
  });

  /* ── 5. Loading veil over the map ─────────────────────────────────── */
  if (container && mapEl) {
    const veil = document.createElement("div");
    veil.className = "kmfx-veil";
    veil.setAttribute("aria-hidden", "true");
    veil.innerHTML = '<span class="kmfx-veil-grid"></span><span class="kmfx-veil-radar"><i></i><i></i><i></i><b></b></span><span class="kmfx-veil-text"></span>';
    veil.querySelector(".kmfx-veil-text").textContent = label("loading");
    container.prepend(veil);
    const ready = () => !!mapEl.querySelector(".gm-style, .leaflet-pane") || mapEl.classList.contains("leaflet-container") || mapEl.dataset.mapUnavailable === "1" || !!mapEl.querySelector("iframe");
    let done = false;
    const lift = () => {
      if (done) return; done = true;
      window.setTimeout(() => {
        veil.classList.add("is-leaving");
        container.classList.add("kmfx-map-ready");
        // One-off focus-in; the class is dropped so no filter stays on the live map.
        if (!reduced.matches) {
          container.classList.add("kmfx-map-focus");
          window.setTimeout(() => container.classList.remove("kmfx-map-focus"), 1100);
        }
        window.setTimeout(() => veil.remove(), 700);
      }, 450);
    };
    if (ready()) lift();
    else if (typeof MutationObserver === "function") {
      const mo = new MutationObserver(() => { if (ready()) { mo.disconnect(); lift(); } });
      mo.observe(mapEl, {childList: true, subtree: true, attributes: true, attributeFilter: ["class", "data-map-initialized"]});
      // Map note / fallback text means nothing more is coming.
      window.setTimeout(() => { if (!done && mapEl.dataset.mapInitialized !== "1" && mapEl.textContent.trim()) { mo.disconnect(); lift(); } }, 9000);
    }
  }

  /* ── 6. Full-screen explorer ──────────────────────────────────────── */
  if (!workspace || !container) return;

  const expandBtn = document.createElement("button");
  expandBtn.type = "button";
  expandBtn.className = "kmfx-expand";
  expandBtn.setAttribute("aria-label", label("expand"));
  expandBtn.setAttribute("aria-expanded", "false");
  expandBtn.innerHTML = icon.expand + '<span class="kmfx-expand-text"></span>';
  expandBtn.querySelector(".kmfx-expand-text").textContent = label("expand");
  container.append(expandBtn);

  const bar = document.createElement("div");
  bar.className = "kmfx-bar";
  const heading = root.querySelector(".home-map-head h2")?.textContent.trim() || "";
  bar.innerHTML =
    '<div class="kmfx-bar-title"><span class="kmfx-bar-dot" aria-hidden="true"></span><strong></strong><span class="kmfx-bar-count"></span></div>' +
    '<div class="kmfx-bar-switch" role="group"><button type="button" data-kmfx-view="map"></button><button type="button" data-kmfx-view="list"></button></div>' +
    '<button type="button" class="kmfx-close"></button>';
  bar.querySelector("strong").textContent = heading;
  bar.querySelector('[data-kmfx-view="map"]').textContent = tabs.find((t) => t.dataset.homeExplorerTab === "map")?.textContent.trim() || label("map");
  bar.querySelector('[data-kmfx-view="list"]').textContent = tabs.find((t) => t.dataset.homeExplorerTab === "list")?.textContent.trim() || label("list");
  const closeBtn = bar.querySelector(".kmfx-close");
  closeBtn.innerHTML = icon.close + '<span></span>';
  closeBtn.querySelector("span").textContent = label("close");
  closeBtn.setAttribute("aria-label", label("close"));
  workspace.prepend(bar);

  const barCount = bar.querySelector(".kmfx-bar-count");
  function syncBar() {
    const counter = counters[0];
    const pillText = root.querySelector(".home-map-live-text")?.textContent.trim() || "";
    if (counter) barCount.textContent = (counter.dataset.kmfxValue || counter.textContent.trim()) + " " + pillText;
    const view = root.dataset.explorerView || "map";
    bar.querySelectorAll("[data-kmfx-view]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.kmfxView === view)));
  }
  bar.querySelectorAll("[data-kmfx-view]").forEach((b) => {
    b.addEventListener("click", () => {
      tabs.find((t) => t.dataset.homeExplorerTab === b.dataset.kmfxView)?.click();
      syncBar();
    });
  });
  if (typeof MutationObserver === "function") {
    new MutationObserver(syncBar).observe(root, {attributes: true, attributeFilter: ["data-explorer-view"]});
  }

  const placeholder = document.createElement("div");
  placeholder.className = "kmfx-placeholder";
  placeholder.setAttribute("aria-hidden", "true");
  let expanded = false;
  let ownHistory = false;
  let lastFocus = null;

  function googleMap() { return mapEl && mapEl.__kidsMapGoogle; }
  function nudgeMap() {
    mapEl?.dispatchEvent(new Event("kidsmap:home-map-visible"));
    window.dispatchEvent(new Event("resize"));
  }
  function setOrigin() {
    const box = container.getBoundingClientRect();
    const vw = window.innerWidth, vh = window.innerHeight;
    workspace.style.setProperty("--kmfx-t", Math.max(0, box.top) + "px");
    workspace.style.setProperty("--kmfx-r", Math.max(0, vw - box.right) + "px");
    workspace.style.setProperty("--kmfx-b", Math.max(0, vh - box.bottom) + "px");
    workspace.style.setProperty("--kmfx-l", Math.max(0, box.left) + "px");
  }

  function open() {
    if (expanded) return;
    expanded = true;
    lastFocus = document.activeElement;
    setOrigin();
    // Placeholder keeps the page from jumping while the workspace is lifted out.
    placeholder.style.height = workspace.offsetHeight + "px";
    workspace.before(placeholder);
    root.classList.add("kmfx-expanded");
    document.documentElement.classList.add("kmfx-lock");
    expandBtn.setAttribute("aria-expanded", "true");
    workspace.setAttribute("role", "dialog");
    workspace.setAttribute("aria-modal", "true");
    workspace.setAttribute("aria-label", heading);
    // Full screen: one finger pans, pinch zooms; on phones the +/- buttons
    // would sit under the top bar, and pinch already does their job.
    googleMap()?.setOptions?.({gestureHandling: "greedy", zoomControl: !mobile.matches});
    syncBar();
    if (!reduced.matches) {
      workspace.classList.add("kmfx-opening");
      workspace.addEventListener("animationend", function done(e) {
        if (e.target !== workspace) return;
        workspace.removeEventListener("animationend", done);
        workspace.classList.remove("kmfx-opening");
        nudgeMap();
      });
    }
    nudgeMap();
    window.requestAnimationFrame(nudgeMap);
    closeBtn.focus({preventScroll: true});
    try { history.pushState({kmfxMap: true}, ""); ownHistory = true; } catch (e) { ownHistory = false; }
  }

  function close(fromHistory) {
    if (!expanded) return;
    expanded = false;
    const finish = () => {
      placeholder.remove();
      workspace.classList.remove("kmfx-closing");
      root.classList.remove("kmfx-expanded");
      document.documentElement.classList.remove("kmfx-lock");
      workspace.removeAttribute("role");
      workspace.removeAttribute("aria-modal");
      workspace.removeAttribute("aria-label");
      googleMap()?.setOptions?.({gestureHandling: "cooperative", zoomControl: true});
      nudgeMap();
      window.requestAnimationFrame(nudgeMap);
      (lastFocus && lastFocus.isConnected ? lastFocus : expandBtn).focus({preventScroll: true});
    };
    expandBtn.setAttribute("aria-expanded", "false");
    if (reduced.matches) finish();
    else {
      // Collapse back to where the map sits in the page (--kmfx-t/r/b/l).
      workspace.classList.add("kmfx-closing");
      let called = false;
      const once = () => { if (!called) { called = true; finish(); } };
      workspace.addEventListener("animationend", function done(e) {
        if (e.target !== workspace) return;
        workspace.removeEventListener("animationend", done);
        once();
      });
      window.setTimeout(once, 600);
    }
    if (!fromHistory && ownHistory) { ownHistory = false; try { history.back(); } catch (e) { /* ignore */ } }
    ownHistory = false;
  }

  expandBtn.addEventListener("click", (event) => { event.stopPropagation(); open(); });
  closeBtn.addEventListener("click", () => close(false));
  window.addEventListener("popstate", () => { if (expanded) close(true); });
  document.addEventListener("keydown", (event) => {
    if (!expanded) return;
    if (event.key === "Escape") {
      // Let an open info window close first.
      if (mapEl?.querySelector(".gm-style-iw, .leaflet-popup")) return;
      event.preventDefault();
      close(false);
    } else if (event.key === "Tab") {
      const focusable = Array.from(workspace.querySelectorAll('button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])'))
        .filter((el) => el.offsetParent !== null || el === document.activeElement);
      if (!focusable.length) return;
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  // Picking a place in the full-screen list on a phone jumps to the map view;
  // home_map.js already does this through the tabs, the bar just follows.
  mobile.addEventListener?.("change", syncBar);
})();
