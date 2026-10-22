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
