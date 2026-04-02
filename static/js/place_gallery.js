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
    const thumbButtons = Array.from(gallery.querySelectorAll("[data-place-gallery-thumb]"));

    if (!mainEl) return;

    function syncThumbs(activeIndex) {
      thumbButtons.forEach(function (thumb, idx) {
        const isActive = idx === activeIndex;
        thumb.classList.toggle("is-active", isActive);
        thumb.setAttribute("aria-current", isActive ? "true" : "false");
      });

      const activeThumb = thumbButtons[activeIndex];
      if (activeThumb) {
        activeThumb.scrollIntoView({
          behavior: "smooth",
          inline: "center",
          block: "nearest",
        });
      }
    }

    const mainSwiper = new window.Swiper(mainEl, {
      slidesPerView: 1,
      spaceBetween: 0,
      speed: 420,
      resistanceRatio: 0.82,
      grabCursor: true,
      watchOverflow: true,
      keyboard: {
        enabled: true,
        onlyInViewport: true,
      },
      navigation:
        prevEl && nextEl
          ? {
              prevEl: prevEl,
              nextEl: nextEl,
            }
          : undefined,
      on: {
        init: function (swiper) {
          updateCounter(swiper, currentEl);
          syncThumbs(swiper.realIndex);
        },
        slideChange: function (swiper) {
          updateCounter(swiper, currentEl);
          syncThumbs(swiper.realIndex);
        },
      },
    });

    thumbButtons.forEach(function (thumb, idx) {
      thumb.addEventListener("click", function () {
        mainSwiper.slideTo(idx);
      });
    });
  }

  document.querySelectorAll("[data-place-gallery]").forEach(mountGallery);
})();
