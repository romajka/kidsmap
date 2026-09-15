/**
 * KidsMap Modern Header & Mobile Drawer Controller
 * Handles mobile slide-over drawer, accessible dropdowns, and scroll elevation.
 */
(function () {
  'use strict';

  function initKidsMapHeader() {
    const header = document.getElementById('km-site-header');
    const drawer = document.getElementById('km-mobile-drawer');
    const burgerOpenBtn = document.getElementById('km-burger-open');
    const burgerCloseBtn = document.getElementById('km-burger-close');
    const drawerBackdrop = document.getElementById('km-drawer-backdrop');

    /* ── 1. Scroll State Elevation ── */
    if (header) {
      let isScrolled = false;
      let ticking = false;

      function onScroll() {
        const scrolled = window.scrollY > 10;
        if (scrolled !== isScrolled) {
          isScrolled = scrolled;
          header.classList.toggle('is-scrolled', isScrolled);
        }
        ticking = false;
      }

      window.addEventListener('scroll', function () {
        if (!ticking) {
          window.requestAnimationFrame(onScroll);
          ticking = true;
        }
      }, { passive: true });

      // Initial check
      onScroll();
    }

    /* ── 2. Mobile Drawer Controls ── */
    if (drawer && burgerOpenBtn) {
      let previousActiveElement = null;

      function openDrawer() {
        previousActiveElement = document.activeElement;
        drawer.classList.add('is-active');
        drawer.setAttribute('aria-hidden', 'false');
        burgerOpenBtn.setAttribute('aria-expanded', 'true');
        if (header) header.classList.add('is-drawer-open');
        document.body.classList.add('km-drawer-locked');
        document.body.style.overflow = 'hidden';

        // Focus close button on open
        if (burgerCloseBtn) {
          setTimeout(function () {
            burgerCloseBtn.focus();
          }, 50);
        }
      }

      function closeDrawer() {
        if (!drawer.classList.contains('is-active')) return;

        drawer.classList.remove('is-active');
        drawer.setAttribute('aria-hidden', 'true');
        burgerOpenBtn.setAttribute('aria-expanded', 'false');
        if (header) header.classList.remove('is-drawer-open');
        document.body.classList.remove('km-drawer-locked');
        document.body.style.overflow = '';

        if (previousActiveElement && typeof previousActiveElement.focus === 'function' && !drawer.contains(previousActiveElement)) {
          previousActiveElement.focus();
        } else if (burgerOpenBtn && typeof burgerOpenBtn.focus === 'function') {
          burgerOpenBtn.focus();
        }
      }

      burgerOpenBtn.addEventListener('click', function (e) {
        e.preventDefault();
        if (drawer.classList.contains('is-active')) {
          closeDrawer();
        } else {
          openDrawer();
        }
      });

      if (burgerCloseBtn) {
        burgerCloseBtn.addEventListener('click', function (e) {
          e.preventDefault();
          closeDrawer();
        });
      }

      if (drawerBackdrop) {
        drawerBackdrop.addEventListener('click', function () {
          closeDrawer();
        });
        drawerBackdrop.addEventListener('touchstart', function (e) {
          e.preventDefault();
          closeDrawer();
        }, { passive: false });
      }

      // Close on ESC key or Trap Focus
      document.addEventListener('keydown', function (e) {
        if (!drawer.classList.contains('is-active')) return;

        if (e.key === 'Escape') {
          closeDrawer();
          return;
        }

        if (e.key === 'Tab') {
          const focusable = drawer.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          if (!focusable.length) return;

          const first = focusable[0];
          const last = focusable[focusable.length - 1];

          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      });
    }

    /* ── 3. Desktop Dropdown Menus ── */
    const dropdownWrappers = document.querySelectorAll('[data-dropdown]');

    dropdownWrappers.forEach(function (wrapper) {
      const trigger = wrapper.querySelector('[data-dropdown-trigger]');
      const menu = wrapper.querySelector('[data-dropdown-menu]');
      if (!trigger || !menu) return;

      function toggleDropdown(open) {
        const shouldOpen = typeof open === 'boolean' ? open : !wrapper.classList.contains('is-open');

        // Close other dropdowns first
        if (shouldOpen) {
          dropdownWrappers.forEach(function (other) {
            if (other !== wrapper) {
              other.classList.remove('is-open');
              const otherTrigger = other.querySelector('[data-dropdown-trigger]');
              if (otherTrigger) otherTrigger.setAttribute('aria-expanded', 'false');
            }
          });
        }

        wrapper.classList.toggle('is-open', shouldOpen);
        trigger.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
      }

      trigger.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        toggleDropdown();
      });

      // Keyboard navigation in menu
      wrapper.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && wrapper.classList.contains('is-open')) {
          e.preventDefault();
          toggleDropdown(false);
          trigger.focus();
        }
      });
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', function (e) {
      dropdownWrappers.forEach(function (wrapper) {
        if (wrapper.classList.contains('is-open') && !wrapper.contains(e.target)) {
          wrapper.classList.remove('is-open');
          const trigger = wrapper.querySelector('[data-dropdown-trigger]');
          if (trigger) trigger.setAttribute('aria-expanded', 'false');
        }
      });
    });

    /* ── 4. Animated Language Switcher Slider ── */
    const langSwitcher = document.querySelector('[data-lang-switcher]');
    if (langSwitcher) {
      const langBtns = Array.from(langSwitcher.querySelectorAll('.km-drawer-lang-btn'));
      let isNavigating = false;

      function selectLanguage(targetBtn) {
        if (!targetBtn || isNavigating) return;
        const targetIndex = targetBtn.getAttribute('data-lang-index');
        if (targetIndex === null) return;

        const currentIndex = langSwitcher.style.getPropertyValue('--lang-index').trim();
        if (targetIndex === currentIndex && targetBtn.classList.contains('active')) {
          return;
        }

        isNavigating = true;
        const targetUrl = targetBtn.getAttribute('href');

        // Trigger smooth glide animation
        langSwitcher.classList.add('is-animating');
        langSwitcher.style.setProperty('--lang-index', targetIndex);

        // Update button visual states
        langBtns.forEach(function (btn) {
          const isActive = btn === targetBtn;
          btn.classList.toggle('active', isActive);
          btn.setAttribute('aria-checked', isActive ? 'true' : 'false');
        });

        // Delay navigation slightly so user sees the fluid slider spring animation
        setTimeout(function () {
          if (targetUrl) {
            window.location.href = targetUrl;
          } else {
            isNavigating = false;
            langSwitcher.classList.remove('is-animating');
          }
        }, 260);
      }

      langBtns.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          selectLanguage(btn);
        });
      });

      // Touch swipe support across segmented pills
      let touchStartX = 0;
      let touchStartIndex = 0;
      let isTouching = false;

      langSwitcher.addEventListener('touchstart', function (e) {
        if (e.touches.length !== 1 || isNavigating) return;
        touchStartX = e.touches[0].clientX;
        const currentActive = langSwitcher.querySelector('.km-drawer-lang-btn.active');
        touchStartIndex = currentActive ? parseInt(currentActive.getAttribute('data-lang-index') || '0', 10) : 0;
        isTouching = true;
      }, { passive: true });

      langSwitcher.addEventListener('touchmove', function (e) {
        if (!isTouching || isNavigating || e.touches.length !== 1) return;
        const touchCurrentX = e.touches[0].clientX;
        const diffX = touchCurrentX - touchStartX;
        const rect = langSwitcher.getBoundingClientRect();
        const itemWidth = rect.width / 3;

        if (Math.abs(diffX) > itemWidth * 0.45) {
          const step = diffX > 0 ? 1 : -1;
          const nextIndex = Math.max(0, Math.min(2, touchStartIndex + step));
          if (nextIndex !== touchStartIndex) {
            const nextBtn = langBtns[nextIndex];
            if (nextBtn) {
              isTouching = false;
              selectLanguage(nextBtn);
            }
          }
        }
      }, { passive: true });

      langSwitcher.addEventListener('touchend', function () {
        isTouching = false;
      }, { passive: true });
    }
  }

  // Initialize once DOM is loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initKidsMapHeader);
  } else {
    initKidsMapHeader();
  }
})();
