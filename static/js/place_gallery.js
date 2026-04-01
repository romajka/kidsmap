(function () {
  function mountGallery(gallery) {
    const stage = gallery.querySelector("[data-gallery-stage]");
    const slides = Array.from(gallery.querySelectorAll("[data-gallery-slide]"));
    const thumbs = Array.from(gallery.querySelectorAll("[data-gallery-thumb]"));
    const prevBtn = gallery.querySelector("[data-gallery-prev]");
    const nextBtn = gallery.querySelector("[data-gallery-next]");
    const currentEl = gallery.querySelector("[data-gallery-current]");
    const hint = gallery.querySelector("[data-gallery-hint]");

    if (!stage || !slides.length) return;

    let index = Math.max(
      0,
      slides.findIndex(function (slide) {
        return slide.classList.contains("is-active");
      })
    );
    let scrollTimer = null;
    let dragState = null;
    let hintHidden = false;

    function hideHint() {
      if (!hint || hintHidden) return;
      hintHidden = true;
      hint.classList.add("is-hidden");
    }

    function updateUi(nextIndex) {
      index = nextIndex;
      slides.forEach(function (slide, slideIndex) {
        const isActive = slideIndex === index;
        slide.classList.toggle("is-active", isActive);
        slide.setAttribute("aria-hidden", isActive ? "false" : "true");
      });
      thumbs.forEach(function (thumb, thumbIndex) {
        thumb.classList.toggle("active", thumbIndex === index);
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

    function scrollToIndex(nextIndex, behavior) {
      const normalizedIndex = (nextIndex + slides.length) % slides.length;
      const targetSlide = slides[normalizedIndex];
      if (!targetSlide) return;

      stage.scrollTo({
        left: targetSlide.offsetLeft,
        behavior: behavior || "smooth",
      });
      updateUi(normalizedIndex);
    }

    function nearestIndex() {
      const currentScroll = stage.scrollLeft;
      let bestIndex = index;
      let bestDistance = Number.POSITIVE_INFINITY;

      slides.forEach(function (slide, slideIndex) {
        const distance = Math.abs(slide.offsetLeft - currentScroll);
        if (distance < bestDistance) {
          bestDistance = distance;
          bestIndex = slideIndex;
        }
      });

      return bestIndex;
    }

    function snapToNearest(behavior) {
      scrollToIndex(nearestIndex(), behavior || "smooth");
    }

    thumbs.forEach(function (thumb) {
      thumb.addEventListener("click", function () {
        hideHint();
        scrollToIndex(Number(thumb.dataset.index || 0), "smooth");
      });
    });

    if (prevBtn) {
      prevBtn.addEventListener("click", function () {
        hideHint();
        scrollToIndex(index - 1, "smooth");
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener("click", function () {
        hideHint();
        scrollToIndex(index + 1, "smooth");
      });
    }

    stage.addEventListener(
      "scroll",
      function () {
        hideHint();
        window.clearTimeout(scrollTimer);
        scrollTimer = window.setTimeout(function () {
          updateUi(nearestIndex());
        }, 70);
      },
      { passive: true }
    );

    stage.addEventListener(
      "touchstart",
      function () {
        hideHint();
      },
      { passive: true }
    );

    stage.addEventListener("keydown", function (event) {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        hideHint();
        scrollToIndex(index - 1, "smooth");
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        hideHint();
        scrollToIndex(index + 1, "smooth");
      }
    });

    stage.addEventListener("dragstart", function (event) {
      event.preventDefault();
    });

    stage.addEventListener("pointerdown", function (event) {
      if (slides.length < 2 || event.pointerType === "touch") return;
      hideHint();

      dragState = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startScrollLeft: stage.scrollLeft,
        moved: false,
      };

      stage.classList.add("is-dragging");
      if (stage.setPointerCapture) {
        stage.setPointerCapture(event.pointerId);
      }
    });

    stage.addEventListener("pointermove", function (event) {
      if (!dragState || event.pointerId !== dragState.pointerId) return;

      const deltaX = event.clientX - dragState.startX;
      if (Math.abs(deltaX) > 4) {
        dragState.moved = true;
      }
      stage.scrollLeft = dragState.startScrollLeft - deltaX;
    });

    function finishPointer(event) {
      if (!dragState || event.pointerId !== dragState.pointerId) return;

      if (stage.releasePointerCapture && stage.hasPointerCapture && stage.hasPointerCapture(event.pointerId)) {
        stage.releasePointerCapture(event.pointerId);
      }
      stage.classList.remove("is-dragging");

      const moved = dragState.moved;
      dragState = null;
      if (moved) {
        snapToNearest("smooth");
      }
    }

    stage.addEventListener("pointerup", finishPointer);
    stage.addEventListener("pointercancel", finishPointer);
    stage.addEventListener("mouseleave", function () {
      if (!dragState) return;
      stage.classList.remove("is-dragging");
    });

    updateUi(index);
    scrollToIndex(index, "auto");
  }

  document.querySelectorAll("[data-gallery]").forEach(mountGallery);
})();
