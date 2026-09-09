(function () {
  const DRAG_THRESHOLD_MIN = 18;
  const DRAG_THRESHOLD_RATIO = 0.06;
  const SWIPE_VELOCITY_THRESHOLD = 0.35;
  const TRACK_TRANSITION = "transform 420ms cubic-bezier(0.25, 1, 0.35, 1)";

  function mountHeroSlider(slider) {
    const viewport = slider.querySelector("[data-home-hero-slider-viewport]");
    const track = slider.querySelector("[data-home-hero-slider-track]");
    const slides = Array.from(slider.querySelectorAll("[data-home-hero-slide]"));
    const dots = Array.from(slider.querySelectorAll("[data-home-hero-slider-dot]"));
    const prevButton = slider.querySelector("[data-home-hero-slider-prev]");
    const nextButton = slider.querySelector("[data-home-hero-slider-next]");

    if (!viewport || !track || slides.length < 2) return;

    let currentIndex = 0;
    let slideWidth = viewport.getBoundingClientRect().width || viewport.clientWidth || 1;
    let dragStartX = 0;
    let dragDeltaX = 0;
    let dragLastX = 0;
    let dragLastTime = 0;
    let dragVelocityX = 0;
    let isDragging = false;
    let activePointerId = null;
    let autoPlayTimer = null;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    function clampIndex(index) {
      if (index < 0) return slides.length - 1;
      if (index >= slides.length) return 0;
      return index;
    }

    function setTrackPosition(offsetPx, withTransition) {
      const appliedOffset = Math.round(offsetPx * 100) / 100;
      track.style.transition = withTransition ? TRACK_TRANSITION : "none";
      track.style.transform = "translate3d(" + appliedOffset + "px, 0, 0)";
    }

    function syncDots() {
      dots.forEach(function (dot, index) {
        const isActive = index === currentIndex;
        dot.classList.toggle("is-active", isActive);
        dot.setAttribute("aria-current", isActive ? "true" : "false");
      });
    }

    function goToSlide(nextIndex, withTransition) {
      currentIndex = clampIndex(nextIndex);
      setTrackPosition(-currentIndex * slideWidth, withTransition !== false);
      syncDots();
    }

    function recalculateWidth() {
      slideWidth = viewport.getBoundingClientRect().width || viewport.clientWidth || 1;
      goToSlide(currentIndex, false);
    }

    function startAutoPlay() {
      if (reducedMotion.matches || slides.length < 2) return;
      stopAutoPlay();
      autoPlayTimer = setInterval(function () {
        if (!isDragging && !slider.matches(":hover")) {
          goToSlide(currentIndex + 1, true);
        }
      }, 5000);
    }

    function stopAutoPlay() {
      if (autoPlayTimer) {
        clearInterval(autoPlayTimer);
        autoPlayTimer = null;
      }
    }

    function finishDrag() {
      if (!isDragging) return;

      const threshold = Math.max(DRAG_THRESHOLD_MIN, slideWidth * DRAG_THRESHOLD_RATIO);
      const nextIndex =
        Math.abs(dragDeltaX) >= threshold ||
        (Math.abs(dragVelocityX) >= SWIPE_VELOCITY_THRESHOLD && Math.abs(dragDeltaX) >= 8)
          ? currentIndex + (dragDeltaX < 0 ? 1 : -1)
          : currentIndex;

      isDragging = false;
      dragDeltaX = 0;
      dragLastX = 0;
      dragLastTime = 0;
      dragVelocityX = 0;
      activePointerId = null;
      viewport.classList.remove("is-dragging");
      goToSlide(nextIndex, true);
      startAutoPlay();
    }

    if (prevButton) {
      prevButton.addEventListener("click", function () {
        goToSlide(currentIndex - 1, true);
        startAutoPlay();
      });
    }

    if (nextButton) {
      nextButton.addEventListener("click", function () {
        goToSlide(currentIndex + 1, true);
        startAutoPlay();
      });
    }

    dots.forEach(function (dot) {
      dot.addEventListener("click", function () {
        const nextIndex = Number(dot.dataset.slideIndex || 0);
        goToSlide(nextIndex, true);
        startAutoPlay();
      });
    });

    slider.addEventListener("mouseenter", stopAutoPlay);
    slider.addEventListener("mouseleave", startAutoPlay);
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stopAutoPlay();
      else startAutoPlay();
    });

    viewport.addEventListener("pointerdown", function (event) {
      if (event.button !== undefined && event.button !== 0) return;

      isDragging = true;
      stopAutoPlay();
      dragStartX = event.clientX;
      dragLastX = event.clientX;
      dragLastTime = event.timeStamp || Date.now();
      dragDeltaX = 0;
      dragVelocityX = 0;
      activePointerId = event.pointerId;
      viewport.classList.add("is-dragging");
      track.style.transition = "none";

      if (viewport.setPointerCapture && activePointerId !== null) {
        viewport.setPointerCapture(activePointerId);
      }
    });

    viewport.addEventListener("pointermove", function (event) {
      if (!isDragging || (activePointerId !== null && event.pointerId !== activePointerId)) return;

      const now = event.timeStamp || Date.now();
      const elapsed = Math.max(1, now - dragLastTime);
      dragVelocityX = (event.clientX - dragLastX) / elapsed;
      dragDeltaX = event.clientX - dragStartX;
      dragLastX = event.clientX;
      dragLastTime = now;
      setTrackPosition(-currentIndex * slideWidth + dragDeltaX, false);
    });

    viewport.addEventListener("pointerup", function (event) {
      if (!isDragging || (activePointerId !== null && event.pointerId !== activePointerId)) return;
      finishDrag();
    });

    viewport.addEventListener("pointercancel", finishDrag);
    viewport.addEventListener("lostpointercapture", finishDrag);
    window.addEventListener("resize", recalculateWidth, { passive: true });

    recalculateWidth();
    startAutoPlay();
  }

  document.querySelectorAll("[data-home-hero-slider]").forEach(mountHeroSlider);
})();
