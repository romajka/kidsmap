(function () {
  function updateCounter(swiper, currentEl) {
    if (!currentEl) return;
    currentEl.textContent = String(swiper.realIndex + 1);
  }

  function mountGallery(gallery) {
    if (typeof window.Swiper === "undefined") return;

    const mainEl = gallery.querySelector("[data-place-gallery-main]");
    const prevEl = gallery.querySelector("[data-place-gallery-prev]");
    const nextEl = gallery.querySelector("[data-place-gallery-next]");
    const currentEl = gallery.querySelector("[data-place-gallery-current]");
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const thumbStrip = gallery.querySelector(".place-gallery__thumbs");
    const thumbButtons = Array.from(gallery.querySelectorAll("[data-place-gallery-thumb]"));

    if (!mainEl) return;

    function syncThumbs(activeIndex, scroll = true) {
      thumbButtons.forEach(function (thumb, idx) {
        const isActive = idx === activeIndex;
        thumb.classList.toggle("is-active", isActive);
        thumb.setAttribute("aria-current", isActive ? "true" : "false");
      });

      const activeThumb = thumbButtons[activeIndex];
      // Move only the thumbnail strip; scrollIntoView also moves the page.
      if (activeThumb && scroll && thumbStrip) {
        const left = activeThumb.offsetLeft;
        const right = left + activeThumb.offsetWidth;
        if (left < thumbStrip.scrollLeft || right > thumbStrip.scrollLeft + thumbStrip.clientWidth) {
          thumbStrip.scrollTo({
            left: Math.max(0, left - (thumbStrip.clientWidth - activeThumb.offsetWidth) / 2),
            behavior: reducedMotion ? "instant" : "smooth",
          });
        }
      }
    }

    const swiperOptions = {
      slidesPerView: 1,
      spaceBetween: 0,
      speed: reducedMotion ? 0 : 320,
      a11y: {
        prevSlideMessage: prevEl ? prevEl.getAttribute("aria-label") : undefined,
        nextSlideMessage: nextEl ? nextEl.getAttribute("aria-label") : undefined,
      },
      threshold: 8,
      touchRatio: 1,
      longSwipesRatio: 0.18,
      longSwipesMs: 220,
      shortSwipes: true,
      followFinger: true,
      resistanceRatio: 0.78,
      centeredSlides: false,
      grabCursor: true,
      simulateTouch: true,
      watchOverflow: true,
      allowTouchMove: true,
      autoHeight: false,
      on: {
        init: function (swiper) {
          updateCounter(swiper, currentEl);
          syncThumbs(swiper.realIndex, false);
        },
        slideChange: function (swiper) {
          updateCounter(swiper, currentEl);
          syncThumbs(swiper.realIndex);
        },
      },
    };

    if (prevEl && nextEl) {
      swiperOptions.navigation = {
        prevEl: prevEl,
        nextEl: nextEl,
      };
    }

    const mainSwiper = new window.Swiper(mainEl, swiperOptions);

    thumbButtons.forEach(function (thumb, idx) {
      thumb.addEventListener("click", function () {
        mainSwiper.slideTo(idx);
      });
    });
  }

  document.querySelectorAll("[data-place-gallery]").forEach(mountGallery);
})();
