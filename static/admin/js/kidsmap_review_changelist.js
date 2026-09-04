(function () {
  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
      return;
    }
    document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var form = document.getElementById("changelist-form");
    var bulkBar = document.querySelector(".km-place-bulk-bar");
    if (!form || !bulkBar) {
      return;
    }

    var rowCheckboxes = Array.prototype.slice.call(form.querySelectorAll("input.action-select"));
    var actionSelects = Array.prototype.slice.call(form.querySelectorAll('select[name="action"]'));
    var actionButtons = Array.prototype.slice.call(bulkBar.querySelectorAll("[data-action]"));
    var countNode = bulkBar.querySelector(".km-place-bulk-bar__count");
    var textNode = bulkBar.querySelector(".km-place-bulk-bar__text");
    var emptyLabel = bulkBar.dataset.emptyLabel || "";
    var selectedLabel = bulkBar.dataset.selectedLabel || "{count}";

    function selectedCount() {
      return rowCheckboxes.filter(function (checkbox) { return checkbox.checked; }).length;
    }

    function ensureIndexField() {
      var existing = form.querySelector('input[name="index"]');
      if (existing) {
        existing.value = "0";
        return;
      }
      var input = document.createElement("input");
      input.type = "hidden";
      input.name = "index";
      input.value = "0";
      form.appendChild(input);
    }

    function setActionValue(actionName) {
      actionSelects.forEach(function (select) { select.value = actionName; });
    }

    function refreshState() {
      var count = selectedCount();
      bulkBar.classList.toggle("is-active", count > 0);
      countNode.textContent = String(count);
      textNode.textContent = count > 0 ? selectedLabel.replace("{count}", String(count)) : emptyLabel;
      actionButtons.forEach(function (button) { button.disabled = count === 0; });
    }

    function toggleAll(checked) {
      rowCheckboxes.forEach(function (checkbox) { checkbox.checked = checked; });
      var master = form.querySelector("#action-toggle");
      if (master) {
        master.checked = checked;
      }
      refreshState();
    }

    bulkBar.addEventListener("click", function (event) {
      var selectionButton = event.target.closest("[data-bulk-select]");
      if (selectionButton) {
        event.preventDefault();
        if (selectionButton.dataset.bulkSelect === "page") {
          toggleAll(true);
        }
        if (selectionButton.dataset.bulkSelect === "clear") {
          toggleAll(false);
        }
        return;
      }

      var actionButton = event.target.closest("[data-action]");
      if (!actionButton || actionButton.disabled) {
        return;
      }
      event.preventDefault();

      var count = selectedCount();
      if (!count) {
        refreshState();
        return;
      }

      if (actionButton.dataset.confirm) {
        var message = actionButton.dataset.confirm.replace("{count}", String(count));
        if (window.kmModal) {
          window.kmModal.confirm({
            title: 'Подтвердите действие',
            message: message,
            iconTone: 'warning',
            confirmText: 'Применить',
            cancelText: 'Отмена',
            isAlertDialog: true
          }).then(function (confirmed) {
            if (!confirmed) return;
            setActionValue(actionButton.dataset.action);
            ensureIndexField();
            if (typeof form.requestSubmit === "function") {
              form.requestSubmit();
            } else {
              form.submit();
            }
          });
          return;
        } else if (!window.confirm(message)) {
          return;
        }
      }

      setActionValue(actionButton.dataset.action);
      ensureIndexField();
      if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
      } else {
        form.submit();
      }
    });

    rowCheckboxes.forEach(function (checkbox) {
      checkbox.addEventListener("change", refreshState);
    });

    var masterCheckbox = form.querySelector("#action-toggle");
    if (masterCheckbox) {
      masterCheckbox.addEventListener("change", refreshState);
    }

    refreshState();
  });
})();
