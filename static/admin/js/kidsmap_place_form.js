(function () {
  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
      return;
    }
    document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var form = document.querySelector("[data-km-admin-form]") || document.getElementById("place_form");
    var sections = Array.prototype.slice.call(document.querySelectorAll("[data-place-accordion-section]"));
    if (!form || !sections.length) {
      return;
    }

    var storageKey = "kidsmap:place-form:accordion:" + (form.dataset.placeAccordionKey || "default");
    var savedState = {};
    try {
      savedState = JSON.parse(window.localStorage.getItem(storageKey) || "{}") || {};
    } catch (error) {}

    function sectionHasErrors(section) {
      return !!section.querySelector(".errorlist, .errors, .errornote, [aria-invalid='true']");
    }

    function sectionIsComplete(section) {
      if (sectionHasErrors(section)) {
        return false;
      }
      var required = Array.prototype.slice.call(section.querySelectorAll("input[required], select[required], textarea[required]"))
        .filter(function (field) { return field.type !== "hidden" && !field.disabled; });
      return required.length > 0 && required.every(function (field) {
        return field.type === "checkbox" || field.type === "radio" ? field.checked : !!String(field.value || "").trim();
      });
    }

    function persist() {
      var state = {};
      sections.forEach(function (section) { state[section.id] = !section.classList.contains("is-collapsed"); });
      try { window.localStorage.setItem(storageKey, JSON.stringify(state)); } catch (error) {}
    }

    function setExpanded(section, expanded, shouldPersist) {
      if (sectionHasErrors(section)) { expanded = true; }
      section.classList.toggle("is-collapsed", !expanded);
      section.classList.toggle("has-errors", sectionHasErrors(section));
      section.classList.toggle("is-complete", sectionIsComplete(section));
      var toggle = section.querySelector("[data-place-section-toggle]");
      if (toggle) { toggle.setAttribute("aria-expanded", String(expanded)); }
      if (shouldPersist) { persist(); }
    }

    var initialId = (window.location.hash || "").replace("#", "") || sections[0].id;
    sections.forEach(function (section) {
      var hasSaved = Object.prototype.hasOwnProperty.call(savedState, section.id);
      setExpanded(section, sectionHasErrors(section) || (hasSaved ? !!savedState[section.id] : section.id === initialId), false);
      var toggle = section.querySelector("[data-place-section-toggle]");
      if (toggle) {
        toggle.addEventListener("click", function () {
          setExpanded(section, section.classList.contains("is-collapsed"), true);
        });
      }
    });

    document.querySelectorAll("[data-place-accordion-collapse-all]").forEach(function (button) {
      button.addEventListener("click", function () { sections.forEach(function (section) { setExpanded(section, false, false); }); persist(); });
    });
    document.querySelectorAll("[data-place-accordion-expand-all]").forEach(function (button) {
      button.addEventListener("click", function () { sections.forEach(function (section) { setExpanded(section, true, false); }); persist(); });
    });

    document.addEventListener("click", function (event) {
      var link = event.target.closest("a[href^='#']");
      if (!link) { return; }
      var id = (link.getAttribute("href") || "").slice(1);
      var section = document.getElementById(id);
      if (section && section.matches("[data-place-accordion-section]")) { setExpanded(section, true, true); }
    });

    form.addEventListener("input", function () { sections.forEach(function (section) { setExpanded(section, !section.classList.contains("is-collapsed"), false); }); });
    form.addEventListener("change", function () { sections.forEach(function (section) { setExpanded(section, !section.classList.contains("is-collapsed"), false); }); });
  });

  ready(function () {
    var sectionNodes = Array.prototype.slice.call(
      document.querySelectorAll("[data-km-admin-section], [data-place-section]")
    );
    var stepLinks = Array.prototype.slice.call(
      document.querySelectorAll("[data-km-admin-step-link], [data-place-step-link]")
    );

    function activateCurrentStep() {
      if (!sectionNodes.length || !stepLinks.length) {
        return;
      }

      var current = sectionNodes[0];
      sectionNodes.forEach(function (section) {
        var rect = section.getBoundingClientRect();
        if (rect.top <= 180 && rect.bottom > 180) {
          current = section;
        }
      });

      stepLinks.forEach(function (link) {
        var targetId = (link.getAttribute("href") || "").replace("#", "");
        link.classList.toggle("is-active", targetId === current.id);
      });
    }

    activateCurrentStep();
    window.addEventListener("scroll", activateCurrentStep, { passive: true });
    window.addEventListener("resize", activateCurrentStep);
  });

  ready(function () {
    var form = document.querySelector("[data-km-admin-form]") || document.getElementById("place_form");
    var checkbox = document.getElementById("id_is_temporary");
    var statusSelect = document.getElementById("id_status");
    if (!form) {
      return;
    }

    var startRow = document.querySelector(".field-temporary_start");
    var endRow = document.querySelector(".field-temporary_end");
    var rejectionRow = document.querySelector(".field-rejection_reason");

    function syncTemporaryRows() {
      if (!checkbox) {
        return;
      }
      var visible = checkbox.checked;
      [startRow, endRow].forEach(function (row) {
        if (!row) {
          return;
        }
        var hasErrors = !!row.querySelector(".errorlist");
        row.style.display = visible || hasErrors ? "" : "none";
      });
    }

    function syncRejectedReason() {
      if (!statusSelect || !rejectionRow) {
        return;
      }
      var rejectedValue = form.dataset.rejectedStatus || "rejected";
      var hasErrors = !!rejectionRow.querySelector(".errorlist");
      rejectionRow.style.display =
        statusSelect.value === rejectedValue || hasErrors ? "" : "none";
    }

    if (checkbox) {
      checkbox.addEventListener("change", syncTemporaryRows);
    }
    if (statusSelect) {
      statusSelect.addEventListener("change", syncRejectedReason);
    }
    syncTemporaryRows();
    syncRejectedReason();
  });

  ready(function () {
    var form = document.querySelector("[data-km-admin-form]") || document.getElementById("place_form");
    var configNode = document.getElementById("km-place-taxonomy-config");
    if (!form || !configNode || form.dataset.kmTaxonomyPickerBound === "1") {
      return;
    }

    var categorySelect = form.querySelector('select[name="category"]');
    var subcategorySelect = form.querySelector('select[name="subcategory"]');
    if (!categorySelect || !subcategorySelect) {
      return;
    }

    var config = {};
    try {
      config = JSON.parse(configNode.textContent || "{}");
    } catch (error) {
      config = {};
    }

    var categories = Array.isArray(config.categories) ? config.categories : [];
    var subcategories = Array.isArray(config.subcategories) ? config.subcategories : [];
    if (!categories.length) {
      return;
    }

    var categoryField = categorySelect.closest(".field-category") || categorySelect.closest(".form-group");
    var subcategoryField = subcategorySelect.closest(".field-subcategory") || subcategorySelect.closest(".form-group");
    var anchor = categoryField && categoryField.parentElement ? categoryField.parentElement : categoryField;
    if (!anchor || !anchor.parentElement) {
      return;
    }

    function dispatchChange(select) {
      select.dispatchEvent(new Event("change", { bubbles: true }));
      if (window.$ && window.$.fn) {
        try {
          window.$(select).trigger("change");
        } catch (error) {}
      }
    }

    function optionExists(select, value) {
      return Array.prototype.some.call(select.options, function (option) {
        return String(option.value) === String(value);
      });
    }

    function makeIcon(category) {
      var iconWrap = document.createElement("span");
      iconWrap.className = "km-taxonomy-card__icon";
      iconWrap.style.backgroundColor = category.color_bg || "#eef7f1";
      iconWrap.style.color = category.color_text || "#087443";

      if (category.icon && /\.svg(?:$|\?)/i.test(category.icon)) {
        var mask = document.createElement("span");
        mask.className = "km-taxonomy-card__icon-mask";
        mask.style.webkitMaskImage = "url('" + category.icon.replace(/'/g, "%27") + "')";
        mask.style.maskImage = "url('" + category.icon.replace(/'/g, "%27") + "')";
        iconWrap.appendChild(mask);
      } else if (category.icon) {
        var img = document.createElement("img");
        img.src = category.icon;
        img.alt = "";
        img.loading = "lazy";
        iconWrap.appendChild(img);
      } else if (category.icon_class) {
        var icon = document.createElement("i");
        icon.className = category.icon_class;
        icon.setAttribute("aria-hidden", "true");
        iconWrap.appendChild(icon);
      } else {
        iconWrap.textContent = String(category.label || "?").slice(0, 1).toUpperCase();
      }

      return iconWrap;
    }

    var picker = document.createElement("section");
    picker.className = "km-taxonomy-picker";
    picker.setAttribute("aria-label", "Выбор категории и подкатегории");

    var selectedBanner = document.createElement("div");
    selectedBanner.className = "km-taxonomy-selected-banner";
    selectedBanner.style.display = "none";

    var bannerLeft = document.createElement("div");
    bannerLeft.className = "km-taxonomy-selected-banner__left";

    var bannerIconWrap = document.createElement("div");
    bannerIconWrap.className = "km-taxonomy-selected-banner__icon-wrap";
    bannerLeft.appendChild(bannerIconWrap);

    var bannerText = document.createElement("div");
    bannerText.className = "km-taxonomy-selected-banner__text";

    var bannerLabel = document.createElement("span");
    bannerLabel.className = "km-taxonomy-selected-banner__label";
    bannerText.appendChild(bannerLabel);

    var bannerSublabel = document.createElement("span");
    bannerSublabel.className = "km-taxonomy-selected-banner__sublabel";
    bannerText.appendChild(bannerSublabel);

    bannerLeft.appendChild(bannerText);
    selectedBanner.appendChild(bannerLeft);

    var bannerToggleBtn = document.createElement("button");
    bannerToggleBtn.type = "button";
    bannerToggleBtn.className = "km-taxonomy-selected-banner__toggle-btn";
    bannerToggleBtn.textContent = "Изменить";
    bannerToggleBtn.addEventListener("click", function (e) {
      e.preventDefault();
      picker.classList.toggle("is-collapsed");
      bannerToggleBtn.textContent = picker.classList.contains("is-collapsed") ? "Изменить" : "Свернуть";
    });
    selectedBanner.appendChild(bannerToggleBtn);

    picker.appendChild(selectedBanner);

    var heading = document.createElement("div");
    heading.className = "km-taxonomy-picker__head";
    heading.innerHTML =
      '<div><strong>Выберите категорию</strong><span>Подкатегории появятся сразу после выбора.</span></div>';
    picker.appendChild(heading);

    var categoryGrid = document.createElement("div");
    categoryGrid.className = "km-taxonomy-grid";
    picker.appendChild(categoryGrid);

    var subcategoryPanel = document.createElement("div");
    subcategoryPanel.className = "km-taxonomy-subpanel";
    subcategoryPanel.innerHTML =
      '<div class="km-taxonomy-subpanel__head"><strong>Подкатегория</strong><span data-km-taxonomy-subhint></span></div>' +
      '<div class="km-taxonomy-subgrid" data-km-taxonomy-subgrid></div>';
    picker.appendChild(subcategoryPanel);

    var subcategoryGrid = subcategoryPanel.querySelector("[data-km-taxonomy-subgrid]");
    var subcategoryHint = subcategoryPanel.querySelector("[data-km-taxonomy-subhint]");
    var categoryButtons = {};
    var subcategoryButtons = {};

    categories.forEach(function (category) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "km-taxonomy-card";
      button.dataset.categoryCode = category.code;
      button.style.setProperty("--km-taxonomy-accent", category.color_text || "#087443");
      button.appendChild(makeIcon(category));

      var copy = document.createElement("span");
      copy.className = "km-taxonomy-card__copy";
      var title = document.createElement("strong");
      title.textContent = category.label || category.code;
      var meta = document.createElement("small");
      var count = Number(category.subcategory_count || 0);
      meta.textContent = count
        ? count + " подкатегорий"
        : "без подкатегорий";
      copy.appendChild(title);
      copy.appendChild(meta);
      button.appendChild(copy);

      button.addEventListener("click", function () {
        categorySelect.value = category.code;
        if (!optionExists(categorySelect, category.code)) {
          return;
        }
        dispatchChange(categorySelect);
        if (!subcategories.some(function (item) { return item.category === category.code; })) {
          subcategorySelect.value = "";
          dispatchChange(subcategorySelect);
        }
        window.setTimeout(render, 0);
      });

      categoryButtons[category.code] = button;
      categoryGrid.appendChild(button);
    });

    function renderSubcategories(selectedCategory) {
      subcategoryGrid.innerHTML = "";
      subcategoryButtons = {};

      var items = subcategories.filter(function (item) {
        return String(item.category) === String(selectedCategory || "");
      });

      subcategoryPanel.classList.toggle("is-disabled", !selectedCategory);
      if (!selectedCategory) {
        subcategoryHint.textContent = "Сначала выберите категорию.";
        return;
      }
      if (!items.length) {
        subcategoryHint.textContent = "Для этой категории подкатегории не нужны.";
        return;
      }

      subcategoryHint.textContent = items.length + " вариантов";
      items.forEach(function (item) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = "km-taxonomy-chip";
        button.dataset.subcategoryId = item.id;
        button.textContent = item.label;
        button.addEventListener("click", function () {
          if (!optionExists(subcategorySelect, item.id)) {
            return;
          }
          subcategorySelect.value = item.id;
          dispatchChange(subcategorySelect);
          render();
        });
        subcategoryButtons[item.id] = button;
        subcategoryGrid.appendChild(button);
      });
    }

    var initialCollapsedApplied = false;

    function render() {
      var selectedCategory = String(categorySelect.value || "");
      var selectedSubcategory = String(subcategorySelect.value || "");

      Object.keys(categoryButtons).forEach(function (code) {
        var active = code === selectedCategory;
        categoryButtons[code].classList.toggle("is-active", active);
        categoryButtons[code].setAttribute("aria-pressed", active ? "true" : "false");
      });

      renderSubcategories(selectedCategory);

      Object.keys(subcategoryButtons).forEach(function (id) {
        var active = id === selectedSubcategory;
        subcategoryButtons[id].classList.toggle("is-active", active);
        subcategoryButtons[id].setAttribute("aria-pressed", active ? "true" : "false");
      });

      if (selectedCategory) {
        var catObj = categories.find(function (c) { return String(c.code) === selectedCategory; });
        if (catObj) {
          bannerIconWrap.innerHTML = "";
          bannerIconWrap.appendChild(makeIcon(catObj));
          bannerLabel.textContent = catObj.label || catObj.code;

          var subObj = subcategories.find(function (s) { return String(s.id) === selectedSubcategory; });
          if (subObj) {
            bannerSublabel.textContent = " › " + subObj.label;
          } else {
            bannerSublabel.textContent = "";
          }
          selectedBanner.style.display = "flex";

          if (!initialCollapsedApplied) {
            picker.classList.add("is-collapsed");
            bannerToggleBtn.textContent = "Изменить";
            initialCollapsedApplied = true;
          }
        }
      } else {
        selectedBanner.style.display = "none";
        picker.classList.remove("is-collapsed");
        initialCollapsedApplied = true;
      }
    }

    anchor.parentElement.insertBefore(picker, anchor);
    if (categoryField) categoryField.classList.add("km-taxonomy-native-field");
    if (subcategoryField) subcategoryField.classList.add("km-taxonomy-native-field");
    form.dataset.kmTaxonomyPickerBound = "1";

    categorySelect.addEventListener("change", function () {
      window.setTimeout(render, 0);
    });
    subcategorySelect.addEventListener("change", render);
    render();
  });

  ready(function () {
    var form = document.querySelector("[data-km-admin-form]") || document.getElementById("place_form");
    var configNode =
      document.getElementById("km-admin-progress-config") ||
      document.getElementById("km-place-progress-config");
    if (!form || !configNode) {
      return;
    }

    var checklistItems = [];
    try {
      checklistItems = JSON.parse(configNode.textContent || "[]");
    } catch (error) {
      checklistItems = [];
    }
    if (!checklistItems.length) {
      return;
    }

    var pctNodes = Array.prototype.slice.call(
      document.querySelectorAll("[data-progress-pct]")
    );
    var doneNodes = Array.prototype.slice.call(
      document.querySelectorAll("[data-progress-done]")
    );
    var totalNodes = Array.prototype.slice.call(
      document.querySelectorAll("[data-progress-total]")
    );
    var ringNode = document.querySelector("[data-progress-ring]");
    var barNode = document.querySelector("[data-progress-bar]");
    var readinessNode = document.querySelector("[data-progress-readiness]");
    var missingListNode = document.querySelector("[data-progress-missing-list]");
    var emptyNode = document.querySelector("[data-progress-empty]");

    function hasFieldValue(item) {
      var input = document.getElementById(item.input_id);
      if (!input) {
        return !!item.initial;
      }

      if (input.type === "file") {
        var clearCheckbox = document.getElementById(item.input_id + "-clear");
        var hasSelectedFile = !!(input.files && input.files.length);
        if (clearCheckbox && clearCheckbox.checked) {
          return hasSelectedFile;
        }
        return hasSelectedFile || !!item.initial;
      }

      if (input.type === "checkbox" || input.type === "radio") {
        return !!input.checked;
      }

      if (input.tagName === "SELECT") {
        return !!(input.value || "").trim();
      }

      return !!(input.value || "").trim();
    }

    function setReadinessTone(tone) {
      if (!readinessNode) {
        return;
      }
      readinessNode.classList.remove("km-place-sidebar-badge--good");
      readinessNode.classList.remove("km-place-sidebar-badge--warn");
      readinessNode.classList.remove("km-place-sidebar-badge--muted");
      readinessNode.classList.add("km-place-sidebar-badge--" + tone);
    }

    function renderMissingItems(missing) {
      if (!missingListNode || !emptyNode) {
        return;
      }

      missingListNode.innerHTML = "";
      missing.slice(0, 5).forEach(function (item) {
        var itemNode = document.createElement("li");
        var linkNode = document.createElement("a");
        linkNode.href = "#" + item.input_id;
        linkNode.textContent = item.label;
        linkNode.className = "km-place-sidebar-missing-link";
        itemNode.appendChild(linkNode);
        missingListNode.appendChild(itemNode);
      });

      var hasMissing = missing.length > 0;
      missingListNode.hidden = !hasMissing;
      emptyNode.hidden = hasMissing;
      if (!hasMissing) {
        emptyNode.textContent = form.dataset.progressEmptyText || "";
      }
    }

    function updateProgress() {
      var completed = 0;
      var missing = [];
      var total = checklistItems.length;

      checklistItems.forEach(function (item) {
        var input = document.getElementById(item.input_id);
        var fieldGroup = input ? input.closest('.form-group, .fieldBox') : null;
        
        if (hasFieldValue(item)) {
          completed += 1;
          if (fieldGroup) fieldGroup.classList.remove('km-field-missing-highlight');
          return;
        }
        missing.push(item);
        if (fieldGroup) fieldGroup.classList.add('km-field-missing-highlight');
      });

      var pct = total ? Math.round((completed / total) * 100) : 0;
      pctNodes.forEach(function (node) {
        node.textContent = pct + "%";
      });
      doneNodes.forEach(function (node) {
        node.textContent = String(completed);
      });
      totalNodes.forEach(function (node) {
        node.textContent = String(total);
      });

      if (ringNode) {
        ringNode.style.setProperty("--km-place-progress", String(pct));
      }
      if (barNode) {
        barNode.style.width = pct + "%";
      }

      var publishBtn = document.getElementById("km-publish-btn");
      if (publishBtn) {
        if (missing.length === 0) {
          publishBtn.removeAttribute("disabled");
        } else {
          publishBtn.setAttribute("disabled", "disabled");
        }
      }

      var publishMobileBtn = document.getElementById("km-publish-mobile-btn");
      if (publishMobileBtn) {
        if (missing.length === 0) {
          publishMobileBtn.removeAttribute("disabled");
        } else {
          publishMobileBtn.setAttribute("disabled", "disabled");
        }
      }

      if (readinessNode) {
        var isComplete = missing.length === 0;
        readinessNode.textContent = isComplete
          ? form.dataset.progressCompleteLabel || ""
          : form.dataset.progressIncompleteLabel || "";
        setReadinessTone(
          isComplete
            ? form.dataset.progressCompleteTone || "good"
            : form.dataset.progressIncompleteTone || "warn"
        );
      }

      renderMissingItems(missing);
    }

    form.addEventListener("input", updateProgress);
    form.addEventListener("change", updateProgress);
    updateProgress();
  });

  ready(function () {
    var phoneInputs = Array.prototype.slice.call(
      document.querySelectorAll('input[data-km-az-phone="1"]')
    );

    function formatAzerbaijanPhone(value) {
      var digits = String(value || "").replace(/\D/g, "");
      var national = digits;

      if (national.slice(0, 3) === "994") {
        national = national.slice(3);
      } else if (national.slice(0, 1) === "0") {
        national = national.slice(1);
      }

      national = national.slice(0, 9);
      if (!national) {
        return "";
      }

      var parts = [];
      [[0, 2], [2, 5], [5, 7], [7, 9]].forEach(function (range) {
        var chunk = national.slice(range[0], range[1]);
        if (chunk) {
          parts.push(chunk);
        }
      });
      return "+994 " + parts.join(" ");
    }

    function syncPhoneInput(input) {
      if (!input) {
        return;
      }
      var formatted = formatAzerbaijanPhone(input.value);
      input.value = formatted;
      var nationalLength = formatted.replace(/\D/g, "").replace(/^994/, "").length;
      if (!formatted || nationalLength === 9) {
        input.setCustomValidity("");
      } else {
        input.setCustomValidity("Введите номер в формате +994 50 123 45 67");
      }
    }

    phoneInputs.forEach(function (input) {
      syncPhoneInput(input);
      input.addEventListener("input", function () {
        syncPhoneInput(input);
      });
      input.addEventListener("blur", function () {
        syncPhoneInput(input);
      });
    });
  });

  ready(function () {
    var azRow = document.querySelector('.form-group.field-name_az.field-description_az');
    var ruRow = document.querySelector('.form-group.field-name_ru.field-description_ru');
    var enRow = document.querySelector('.form-group.field-name_en.field-description_en');

    if (!azRow || !ruRow || !enRow) {
      return;
    }

    var tabsContainer = document.createElement('div');
    tabsContainer.className = 'km-lang-tabs';

    var tabs = [
      { id: 'az', label: 'Азербайджанский (Основной)', element: azRow },
      { id: 'ru', label: 'Русский', element: ruRow },
      { id: 'en', label: 'English', element: enRow }
    ];

    var tabButtons = {};

    tabs.forEach(function (tab) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'km-lang-tab-btn';
      btn.textContent = tab.label;
      
      var hasErrors = !!tab.element.querySelector('.errorlist');
      if (hasErrors) {
        btn.classList.add('has-error');
        var badge = document.createElement('span');
        badge.className = 'error-badge';
        badge.textContent = '!';
        btn.appendChild(badge);
      }

      btn.addEventListener('click', function () {
        setActiveTab(tab.id);
      });

      tabsContainer.appendChild(btn);
      tabButtons[tab.id] = btn;
    });

    azRow.parentNode.insertBefore(tabsContainer, azRow);

    function setActiveTab(activeId) {
      tabs.forEach(function (tab) {
        var isActive = tab.id === activeId;
        tab.element.style.display = isActive ? '' : 'none';
        
        var btn = tabButtons[tab.id];
        if (isActive) {
          btn.classList.add('is-active');
        } else {
          btn.classList.remove('is-active');
        }
      });
    }

    // Если есть ошибка в каком-то табе, делаем его активным по умолчанию, иначе AZ
    var activeDefault = 'az';
    if (ruRow.querySelector('.errorlist')) {
      activeDefault = 'ru';
    } else if (enRow.querySelector('.errorlist')) {
      activeDefault = 'en';
    }

    setActiveTab(activeDefault);
  });

  ready(function () {
    // 0. Автоматически переносим все лейблы внутрь соответствующих .fieldBox
    document.querySelectorAll('.km-place-section .form-group, .km-place-secondary .form-group').forEach(function (formGroup) {
      var row = formGroup.querySelector('.row');
      if (!row) return;

      var fieldBoxes = row.querySelectorAll('.fieldBox');
      fieldBoxes.forEach(function (fb) {
        var label = null;
        var input = fb.querySelector('input, select, textarea');
        if (input && input.id) {
          label = row.querySelector('label[for="' + input.id + '"]');
        }
        
        // Если лейбл не найден по ID (например, readonly поле), ищем предшествующий лейбл
        if (!label) {
          var prev = fb.previousElementSibling;
          while (prev) {
            if (prev.tagName === 'LABEL') {
              label = prev;
              break;
            }
            if (prev.classList.contains('fieldBox')) {
              break;
            }
            prev = prev.previousElementSibling;
          }
        }

        if (label) {
          fb.insertBefore(label, fb.firstChild);
        }
      });
    });

    var pageLang = (document.documentElement.lang || 'ru').toLowerCase();
    var freeRangePriceHint = '0 — 0 будет показано как «Бесплатно».';
    if (pageLang.indexOf('az') === 0) {
      freeRangePriceHint = '0 — 0 pulsuz olaraq göstəriləcək.';
    } else if (pageLang.indexOf('en') === 0) {
      freeRangePriceHint = '0 — 0 will be shown as Free.';
    }

    // 1. Добавляем суффиксы к полям
    var suffixMap = [
      { id: 'id_age_from', text: 'лет' },
      { id: 'id_age_to', text: 'лет' },
      { id: 'id_lesson_duration_minutes', text: 'мин' },
      { id: 'id_price_from', text: '₼' },
      { id: 'id_price_to', text: '₼' },
      { id: 'id_price_per_lesson', text: '₼' },
      { id: 'id_price_per_month', text: '₼' },
      { id: 'id_price_per_8_lessons', text: '₼' }
    ];

    suffixMap.forEach(function (item) {
      var input = document.getElementById(item.id);
      if (!input) {
        return;
      }
      
      if (input.parentNode.classList.contains('km-input-wrapper')) {
        return;
      }

      var wrapper = document.createElement('div');
      wrapper.className = 'km-input-wrapper';

      input.parentNode.insertBefore(wrapper, input);
      wrapper.appendChild(input);

      var suffix = document.createElement('span');
      suffix.className = 'km-input-suffix';
      suffix.textContent = item.text;
      wrapper.appendChild(suffix);
    });

    // 2. Объединяем "Возраст от" и "Возраст до" в один блок диапазона
    var ageFromInput = document.getElementById('id_age_from');
    var ageToInput = document.getElementById('id_age_to');
    
    if (ageFromInput && ageToInput) {
      var fromBox = ageFromInput.closest('.fieldBox');
      var toBox = ageToInput.closest('.fieldBox');
      
      if (fromBox && toBox) {
        var row = fromBox.parentNode;
        
        var ageGroup = document.createElement('div');
        ageGroup.className = 'col-auto fieldBox km-range-fieldbox';
        
        var label = document.createElement('label');
        label.textContent = 'Возраст (от — до)';
        ageGroup.appendChild(label);
        
        var rangeContainer = document.createElement('div');
        rangeContainer.className = 'km-range-container';
        
        var fromInputWrap = fromBox.querySelector('.km-input-wrapper') || ageFromInput;
        var toInputWrap = toBox.querySelector('.km-input-wrapper') || ageToInput;
        
        rangeContainer.appendChild(fromInputWrap);
        
        var sep = document.createElement('span');
        sep.className = 'km-range-separator';
        sep.textContent = '—';
        rangeContainer.appendChild(sep);
        
        rangeContainer.appendChild(toInputWrap);
        ageGroup.appendChild(rangeContainer);
        
        // Копируем ошибки, если они есть
        var errorList = fromBox.querySelector('.errorlist') || toBox.querySelector('.errorlist');
        if (errorList) {
          ageGroup.appendChild(errorList.cloneNode(true));
          ageGroup.classList.add('errors');
        }
        
        row.insertBefore(ageGroup, fromBox);
        
        row.removeChild(fromBox);
        row.removeChild(toBox);
      }
    }

    // 3. Объединяем "Цена от" и "Цена до" в один блок диапазона
    var priceFromInput = document.getElementById('id_price_from');
    var priceToInput = document.getElementById('id_price_to');
    
    if (priceFromInput && priceToInput) {
      var fromBox = priceFromInput.closest('.fieldBox');
      var toBox = priceToInput.closest('.fieldBox');
      
      if (fromBox && toBox) {
        var row = fromBox.parentNode;
        
        var priceGroup = document.createElement('div');
        priceGroup.className = 'col-auto fieldBox km-range-fieldbox';
        
        var label = document.createElement('label');
        label.textContent = 'Цена (от — до)';
        priceGroup.appendChild(label);
        
        var rangeContainer = document.createElement('div');
        rangeContainer.className = 'km-range-container';
        
        var fromInputWrap = fromBox.querySelector('.km-input-wrapper') || priceFromInput;
        var toInputWrap = toBox.querySelector('.km-input-wrapper') || priceToInput;
        
        rangeContainer.appendChild(fromInputWrap);
        
        var sep = document.createElement('span');
        sep.className = 'km-range-separator';
        sep.textContent = '—';
        rangeContainer.appendChild(sep);
        
        rangeContainer.appendChild(toInputWrap);
        priceGroup.appendChild(rangeContainer);

        var helpText = document.createElement('p');
        helpText.className = 'help';
        helpText.textContent = freeRangePriceHint;
        priceGroup.appendChild(helpText);
        
        // Копируем ошибки, если они есть
        var errorList = fromBox.querySelector('.errorlist') || toBox.querySelector('.errorlist');
        if (errorList) {
          priceGroup.appendChild(errorList.cloneNode(true));
          priceGroup.classList.add('errors');
        }
        
        row.insertBefore(priceGroup, fromBox);
        
        row.removeChild(fromBox);
        row.removeChild(toBox);
      }
    }

    // 4. Скрываем пустые readonly-слаги на форме добавления и делаем соседние поля на всю ширину
    var slugReadonly = document.querySelector('.field-slug .readonly');
    if (slugReadonly) {
      var slugText = slugReadonly.textContent.trim();
      if (slugText === '-' || slugText === '') {
        var slugBox = slugReadonly.closest('.fieldBox');
        if (slugBox) {
          slugBox.style.display = 'none';
        }
      }
    }

    // 5. Если в строке остался только один видимый блок .fieldBox, расширяем его на всю ширину
    document.querySelectorAll('.km-place-section .form-group > .row, .km-place-secondary .form-group > .row').forEach(function(row) {
      var visibleBoxes = Array.from(row.querySelectorAll('.fieldBox')).filter(function(fb) {
        return window.getComputedStyle(fb).display !== 'none';
      });
      if (visibleBoxes.length === 1) {
        visibleBoxes[0].style.gridColumn = '1 / -1';
      }
    });
  });

  ready(function () {
    var locationSection = document.querySelector("[data-km-location-section]");
    if (!locationSection) return;

    var latInput = document.getElementById('id_lat');
    var lngInput = document.getElementById('id_lng');
    var coordBadge = locationSection.querySelector("[data-location-coordinates-badge]");
    var coordFilledLabel = coordBadge ? coordBadge.getAttribute("data-location-coordinates-label-filled") || "Координаты заполнены" : "";
    var coordMissingLabel = coordBadge ? coordBadge.getAttribute("data-location-coordinates-label-missing") || "Нужны координаты" : "";

    function syncCoordBadge() {
      if (!coordBadge) return;
      var hasLat = !!(latInput && latInput.value.trim());
      var hasLng = !!(lngInput && lngInput.value.trim());
      var hasCoordinates = hasLat && hasLng;
      coordBadge.className = "km-location-badge km-location-badge--" + (hasCoordinates ? "good" : "warn");
      coordBadge.textContent = hasCoordinates ? coordFilledLabel : coordMissingLabel;
    }

    if (latInput) latInput.addEventListener('input', syncCoordBadge);
    if (lngInput) lngInput.addEventListener('input', syncCoordBadge);
    syncCoordBadge();
  });

  ready(function () {
    var mediaSection = document.querySelector("[data-place-media-section]");
    if (!mediaSection) {
      return;
    }

    var mainInput = document.getElementById("id_photo");
    var mainPreview = mediaSection.querySelector("[data-main-photo-preview]");
    var mainPlaceholder = mediaSection.querySelector("[data-main-photo-placeholder]");
    var mainPickButton = mediaSection.querySelector("[data-main-photo-pick]");
    var mainClearButton = mediaSection.querySelector("[data-main-photo-clear]");
    var mainFileName = mediaSection.querySelector("[data-main-photo-file-name]");
    var mainFileSize = mediaSection.querySelector("[data-main-photo-file-size]");
    var mainClearCheckbox = mainInput && mainInput.id ? document.getElementById(mainInput.id + "-clear") : null;
    var mainDropzone = mediaSection.querySelector("[data-main-photo-preview-wrap]");
    var mainRoot = mediaSection.querySelector("[data-main-photo-root]");

    function formatBytes(bytes) {
      var size = Number(bytes || 0);
      if (!size) {
        return "";
      }
      var units = ["B", "KB", "MB", "GB"];
      var unitIndex = 0;
      while (size >= 1024 && unitIndex < units.length - 1) {
        size = size / 1024;
        unitIndex += 1;
      }
      return (unitIndex === 0 ? Math.round(size) : size.toFixed(size >= 10 ? 0 : 1)) + " " + units[unitIndex];
    }

    function clearPreviewImage(img) {
      if (!img) {
        return;
      }
      img.removeAttribute("src");
      img.hidden = true;
    }

    function setPreviewImage(img, url) {
      if (!img) {
        return;
      }
      img.hidden = false;
      img.src = url;
    }

    function syncMainPhotoState() {
      if (!mainInput) {
        return;
      }

      var selectedFile = mainInput.files && mainInput.files.length ? mainInput.files[0] : null;
      var isCleared = !!(mainClearCheckbox && mainClearCheckbox.checked);
      var showSelected = !!selectedFile && !isCleared;

      if (mainRoot) {
        var hasPhoto = !!(showSelected || (!isCleared && mainPreview && mainPreview.getAttribute("data-main-photo-initial-url")));
        mainRoot.classList.toggle("has-photo", hasPhoto);
      }

      if (showSelected) {
        if (mainPlaceholder) {
          mainPlaceholder.hidden = true;
        }
        var previewUrl = window.URL ? window.URL.createObjectURL(selectedFile) : "";
        if (previewUrl) {
          setPreviewImage(mainPreview, previewUrl);
          mainPreview.onload = function () {
            if (previewUrl && window.URL) {
              window.URL.revokeObjectURL(previewUrl);
            }
          };
        }
        if (mainFileName) {
          mainFileName.textContent = selectedFile.name || "";
        }
        if (mainFileSize) {
          mainFileSize.textContent = formatBytes(selectedFile.size);
        }
      } else {
        if (mainClearCheckbox && isCleared) {
          mainClearCheckbox.checked = true;
        }
        if (!isCleared && mainPreview && mainPreview.getAttribute("data-main-photo-initial-url")) {
          setPreviewImage(mainPreview, mainPreview.getAttribute("data-main-photo-initial-url"));
          if (mainFileName) {
            mainFileName.textContent = mainPreview.getAttribute("data-main-photo-initial-name") || "";
          }
          if (mainFileSize) {
            mainFileSize.textContent = formatBytes(mainPreview.getAttribute("data-main-photo-initial-size"));
          }
          if (mainPlaceholder) {
            mainPlaceholder.hidden = true;
          }
        } else {
          clearPreviewImage(mainPreview);
          if (mainPlaceholder) {
            mainPlaceholder.hidden = false;
          }
          if (mainFileName) {
            mainFileName.textContent = "Файл не выбран";
          }
          if (mainFileSize) {
            mainFileSize.textContent = "";
          }
        }
      }
    }

    function clearMainPhoto() {
      if (mainInput) {
        mainInput.value = "";
      }
      if (mainClearCheckbox) {
        mainClearCheckbox.checked = true;
      }
      syncMainPhotoState();
    }

    if (mainInput) {
      mainInput.addEventListener("change", function () {
        if (mainClearCheckbox) {
          mainClearCheckbox.checked = false;
        }
        syncMainPhotoState();
      });
    }
    if (mainClearCheckbox) {
      mainClearCheckbox.addEventListener("change", syncMainPhotoState);
    }
    if (mainPickButton && mainInput) {
      mainPickButton.addEventListener("click", function () {
        mainInput.click();
      });
    }
    if (mainClearButton) {
      mainClearButton.addEventListener("click", clearMainPhoto);
    }
    if (mainDropzone && mainInput) {
      mainDropzone.addEventListener("click", function (event) {
        if (event.target && event.target.closest && event.target.closest("[data-main-photo-clear], [data-main-photo-pick]")) {
          return;
        }
        mainInput.click();
      });
      mainDropzone.addEventListener("dragover", function (event) {
        event.preventDefault();
        mainDropzone.classList.add("is-dragover");
      });
      mainDropzone.addEventListener("dragleave", function () {
        mainDropzone.classList.remove("is-dragover");
      });
      mainDropzone.addEventListener("drop", function (event) {
        var file = event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files[0] : null;
        if (!file) {
          return;
        }
        event.preventDefault();
        mainDropzone.classList.remove("is-dragover");
        if (typeof DataTransfer !== "undefined") {
          var transfer = new DataTransfer();
          transfer.items.add(file);
          mainInput.files = transfer.files;
          mainInput.dispatchEvent(new Event("change", { bubbles: true }));
        }
      });
    }

    syncMainPhotoState();
  });

  ready(function () {
    var galleryRoot = document.querySelector("[data-gallery-root]");
    if (!galleryRoot) {
      return;
    }
    var mediaSection = galleryRoot.closest("[data-place-media-section]") || galleryRoot.closest(".km-gallery-section") || galleryRoot.parentElement;

    var grid = galleryRoot.querySelector("[data-gallery-grid]");
    var emptyState = mediaSection ? mediaSection.querySelector("[data-gallery-empty-state]") : null;
    var galleryCountValue = mediaSection ? mediaSection.querySelector("[data-gallery-count-value]") : null;
    var galleryEmptyCount = mediaSection ? mediaSection.querySelector("[data-gallery-count-empty]") : null;
    var totalFormsInput = galleryRoot.querySelector('input[name$="-TOTAL_FORMS"]');
    var template = galleryRoot.querySelector("[data-gallery-empty-template]");
    var uploadPicker = document.createElement("input");
    var nextIndex = totalFormsInput ? parseInt(totalFormsInput.value, 10) || 0 : 0;

    uploadPicker.type = "file";
    uploadPicker.accept = "image/*";
    uploadPicker.multiple = true;
    uploadPicker.hidden = true;
    galleryRoot.appendChild(uploadPicker);

    function formatBytes(bytes) {
      var size = Number(bytes || 0);
      if (!size) {
        return "";
      }
      var units = ["B", "KB", "MB", "GB"];
      var unitIndex = 0;
      while (size >= 1024 && unitIndex < units.length - 1) {
        size = size / 1024;
        unitIndex += 1;
      }
      return (unitIndex === 0 ? Math.round(size) : size.toFixed(size >= 10 ? 0 : 1)) + " " + units[unitIndex];
    }

    function getFileNameOnly(path) {
      if (!path) return "";
      return path.substring(path.lastIndexOf('/') + 1).substring(path.lastIndexOf('\\') + 1);
    }

    function updateTotalFormsCount() {
      if (totalFormsInput) {
        totalFormsInput.value = String(nextIndex);
      }
    }

    function getCards() {
      return Array.prototype.slice.call(grid.querySelectorAll("[data-gallery-card]"));
    }

    function getActivePhotosCount() {
      return getCards().filter(function (card) {
        var deleteInput = card.querySelector('input[type="checkbox"][name$="-DELETE"]');
        var previewEl = card.querySelector("[data-gallery-preview]");
        var hasFile = hasAssignedFile(card) || (previewEl ? previewEl.getAttribute("data-gallery-initial-url") : null);
        return !card.hidden && !(deleteInput && deleteInput.checked) && hasFile;
      }).length;
    }

    function updateGalleryCounter() {
      var activeCount = getActivePhotosCount();
      if (galleryCountValue) {
        galleryCountValue.textContent = activeCount + " / 10";
      }
      if (galleryEmptyCount) {
        galleryEmptyCount.textContent = "Сейчас загружено " + activeCount + " из 10 фото";
      }
    }

    function renumberVisibleCards() {
      var order = 1;
      getCards().forEach(function (card) {
        if (card.hidden) {
          return;
        }
        var orderInput = card.querySelector('input[type="number"][name$="-order"]');
        if (orderInput) {
          orderInput.value = String(order);
        }
        order += 1;
      });
    }

    function updateGalleryEmptyState() {
      if (!emptyState) {
        return;
      }
      var visibleCards = getActivePhotosCount();
      if (visibleCards === 0) {
        emptyState.style.display = "block";
      } else {
        emptyState.style.display = "none";
      }
      updateGalleryCounter();
    }

    function setCardPreview(card, file, url) {
      var preview = card.querySelector("[data-gallery-preview]");
      var placeholder = card.querySelector("[data-gallery-placeholder]");
      var fileMeta = card.querySelector("[data-gallery-file-meta]");
      if (!preview) {
        return;
      }

      if (url) {
        preview.hidden = false;
        preview.src = url;
        preview.onload = function () {
          if (url && window.URL) {
            window.URL.revokeObjectURL(url);
          }
        };
        if (placeholder) {
          placeholder.hidden = true;
        }
        if (fileMeta) {
          fileMeta.textContent = file.name ? getFileNameOnly(file.name) : "";
        }
      } else {
        var initialUrl = preview.getAttribute("data-gallery-initial-url");
        if (initialUrl) {
          preview.hidden = false;
          preview.src = initialUrl;
          if (placeholder) {
            placeholder.hidden = true;
          }
          if (fileMeta) {
            var initialName = preview.getAttribute("data-gallery-initial-name") || "";
            fileMeta.textContent = getFileNameOnly(initialName);
          }
        } else {
          preview.removeAttribute("src");
          preview.hidden = true;
          if (placeholder) {
            placeholder.hidden = false;
          }
          if (fileMeta) {
            fileMeta.textContent = "Файл не выбран";
          }
        }
      }
      if (fileMeta && file && file.size) {
        fileMeta.textContent = getFileNameOnly(file.name || "") + (file.name ? " · " : "") + formatBytes(file.size);
      }
    }

    function getPersistedIdInput(card) {
      return card.querySelector('input[type="hidden"][name$="-id"]');
    }

    function hasAssignedFile(card) {
      var input = card.querySelector('input[type="file"]');
      return !!(input && input.files && input.files.length);
    }

    function assignFileToCard(card, file) {
      var input = card.querySelector('input[type="file"]');
      if (!input || !file) {
        return false;
      }
      if (typeof DataTransfer === "undefined") {
        return false;
      }
      var transfer = new DataTransfer();
      transfer.items.add(file);
      input.files = transfer.files;
      input.dispatchEvent(new Event("change", { bubbles: true }));
      return true;
    }

    function setCardHiddenState(card, hidden) {
      card.hidden = !!hidden;
      card.classList.toggle("is-hidden", !!hidden);
    }

    function wireCard(card) {
      var input = card.querySelector('input[type="file"]');
      var dropzone = card.querySelector("[data-gallery-dropzone]");
      var removeButton = card.querySelector("[data-gallery-remove]");
      var deleteInput = card.querySelector('input[type="checkbox"][name$="-DELETE"]');
      var orderInput = card.querySelector('input[type="number"][name$="-order"]');
      var preview = card.querySelector("[data-gallery-preview]");
      var placeholder = card.querySelector("[data-gallery-placeholder]");

      function syncFromInput() {
        var idInput = getPersistedIdInput(card);
        var persisted = !!(idInput && String(idInput.value || "").trim());
        if (deleteInput && deleteInput.checked) {
          setCardHiddenState(card, true);
          return;
        }
        var file = input && input.files && input.files.length ? input.files[0] : null;
        if (file) {
          card.dataset.galleryCardState = "filled";
          setCardHiddenState(card, false);
          if (deleteInput) {
            deleteInput.checked = false;
          }
          if (placeholder) {
            placeholder.hidden = true;
          }
          setCardPreview(card, file, window.URL ? window.URL.createObjectURL(file) : "");
          return;
        }

        if (preview && preview.getAttribute("data-gallery-initial-url")) {
          card.dataset.galleryCardState = "filled";
          preview.hidden = false;
          preview.src = preview.getAttribute("data-gallery-initial-url");
          if (placeholder) {
            placeholder.hidden = true;
          }
          if (card.querySelector("[data-gallery-file-meta]")) {
            var initialName = preview.getAttribute("data-gallery-initial-name") || "";
            var initialSize = preview.getAttribute("data-gallery-initial-size");
            var sizeStr = initialSize ? " · " + formatBytes(initialSize) : "";
            card.querySelector("[data-gallery-file-meta]").textContent = getFileNameOnly(initialName) + sizeStr;
          }
        } else {
          card.dataset.galleryCardState = "empty";
          if (preview) {
            preview.removeAttribute("src");
            preview.hidden = true;
          }
          if (placeholder) {
            placeholder.hidden = false;
          }
          if (card.querySelector("[data-gallery-file-meta]")) {
            card.querySelector("[data-gallery-file-meta]").textContent = "Файл не выбран";
          }
          setCardHiddenState(card, !persisted);
        }
      }

      if (input) {
        input.addEventListener("change", function () {
          if (deleteInput) {
            deleteInput.checked = false;
          }
          syncFromInput();
          renumberVisibleCards();
          updateGalleryEmptyState();
        });
      }

      if (dropzone) {
        dropzone.addEventListener("click", function (event) {
          if (event.target && event.target.closest && event.target.closest("[data-gallery-remove], [data-gallery-drag-handle]")) {
            return;
          }
          var isReplace = event.target.closest("[data-gallery-replace-trigger]");
          if ((card.dataset.galleryCardState === "empty" || isReplace) && input) {
            input.click();
          }
        });
        dropzone.addEventListener("dragover", function (event) {
          event.preventDefault();
          card.classList.add("is-dragover");
        });
        dropzone.addEventListener("dragleave", function () {
          card.classList.remove("is-dragover");
        });
        dropzone.addEventListener("drop", function (event) {
          var file = event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files[0] : null;
          if (!file) {
            return;
          }
          event.preventDefault();
          event.stopPropagation();
          card.classList.remove("is-dragover");
          assignFileToCard(card, file);
        });
      }

      if (removeButton) {
        removeButton.addEventListener("click", function () {
          var idInput = getPersistedIdInput(card);
          var persisted = !!(idInput && String(idInput.value || "").trim());
          if (persisted && deleteInput) {
            deleteInput.checked = true;
            setCardHiddenState(card, true);
          } else {
            if (input) {
              input.value = "";
            }
            if (deleteInput) {
              deleteInput.checked = false;
            }
            setCardHiddenState(card, true);
          }
          syncFromInput();
          renumberVisibleCards();
          updateGalleryEmptyState();
          updateAddCardVisibility();
        });
      }

      if (orderInput) {
        orderInput.addEventListener("change", function () {
          renumberVisibleCards();
          updateGalleryEmptyState();
          updateAddCardVisibility();
        });
      }

      syncFromInput();
    }

    function createCardFromTemplate() {
      if (!template) {
        return null;
      }

      var container = document.createElement("div");
      container.innerHTML = template.innerHTML.replace(/__prefix__/g, String(nextIndex));
      nextIndex += 1;
      updateTotalFormsCount();
      var card = container.firstElementChild;
      if (!card) {
        return null;
      }
      grid.appendChild(card);
      wireCard(card);
      renumberVisibleCards();
      return card;
    }

    function findReusableCard() {
      var cards = getCards();
      for (var i = 0; i < cards.length; i += 1) {
        var card = cards[i];
        if (card.hidden) {
          var idInput = getPersistedIdInput(card);
          if (!idInput || !String(idInput.value || "").trim()) {
            return card;
          }
        }
        if (!card.hidden && !hasAssignedFile(card)) {
          var existingId = getPersistedIdInput(card);
          if (!existingId || !String(existingId.value || "").trim()) {
            return card;
          }
        }
      }
      return null;
    }

    function addFiles(files) {
      var list = Array.prototype.slice.call(files || []);
      var activeCount = getActivePhotosCount();

      var allowedToAdd = 10 - activeCount;
      if (allowedToAdd <= 0) {
        alert("Максимальное количество фотографий — 10.");
        return;
      }

      var addedAny = false;
      list.slice(0, allowedToAdd).forEach(function (file) {
        if (!file || !file.type || file.type.indexOf("image/") !== 0) {
          return;
        }
        var card = findReusableCard();
        if (!card) {
          card = createCardFromTemplate();
        } else {
          setCardHiddenState(card, false);
        }
        if (!card) {
          return;
        }
        assignFileToCard(card, file);
        addedAny = true;
      });

      if (list.length > allowedToAdd) {
        alert("Превышен лимит в 10 фотографий. Добавлено только " + allowedToAdd + " шт.");
      }

      renumberVisibleCards();
      updateGalleryEmptyState();
      updateAddCardVisibility();
    }

    function updateAddCardVisibility() {
      var addCard = galleryRoot.querySelector("[data-gallery-add-button-card]");
      var topAddButton = mediaSection ? mediaSection.querySelector("[data-gallery-add-button]") : null;
      
      var activePhotosCount = getActivePhotosCount();

      if (activePhotosCount >= 10) {
        if (addCard) addCard.style.display = "none";
        if (topAddButton) topAddButton.style.display = "none";
      } else {
        if (topAddButton) topAddButton.style.display = "inline-flex";
        if (addCard) {
          if (activePhotosCount === 0) {
            addCard.style.display = "none";
          } else {
            addCard.style.display = "flex";
            grid.appendChild(addCard);
          }
        }
      }
    }

    getCards().forEach(wireCard);
    updateGalleryCounter();

    var addButtons = mediaSection
      ? mediaSection.querySelectorAll("[data-gallery-add-button], [data-gallery-add-button-empty]")
      : galleryRoot.querySelectorAll("[data-gallery-add-button], [data-gallery-add-button-empty]");
    addButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        uploadPicker.value = "";
        uploadPicker.click();
      });
    });

    var addCard = galleryRoot.querySelector("[data-gallery-add-button-card]");
    if (addCard) {
      addCard.addEventListener("click", function () {
        uploadPicker.value = "";
        uploadPicker.click();
      });
    }

    uploadPicker.addEventListener("change", function () {
      addFiles(uploadPicker.files);
      uploadPicker.value = "";
    });

    function handleEmptyStateDragOver(event) {
      event.preventDefault();
      if (emptyState) {
        emptyState.classList.add("is-dragover");
      }
    }

    function handleEmptyStateDragLeave(event) {
      if (!emptyState) {
        return;
      }
      if (event.relatedTarget && emptyState.contains(event.relatedTarget)) {
        return;
      }
      emptyState.classList.remove("is-dragover");
    }

    function handleEmptyStateDrop(event) {
      var droppedFiles = event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files : null;
      if (!droppedFiles || !droppedFiles.length) {
        return;
      }
      event.preventDefault();
      if (emptyState) {
        emptyState.classList.remove("is-dragover");
      }
      addFiles(droppedFiles);
    }

    if (emptyState) {
      emptyState.addEventListener("dragover", handleEmptyStateDragOver);
      emptyState.addEventListener("dragleave", handleEmptyStateDragLeave);
      emptyState.addEventListener("drop", handleEmptyStateDrop);
    }

    grid.addEventListener("dragover", function (event) {
      event.preventDefault();
    });

    grid.addEventListener("drop", function (event) {
      var droppedFiles = event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files : null;
      if (!droppedFiles || !droppedFiles.length) {
        return;
      }
      event.preventDefault();
      addFiles(droppedFiles);
    });

    // Drag & Drop sorting implementation
    var dragSrcEl = null;

    function handleDragStart(e) {
      if (e.target.closest('[data-gallery-remove]') || e.target.closest('[data-gallery-replace-trigger]') || e.target.closest('[data-gallery-add-button-card]')) {
        e.preventDefault();
        return;
      }
      var card = e.target.closest('[data-gallery-card]');
      if (!card) {
        return;
      }
      dragSrcEl = card;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', ''); // Required for Firefox
      card.classList.add('is-dragging');
    }

    function handleDragOver(e) {
      if (e.preventDefault) {
        e.preventDefault();
      }
      e.dataTransfer.dropEffect = 'move';
      
      var card = e.target.closest('[data-gallery-card], [data-gallery-add-button-card]');
      if (card && card !== dragSrcEl) {
        if (card.hasAttribute('data-gallery-add-button-card')) {
          grid.insertBefore(dragSrcEl, card);
        } else {
          var rect = card.getBoundingClientRect();
          var next = (e.clientX - rect.left) / (rect.right - rect.left) > 0.5;
          grid.insertBefore(dragSrcEl, next ? card.nextSibling : card);
        }
      }
      return false;
    }

    function handleDragEnd(e) {
      var cards = getCards();
      cards.forEach(function (card) {
        card.classList.remove('is-dragging');
      });
      dragSrcEl = null;
      renumberVisibleCards();
      updateGalleryEmptyState();
      updateAddCardVisibility();
    }

    grid.addEventListener('dragstart', handleDragStart);
    grid.addEventListener('dragover', handleDragOver);
    grid.addEventListener('dragend', handleDragEnd);

    renumberVisibleCards();
    updateGalleryEmptyState();
    updateAddCardVisibility();
  });

  ready(function () {
    var uploadInput = document.querySelector("[data-filepond-gallery-upload]");
    var panel = document.querySelector("[data-filepond-gallery-panel]");
    var meta = document.querySelector("[data-filepond-gallery-meta]");
    if (!uploadInput || !panel || panel.dataset.filepondReady === "1") {
      return;
    }

    function getExistingGalleryCount() {
      var cards = Array.prototype.slice.call(document.querySelectorAll("[data-gallery-card]"));
      return cards.filter(function (card) {
        if (card.hidden) {
          return false;
        }
        var deleteInput = card.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteInput && deleteInput.checked) {
          return false;
        }
        var preview = card.querySelector("[data-gallery-preview]");
        var fileInput = card.querySelector('input[type="file"]');
        return !!(
          (preview && preview.getAttribute("data-gallery-initial-url")) ||
          (fileInput && fileInput.files && fileInput.files.length)
        );
      }).length;
    }

    function updateMeta(count, maxFiles) {
      if (!meta) {
        return;
      }
      if (maxFiles <= 0) {
        meta.textContent = "Лимит галереи заполнен. Удалите одно фото, чтобы добавить новое.";
        return;
      }
      meta.textContent = count
        ? "Будет добавлено новых фото: " + count + " из " + maxFiles + ". Сохраните карточку, чтобы применить."
        : "Новые фото добавятся в галерею после сохранения карточки. Можно изменить порядок перетаскиванием.";
    }

    var maxFiles = Math.max(10 - getExistingGalleryCount(), 0);
    uploadInput.dataset.allowReorder = "true";
    uploadInput.dataset.storeAsFile = "true";
    uploadInput.dataset.maxFiles = String(maxFiles);

    if (!window.FilePond) {
      panel.classList.add("km-filepond-gallery--fallback");
      updateMeta(0, maxFiles);
      return;
    }

    try {
      if (window.FilePondPluginImagePreview) {
        window.FilePond.registerPlugin(window.FilePondPluginImagePreview);
      }
    } catch (error) {}

    var pond = window.FilePond.create(uploadInput, {
      allowMultiple: true,
      allowReorder: true,
      allowImagePreview: true,
      credits: false,
      imagePreviewHeight: 118,
      itemInsertLocation: "after",
      maxFiles: maxFiles || 1,
      storeAsFile: true,
      labelIdle: maxFiles > 0
        ? 'Перетащите фото сюда или <span class="filepond--label-action">выберите файлы</span>'
        : "Лимит галереи заполнен",
      labelMaxFileCountExceeded: "Можно добавить не больше {maxFiles} фото",
      labelMaxFileCount: "Максимум {maxFiles} фото",
      labelTapToCancel: "нажмите для отмены",
      labelTapToRetry: "нажмите для повтора",
      labelTapToUndo: "нажмите для отмены",
      labelButtonRemoveItem: "Удалить",
      labelButtonAbortItemLoad: "Отменить",
      labelButtonRetryItemLoad: "Повторить",
      labelButtonAbortItemProcessing: "Отменить",
      labelButtonUndoItemProcessing: "Отменить",
      labelButtonRetryItemProcessing: "Повторить",
      labelButtonProcessItem: "Загрузить"
    });

    if (maxFiles <= 0) {
      pond.setOptions({ disabled: true });
    }

    pond.on("updatefiles", function (files) {
      updateMeta(files.length, maxFiles);
    });
    panel.dataset.filepondReady = "1";
    updateMeta(0, maxFiles);
  });

  ready(function () {
    document.addEventListener("keydown", function (e) {
      var target = e.target;
      if (target && target.tagName === "INPUT" && target.getAttribute("inputmode") === "numeric") {
        if (
          [46, 8, 9, 27, 13].indexOf(e.keyCode) !== -1 ||
          (e.keyCode === 65 && (e.ctrlKey === true || e.metaKey === true)) ||
          (e.keyCode === 67 && (e.ctrlKey === true || e.metaKey === true)) ||
          (e.keyCode === 86 && (e.ctrlKey === true || e.metaKey === true)) ||
          (e.keyCode === 88 && (e.ctrlKey === true || e.metaKey === true)) ||
          (e.keyCode >= 35 && e.keyCode <= 40)
        ) {
          return;
        }
        if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
          e.preventDefault();
        }
      }
    });

    document.addEventListener("input", function (e) {
      var target = e.target;
      if (target && target.tagName === "INPUT" && target.getAttribute("inputmode") === "numeric") {
        var val = target.value;
        var clean = val.replace(/\D/g, "");
        if (val !== clean) {
          target.value = clean;
        }
      }
    });

    // Intercept deletelink clicks to show SweetAlert2 before navigating to delete confirmation page
    document.addEventListener("click", function (event) {
      var deleteLink = event.target.closest(".deletelink");
      if (!deleteLink) {
        return;
      }
      event.preventDefault();
      var href = deleteLink.getAttribute("href");

      if (typeof Swal !== "undefined") {
        Swal.fire({
          title: "Переместить в удаленные?",
          text: "Вы будете перенаправлены на страницу подтверждения удаления.",
          icon: "warning",
          showCancelButton: true,
          confirmButtonColor: "#ef4444",
          cancelButtonColor: "#475569",
          confirmButtonText: "Да, продолжить",
          cancelButtonText: "Отмена",
          background: document.body.classList.contains("dark-mode") ? "#1e293b" : "#ffffff",
          color: document.body.classList.contains("dark-mode") ? "#f8fafc" : "#0f172a",
        }).then(function (result) {
          if (result.isConfirmed) {
            window.location.href = href;
          }
        });
      } else {
        if (window.confirm("Вы уверены, что хотите перейти к удалению?")) {
          window.location.href = href;
        }
      }
    });
  });

  ready(function () {
    var form = document.querySelector("[data-km-admin-form]") || document.getElementById("place_form");
    if (!form) return;

    var nameFields = ["id_name_ru", "id_name_az", "id_name_en", "id_name"];
    var categorySelect = form.querySelector('select[name="category"]');

    var CHECKLIST_CONFIG = [
      {
        field: "name",
        label: "Название",
        getTargetInput: function() {
          return document.getElementById("id_name_ru") || document.getElementById("id_name_az") || document.getElementById("id_name_en") || document.getElementById("id_name");
        },
        isFilled: function() {
          for (var i = 0; i < nameFields.length; i++) {
            var el = document.getElementById(nameFields[i]);
            if (el && el.value.trim()) return true;
          }
          return false;
        }
      },
      {
        field: "category",
        label: "Категория",
        getTargetInput: function() {
          return document.querySelector('select[name="category"]');
        },
        isFilled: function() {
          var el = document.querySelector('select[name="category"]');
          return !!(el && el.value);
        }
      },
      {
        field: "description_az",
        label: "Описание (AZ)",
        getTargetInput: function() {
          return document.getElementById("id_description_az");
        },
        isFilled: function() {
          var el = document.getElementById("id_description_az");
          return !!(el && el.value.trim());
        }
      },
      {
        field: "age_from",
        label: "Возраст от",
        getTargetInput: function() {
          return document.getElementById("id_age_from");
        },
        isFilled: function() {
          var el = document.getElementById("id_age_from");
          return !!(el && el.value.trim());
        }
      },
      {
        field: "age_to",
        label: "Возраст до",
        getTargetInput: function() {
          return document.getElementById("id_age_to");
        },
        isFilled: function() {
          var el = document.getElementById("id_age_to");
          var openEnded = document.getElementById("id_age_open_ended");
          return !!(openEnded && openEnded.checked) || !!(el && el.value.trim());
        }
      },
      {
        field: "address",
        label: "Адрес",
        getTargetInput: function() {
          return document.getElementById("id_address");
        },
        isFilled: function() {
          var el = document.getElementById("id_address");
          return !!(el && el.value.trim());
        }
      },
      {
        field: "phone1",
        label: "Телефон",
        getTargetInput: function() {
          return document.getElementById("id_phone1");
        },
        isFilled: function() {
          var el = document.getElementById("id_phone1");
          return !!(el && el.value.trim());
        }
      },
      {
        field: "photo",
        label: "Главное фото",
        getTargetInput: function() {
          return document.getElementById("id_photo");
        },
        isFilled: function() {
          var mainInput = document.getElementById("id_photo");
          var mainPreview = document.querySelector("[data-main-photo-preview]");
          var mainClearCheckbox = document.getElementById("id_photo-clear");
          var hasPhoto = !!(
            (mainInput && mainInput.files && mainInput.files.length) || 
            (mainPreview && mainPreview.getAttribute("data-main-photo-initial-url") && !(mainClearCheckbox && mainClearCheckbox.checked))
          );
          return hasPhoto;
        }
      }
    ];

    function updateMockupTitle() {
      var titleEl = document.getElementById("km-preview-title");
      if (!titleEl) return;
      var val = "";
      for (var i = 0; i < nameFields.length; i++) {
        var input = document.getElementById(nameFields[i]);
        if (input && input.value.trim()) {
          val = input.value.trim();
          break;
        }
      }
      titleEl.textContent = val || "Название места";
    }

    function updateMockupCategory() {
      var catEl = document.getElementById("km-preview-category");
      if (!catEl || !categorySelect) return;
      var selectedOption = categorySelect.options[categorySelect.selectedIndex];
      if (selectedOption && selectedOption.value) {
        catEl.textContent = selectedOption.text;
        var configNode = document.getElementById("km-place-taxonomy-config");
        if (configNode) {
          try {
            var config = JSON.parse(configNode.textContent || "{}");
            var categories = config.categories || [];
            var matched = categories.find(function(c) { return String(c.code) === String(selectedOption.value); });
            if (matched) {
              catEl.style.backgroundColor = matched.color_bg || "#f3f4f6";
              catEl.style.color = matched.color_text || "#1f2937";
            } else {
              catEl.style.backgroundColor = "#f3f4f6";
              catEl.style.color = "#1f2937";
            }
          } catch(e) {
            catEl.style.backgroundColor = "#f3f4f6";
            catEl.style.color = "#1f2937";
          }
        }
      } else {
        catEl.textContent = "Категория не выбрана";
        catEl.style.backgroundColor = "#f3f4f6";
        catEl.style.color = "#6b7280";
      }
    }

    function updateMockupAge() {
      var ageEl = document.getElementById("km-preview-age");
      if (!ageEl) return;
      var fromVal = (document.getElementById("id_age_from") || {}).value;
      var toVal = (document.getElementById("id_age_to") || {}).value;
      if (fromVal || toVal) {
        if (fromVal && toVal) {
          ageEl.textContent = fromVal + " – " + toVal;
        } else if (fromVal) {
          ageEl.textContent = fromVal + "+";
        } else {
          ageEl.textContent = "до " + toVal;
        }
      } else {
        ageEl.textContent = "—";
      }
    }

    function updateMockupPrice() {
      var priceEl = document.getElementById("km-preview-price");
      var priceTag = document.getElementById("km-preview-price-tag");
      if (!priceEl || !priceTag) return;
      var pFrom = (document.getElementById("id_price_from") || {}).value;
      var pTo = (document.getElementById("id_price_to") || {}).value;
      var pLesson = (document.getElementById("id_price_per_lesson") || {}).value;
      
      var labelSpan = priceTag.querySelector(".label");
      if (!labelSpan) {
        labelSpan = document.createElement("span");
        labelSpan.className = "label";
        priceTag.insertBefore(labelSpan, priceEl);
      }
      
      if (pFrom || pTo) {
        priceTag.style.display = "";
        labelSpan.textContent = "Цена ";
        if (pFrom && pTo) {
          priceEl.textContent = pFrom + " – " + pTo + " ₼";
        } else if (pFrom) {
          priceEl.textContent = "от " + pFrom + " ₼";
        } else {
          priceEl.textContent = "до " + pTo + " ₼";
        }
      } else if (pLesson) {
        priceTag.style.display = "";
        labelSpan.textContent = "Урок ";
        priceEl.textContent = pLesson + " ₼";
      } else {
        priceTag.style.display = "none";
        priceEl.textContent = "—";
      }
    }

    function updateMockupAddress() {
      var addrEl = document.getElementById("km-preview-address");
      if (!addrEl) return;
      var val = (document.getElementById("id_address") || {}).value || "";
      addrEl.textContent = val.trim() || "Адрес не указан";
    }

    function updateMockupBadges() {
      var verifiedCheckbox = document.getElementById("id_is_verified");
      var tempCheckbox = document.getElementById("id_is_temporary");
      
      var verifiedBadge = document.getElementById("km-preview-badge-verified");
      var tempBadge = document.getElementById("km-preview-badge-temporary");
      
      if (verifiedBadge) {
        verifiedBadge.style.display = (verifiedCheckbox && verifiedCheckbox.checked) ? "" : "none";
      }
      if (tempBadge) {
        tempBadge.style.display = (tempCheckbox && tempCheckbox.checked) ? "" : "none";
      }
    }

    function updateMockupPhoto() {
      var previewImg = document.getElementById("km-preview-img");
      var placeholder = document.getElementById("km-preview-img-placeholder");
      var photoStatusBadge = document.getElementById("km-status-photo-badge");
      if (!previewImg || !placeholder) return;
      
      var mainInput = document.getElementById("id_photo");
      var mainPreview = document.querySelector("[data-main-photo-preview]");
      var mainClearCheckbox = document.getElementById("id_photo-clear");
      var hasPhoto = !!(
        (mainInput && mainInput.files && mainInput.files.length) || 
        (mainPreview && mainPreview.getAttribute("data-main-photo-initial-url") && !(mainClearCheckbox && mainClearCheckbox.checked))
      );
      
      if (hasPhoto) {
        var src = "";
        if (mainInput && mainInput.files && mainInput.files.length) {
          src = mainPreview && mainPreview.src ? mainPreview.src : "";
        } else if (mainPreview) {
          src = mainPreview.getAttribute("data-main-photo-initial-url") || "";
        }
        
        if (src) {
          previewImg.src = src;
          previewImg.style.display = "";
          placeholder.style.display = "none";
        } else {
          previewImg.style.display = "none";
          placeholder.style.display = "";
        }
        
        if (photoStatusBadge) {
          photoStatusBadge.className = "badge km-badge-compact km-badge-compact--good";
          photoStatusBadge.textContent = "Главное фото загружено";
        }
      } else {
        previewImg.style.display = "none";
        placeholder.style.display = "";
        if (photoStatusBadge) {
          photoStatusBadge.className = "badge km-badge-compact km-badge-compact--warn";
          photoStatusBadge.textContent = "Главное фото отсутствует";
        }
      }
    }

    function updateVerificationCoordinates() {
      var latInput = document.getElementById("id_lat");
      var lngInput = document.getElementById("id_lng");
      var latVal = latInput ? latInput.value.trim() : "";
      var lngVal = lngInput ? lngInput.value.trim() : "";
      var hasCoords = !!(latVal && lngVal);
      
      var statusBadge = document.getElementById("km-status-coordinates-badge");
      if (statusBadge) {
        if (hasCoords) {
          statusBadge.className = "badge km-badge-compact km-badge-compact--good";
          statusBadge.textContent = "Координаты указаны";
        } else {
          statusBadge.className = "badge km-badge-compact km-badge-compact--warn";
          statusBadge.textContent = "Координаты не указаны";
        }
      }
      
      var headerBadge = document.getElementById("km-header-coords-badge");
      if (headerBadge) {
        if (hasCoords) {
          headerBadge.className = "km-badge-compact km-badge-compact--good";
          headerBadge.textContent = "Координаты указаны";
        } else {
          headerBadge.className = "km-badge-compact km-badge-compact--warn";
          headerBadge.textContent = "Нужны координаты";
        }
      }
    }

    function updateVerificationChecklist() {
      var checklistContainer = document.getElementById("km-verification-checklist");
      var allFilledContainer = document.getElementById("km-verification-all-filled");
      if (!checklistContainer || !allFilledContainer) return;
      
      checklistContainer.innerHTML = "";
      var missingCount = 0;
      
      CHECKLIST_CONFIG.forEach(function(item) {
        var filled = item.isFilled();
        if (!filled) {
          missingCount++;
          var link = document.createElement("a");
          link.href = "#";
          link.className = "km-checklist-link";
          link.innerHTML = "<span>" + item.label + "</span> <i class=\"fas fa-arrow-right\"></i>";
          link.addEventListener("click", function(e) {
            e.preventDefault();
            var targetInput = item.getTargetInput();
            var targetScroll = null;

            if (item.field === "photo") {
              targetScroll = document.querySelector("[data-main-photo-root]");
            }

            if (!targetScroll && targetInput) {
              targetScroll = targetInput.closest(".form-row") || targetInput;
            }

            if (targetScroll) {
              var fieldset = targetScroll.closest("fieldset.collapse");
              if (fieldset && fieldset.classList.contains("collapsed")) {
                var toggleLink = fieldset.querySelector("a.collapse-toggle");
                if (toggleLink) {
                  toggleLink.click();
                } else {
                  fieldset.classList.remove("collapsed");
                }
              }

              targetScroll.scrollIntoView({ behavior: "smooth", block: "center" });
              
              targetScroll.classList.add("km-highlight-flash");
              setTimeout(function() {
                targetScroll.classList.remove("km-highlight-flash");
              }, 2500);

              if (targetInput) {
                setTimeout(function() {
                  try {
                    targetInput.focus();
                  } catch(err) {}
                  if (targetInput.classList.contains("select2-hidden-accessible")) {
                    try {
                      window.$(targetInput).select2("open");
                    } catch(err) {}
                  }
                }, 400);
              }
            }
          });

          checklistContainer.appendChild(link);
        }
      });

      if (missingCount === 0) {
        allFilledContainer.style.display = "";
      } else {
        allFilledContainer.style.display = "none";
      }
    }

    function updateRealtimeProgress() {
      var total = CHECKLIST_CONFIG.length;
      var completed = 0;
      CHECKLIST_CONFIG.forEach(function(item) {
        if (item.isFilled()) completed++;
      });
      
      var pct = Math.round((completed / total) * 100);
      
      var pctNodes = document.querySelectorAll("[data-progress-pct]");
      var doneNodes = document.querySelectorAll("[data-progress-done]");
      var totalNodes = document.querySelectorAll("[data-progress-total]");
      var barFillNodes = document.querySelectorAll("[data-progress-bar]");
      
      pctNodes.forEach(function(node) {
        node.textContent = pct + "%";
      });
      doneNodes.forEach(function(node) {
        node.textContent = completed;
      });
      totalNodes.forEach(function(node) {
        node.textContent = total;
      });
      barFillNodes.forEach(function(node) {
        node.style.width = pct + "%";
      });
      
      var readinessBadge = document.querySelector("[data-progress-readiness]");
      if (readinessBadge) {
        var readyLabel = form.dataset.progressReadyLabel || "Готово к публикации";
        var incompleteLabel = form.dataset.progressIncompleteLabel || "Нужна доработка";
        var readyTone = form.dataset.progressReadyTone || "good";
        var incompleteTone = form.dataset.progressIncompleteTone || "warn";
        
        if (completed === total) {
          readinessBadge.textContent = readyLabel;
          readinessBadge.className = "km-badge-compact km-badge-compact--" + readyTone;
        } else {
          readinessBadge.textContent = incompleteLabel;
          readinessBadge.className = "km-badge-compact km-badge-compact--" + incompleteTone;
        }
      }
      
      var publishMobileBtn = document.getElementById("km-publish-mobile-btn");
      if (publishMobileBtn) {
        if (completed === total) {
          publishMobileBtn.removeAttribute("disabled");
        } else {
          publishMobileBtn.setAttribute("disabled", "disabled");
        }
      }
    }

    function updateAllVerificationAndMockupStates() {
      updateMockupTitle();
      updateMockupCategory();
      updateMockupAge();
      updateMockupPrice();
      updateMockupAddress();
      updateMockupBadges();
      updateMockupPhoto();
      updateVerificationCoordinates();
      updateVerificationChecklist();
      updateRealtimeProgress();
    }

    form.addEventListener("input", updateAllVerificationAndMockupStates);
    form.addEventListener("change", updateAllVerificationAndMockupStates);

    document.addEventListener("click", function(e) {
      var target = e.target;
      if (target && target.closest("[data-main-photo-clear], [data-main-photo-pick]")) {
        setTimeout(updateAllVerificationAndMockupStates, 100);
      }
    });

    // Execute immediately
    setTimeout(updateAllVerificationAndMockupStates, 100);

    setInterval(updateAllVerificationAndMockupStates, 1000);

    // Expand collapsed secondary details if there are errors inside
    var secondaryDetails = document.querySelectorAll("details.km-place-secondary");
    secondaryDetails.forEach(function (details) {
      if (details.querySelector(".errors, .errorlist, .errornote")) {
        details.open = true;
      }
    });

    // Unsaved changes confirmation dialog
    var initialSerializedForm = "";
    var formSubmitted = false;

    function serializeForm(f) {
      var parts = [];
      for (var i = 0; i < f.elements.length; i++) {
        var el = f.elements[i];
        if (!el.name || el.disabled || el.type === "submit" || el.type === "button") continue;
        if (el.type === "checkbox" || el.type === "radio") {
          parts.push(encodeURIComponent(el.name) + "=" + (el.checked ? "1" : "0"));
        } else if (el.type === "file") {
          parts.push(encodeURIComponent(el.name) + "=" + (el.files ? el.files.length : "0"));
        } else {
          parts.push(encodeURIComponent(el.name) + "=" + encodeURIComponent(el.value));
        }
      }
      return parts.join("&");
    }

    // Set initial serialized form after a short delay to allow default values and scripts to initialize
    setTimeout(function() {
      if (form) {
        initialSerializedForm = serializeForm(form);
      }
    }, 1000);

    function isFormDirty() {
      if (!form || !initialSerializedForm) return false;
      return serializeForm(form) !== initialSerializedForm;
    }

    form.addEventListener("submit", function() {
      formSubmitted = true;
    });

    window.addEventListener("beforeunload", function(e) {
      if (!formSubmitted && isFormDirty()) {
        e.preventDefault();
        e.returnValue = "";
        return "";
      }
    });

    document.addEventListener("click", function(event) {
      if (formSubmitted) return;
      var anchor = event.target.closest("a");
      if (!anchor) return;

      var href = anchor.getAttribute("href");
      if (!href || href === "#" || href.startsWith("javascript:") || href.startsWith("#")) {
        return;
      }

      if (anchor.getAttribute("target") === "_blank") {
        return;
      }

      // Do not intercept click on delete links or popup widget links
      if (anchor.closest(".deletelink") ||
          anchor.classList.contains("related-widget-wrapper-link") || 
          anchor.classList.contains("add-related") || 
          anchor.classList.contains("change-related") || 
          anchor.classList.contains("delete-related") ||
          anchor.closest(".related-widget-wrapper-link")) {
        return;
      }

      if (isFormDirty()) {
        event.preventDefault();
        if (typeof Swal !== "undefined") {
          Swal.fire({
            title: "Несохраненные изменения",
            text: "У вас есть несохраненные изменения. Сохранить их перед выходом?",
            icon: "warning",
            showDenyButton: true,
            showCancelButton: true,
            confirmButtonText: "Сохранить и выйти",
            denyButtonText: "Выйти без сохранения",
            cancelButtonText: "Остаться и продолжить",
            confirmButtonColor: "#10b981",
            denyButtonColor: "#ef4444",
            cancelButtonColor: "#64748b",
            background: document.body.classList.contains("dark-mode") ? "#1e293b" : "#ffffff",
            color: document.body.classList.contains("dark-mode") ? "#f8fafc" : "#0f172a",
          }).then(function(result) {
            if (result.isConfirmed) {
              var saveInput = document.createElement("input");
              saveInput.type = "hidden";
              saveInput.name = "_save";
              saveInput.value = "Save";
              form.appendChild(saveInput);
              formSubmitted = true;
              form.submit();
            } else if (result.isDenied) {
              formSubmitted = true;
              window.location.href = href;
            }
          });
        } else {
          if (confirm("У вас есть несохраненные изменения. Выйти без сохранения?")) {
            formSubmitted = true;
            window.location.href = href;
          }
        }
      }
    });
  });

})();
