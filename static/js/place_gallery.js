(function () {
  const DRAG_START_THRESHOLD = 6;
  const SWIPE_THRESHOLD_MIN = 56;
  const SWIPE_THRESHOLD_RATIO = 0.14;

  function normalizeIndex(nextIndex, length) {
    return ((nextIndex % length) + length) % length;
  }

  function mountGallery(gallery) {
    const viewport = gallery.querySelector("[data-gallery-viewport]");
    const track = gallery.querySelector("[data-gallery-track]");
    const slides = Array.from(gallery.querySelectorAll("[data-gallery-slide]"));
    const thumbs = Array.from(gallery.querySelectorAll("[data-gallery-thumb]"));
    const prevBtn = gallery.querySelector("[data-gallery-prev]");
    const nextBtn = gallery.querySelector("[data-gallery-next]");
    const currentEl = gallery.querySelector("[data-gallery-current]");
    const hint = gallery.querySelector("[data-gallery-hint]");

    if (!viewport || !track || !slides.length) return;

    let index = Math.max(
      0,
      slides.findIndex(function (slide) {
        return slide.classList.contains("is-active");
      })
    );
    let dragState = null;
    let suppressClick = false;
    let hintHidden = false;

    function getViewportWidth() {
      return Math.max(viewport.clientWidth, 1);
    }

    function hideHint() {
      if (!hint || hintHidden) return;
      hintHidden = true;
      hint.classList.add("is-hidden");
    }

    function updateUi() {
      slides.forEach(function (slide, slideIndex) {
        const isActive = slideIndex === index;
        slide.classList.toggle("is-active", isActive);
        slide.setAttribute("aria-hidden", isActive ? "false" : "true");
      });

      thumbs.forEach(function (thumb, thumbIndex) {
        const isActive = thumbIndex === index;
        thumb.classList.toggle("active", isActive);
        thumb.setAttribute("aria-selected", isActive ? "true" : "false");
        thumb.tabIndex = isActive ? 0 : -1;
      });

      if (currentEl) {
        currentEl.textContent = String(index + 1);
      }

      const activeThumb = thumbs[index];
      if (activeThumb) {
        activeThumb.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
          inline: "center",
        });
      }
    }

    function setTrackPosition(offsetX, animate) {
      track.style.transition = animate ? "" : "none";
      track.style.transform = "translate3d(" + offsetX + "px, 0, 0)";
    }

    function goTo(nextIndex, options) {
      const config = options || {};
      index = normalizeIndex(nextIndex, slides.length);
      const offsetX = -index * getViewportWidth();
      gallery.classList.toggle("is-settling", config.animate !== false);
      track.classList.remove("is-dragging");
      setTrackPosition(offsetX, config.animate !== false);
      updateUi();
    }

    function goRelative(step) {
      hideHint();
      goTo(index + step, { animate: true });
    }

    function handlePointerDown(event) {
      if (slides.length < 2) return;
      if (event.pointerType === "mouse" && event.button !== 0) return;

      hideHint();
      dragState = {
        pointerId: event.pointerId,
        startX: event.clientX,
        deltaX: 0,
        moved: false,
        width: getViewportWidth(),
      };

      gallery.classList.add("is-dragging");
      track.classList.add("is-dragging");
      setTrackPosition(-index * dragState.width, false);

      if (viewport.setPointerCapture) {
        viewport.setPointerCapture(event.pointerId);
      }
    }

    function handlePointerMove(event) {
      if (!dragState || event.pointerId !== dragState.pointerId) return;

      dragState.deltaX = event.clientX - dragState.startX;
      if (!dragState.moved && Math.abs(dragState.deltaX) > DRAG_START_THRESHOLD) {
        dragState.moved = true;
        suppressClick = true;
      }

      if (!dragState.moved) return;

      event.preventDefault();
      setTrackPosition(-index * dragState.width + dragState.deltaX, false);
    }

    function finishPointer(event) {
      if (!dragState || event.pointerId !== dragState.pointerId) return;

      if (viewport.releasePointerCapture && viewport.hasPointerCapture && viewport.hasPointerCapture(event.pointerId)) {
        viewport.releasePointerCapture(event.pointerId);
      }

      const deltaX = dragState.deltaX;
      const moved = dragState.moved;
      const threshold = Math.max(SWIPE_THRESHOLD_MIN, dragState.width * SWIPE_THRESHOLD_RATIO);
      dragState = null;

      gallery.classList.remove("is-dragging");

      if (moved && Math.abs(deltaX) >= threshold) {
        goTo(index + (deltaX < 0 ? 1 : -1), { animate: true });
      } else {
        goTo(index, { animate: true });
      }

      window.setTimeout(function () {
        suppressClick = false;
      }, 0);
    }

    function handleKeydown(event) {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        goRelative(-1);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        goRelative(1);
      } else if (event.key === "Home") {
        event.preventDefault();
        hideHint();
        goTo(0, { animate: true });
      } else if (event.key === "End") {
        event.preventDefault();
        hideHint();
        goTo(slides.length - 1, { animate: true });
      }
    }

    function createTouchHandlers() {
      let touchState = null;

      function handleTouchStart(event) {
        if (slides.length < 2) return;
        const touch = event.touches[0];
        if (!touch) return;

        hideHint();
        touchState = {
          startX: touch.clientX,
          startY: touch.clientY,
          deltaX: 0,
          deltaY: 0,
          moved: false,
          width: getViewportWidth(),
        };

        gallery.classList.add("is-dragging");
        track.classList.add("is-dragging");
        setTrackPosition(-index * touchState.width, false);
      }

      function handleTouchMove(event) {
        if (!touchState) return;
        const touch = event.touches[0];
        if (!touch) return;

        touchState.deltaX = touch.clientX - touchState.startX;
        touchState.deltaY = touch.clientY - touchState.startY;

        if (!touchState.moved) {
          if (Math.abs(touchState.deltaX) < DRAG_START_THRESHOLD) return;
          if (Math.abs(touchState.deltaY) > Math.abs(touchState.deltaX)) {
            touchState = null;
            gallery.classList.remove("is-dragging");
            track.classList.remove("is-dragging");
            return;
          }
          touchState.moved = true;
          suppressClick = true;
        }

        event.preventDefault();
        setTrackPosition(-index * touchState.width + touchState.deltaX, false);
      }

      function handleTouchEnd() {
        if (!touchState) return;
        const deltaX = touchState.deltaX;
        const moved = touchState.moved;
        const threshold = Math.max(SWIPE_THRESHOLD_MIN, touchState.width * SWIPE_THRESHOLD_RATIO);
        touchState = null;

        gallery.classList.remove("is-dragging");
        track.classList.remove("is-dragging");

        if (moved && Math.abs(deltaX) >= threshold) {
          goTo(index + (deltaX < 0 ? 1 : -1), { animate: true });
        } else {
          goTo(index, { animate: true });
        }

        window.setTimeout(function () {
          suppressClick = false;
        }, 0);
      }

      viewport.addEventListener("touchstart", handleTouchStart, { passive: true });
      viewport.addEventListener("touchmove", handleTouchMove, { passive: false });
      viewport.addEventListener("touchend", handleTouchEnd);
      viewport.addEventListener("touchcancel", handleTouchEnd);
    }

    thumbs.forEach(function (thumb) {
      thumb.addEventListener("click", function () {
        hideHint();
        goTo(Number(thumb.dataset.index || 0), { animate: true });
      });
    });

    if (prevBtn) {
      prevBtn.addEventListener("click", function () {
        goRelative(-1);
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener("click", function () {
        goRelative(1);
      });
    }

    viewport.addEventListener("pointerdown", handlePointerDown);
    viewport.addEventListener("pointermove", handlePointerMove);
    viewport.addEventListener("pointerup", finishPointer);
    viewport.addEventListener("pointercancel", finishPointer);
    viewport.addEventListener("keydown", handleKeydown);
    viewport.addEventListener("dragstart", function (event) {
      event.preventDefault();
    });
    viewport.addEventListener(
      "click",
      function (event) {
        if (!suppressClick) return;
        event.preventDefault();
        event.stopPropagation();
      },
      true
    );

    if (!("PointerEvent" in window)) {
      createTouchHandlers();
    }

    if (typeof ResizeObserver !== "undefined") {
      const resizeObserver = new ResizeObserver(function () {
        goTo(index, { animate: false });
      });
      resizeObserver.observe(viewport);
    } else {
      window.addEventListener(
        "resize",
        function () {
          goTo(index, { animate: false });
        },
        { passive: true }
      );
    }

    track.addEventListener("transitionend", function () {
      gallery.classList.remove("is-settling");
    });

    updateUi();
    goTo(index, { animate: false });
  }

  document.querySelectorAll("[data-gallery]").forEach(mountGallery);
})();
