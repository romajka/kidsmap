/* Place gallery: main slider + thumbnails + dots + fullscreen viewer.
 * - slide counter, thumbnails and dots stay in sync
 * - ← → keys work when the gallery is focused or hovered
 * - tap/click a photo opens a fullscreen viewer (swipe, pinch/double-tap zoom, Esc)
 * - neighbouring photos are preloaded so the next swipe never shows a blank
 */
(function () {
  "use strict";

  var reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var lang = (document.documentElement.lang || "az").slice(0, 2);
  var CLOSE = { az: "Bağla", ru: "Закрыть", en: "Close" }[lang] || "Close";

  var OPEN = { az: "Şəkli aç", ru: "Открыть фото", en: "Open photo" }[lang] || "Open photo";

  function preload(urls) {
    urls.forEach(function (url) {
      if (!url) return;
      var img = new Image();
      img.decoding = "async";
      img.src = url;
    });
  }

  function mountGallery(gallery) {
    if (typeof window.Swiper === "undefined") return;

    var mainEl = gallery.querySelector("[data-place-gallery-main]");
    var prevEl = gallery.querySelector("[data-place-gallery-prev]");
    var nextEl = gallery.querySelector("[data-place-gallery-next]");
    var currentEl = gallery.querySelector("[data-place-gallery-current]");
    var thumbStrip = gallery.querySelector(".place-gallery__thumbs");
    var thumbButtons = Array.prototype.slice.call(gallery.querySelectorAll("[data-place-gallery-thumb]"));
    if (!mainEl) return;

    var images = Array.prototype.slice.call(mainEl.querySelectorAll(".place-gallery__image"));
    var urls = images.map(function (img) { return img.currentSrc || img.src; });
    var count = images.length;

    // Loaded photos fade in instead of popping.
    images.forEach(function (img) {
      img.setAttribute("role", "button");
      img.setAttribute("aria-label", img.alt ? OPEN + " · " + img.alt : OPEN);
      img.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          showViewer();
        }
      });
      var slide = img.closest(".place-gallery__slide");
      if (!slide) return;
      if (img.complete && img.naturalWidth) slide.classList.add("is-loaded");
      else img.addEventListener("load", function () { slide.classList.add("is-loaded"); }, { once: true });
      img.addEventListener("error", function () { slide.classList.add("is-loaded"); }, { once: true });
    });

    // Dots / progress for phones (thumbnails are hidden there).
    var dots = null;
    if (count > 1) {
      dots = document.createElement("div");
      dots.className = "place-gallery__dots";
      dots.setAttribute("aria-hidden", "true");
      for (var i = 0; i < count; i++) dots.appendChild(document.createElement("i"));
      mainEl.appendChild(dots);
    }

    function syncUi(index, scroll) {
      images.forEach(function (img, idx) { img.tabIndex = idx === index ? 0 : -1; });
      if (currentEl) currentEl.textContent = String(index + 1);
      thumbButtons.forEach(function (thumb, idx) {
        var on = idx === index;
        thumb.classList.toggle("is-active", on);
        thumb.setAttribute("aria-current", on ? "true" : "false");
      });
      if (dots) {
        Array.prototype.forEach.call(dots.children, function (dot, idx) { dot.classList.toggle("is-active", idx === index); });
        // Many photos: keep the active dot centred in a short window.
        if (count > 7) dots.style.setProperty("--dots-shift", Math.max(0, Math.min(index - 3, count - 7)));
      }
      var activeThumb = thumbButtons[index];
      if (activeThumb && scroll !== false && thumbStrip) {
        var left = activeThumb.offsetLeft, right = left + activeThumb.offsetWidth;
        if (left < thumbStrip.scrollLeft || right > thumbStrip.scrollLeft + thumbStrip.clientWidth) {
          thumbStrip.scrollTo({ left: Math.max(0, left - (thumbStrip.clientWidth - activeThumb.offsetWidth) / 2), behavior: reducedMotion ? "auto" : "smooth" });
        }
      }
      preload([urls[index + 1], urls[index - 1]]);
    }

    var options = {
      slidesPerView: 1,
      spaceBetween: 0,
      speed: reducedMotion ? 0 : 380,
      threshold: 6,
      longSwipesRatio: 0.18,
      longSwipesMs: 220,
      resistanceRatio: 0.6,
      grabCursor: true,
      watchOverflow: true,
      keyboard: { enabled: true, onlyInViewport: true },
      a11y: {
        prevSlideMessage: prevEl ? prevEl.getAttribute("aria-label") : undefined,
        nextSlideMessage: nextEl ? nextEl.getAttribute("aria-label") : undefined
      },
      on: {
        init: function (swiper) { syncUi(swiper.realIndex, false); },
        slideChange: function (swiper) { syncUi(swiper.realIndex); }
      }
    };
    if (prevEl && nextEl) options.navigation = { prevEl: prevEl, nextEl: nextEl, disabledClass: "is-disabled" };

    var main = new window.Swiper(mainEl, options);

    thumbButtons.forEach(function (thumb, idx) {
      thumb.addEventListener("click", function () { main.slideTo(idx); });
    });

    function showViewer() {
      var keyboardWasEnabled = main.keyboard && main.keyboard.enabled;
      if (keyboardWasEnabled) main.keyboard.disable();
      openViewer(gallery, urls, main.realIndex, options.a11y, function (index) {
        main.slideTo(index, 0);
        if (keyboardWasEnabled) main.keyboard.enable();
        images[index].focus({ preventScroll: true });
      });
    }

    // Fullscreen viewer: a tap (not a swipe) on the photo.
    var downX = 0, downY = 0;
    mainEl.addEventListener("pointerdown", function (e) { downX = e.clientX; downY = e.clientY; });
    mainEl.addEventListener("click", function (e) {
      if (e.target.closest("button")) return;
      if (Math.abs(e.clientX - downX) > 8 || Math.abs(e.clientY - downY) > 8) return;
      showViewer();
    });
    mainEl.classList.add("is-zoomable");
  }

  function openViewer(gallery, urls, start, a11y, onClose) {
    var alt = (gallery.querySelector(".place-gallery__image") || {}).alt || "";
    var root = document.createElement("div");
    root.className = "place-viewer";
    root.setAttribute("role", "dialog");
    root.setAttribute("aria-modal", "true");
    root.setAttribute("aria-label", alt);
    root.innerHTML =
      '<div class="place-viewer__top"><span class="place-viewer__count"><b>' + (start + 1) + '</b> / ' + urls.length + '</span>' +
      '<button type="button" class="place-viewer__close" aria-label="' + CLOSE + '"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg></button></div>' +
      '<div class="place-viewer__swiper swiper"><div class="swiper-wrapper">' +
      urls.map(function (u) { return '<div class="swiper-slide"><div class="swiper-zoom-container"><img src="' + u.replace(/"/g, "&quot;") + '" alt="" decoding="async" draggable="false"></div></div>'; }).join("") +
      '</div>' +
      (urls.length > 1 ? '<button type="button" class="place-viewer__nav place-viewer__nav--prev"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 5 8 12l6.5 7"/></svg></button><button type="button" class="place-viewer__nav place-viewer__nav--next"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m9.5 5 6.5 7-6.5 7"/></svg></button>' : '') +
      '</div>';
    document.body.appendChild(root);
    var prevOverflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    var previous = root.querySelector(".place-viewer__nav--prev");
    var next = root.querySelector(".place-viewer__nav--next");
    if (previous && next) {
      previous.setAttribute("aria-label", a11y.prevSlideMessage);
      next.setAttribute("aria-label", a11y.nextSlideMessage);
    }

    var countEl = root.querySelector(".place-viewer__count b");
    var viewer = new window.Swiper(root.querySelector(".place-viewer__swiper"), {
      initialSlide: start,
      speed: reducedMotion ? 0 : 360,
      spaceBetween: 24,
      zoom: { maxRatio: 3 },
      keyboard: { enabled: true },
      a11y: a11y,
      navigation: urls.length > 1 ? { prevEl: previous, nextEl: next, disabledClass: "is-disabled" } : undefined,
      on: { slideChange: function (s) { countEl.textContent = String(s.realIndex + 1); } }
    });

    requestAnimationFrame(function () { root.classList.add("is-open"); });
    var closeBtn = root.querySelector(".place-viewer__close");
    closeBtn.focus({ preventScroll: true });

    function close() {
      if (root.classList.contains("is-closing")) return;
      document.removeEventListener("keydown", onKey, true);
      var index = viewer.realIndex;
      root.classList.remove("is-open");
      root.classList.add("is-closing");
      window.setTimeout(function () {
        viewer.destroy(true, true);
        root.remove();
        document.documentElement.style.overflow = prevOverflow;
        onClose(index);
      }, reducedMotion ? 0 : 220);
    }
    function onKey(e) {
      if (e.key === "Escape") { e.preventDefault(); close(); }
      if (e.key === "Tab") {
        var buttons = Array.from(root.querySelectorAll('button:not(:disabled):not([aria-disabled="true"])')).filter(function (button) {
          return window.getComputedStyle(button).display !== "none";
        });
        var first = buttons[0], last = buttons[buttons.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    }
    document.addEventListener("keydown", onKey, true);
    closeBtn.addEventListener("click", close);
    // Tap on the dark area around the photo closes.
    root.addEventListener("click", function (e) {
      if (e.target === root || e.target.classList.contains("swiper-zoom-container") || e.target.classList.contains("swiper-slide")) {
        if (!viewer.zoom || viewer.zoom.scale === 1) close();
      }
    });
  }

  document.querySelectorAll("[data-place-gallery]").forEach(mountGallery);
})();
