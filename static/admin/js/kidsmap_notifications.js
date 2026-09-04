/**
 * KidsMap Admin - Unified Notifications, Modals, Toasts & Confirm Dialogs
 *
 * Accessible, zero-dependency notification engine for Django Admin.
 * Provides:
 *   - window.kmModal (.show, .confirm, .alert, .unsavedChanges, .close)
 *   - window.kmToast (.success, .warning, .error, .info, .dismiss, .clearAll)
 *   - window.kmConfirm
 *   - window.kmAlert
 */
(function (root, factory) {
  if (typeof define === "function" && define.amd) {
    define([], factory);
  } else if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    var km = factory();
    root.kmModal = km.kmModal;
    root.kmToast = km.kmToast;
    root.kmConfirm = km.kmConfirm;
    root.kmAlert = km.kmAlert;
  }
})(typeof globalThis !== "undefined" ? globalThis : window, function () {
  // Ensure window.django.jQuery compatibility for admin cancel.js and legacy widgets
  if (typeof window !== "undefined") {
    if (typeof window.django === "undefined") {
      window.django = {};
    }
    if (!window.django.jQuery) {
      try {
        Object.defineProperty(window.django, "jQuery", {
          get: function () {
            return window.jQuery || window.$;
          },
          set: function (val) {
            Object.defineProperty(window.django, "jQuery", { value: val, writable: true, configurable: true });
          },
          configurable: true
        });
      } catch (e) {
        window.django.jQuery = window.jQuery || window.$;
      }
    }
  }

  var SVG_NS = "http://www.w3.org/2000/svg";

  /* Embedded fallback SVGs (Material Symbols Rounded) in case SVG sprite is not loaded */
  var FALLBACK_ICONS = {
    check_circle: '<circle cx="12" cy="12" r="9.25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="7.75 12 10.75 15 16.25 9" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>',
    check: '<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" fill="currentColor"/>',
    warning: '<path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" fill="currentColor"/>',
    error: '<circle cx="12" cy="12" r="9.25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="7.5" x2="12" y2="12.5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="16" r="1.2" fill="currentColor"/>',
    info: '<circle cx="12" cy="12" r="9.25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="11" x2="12" y2="16.5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="7.5" r="1.2" fill="currentColor"/>',
    delete: '<path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" fill="currentColor"/>',
    close: '<path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/>'
  };

  function createIconElement(name, className) {
    var iconName = name || "info";
    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", className ? "km-i " + className : "km-i");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");

    var spriteSymbol = document.getElementById("kmi-" + iconName);
    if (spriteSymbol) {
      var viewBox = spriteSymbol.getAttribute("viewBox") || "0 0 960 960";
      svg.setAttribute("viewBox", viewBox);
      var use = document.createElementNS(SVG_NS, "use");
      use.setAttribute("href", "#kmi-" + iconName);
      svg.appendChild(use);
    } else if (FALLBACK_ICONS[iconName]) {
      svg.setAttribute("viewBox", "0 0 24 24");
      svg.innerHTML = FALLBACK_ICONS[iconName];
    } else {
      svg.setAttribute("viewBox", "0 0 24 24");
      svg.innerHTML = FALLBACK_ICONS.info;
    }
    return svg;
  }

  /* ==========================================================================
     Unified Modal Engine
     ========================================================================== */
  var kmModal = (function () {
    var activeModal = null;
    var lastFocusedElement = null;

    function getFocusableElements(container) {
      if (!container) return [];
      var selectors = [
        'button:not([disabled])',
        '[href]:not([disabled])',
        'input:not([disabled]):not([type="hidden"])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        '[tabindex]:not([tabindex="-1"])'
      ];
      return Array.prototype.slice.call(container.querySelectorAll(selectors.join(', ')))
        .filter(function (el) {
          return el.offsetWidth > 0 || el.offsetHeight > 0 || el.getClientRects().length > 0;
        });
    }

    function handleKeydown(e) {
      if (!activeModal) return;

      // Handle ESC key
      if (e.key === "Escape" || e.keyCode === 27) {
        if (activeModal.closeOnEscape !== false) {
          e.preventDefault();
          e.stopPropagation();
          close();
        }
        return;
      }

      // Handle Tab navigation inside modal (Focus Trap)
      if (e.key === "Tab" || e.keyCode === 9) {
        var focusables = getFocusableElements(activeModal.dialog);
        if (!focusables.length) {
          e.preventDefault();
          return;
        }
        var first = focusables[0];
        var last = focusables[focusables.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first || !activeModal.dialog.contains(document.activeElement)) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last || !activeModal.dialog.contains(document.activeElement)) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    }

    function close() {
      if (!activeModal) return;
      var current = activeModal;
      activeModal = null;

      var backdrop = current.backdrop;
      backdrop.classList.remove("is-visible");
      document.body.classList.remove("km-modal-open");
      document.removeEventListener("keydown", handleKeydown, true);

      window.setTimeout(function () {
        if (backdrop.parentNode) {
          backdrop.parentNode.removeChild(backdrop);
        }
        if (lastFocusedElement && typeof lastFocusedElement.focus === "function") {
          try {
            lastFocusedElement.focus();
          } catch (err) {
            // Element might no longer exist or be disabled
          }
        }
      }, 220);

      if (typeof current.onClose === "function") {
        current.onClose();
      }
    }

    function show(options) {
      if (!options) options = {};
      if (activeModal) {
        close();
      }

      lastFocusedElement = document.activeElement;

      var backdrop = document.createElement("div");
      backdrop.className = "km-modal-backdrop";
      backdrop.setAttribute("role", "presentation");

      var dialog = document.createElement("div");
      dialog.className = "km-modal" + (options.customClass ? " " + options.customClass : "");
      dialog.setAttribute("role", options.isAlertDialog ? "alertdialog" : "dialog");
      dialog.setAttribute("aria-modal", "true");
      dialog.tabIndex = -1;

      var titleId = "km-modal-title-" + Date.now();
      var descId = "km-modal-desc-" + Date.now();
      dialog.setAttribute("aria-labelledby", titleId);

      // Header with icon and titles
      var header = document.createElement("div");
      header.className = "km-modal__header";

      // Icon tone mapping (5 states: success, warning, error, info, danger)
      var tone = options.iconTone || options.tone || "info";
      if (tone === "warn") tone = "warning";
      if (tone === "good") tone = "success";
      if (tone === "destructive") tone = "danger";

      var iconMap = {
        success: "check_circle",
        warning: "warning",
        error: "error",
        info: "info",
        danger: "delete"
      };

      var iconName = options.icon || iconMap[tone] || "info";

      var iconWrap = document.createElement("div");
      iconWrap.className = "km-modal__icon km-modal__icon--" + tone;
      iconWrap.appendChild(createIconElement(iconName));
      header.appendChild(iconWrap);

      var titles = document.createElement("div");
      titles.className = "km-modal__titles";

      var title = document.createElement("h3");
      title.id = titleId;
      title.className = "km-modal__title";
      if (typeof options.title === "string") {
        title.textContent = options.title;
      } else if (options.title instanceof Node) {
        title.appendChild(options.title);
      }
      titles.appendChild(title);

      if (options.message) {
        dialog.setAttribute("aria-describedby", descId);
        var desc = document.createElement("p");
        desc.id = descId;
        desc.className = "km-modal__desc";
        if (typeof options.message === "string") {
          desc.textContent = options.message;
        } else if (options.message instanceof Node) {
          desc.appendChild(options.message);
        }
        titles.appendChild(desc);
      }

      header.appendChild(titles);
      dialog.appendChild(header);

      // Optional extra body content
      if (options.body) {
        var bodyWrap = document.createElement("div");
        bodyWrap.className = "km-modal__body";
        if (typeof options.body === "string") {
          bodyWrap.innerHTML = options.body;
        } else if (options.body instanceof Node) {
          bodyWrap.appendChild(options.body);
        }
        dialog.appendChild(bodyWrap);
      }

      // Actions container
      var actionsWrap = document.createElement("div");
      actionsWrap.className = "km-modal__actions";

      var actions = options.actions || [{ label: "OK", tone: "primary", onClick: close }];

      actions.forEach(function (act) {
        var btn = document.createElement("button");
        btn.type = "button";
        var btnClass = "km-btn-modal";
        var actTone = act.tone || "secondary";

        if (actTone === "primary") btnClass += " km-btn-modal--primary";
        else if (actTone === "warning") btnClass += " km-btn-modal--warning";
        else if (actTone === "danger" || actTone === "danger-filled") btnClass += " km-btn-modal--danger";
        else if (actTone === "danger-quiet") btnClass += " km-btn-modal--danger-quiet";
        else if (actTone === "quiet" || actTone === "ghost") btnClass += " km-btn-modal--quiet";
        else btnClass += " km-btn-modal--secondary";

        btn.className = btnClass;
        btn.textContent = act.label || "Action";

        btn.addEventListener("click", function () {
          if (typeof act.onClick === "function") {
            var result = act.onClick({ close: close });
            if (result !== false) {
              close();
            }
          } else {
            close();
          }
        });

        actionsWrap.appendChild(btn);
      });

      dialog.appendChild(actionsWrap);
      backdrop.appendChild(dialog);

      if (options.closeOnBackdrop !== false) {
        backdrop.addEventListener("click", function (e) {
          if (e.target === backdrop) {
            close();
          }
        });
      }

      document.body.appendChild(backdrop);
      document.body.classList.add("km-modal-open");

      activeModal = {
        backdrop: backdrop,
        dialog: dialog,
        closeOnEscape: options.closeOnEscape !== false,
        onClose: options.onClose
      };

      document.addEventListener("keydown", handleKeydown, true);

      // Trigger animations and focus
      window.requestAnimationFrame(function () {
        backdrop.classList.add("is-visible");
        var focusables = getFocusableElements(dialog);
        // Default focus: primary button or first focusable
        var primaryBtn = dialog.querySelector(".km-btn-modal--primary, .km-btn-modal--danger") || focusables[0];
        if (primaryBtn && typeof primaryBtn.focus === "function") {
          primaryBtn.focus();
        } else {
          dialog.focus();
        }
      });

      return { close: close };
    }

    /**
     * Confirmation Modal helper returning Promise
     */
    function confirm(options) {
      if (typeof options === "string") {
        options = { message: options };
      }
      options = options || {};

      return new Promise(function (resolve) {
        var tone = options.tone || options.iconTone || "danger";
        var isDanger = tone === "danger" || tone === "destructive";
        var defaultIcon = isDanger ? "delete" : (tone === "warning" ? "warning" : (tone === "success" ? "check_circle" : "info"));
        var defaultConfirmTone = isDanger ? "danger" : (tone === "warning" ? "warning" : "primary");
        var defaultConfirmText = isDanger ? "Удалить" : (tone === "warning" ? "Продолжить" : "Подтвердить");

        show({
          title: options.title || (isDanger ? "Подтвердите действие" : "Подтверждение"),
          message: options.message || "",
          icon: options.icon || defaultIcon,
          iconTone: tone,
          isAlertDialog: options.isAlertDialog !== undefined ? options.isAlertDialog : isDanger,
          closeOnBackdrop: options.closeOnBackdrop !== false,
          closeOnEscape: options.closeOnEscape !== false,
          actions: [
            {
              label: options.cancelText || "Отмена",
              tone: "secondary",
              onClick: function () {
                if (typeof options.onCancel === "function") options.onCancel();
                resolve(false);
              }
            },
            {
              label: options.confirmText || defaultConfirmText,
              tone: options.confirmTone || defaultConfirmTone,
              onClick: function () {
                if (typeof options.onConfirm === "function") options.onConfirm();
                resolve(true);
              }
            }
          ],
          onClose: function () {
            // If closed without action button (e.g. via backdrop/esc)
            resolve(false);
          }
        });
      });
    }

    /**
     * Alert Modal helper returning Promise
     */
    function alertModal(options) {
      if (typeof options === "string") {
        options = { message: options };
      }
      options = options || {};

      return new Promise(function (resolve) {
        show({
          title: options.title || "Внимание",
          message: options.message || "",
          icon: options.icon || (options.tone === "error" ? "error" : "info"),
          iconTone: options.tone || "info",
          actions: [
            {
              label: options.okText || "Понятно",
              tone: "primary",
              onClick: function () {
                if (typeof options.onOk === "function") options.onOk();
                resolve(true);
              }
            }
          ],
          onClose: function () {
            resolve(true);
          }
        });
      });
    }

    /**
     * Dedicated Unsaved Changes Dialog with 3 explicit actions:
     * 1. "Остаться" (Stay & continue editing)
     * 2. "Сохранить и выйти" (Save & proceed)
     * 3. "Выйти без сохранения" (Discard & proceed)
     */
    function unsavedChanges(options) {
      options = options || {};

      if (activeModal) {
        close();
      }

      lastFocusedElement = document.activeElement;

      var backdrop = document.createElement("div");
      backdrop.className = "km-modal-backdrop";
      backdrop.setAttribute("role", "presentation");

      var dialog = document.createElement("div");
      dialog.className = "km-modal km-modal--unsaved";
      dialog.setAttribute("role", "alertdialog");
      dialog.setAttribute("aria-modal", "true");
      dialog.tabIndex = -1;

      var titleId = "km-unsaved-title-" + Date.now();
      var descId = "km-unsaved-desc-" + Date.now();
      dialog.setAttribute("aria-labelledby", titleId);
      dialog.setAttribute("aria-describedby", descId);

      // Header
      var header = document.createElement("div");
      header.className = "km-modal__header";

      var iconWrap = document.createElement("div");
      iconWrap.className = "km-modal__icon km-modal__icon--warning";
      iconWrap.appendChild(createIconElement("warning"));
      header.appendChild(iconWrap);

      var titles = document.createElement("div");
      titles.className = "km-modal__titles";

      var title = document.createElement("h3");
      title.id = titleId;
      title.className = "km-modal__title";
      title.textContent = options.title || "Есть несохранённые изменения";
      titles.appendChild(title);

      var desc = document.createElement("p");
      desc.id = descId;
      desc.className = "km-modal__desc";
      desc.textContent = options.message || "Вы изменили карточку, но ещё не сохранили изменения.";
      titles.appendChild(desc);

      header.appendChild(titles);
      dialog.appendChild(header);

      // Actions Container structured in 2 distinct tiers:
      // Tier 1: Primary actions (Остаться / Сохранить и выйти)
      // Tier 2: Safe destructive action (Выйти без сохранения) separated by a divider
      var actionsContainer = document.createElement("div");
      actionsContainer.className = "km-unsaved-actions";

      var mainRow = document.createElement("div");
      mainRow.className = "km-unsaved-actions__main";

      var stayBtn = document.createElement("button");
      stayBtn.type = "button";
      stayBtn.className = "km-btn-modal km-btn-modal--quiet";
      stayBtn.textContent = options.stayText || "Остаться";
      stayBtn.addEventListener("click", function () {
        close();
        if (typeof options.onStay === "function") options.onStay();
      });
      mainRow.appendChild(stayBtn);

      var saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.className = "km-btn-modal km-btn-modal--primary";
      saveBtn.textContent = options.saveText || "Сохранить и выйти";
      saveBtn.addEventListener("click", function () {
        close();
        if (typeof options.onSaveAndExit === "function") {
          options.onSaveAndExit();
        }
      });
      mainRow.appendChild(saveBtn);

      actionsContainer.appendChild(mainRow);

      var divider = document.createElement("div");
      divider.className = "km-unsaved-actions__divider";
      actionsContainer.appendChild(divider);

      var dangerRow = document.createElement("div");
      dangerRow.className = "km-unsaved-actions__danger-row";

      var discardBtn = document.createElement("button");
      discardBtn.type = "button";
      discardBtn.className = "km-btn-modal km-btn-modal--danger-quiet";
      discardBtn.textContent = options.discardText || "Выйти без сохранения";
      discardBtn.addEventListener("click", function () {
        close();
        if (typeof options.onExitWithoutSaving === "function") {
          options.onExitWithoutSaving();
        }
      });
      dangerRow.appendChild(discardBtn);

      actionsContainer.appendChild(dangerRow);
      dialog.appendChild(actionsContainer);
      backdrop.appendChild(dialog);

      // Do not close on outside click for data loss prevention
      document.body.appendChild(backdrop);
      document.body.classList.add("km-modal-open");

      activeModal = {
        backdrop: backdrop,
        dialog: dialog,
        closeOnEscape: true,
        onClose: options.onStay
      };

      document.addEventListener("keydown", handleKeydown, true);

      window.requestAnimationFrame(function () {
        backdrop.classList.add("is-visible");
        // Focus Save & Exit as primary safe action
        saveBtn.focus();
      });

      return { close: close };
    }

    return {
      show: show,
      confirm: confirm,
      alert: alertModal,
      unsavedChanges: unsavedChanges,
      close: close
    };
  })();

  /* ==========================================================================
     Unified Toast System
     ========================================================================== */
  var kmToast = (function () {
    var container = null;
    var MAX_TOASTS = 3;

    function getContainer() {
      if (!container || !container.parentNode) {
        container = document.querySelector(".km-toast-container");
        if (!container) {
          container = document.createElement("div");
          container.className = "km-toast-container";
          container.setAttribute("aria-live", "polite");
          document.body.appendChild(container);
        }
      }
      return container;
    }

    function dismiss(toast) {
      if (!toast || toast.classList.contains("is-leaving")) return;
      if (toast._timer) window.clearTimeout(toast._timer);
      toast.classList.remove("is-visible");
      toast.classList.add("is-leaving");
      window.setTimeout(function () {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 220);
    }

    function clearAll() {
      var cont = getContainer();
      var toasts = Array.prototype.slice.call(cont.children);
      toasts.forEach(dismiss);
    }

    function show(options) {
      if (typeof options === "string") {
        options = { title: options };
      }
      options = options || {};

      var cont = getContainer();

      while (cont.children.length >= MAX_TOASTS) {
        dismiss(cont.children[0]);
      }

      var type = options.type || "info";
      if (type === "warn") type = "warning";
      if (type === "good") type = "success";
      if (type === "destructive") type = "error";

      var icons = {
        success: "check_circle",
        error: "error",
        warning: "warning",
        info: "info",
        danger: "error"
      };

      var toast = document.createElement("div");
      toast.className = "km-toast km-toast--" + type;
      toast.setAttribute("role", type === "error" || type === "danger" ? "alert" : "status");

      var iconWrap = document.createElement("span");
      iconWrap.className = "km-toast__icon";
      iconWrap.appendChild(createIconElement(options.icon || icons[type] || "info"));
      toast.appendChild(iconWrap);

      var body = document.createElement("div");
      body.className = "km-toast__body";

      var title = document.createElement("div");
      title.className = "km-toast__title";
      title.textContent = options.title || "";
      body.appendChild(title);

      if (options.message) {
        if (typeof options.message === "string") {
          var msg = document.createElement("div");
          msg.className = "km-toast__message";
          msg.textContent = options.message;
          body.appendChild(msg);
        } else if (options.message instanceof Node) {
          var msg = document.createElement("div");
          msg.className = "km-toast__message";
          msg.appendChild(options.message);
          body.appendChild(msg);
        }
      }
      toast.appendChild(body);

      if (options.action && options.action.label) {
        var actBtn = document.createElement("button");
        actBtn.type = "button";
        actBtn.className = "km-toast__action";
        actBtn.textContent = options.action.label;
        actBtn.addEventListener("click", function (e) {
          e.stopPropagation();
          if (typeof options.action.onClick === "function") options.action.onClick();
          dismiss(toast);
        });
        toast.appendChild(actBtn);
      }

      var closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.className = "km-toast__close";
      closeBtn.setAttribute("aria-label", "Закрыть");
      closeBtn.appendChild(createIconElement("close"));
      closeBtn.addEventListener("click", function () {
        dismiss(toast);
      });
      toast.appendChild(closeBtn);

      cont.appendChild(toast);

      window.requestAnimationFrame(function () {
        toast.classList.add("is-visible");
      });

      var duration = options.duration !== undefined
        ? options.duration
        : (type === "error" || type === "danger" ? 7500 : (type === "warning" ? 5500 : 3500));

      function startTimer() {
        if (duration > 0) {
          toast._timer = window.setTimeout(function () {
            dismiss(toast);
          }, duration);
        }
      }

      function stopTimer() {
        if (toast._timer) {
          window.clearTimeout(toast._timer);
          toast._timer = null;
        }
      }

      // Pause on hover
      toast.addEventListener("mouseenter", stopTimer);
      toast.addEventListener("mouseleave", startTimer);

      startTimer();

      return toast;
    }

    function makeToastHelper(type) {
      return function (title, message, action) {
        if (typeof message === "object" && message !== null && !(message instanceof Node)) {
          var opts = { type: type, title: title };
          for (var key in message) {
            if (Object.prototype.hasOwnProperty.call(message, key)) {
              opts[key] = message[key];
            }
          }
          return show(opts);
        }
        return show({ type: type, title: title, message: message, action: action });
      };
    }

    return {
      show: show,
      dismiss: dismiss,
      clearAll: clearAll,
      success: makeToastHelper("success"),
      error: makeToastHelper("error"),
      warning: makeToastHelper("warning"),
      info: makeToastHelper("info")
    };
  })();

  return {
    kmModal: kmModal,
    kmToast: kmToast,
    kmConfirm: kmModal.confirm,
    kmAlert: kmModal.alert
  };
});
