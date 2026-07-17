(function () {
  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
      return;
    }
    document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    Array.prototype.slice.call(
      document.querySelectorAll("[data-filter-select]")
    ).forEach(function (select) {
      select.addEventListener("pointerdown", function () {
        select.focus();
      });

      select.addEventListener("change", function () {
        if (!select.value) {
          return;
        }
        window.location.href = select.value;
      });
    });

    var form = document.getElementById("changelist-form");
    var bulkBar = document.querySelector(".place-admin-dashboard__bulk-bar");
    if (!form || !bulkBar) {
      return;
    }

    var rowCheckboxes = Array.prototype.slice.call(
      form.querySelectorAll('input.action-select')
    );
    var actionSelects = Array.prototype.slice.call(
      form.querySelectorAll('select[name="action"]')
    );
    var actionButtons = Array.prototype.slice.call(
      bulkBar.querySelectorAll("[data-action]")
    );
    var countNode = bulkBar.querySelector(".place-admin-dashboard__bulk-count");
    var textNode = bulkBar.querySelector(".place-admin-dashboard__bulk-text");
    var emptyLabel = bulkBar.dataset.emptyLabel || "";
    var selectedLabel = bulkBar.dataset.selectedLabel || "{count}";

    function selectedCount() {
      return rowCheckboxes.filter(function (checkbox) {
        return checkbox.checked;
      }).length;
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
      actionSelects.forEach(function (select) {
        select.value = actionName;
      });
    }

    function refreshState() {
      var count = selectedCount();
      bulkBar.classList.toggle("is-active", count > 0);
      countNode.textContent = String(count);
      textNode.textContent = count > 0
        ? (
          selectedLabel.indexOf("{count}") >= 0
            ? selectedLabel.replace("{count}", String(count))
            : selectedLabel
        )
        : emptyLabel;
      actionButtons.forEach(function (button) {
        button.disabled = count === 0;
      });
    }

    function toggleAll(checked) {
      rowCheckboxes.forEach(function (checkbox) {
        checkbox.checked = checked;
      });
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

      function executeBulkAction() {
        setActionValue(actionButton.dataset.action);
        ensureIndexField();
        if (typeof form.requestSubmit === "function") {
          form.requestSubmit();
        } else {
          form.submit();
        }
      }

      var confirmTemplate = actionButton.dataset.confirm;
      if (confirmTemplate) {
        var confirmMessage = confirmTemplate.replace("{count}", String(count));
        if (typeof Swal !== "undefined") {
          var isDanger = actionButton.classList.contains("place-admin-dashboard__bulk-action--danger");
          Swal.fire({
            title: isDanger ? "Переместить в удаленные?" : "Подтвердите действие",
            text: confirmMessage,
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: isDanger ? "#ef4444" : "#10b981",
            cancelButtonColor: "#475569",
            confirmButtonText: "Да, продолжить",
            cancelButtonText: "Отмена",
            background: document.body.classList.contains("dark-mode") ? "#1e293b" : "#ffffff",
            color: document.body.classList.contains("dark-mode") ? "#f8fafc" : "#0f172a",
          }).then(function (result) {
            if (result.isConfirmed) {
              executeBulkAction();
            }
          });
        } else {
          if (window.confirm(confirmMessage)) {
            executeBulkAction();
          }
        }
      } else {
        executeBulkAction();
      }
    });

    // Intercept individual row delete action to show SweetAlert2
    document.addEventListener("click", function (event) {
      var visibilityButton = event.target.closest("[data-place-visibility-url]");
      if (visibilityButton) {
        event.preventDefault();
        var visibilityForm = document.createElement("form");
        visibilityForm.method = "POST";
        visibilityForm.action = visibilityButton.dataset.placeVisibilityUrl;

        var visibilityCsrf = document.createElement("input");
        visibilityCsrf.type = "hidden";
        visibilityCsrf.name = "csrfmiddlewaretoken";
        visibilityCsrf.value = document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
        visibilityForm.appendChild(visibilityCsrf);
        document.body.appendChild(visibilityForm);
        visibilityForm.submit();
        return;
      }

      var deleteLink = event.target.closest(".km-admin-action-menu__link--danger");
      if (!deleteLink) {
        return;
      }
      event.preventDefault();
      var href = deleteLink.href;

      if (typeof Swal !== "undefined") {
        Swal.fire({
          title: "Переместить в удаленные?",
          text: "Карточка скроется с сайта, но её можно будет восстановить из админки.",
          icon: "warning",
          showCancelButton: true,
          confirmButtonColor: "#ef4444",
          cancelButtonColor: "#475569",
          confirmButtonText: "Да, переместить",
          cancelButtonText: "Отмена",
          background: document.body.classList.contains("dark-mode") ? "#1e293b" : "#ffffff",
          color: document.body.classList.contains("dark-mode") ? "#f8fafc" : "#0f172a",
        }).then(function (result) {
          if (result.isConfirmed) {
            // Direct POST to Django delete url bypasses confirmation page
            var directForm = document.createElement("form");
            directForm.method = "POST";
            directForm.action = href;

            var csrfInput = document.createElement("input");
            csrfInput.type = "hidden";
            csrfInput.name = "csrfmiddlewaretoken";
            csrfInput.value = document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
            directForm.appendChild(csrfInput);

            var postInput = document.createElement("input");
            postInput.type = "hidden";
            postInput.name = "post";
            postInput.value = "yes";
            directForm.appendChild(postInput);

            document.body.appendChild(directForm);
            directForm.submit();
          }
        });
      } else {
        if (window.confirm("Переместить в удаленные? Карточка скроется с сайта.")) {
          window.location.href = href;
        }
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
    refreshState();
  });

  // Placeholder labels for selects
  ready(function () {
    var placeholders = {
      'category': 'Все категории',
      'district': 'Все районы',
      'status': 'Все статусы'
    };
    
    var selects = document.querySelectorAll('.km-admin-select-placeholder');
    for (var i = 0; i < selects.length; i++) {
      var select = selects[i];
      var field = select.dataset.field;
      if (!field || !placeholders[field]) continue;
      
      var options = select.options;
      if (options.length > 0) {
        options[0].text = placeholders[field];
      }
    }
  });

  ready(function () {
    var root = document.querySelector("[data-search-suggest-root]");
    if (!root) {
      return;
    }

    var input = root.querySelector(".place-admin-dashboard__search-input");
    var form = document.getElementById("changelist-search");
    var dropdown = root.querySelector("[data-search-suggestions]");
    var suggestionsUrl = root.dataset.suggestionsUrl || "";
    var emptyLabel = root.dataset.suggestionsEmpty || "Nothing found";
    var requestTimer = null;
    var activeIndex = -1;

    if (!input || !form || !dropdown || !suggestionsUrl) {
      return;
    }

    function items() {
      return Array.prototype.slice.call(
        dropdown.querySelectorAll("[data-search-suggestion-item]")
      );
    }

    function closeDropdown() {
      dropdown.hidden = true;
      dropdown.innerHTML = "";
      activeIndex = -1;
      input.setAttribute("aria-expanded", "false");
    }

    function markActive(nextIndex) {
      var nodes = items();
      activeIndex = nextIndex;
      nodes.forEach(function (node, index) {
        var isActive = index === activeIndex;
        node.classList.toggle("is-active", isActive);
        if (isActive) {
          input.setAttribute("aria-activedescendant", node.id);
        }
      });
      if (activeIndex < 0) {
        input.removeAttribute("aria-activedescendant");
      }
    }

    function applySuggestion(value) {
      input.value = value || "";
      closeDropdown();
      if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
      } else {
        form.submit();
      }
    }

    function renderResults(results) {
      if (!results.length) {
        dropdown.innerHTML =
          '<div class="place-admin-dashboard__search-suggestion-empty">' +
          emptyLabel +
          "</div>";
        dropdown.hidden = false;
        input.setAttribute("aria-expanded", "true");
        markActive(-1);
        return;
      }

      dropdown.innerHTML = results.map(function (item, index) {
        var safeLabel = String(item.label || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        var safeMeta = String(item.meta || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        var safeValue = String(item.value || "").replace(/"/g, "&quot;");
        return (
          '<button type="button" class="place-admin-dashboard__search-suggestion" ' +
          'id="place-search-suggestion-' + index + '" ' +
          'data-search-suggestion-item data-value="' + safeValue + '" role="option">' +
          '<span class="place-admin-dashboard__search-suggestion-title">' + safeLabel + '</span>' +
          (safeMeta ? '<span class="place-admin-dashboard__search-suggestion-meta">' + safeMeta + "</span>" : "") +
          "</button>"
        );
      }).join("");

      dropdown.hidden = false;
      input.setAttribute("aria-expanded", "true");
      markActive(-1);
    }

    function fetchSuggestions() {
      var query = (input.value || "").trim();
      if (query.length < 2) {
        closeDropdown();
        return;
      }

      var url = suggestionsUrl + "?q=" + encodeURIComponent(query);
      window.fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin"
      })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("bad_response");
          }
          return response.json();
        })
        .then(function (payload) {
          renderResults(Array.isArray(payload.results) ? payload.results : []);
        })
        .catch(function () {
          closeDropdown();
        });
    }

    input.addEventListener("input", function () {
      if (requestTimer) {
        window.clearTimeout(requestTimer);
      }
      requestTimer = window.setTimeout(fetchSuggestions, 140);
    });

    input.addEventListener("keydown", function (event) {
      var nodes = items();
      if (!nodes.length || dropdown.hidden) {
        return;
      }

      if (event.key === "ArrowDown") {
        event.preventDefault();
        markActive(Math.min(activeIndex + 1, nodes.length - 1));
        return;
      }

      if (event.key === "ArrowUp") {
        event.preventDefault();
        markActive(Math.max(activeIndex - 1, 0));
        return;
      }

      if (event.key === "Enter" && activeIndex >= 0 && nodes[activeIndex]) {
        event.preventDefault();
        applySuggestion(nodes[activeIndex].dataset.value || "");
        return;
      }

      if (event.key === "Escape") {
        closeDropdown();
      }
    });

    dropdown.addEventListener("click", function (event) {
      var button = event.target.closest("[data-search-suggestion-item]");
      if (!button) {
        return;
      }
      applySuggestion(button.dataset.value || "");
    });

    document.addEventListener("click", function (event) {
      if (!root.contains(event.target)) {
        closeDropdown();
      }
    });
  });
})();
