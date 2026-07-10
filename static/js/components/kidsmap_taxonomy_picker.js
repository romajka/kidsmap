(function () {
  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
      return;
    }
    document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var form = document.querySelector(".owner-wizard-form") || document.querySelector("[data-owner-wizard]") || document.getElementById("place_form");
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

    // Determine language-specific UI labels from dataset attributes
    var wizardShell = document.querySelector("[data-owner-wizard-shell]") || form;
    var changeLabel = wizardShell.dataset.taxonomyPickerChangeLabel || "Изменить";
    var collapseLabel = wizardShell.dataset.taxonomyPickerCollapseLabel || "Свернуть";
    var selectCategoryLabel = wizardShell.dataset.taxonomyPickerSelectCategoryLabel || "Выберите категорию";
    var subcategoriesHint = wizardShell.dataset.taxonomyPickerSubcategoriesHint || "Подкатегории появятся сразу после выбора.";
    var subcategoryLabel = wizardShell.dataset.taxonomyPickerSubcategoryLabel || "Подкатегория";
    var subcategoriesCountMany = wizardShell.dataset.taxonomyPickerSubcategoriesCountMany || "подкатегорий";
    var subcategoriesCountNone = wizardShell.dataset.taxonomyPickerSubcategoriesCountNone || "без подкатегорий";
    var selectSubcategoryFirst = wizardShell.dataset.taxonomyPickerSelectSubcategoryFirst || "Сначала выберите категорию.";
    var subcategoriesNotNeeded = wizardShell.dataset.taxonomyPickerSubcategoriesNotNeeded || "Для этой категории подкатегории не нужны.";
    var subcategoriesVariants = wizardShell.dataset.taxonomyPickerSubcategoriesVariants || "вариантов";

    var categoryField = categorySelect.closest(".owner-form-field") || categorySelect.closest(".form-group");
    var subcategoryField = subcategorySelect.closest(".owner-form-details-secondary") || subcategorySelect.closest(".owner-form-field") || subcategorySelect.closest(".form-group");

    var anchor = categoryField;
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

      if (category.icon && /\.svg/i.test(category.icon)) {
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
    picker.setAttribute("aria-label", selectCategoryLabel);

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
    bannerToggleBtn.textContent = changeLabel;
    bannerToggleBtn.addEventListener("click", function (e) {
      e.preventDefault();
      picker.classList.toggle("is-collapsed");
      bannerToggleBtn.textContent = picker.classList.contains("is-collapsed") ? changeLabel : collapseLabel;
    });
    selectedBanner.appendChild(bannerToggleBtn);

    picker.appendChild(selectedBanner);

    var heading = document.createElement("div");
    heading.className = "km-taxonomy-picker__head";
    heading.innerHTML =
      '<div><strong>' + selectCategoryLabel + '</strong><span>' + subcategoriesHint + '</span></div>';
    picker.appendChild(heading);

    var categoryGrid = document.createElement("div");
    categoryGrid.className = "km-taxonomy-grid";
    picker.appendChild(categoryGrid);

    var subcategoryPanel = document.createElement("div");
    subcategoryPanel.className = "km-taxonomy-subpanel";
    subcategoryPanel.innerHTML =
      '<div class="km-taxonomy-subpanel__head"><strong>' + subcategoryLabel + '</strong><span data-km-taxonomy-subhint></span></div>' +
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
        ? count + " " + subcategoriesCountMany
        : subcategoriesCountNone;
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
        subcategoryHint.textContent = selectSubcategoryFirst;
        return;
      }
      if (!items.length) {
        subcategoryHint.textContent = subcategoriesNotNeeded;
        return;
      }

      subcategoryHint.textContent = items.length + " " + subcategoriesVariants;
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
            bannerToggleBtn.textContent = changeLabel;
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
})();
