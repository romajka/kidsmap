/**
 * KidsMap - Public Organization Page Interactivity
 * Handles:
 * - Description clamp & "Read more" toggle
 * - Fast client-side branch filtering (district, direction/activity, keyword)
 * - Empty filter state & reset controls
 * - Sticky section navigation & scroll spy
 * - Smooth scroll & focus on "Choose a branch"
 */
(function () {
  'use strict';

  function init() {
    var orgPage = document.querySelector('.public-entity--organization');
    if (!orgPage) return;

    initDescriptionToggle();
    initStickyNav();
    initBranchFilters();
    initHeroCta();
    initReviewsToggle();
  }

  /* ---------------------------------------------------------
   * Description Clamp & Expand
   * --------------------------------------------------------- */
  function initDescriptionToggle() {
    var descEl = document.getElementById('org-description');
    var toggleBtn = document.getElementById('org-desc-toggle');
    if (!descEl || !toggleBtn) return;

    // Check if the text actually overflows a reasonable clamp threshold (e.g. 112px / ~4 lines)
    var maxHeight = 112;
    if (descEl.scrollHeight > maxHeight + 16) {
      descEl.classList.add('is-clamped');
      toggleBtn.hidden = false;

      var textSpan = toggleBtn.querySelector('.public-prose-toggle__text');
      var moreText = textSpan ? (textSpan.getAttribute('data-more') || 'Читать полностью') : 'Читать полностью';
      var lessText = textSpan ? (textSpan.getAttribute('data-less') || 'Свернуть') : 'Свернуть';

      toggleBtn.addEventListener('click', function () {
        var isExpanded = descEl.classList.toggle('is-expanded');
        toggleBtn.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
        if (textSpan) {
          textSpan.textContent = isExpanded ? lessText : moreText;
        }
      });
    }
  }

  /* ---------------------------------------------------------
   * Hero CTA "Choose a branch" Smooth Scroll & Focus
   * --------------------------------------------------------- */
  function initHeroCta() {
    var ctaBtn = document.getElementById('hero-select-branch-btn');
    if (!ctaBtn) return;

    ctaBtn.addEventListener('click', function (e) {
      var target = document.getElementById('branches');
      if (!target) return;
      e.preventDefault();

      var headerOffset = getNavOffset();
      var targetPos = target.getBoundingClientRect().top + window.pageYOffset - headerOffset;
      window.scrollTo({ top: Math.max(0, targetPos), behavior: 'smooth' });

      // Focus first available filter input after scroll
      setTimeout(function () {
        var districtSelect = document.getElementById('branch-district-filter');
        var searchInput = document.getElementById('branch-search-input');
        if (districtSelect) {
          districtSelect.focus({ preventScroll: true });
        } else if (searchInput) {
          searchInput.focus({ preventScroll: true });
        }
      }, 350);
    });
  }

  /* ---------------------------------------------------------
   * Sticky Nav & Scroll Spy
   * --------------------------------------------------------- */
  function getNavOffset() {
    var nav = document.getElementById('public-entity-nav');
    var navHeight = nav ? nav.offsetHeight : 0;
    // Account for any fixed site header (approx 64px) + sticky nav
    return navHeight + 70;
  }

  function initStickyNav() {
    var nav = document.getElementById('public-entity-nav');
    if (!nav) return;

    var navList = nav.querySelector('.public-entity-nav__list');
    var links = nav.querySelectorAll('.public-entity-nav__link');
    if (!links.length) return;

    // Collect all valid target sections dynamically from the nav links
    var sections = [];
    links.forEach(function (link) {
      var href = link.getAttribute('href');
      if (href && href.indexOf('#') === 0) {
        var targetId = href.substring(1);
        var el = document.getElementById(targetId);
        if (el) {
          sections.push({ id: targetId, el: el, link: link });
        }
      }
    });

    if (!sections.length) return;

    function scrollNavIntoView(activeLink) {
      if (!navList || !activeLink) return;
      var listRect = navList.getBoundingClientRect();
      var linkRect = activeLink.getBoundingClientRect();
      if (linkRect.left < listRect.left + 24 || linkRect.right > listRect.right - 24) {
        activeLink.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }
    }

    function setActiveLink(activeLink) {
      links.forEach(function (l) {
        if (l === activeLink) {
          if (!l.classList.contains('is-active')) {
            l.classList.add('is-active');
            scrollNavIntoView(l);
          }
        } else {
          l.classList.remove('is-active');
        }
      });
    }

    var isManualScrolling = false;
    var manualScrollTimer = null;

    // Smooth scrolling for nav links with offset
    links.forEach(function (link) {
      link.addEventListener('click', function (e) {
        var href = link.getAttribute('href');
        if (!href || href.indexOf('#') !== 0) return;
        var targetId = href.substring(1);
        var target = document.getElementById(targetId);
        if (!target) return;

        e.preventDefault();
        isManualScrolling = true;
        clearTimeout(manualScrollTimer);

        setActiveLink(link);

        var offset = getNavOffset();
        var top = target.getBoundingClientRect().top + window.pageYOffset - offset + 8;
        window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });

        manualScrollTimer = setTimeout(function () {
          isManualScrolling = false;
        }, 800);
      });
    });

    // Real-time Scroll Spy with requestAnimationFrame
    var ticking = false;

    function updateActiveOnScroll() {
      if (isManualScrolling) {
        ticking = false;
        return;
      }

      var scrollPos = window.pageYOffset + getNavOffset() + 30;
      var docHeight = document.documentElement.scrollHeight;
      var winBottom = window.pageYOffset + window.innerHeight;

      var currentSection = sections[0];

      // If scrolled to the very bottom of the page, activate the last section
      if (winBottom >= docHeight - 50) {
        currentSection = sections[sections.length - 1];
      } else {
        for (var i = 0; i < sections.length; i++) {
          var secTop = sections[i].el.getBoundingClientRect().top + window.pageYOffset;
          if (secTop <= scrollPos) {
            currentSection = sections[i];
          }
        }
      }

      if (currentSection && currentSection.link) {
        setActiveLink(currentSection.link);
      }

      ticking = false;
    }

    window.addEventListener('scroll', function () {
      if (!ticking) {
        requestAnimationFrame(updateActiveOnScroll);
        ticking = true;
      }
    }, { passive: true });

    // Initial check
    updateActiveOnScroll();
  }

  /* ---------------------------------------------------------
   * Fast Client-Side Branch Filtering
   * --------------------------------------------------------- */
  function initBranchFilters() {
    var branchList = document.getElementById('public-branches-list');
    if (!branchList) return;

    var branchItems = branchList.querySelectorAll('.public-branch-item');
    if (!branchItems.length) return;

    var districtSelect = document.getElementById('branch-district-filter');
    var activitySelect = document.getElementById('branch-activity-filter');
    var searchInput = document.getElementById('branch-search-input');
    var resetBtn = document.getElementById('branch-filter-reset');
    var emptyResetBtn = document.getElementById('branch-empty-reset-btn');
    var shownCountEl = document.getElementById('branch-shown-count');
    var emptyState = document.getElementById('branch-filter-empty');

    var debounceTimer = null;

    function applyFilters() {
      var selectedDistrict = districtSelect ? districtSelect.value.trim() : '';
      var selectedActivity = activitySelect ? activitySelect.value.trim().toLowerCase() : '';
      var query = searchInput ? searchInput.value.trim().toLowerCase() : '';
      var queryTokens = query ? query.split(/\s+/).filter(Boolean) : [];

      var hasActiveFilters = Boolean(selectedDistrict || selectedActivity || query);
      var visibleCount = 0;

      branchItems.forEach(function (item) {
        var itemDistrict = item.getAttribute('data-district') || '';
        var itemActivities = (item.getAttribute('data-activities') || '').toLowerCase();
        var itemSearch = (item.getAttribute('data-search') || '').toLowerCase();

        // 1. District match
        var districtMatches = !selectedDistrict || (itemDistrict === selectedDistrict);

        // 2. Activity match
        var activityMatches = true;
        if (selectedActivity) {
          var acts = itemActivities.split(',').map(function (s) { return s.trim(); });
          activityMatches = acts.indexOf(selectedActivity) !== -1 || itemActivities.indexOf(selectedActivity) !== -1;
        }

        // 3. Search text match (all tokens must match)
        var searchMatches = true;
        if (queryTokens.length > 0) {
          for (var i = 0; i < queryTokens.length; i++) {
            if (itemSearch.indexOf(queryTokens[i]) === -1) {
              searchMatches = false;
              break;
            }
          }
        }

        var isVisible = districtMatches && activityMatches && searchMatches;
        item.hidden = !isVisible;
        if (isVisible) {
          visibleCount++;
        }
      });

      // Update counter
      if (shownCountEl) {
        shownCountEl.textContent = String(visibleCount);
      }

      // Toggle reset button
      if (resetBtn) {
        resetBtn.hidden = !hasActiveFilters;
      }

      // Toggle empty state
      if (emptyState) {
        emptyState.hidden = visibleCount > 0;
      }
      branchList.hidden = visibleCount === 0;
    }

    // Initialize Custom Dropdowns
    initCustomSelects();

    function initCustomSelects() {
      var customSelects = document.querySelectorAll('.km-custom-select');
      if (!customSelects.length) return;

      customSelects.forEach(function (cs) {
        var trigger = cs.querySelector('.km-custom-select__trigger');
        var menu = cs.querySelector('.km-custom-select__menu');
        var valueSpan = cs.querySelector('.km-custom-select__value');
        var options = cs.querySelectorAll('.km-custom-select__option');
        var nativeSelect = cs.querySelector('select');
        if (!trigger || !menu || !options.length) return;

        function close() {
          cs.classList.remove('is-open');
          trigger.setAttribute('aria-expanded', 'false');
        }

        function open() {
          // Close other open custom dropdowns first
          customSelects.forEach(function (other) {
            if (other !== cs) {
              other.classList.remove('is-open');
              var otherTrig = other.querySelector('.km-custom-select__trigger');
              if (otherTrig) otherTrig.setAttribute('aria-expanded', 'false');
            }
          });
          cs.classList.add('is-open');
          trigger.setAttribute('aria-expanded', 'true');
        }

        trigger.addEventListener('click', function (e) {
          e.stopPropagation();
          if (cs.classList.contains('is-open')) {
            close();
          } else {
            open();
          }
        });

        options.forEach(function (opt) {
          opt.addEventListener('click', function (e) {
            e.stopPropagation();
            var val = opt.getAttribute('data-value') || '';
            var optText = opt.querySelector('.km-custom-select__opt-text');
            var label = optText ? optText.textContent.trim() : opt.textContent.trim();
            var optCount = opt.querySelector('.km-custom-select__opt-count');

            // Update selected class
            options.forEach(function (o) {
              o.classList.remove('is-selected');
              o.setAttribute('aria-selected', 'false');
            });
            opt.classList.add('is-selected');
            opt.setAttribute('aria-selected', 'true');

            // Update trigger text
            if (valueSpan) {
              if (optCount && val) {
                valueSpan.textContent = label + ' (' + optCount.textContent.trim() + ')';
              } else if (val) {
                valueSpan.textContent = label;
              } else {
                // If "all" selected, restore default prompt
                valueSpan.textContent = optCount ? label + ' (' + optCount.textContent.trim() + ')' : label;
              }
            }

            // Sync with native select
            if (nativeSelect) {
              nativeSelect.value = val;
              nativeSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }

            close();
            trigger.focus();
          });
        });

        // Keyboard navigation
        trigger.addEventListener('keydown', function (e) {
          if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            open();
            var firstOpt = menu.querySelector('.km-custom-select__option.is-selected') || options[0];
            if (firstOpt) firstOpt.focus();
          } else if (e.key === 'Escape') {
            close();
          }
        });

        menu.addEventListener('keydown', function (e) {
          var cur = document.activeElement;
          var curIndex = Array.prototype.indexOf.call(options, cur);

          if (e.key === 'ArrowDown') {
            e.preventDefault();
            var nextIndex = curIndex < options.length - 1 ? curIndex + 1 : 0;
            options[nextIndex].focus();
          } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            var prevIndex = curIndex > 0 ? curIndex - 1 : options.length - 1;
            options[prevIndex].focus();
          } else if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (cur && cur.classList.contains('km-custom-select__option')) {
              cur.click();
            }
          } else if (e.key === 'Escape') {
            close();
            trigger.focus();
          }
        });
      });

      // Global outside click closes all custom selects
      document.addEventListener('click', function (e) {
        if (!e.target.closest('.km-custom-select')) {
          customSelects.forEach(function (cs) {
            cs.classList.remove('is-open');
            var trig = cs.querySelector('.km-custom-select__trigger');
            if (trig) trig.setAttribute('aria-expanded', 'false');
          });
        }
      });
    }

    function resetFilters() {
      if (districtSelect) districtSelect.value = '';
      if (activitySelect) activitySelect.value = '';
      if (searchInput) searchInput.value = '';

      // Reset custom selects visual labels & states
      document.querySelectorAll('.km-custom-select').forEach(function (cs) {
        var options = cs.querySelectorAll('.km-custom-select__option');
        var firstOpt = options[0];
        var valSpan = cs.querySelector('.km-custom-select__value');
        if (firstOpt) {
          options.forEach(function (o) {
            o.classList.remove('is-selected');
            o.setAttribute('aria-selected', 'false');
          });
          firstOpt.classList.add('is-selected');
          firstOpt.setAttribute('aria-selected', 'true');
          if (valSpan) {
            var optText = firstOpt.querySelector('.km-custom-select__opt-text');
            var optCount = firstOpt.querySelector('.km-custom-select__opt-count');
            var txt = optText ? optText.textContent.trim() : firstOpt.textContent.trim();
            valSpan.textContent = optCount ? txt + ' (' + optCount.textContent.trim() + ')' : txt;
          }
        }
      });

      applyFilters();
      var firstTrigger = document.querySelector('.km-custom-select__trigger');
      if (firstTrigger) {
        firstTrigger.focus();
      } else if (districtSelect) {
        districtSelect.focus();
      }
    }

    // Event listeners
    if (districtSelect) {
      districtSelect.addEventListener('change', applyFilters);
    }
    if (activitySelect) {
      activitySelect.addEventListener('change', applyFilters);
    }
    if (searchInput) {
      searchInput.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(applyFilters, 120);
      });
      searchInput.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          if (searchInput.value) {
            searchInput.value = '';
            applyFilters();
          } else {
            resetFilters();
          }
        }
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', resetFilters);
    }
    if (emptyResetBtn) {
      emptyResetBtn.addEventListener('click', resetFilters);
    }
  }

  /* ---------------------------------------------------------
   * Reviews Expand / Collapse Toggle
   * --------------------------------------------------------- */
  function initReviewsToggle() {
    var toggleBtn = document.getElementById('reviews-toggle-btn');
    var reviewsGrid = document.getElementById('public-reviews-grid');
    if (!toggleBtn || !reviewsGrid) return;

    var textSpan = toggleBtn.querySelector('.public-reviews-toggle-text');
    var expandText = textSpan ? (textSpan.getAttribute('data-expand') || 'Показать все отзывы') : 'Показать все отзывы';
    var collapseText = textSpan ? (textSpan.getAttribute('data-collapse') || 'Свернуть отзывы') : 'Свернуть отзывы';

    toggleBtn.addEventListener('click', function () {
      var isExpanded = reviewsGrid.classList.toggle('is-expanded');
      toggleBtn.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
      toggleBtn.classList.toggle('is-expanded', isExpanded);

      if (textSpan) {
        textSpan.textContent = isExpanded ? collapseText : expandText;
      }

      // If collapsing, scroll smoothly back to reviews heading
      if (!isExpanded) {
        var reviewsSec = document.getElementById('reviews');
        if (reviewsSec) {
          var offset = getNavOffset();
          var top = reviewsSec.getBoundingClientRect().top + window.pageYOffset - offset;
          window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
        }
      }
    });
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
