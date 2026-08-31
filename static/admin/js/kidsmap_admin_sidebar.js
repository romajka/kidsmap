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

  function syncSearchClearButton(input) {
    var button = input.parentElement.querySelector("[data-km-admin-search-clear]");
    if (button) {
      button.hidden = !input.value;
    }
  }

  function initSearchClearButtons() {
    document
      .querySelectorAll('input[name="q"]:not([type="hidden"])')
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
    document.addEventListener("DOMContentLoaded", initSidebarGroups);
  } else {
    initSidebarGroups();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSearchClearButtons);
  } else {
    initSearchClearButtons();
  }
})();
