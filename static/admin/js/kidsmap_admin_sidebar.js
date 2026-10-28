(function () {
  function isMobileSidebar() {
    return window.innerWidth < 768;
  }

  function scrollBehavior(smooth) {
    var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    return smooth && !reducedMotion ? 'smooth' : 'auto';
  }

  function applyGroupState(group, isOpen, persist) {
    var button = group.querySelector("[data-km-sidebar-toggle]");
    var panel = group.querySelector("[data-km-sidebar-panel]");
    var key = group.getAttribute("data-km-sidebar-key");

    if (!button || !panel || !key) {
      return;
    }

    group.setAttribute("data-open", isOpen ? "true" : "false");
    button.setAttribute("aria-expanded", isOpen ? "true" : "false");
    panel.hidden = !isOpen;

    if (persist) {
      try {
        window.localStorage.setItem("km-admin-sidebar:" + key, isOpen ? "1" : "0");
      } catch (error) {
        // Ignore storage failures in restrictive environments.
      }
    }
  }

  function resolveInitialState(group) {
    var key = group.getAttribute("data-km-sidebar-key");
    var defaultOpen = group.getAttribute("data-default-open") === "true";
    if (isMobileSidebar()) return defaultOpen;
    if (defaultOpen) return true;

    if (!key) {
      return defaultOpen;
    }

    try {
      var stored = window.localStorage.getItem("km-admin-sidebar:" + key);
      if (stored === "1") {
        return true;
      }
      if (stored === "0") {
        return false;
      }
    } catch (error) {
      // Ignore storage failures and fall back to template state.
    }

    return defaultOpen;
  }

  var STORAGE_KEY_SCROLL = "km-admin-sidebar-scroll";

  function isElementVisibleInScroller(scroller, el) {
    if (!scroller || !el) return false;
    var scrollerRect = scroller.getBoundingClientRect();
    var elRect = el.getBoundingClientRect();
    var buffer = 15;
    return (
      elRect.top >= scrollerRect.top + buffer &&
      elRect.bottom <= scrollerRect.bottom - buffer
    );
  }

  function scrollActiveIntoView(scroller, activeElement, smooth) {
    if (!scroller || !activeElement) return;
    try {
      activeElement.scrollIntoView({
        behavior: scrollBehavior(smooth),
        block: "center",
        inline: "nearest"
      });
    } catch (e) {
      var scrollerRect = scroller.getBoundingClientRect();
      var elRect = activeElement.getBoundingClientRect();
      var targetScrollTop =
        scroller.scrollTop +
        (elRect.top - scrollerRect.top) -
        scrollerRect.height / 2 +
        elRect.height / 2;
      scroller.scrollTop = Math.max(0, targetScrollTop);
    }
  }

  function restoreSidebarScroll(options) {
    var scroller = document.querySelector(".km-admin-sidebar__scroller");
    if (!scroller) return;

    var smooth = !!(options && options.smooth);
    var activeLink =
      scroller.querySelector(".km-admin-sidebar__link.is-active") ||
      scroller.querySelector(".km-admin-sidebar__link[aria-current='page']");

    if (activeLink) {
      var parentGroup = activeLink.closest("[data-km-sidebar-group]");
      if (parentGroup && parentGroup.getAttribute("data-open") !== "true") {
        if (isMobileSidebar()) {
          document.querySelectorAll('[data-km-sidebar-group]').forEach(function (group) {
            if (group !== parentGroup) applyGroupState(group, false, false);
          });
        }
        applyGroupState(parentGroup, true, false);
      }
    }

    var restored = false;
    try {
      var saved = window.sessionStorage.getItem(STORAGE_KEY_SCROLL);
      if (saved !== null && saved !== "") {
        var parsed = parseInt(saved, 10);
        if (!isNaN(parsed) && parsed >= 0) {
          scroller.scrollTop = parsed;
          restored = true;
        }
      }
    } catch (e) {}

    window.requestAnimationFrame(function () {
      if (activeLink) {
        if (!restored || !isElementVisibleInScroller(scroller, activeLink)) {
          scrollActiveIntoView(scroller, activeLink, smooth);
        }
      }
    });
  }

  function initSidebarScroll() {
    var scroller = document.querySelector(".km-admin-sidebar__scroller");
    if (!scroller) return;

    restoreSidebarScroll({ smooth: false });

    var scrollTimeout = null;
    scroller.addEventListener(
      "scroll",
      function () {
        if (scrollTimeout) {
          clearTimeout(scrollTimeout);
        }
        scrollTimeout = setTimeout(function () {
          try {
            window.sessionStorage.setItem(STORAGE_KEY_SCROLL, String(scroller.scrollTop));
          } catch (e) {}
        }, 80);
      },
      { passive: true }
    );

    scroller.addEventListener("click", function (event) {
      var link = event.target.closest("a.km-admin-sidebar__link");
      if (link) {
        try {
          window.sessionStorage.setItem(STORAGE_KEY_SCROLL, String(scroller.scrollTop));
        } catch (e) {}
      }
    });

    window.addEventListener("beforeunload", function () {
      try {
        window.sessionStorage.setItem(STORAGE_KEY_SCROLL, String(scroller.scrollTop));
      } catch (e) {}
    });
  }

  function initSidebarGroups() {
    var groups = document.querySelectorAll("[data-km-sidebar-group]");
    if (!groups.length) {
      return;
    }

    var mobile = isMobileSidebar();
    function restoreGroupStates() {
      var mobileGroupOpened = false;
      groups.forEach(function (group) {
        var open = resolveInitialState(group);
        if (mobile && open) {
          open = !mobileGroupOpened;
          mobileGroupOpened = true;
        }
        applyGroupState(group, open, false);
      });
    }
    restoreGroupStates();

    window.addEventListener('resize', function () {
      var nextMobile = isMobileSidebar();
      if (mobile === nextMobile) return;
      mobile = nextMobile;
      restoreGroupStates();
      restoreSidebarScroll({ smooth: false });
    });

    groups.forEach(function (group) {
      var button = group.querySelector("[data-km-sidebar-toggle]");
      if (!button) {
        return;
      }

      button.addEventListener("click", function () {
        var isOpen = button.getAttribute("aria-expanded") === "true";
        var willBeOpen = !isOpen;
        if (mobile && willBeOpen) {
          groups.forEach(function (otherGroup) {
            if (otherGroup !== group) applyGroupState(otherGroup, false, false);
          });
        }
        applyGroupState(group, willBeOpen, !mobile);
        if (willBeOpen) {
          window.requestAnimationFrame(function () {
            var scroller = document.querySelector(".km-admin-sidebar__scroller");
            if (scroller && !isElementVisibleInScroller(scroller, button)) {
              button.scrollIntoView({ behavior: scrollBehavior(true), block: "nearest" });
            }
          });
        }
      });

      button.addEventListener("keydown", function (event) {
        if (event.key !== "Enter" && event.key !== " ") {
          return;
        }
        event.preventDefault();
        button.click();
      });
    });
  }

  function initSidebarDismissal() {
    var sidebar = document.querySelector('.main-sidebar');
    var opener = document.querySelector('.km-admin-header__toggle[data-widget="pushmenu"]');
    if (!sidebar || !opener) return;
    var close = sidebar.querySelector('[data-km-sidebar-close]');
    var wasExpanded = expanded();

    function expanded() {
      return window.innerWidth < 768
        ? document.body.classList.contains('sidebar-open')
        : !document.body.classList.contains('sidebar-collapse');
    }

    function sync() {
      var nowExpanded = expanded();
      opener.setAttribute('aria-expanded', nowExpanded ? 'true' : 'false');
      if (!wasExpanded && nowExpanded) {
        setTimeout(function () {
          restoreSidebarScroll({ smooth: false });
        }, 80);
      }
      wasExpanded = nowExpanded;
    }

    function restoreFocus() {
      window.requestAnimationFrame(function () {
        opener.focus({preventScroll: true});
      });
    }

    function dismiss() {
      if (!expanded()) return;
      opener.click();
      restoreFocus();
    }

    opener.setAttribute('aria-controls', sidebar.id);
    if (close) close.addEventListener('click', dismiss);
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape' || event.defaultPrevented || !expanded()) return;
      if (window.innerWidth >= 768 && !sidebar.contains(document.activeElement)
          && document.activeElement !== opener) return;
      event.preventDefault();
      dismiss();
    });
    document.addEventListener('click', function (event) {
      if (event.target.id === 'sidebar-overlay') restoreFocus();
    });
    new MutationObserver(sync).observe(document.body, {attributes: true, attributeFilter: ['class']});
    window.addEventListener('resize', sync);
    sync();
  }

  function syncSearchClearButton(input) {
    var button = input.parentElement.querySelector("[data-km-admin-search-clear]");
    if (button) {
      button.hidden = !input.value;
    }
  }

  function initSearchClearButtons() {
    document
      .querySelectorAll('#changelist-search input[name="q"]:not([type="hidden"])')
      .forEach(function (input) {
        if (input.closest("[data-km-admin-search-clear-wrapper]")) {
          return;
        }

        var wrapper = document.createElement("span");
        wrapper.className = "km-admin-search-clear-wrapper";
        wrapper.setAttribute("data-km-admin-search-clear-wrapper", "");
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        var button = document.createElement("button");
        button.type = "button";
        button.className = "km-admin-search-clear";
        button.setAttribute("data-km-admin-search-clear", "");
        button.setAttribute("aria-label", "Очистить поиск");
        wrapper.appendChild(button);

        button.addEventListener("click", function () {
          input.value = "";
          input.dispatchEvent(new Event("input", { bubbles: true }));
          input.focus();

          var form = input.form || input.closest("form");
          if (form) {
            form.requestSubmit ? form.requestSubmit() : form.submit();
          }
        });

        input.addEventListener("input", function () {
          syncSearchClearButton(input);
        });
        syncSearchClearButton(input);
      });
  }

  function escapeSuggestHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function highlightSuggestMatch(text, query) {
    if (!text || !query) return escapeSuggestHtml(text || '');
    var escapedText = escapeSuggestHtml(text);
    var safeQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    var regex = new RegExp('(' + safeQuery + ')', 'gi');
    return escapedText.replace(regex, '<mark class="km-search-highlight">$1</mark>');
  }

  function initGlobalSearchSuggestions() {
    var searchBoxes = document.querySelectorAll('[data-search-suggest-root]');
    searchBoxes.forEach(function (searchBox) {
      if (searchBox.dataset.suggestBound === 'true') return;
      searchBox.dataset.suggestBound = 'true';

      var input = searchBox.querySelector('.km-search-input') ||
                  searchBox.querySelector('.km-admin-header__search-input') ||
                  searchBox.querySelector('input[type="search"]') ||
                  searchBox.querySelector('input[name="q"]');
      var suggestionsUrl = searchBox.dataset.suggestionsUrl;
      var emptyLabel = searchBox.dataset.suggestionsEmpty || 'Ничего не найдено';
      var dropdown = searchBox.querySelector('[data-search-suggestions]');
      var timer = null;
      var activeIndex = -1;

      if (!input || !suggestionsUrl || !dropdown) return;

      var parentForm = input.closest('form');

      function updateActiveItem(items) {
        items.forEach(function (el, idx) {
          el.classList.toggle('is-selected', idx === activeIndex);
          el.setAttribute('aria-selected', idx === activeIndex ? 'true' : 'false');
        });
        if (activeIndex >= 0 && items[activeIndex]) {
          items[activeIndex].scrollIntoView({ block: 'nearest' });
        }
      }

      function selectItem(item) {
        if (!item) return;
        input.value = item.dataset.val || '';
        dropdown.hidden = true;
        activeIndex = -1;
        if (parentForm) {
          parentForm.submit();
        }
      }

      input.addEventListener('input', function () {
        if (timer) clearTimeout(timer);
        var q = input.value.trim();
        if (q.length < 2) {
          dropdown.hidden = true;
          dropdown.innerHTML = '';
          activeIndex = -1;
          return;
        }

        timer = setTimeout(function () {
          fetch(suggestionsUrl + '?q=' + encodeURIComponent(q), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
          })
            .then(function (res) { return res.json(); })
            .then(function (data) {
              var results = data.results || [];
              var suggestLabels = data.labels || {};
              activeIndex = -1;
              if (!results.length) {
                dropdown.innerHTML = '<div class="km-search-suggest-empty">' +
                  '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true" focusable="false"><use href="#kmi-search"></use></svg>' +
                  '<span>' + escapeSuggestHtml(emptyLabel) + '</span>' +
                  '</div>';
              } else {
                var itemsHtml = results.map(function (item) {
                  var safeVal = escapeSuggestHtml(item.value || item.label || '');
                  var safeLabel = item.label || item.value || '';
                  var highlightedTitle = highlightSuggestMatch(safeLabel, q);
                  var safeChangeUrl = item.change_url ? escapeSuggestHtml(item.change_url) : '';
                  var safeCategory = item.category ? escapeSuggestHtml(item.category) : '';
                  var safeStatusLabel = item.status_label ? escapeSuggestHtml(item.status_label) : '';
                  var safeStatusTone = item.status_tone ? escapeSuggestHtml(item.status_tone) : 'muted';
                  var safeDistrict = item.district ? escapeSuggestHtml(item.district) : '';
                  var safeAddress = item.address ? escapeSuggestHtml(item.address) : '';
                  var safePhone = item.phone ? escapeSuggestHtml(item.phone) : '';
                  var safeOwner = item.owner ? escapeSuggestHtml(item.owner) : '';
                  var safeMeta = escapeSuggestHtml(item.meta || '');

                  var badgeHtml = safeStatusLabel
                    ? '<span class="km-search-suggest-badge km-search-suggest-badge--' + safeStatusTone + '">' + safeStatusLabel + '</span>'
                    : '';

                  var categoryHtml = safeCategory
                    ? '<span class="km-search-suggest-cat">' + safeCategory + '</span>'
                    : '';

                  var metaPartsHtml = '';
                  var locText = safeDistrict ? (safeDistrict + (safeAddress ? ', ' + safeAddress : '')) : safeAddress;
                  if (locText) {
                    metaPartsHtml += '<span class="km-search-suggest-loc"><svg class="km-i" viewBox="0 0 960 960" aria-hidden="true" focusable="false"><use href="#kmi-place"></use></svg>' + locText + '</span>';
                  }
                  if (safePhone) {
                    metaPartsHtml += '<span class="km-search-suggest-phone"><svg class="km-i" viewBox="0 0 960 960" aria-hidden="true" focusable="false"><use href="#kmi-call"></use></svg>' + safePhone + '</span>';
                  }
                  if (safeOwner) {
                    metaPartsHtml += '<span class="km-search-suggest-owner"><svg class="km-i" viewBox="0 0 960 960" aria-hidden="true" focusable="false"><use href="#kmi-person"></use></svg>' + safeOwner + '</span>';
                  }
                  if (!metaPartsHtml && safeMeta) {
                    metaPartsHtml = '<span class="km-search-suggest-meta-raw">' + safeMeta + '</span>';
                  }

                  return '<div class="km-search-suggest-item" role="option" data-val="' + safeVal + '" data-url="' + safeChangeUrl + '">' +
                    '<div class="km-search-suggest-item__main">' +
                      '<div class="km-search-suggest-item__head">' +
                        '<span class="km-search-suggest-item__title">' + highlightedTitle + '</span>' +
                        badgeHtml +
                        categoryHtml +
                      '</div>' +
                      '<div class="km-search-suggest-item__meta">' +
                        metaPartsHtml +
                      '</div>' +
                    '</div>' +
                    (safeChangeUrl ? '<div class="km-search-suggest-item__actions">' +
                      '<a href="' + safeChangeUrl + '" class="km-search-suggest-btn" title="' + escapeSuggestHtml(suggestLabels.edit || '') + '" aria-label="' + escapeSuggestHtml(suggestLabels.edit || '') + '">' +
                        '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true" focusable="false"><use href="#kmi-edit"></use></svg>' +
                      '</a>' +
                    '</div>' : '') +
                  '</div>';
                }).join('');

                var footerHtml = '<div class="km-search-suggest-footer">' +
                  '<span aria-hidden="true">↑ ↓ · Enter</span>' +
                  '<span class="km-search-suggest-count">' + escapeSuggestHtml(suggestLabels.found || '') + ': ' + results.length + '</span>' +
                '</div>';

                dropdown.innerHTML = itemsHtml + footerHtml;
              }
              dropdown.hidden = false;
            })
            .catch(function () {
              dropdown.hidden = true;
            });
        }, 120);
      });

      input.addEventListener('keydown', function (e) {
        if (dropdown.hidden) return;
        var items = dropdown.querySelectorAll('.km-search-suggest-item');
        if (!items.length) return;

        if (e.key === 'ArrowDown') {
          e.preventDefault();
          activeIndex = Math.min(activeIndex + 1, items.length - 1);
          updateActiveItem(items);
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          activeIndex = Math.max(activeIndex - 1, 0);
          updateActiveItem(items);
        } else if (e.key === 'Enter' && activeIndex >= 0 && items[activeIndex]) {
          e.preventDefault();
          selectItem(items[activeIndex]);
        } else if (e.key === 'Escape') {
          dropdown.hidden = true;
          activeIndex = -1;
        }
      });

      dropdown.addEventListener('click', function (e) {
        if (e.target.closest('.km-search-suggest-btn')) return;
        var item = e.target.closest('[data-val]');
        if (item) {
          selectItem(item);
        }
      });

      document.addEventListener('click', function (e) {
        if (!searchBox.contains(e.target)) {
          dropdown.hidden = true;
          activeIndex = -1;
        }
      });
    });
  }

  window.initGlobalSearchSuggestions = initGlobalSearchSuggestions;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initGlobalSearchSuggestions);
  } else {
    initGlobalSearchSuggestions();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSidebarDismissal);
  } else {
    initSidebarDismissal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSidebarGroups);
  } else {
    initSidebarGroups();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSidebarScroll);
  } else {
    initSidebarScroll();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSearchClearButtons);
  } else {
    initSearchClearButtons();
  }
})();
