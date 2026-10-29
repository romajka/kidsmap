/**
 * KidsMap - Category & Specialization Strip Horizontal Scrolling Controller
 * Supports:
 * - Prev / Next floating arrow buttons with dynamic overflow detection
 * - Left & right fade gradient masks (prevents "eaten/cut-off" appearance)
 * - Mouse wheel vertical delta translation to smooth horizontal scrolling
 * - Grab-to-scroll (mouse drag) with click suppression on drag
 * - Auto-centering / auto-scroll for active category chip on page load
 */
(function () {
  'use strict';

  function initCategoryStrip(wrap) {
    if (!wrap || wrap.dataset.categoryStripInit === 'true') return;
    wrap.dataset.categoryStripInit = 'true';

    var strip = wrap.querySelector('.catalog-category-strip');
    if (!strip) return;

    var prevBtn = wrap.querySelector('[data-strip-prev]');
    var nextBtn = wrap.querySelector('[data-strip-next]');

    function updateOverflowState() {
      var sl = Math.ceil(strip.scrollLeft);
      var max = strip.scrollWidth - strip.clientWidth;
      var hasLeft = sl > 8;
      var hasRight = sl < (max - 8);

      wrap.classList.toggle('has-overflow-left', hasLeft);
      wrap.classList.toggle('has-overflow-right', hasRight);

      if (prevBtn) {
        prevBtn.hidden = !hasLeft;
      }
      if (nextBtn) {
        nextBtn.hidden = !hasRight;
      }
    }

    // 1. Arrow navigation buttons
    if (prevBtn) {
      prevBtn.addEventListener('click', function (e) {
        e.preventDefault();
        var step = Math.max(220, Math.floor(strip.clientWidth * 0.72));
        strip.scrollBy({ left: -step, behavior: 'smooth' });
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', function (e) {
        e.preventDefault();
        var step = Math.max(220, Math.floor(strip.clientWidth * 0.72));
        strip.scrollBy({ left: step, behavior: 'smooth' });
      });
    }

    // 2. Mouse wheel translation (vertical wheel -> horizontal scroll)
    strip.addEventListener('wheel', function (e) {
      if (Math.abs(e.deltaY) > Math.abs(e.deltaX) && strip.scrollWidth > strip.clientWidth) {
        var sl = strip.scrollLeft;
        var max = strip.scrollWidth - strip.clientWidth;
        var movingForward = e.deltaY > 0;
        var canScroll = (movingForward && sl < max - 1) || (!movingForward && sl > 1);
        if (canScroll) {
          e.preventDefault();
          strip.scrollLeft += e.deltaY;
          updateOverflowState();
        }
      }
    }, { passive: false });

    // 3. Pointer drag-to-scroll (desktop grab and scroll)
    var isDown = false;
    var startX = 0;
    var scrollStart = 0;
    var hasDragged = false;
    var dragThreshold = 6;

    strip.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return; // left click only
      isDown = true;
      hasDragged = false;
      startX = e.pageX;
      scrollStart = strip.scrollLeft;
    });

    window.addEventListener('mousemove', function (e) {
      if (!isDown) return;
      var delta = e.pageX - startX;
      if (Math.abs(delta) > dragThreshold) {
        hasDragged = true;
        strip.classList.add('is-dragging');
      }
      if (hasDragged) {
        strip.scrollLeft = scrollStart - delta;
      }
    });

    function endDrag() {
      if (!isDown) return;
      isDown = false;
      strip.classList.remove('is-dragging');
      if (hasDragged) {
        setTimeout(function () {
          hasDragged = false;
        }, 60);
      }
    }

    window.addEventListener('mouseup', endDrag);

    // Suppress child click when dragging
    strip.addEventListener('click', function (e) {
      if (hasDragged) {
        e.preventDefault();
        e.stopPropagation();
      }
    }, true);

    // 4. Auto-scroll active chip into view on load
    var activeChip = strip.querySelector('.catalog-category-chip.is-active, .catalog-category-chip[aria-selected="true"]');
    if (activeChip) {
      var chipLeft = activeChip.offsetLeft;
      var chipWidth = activeChip.offsetWidth;
      var stripWidth = strip.clientWidth;
      if (chipLeft + chipWidth > stripWidth || chipLeft < strip.scrollLeft) {
        strip.scrollTo({
          left: Math.max(0, chipLeft - Math.floor((stripWidth - chipWidth) / 2)),
          behavior: 'smooth'
        });
      }
    }

    strip.addEventListener('scroll', updateOverflowState, { passive: true });
    window.addEventListener('resize', updateOverflowState);

    // Initial check (and after webfonts/icons render)
    updateOverflowState();
    setTimeout(updateOverflowState, 100);
    setTimeout(updateOverflowState, 400);
  }

  function initAllStrips() {
    document.querySelectorAll('[data-catalog-categories-scroll]').forEach(initCategoryStrip);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAllStrips);
  } else {
    initAllStrips();
  }

  window.kidsMapInitCategoryStrip = initAllStrips;
})();
