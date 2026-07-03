(function () {
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

  function initSidebarGroups() {
    var groups = document.querySelectorAll("[data-km-sidebar-group]");
    if (!groups.length) {
      return;
    }

    groups.forEach(function (group) {
      var button = group.querySelector("[data-km-sidebar-toggle]");
      if (!button) {
        return;
      }

      applyGroupState(group, resolveInitialState(group), false);

      button.addEventListener("click", function () {
        var isOpen = button.getAttribute("aria-expanded") === "true";
        applyGroupState(group, !isOpen, true);
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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSidebarGroups);
  } else {
    initSidebarGroups();
  }
})();
