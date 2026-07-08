(function () {
  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
      return;
    }
    document.addEventListener("DOMContentLoaded", fn);
  }

  function bindCategorySubcategoryPair(categorySelect, subcategorySelect) {
    if (!categorySelect || !subcategorySelect || subcategorySelect.dataset.kmSubcategoryBound === "1") {
      return;
    }

    var allOptions = Array.prototype.slice.call(subcategorySelect.options).map(function (option) {
      return option.cloneNode(true);
    });

    function syncSelect2(select) {
      if (!(window.$ && window.$.fn && typeof window.$.fn.select2 !== "undefined")) {
        return;
      }
      try {
        window.$(select).trigger("change.select2");
      } catch (error) {}
    }

    function rebuildSubcategories() {
      var selectedCategoryValue = String(categorySelect.value || "");
      var currentValue = String(subcategorySelect.value || "");
      var fragment = document.createDocumentFragment();
      var hasValidSelection = false;
      var visibleOptions = 0;

      allOptions.forEach(function (option) {
        if (!option.value) {
          fragment.appendChild(option.cloneNode(true));
          return;
        }

        if (selectedCategoryValue && String(option.dataset.category || "") === selectedCategoryValue) {
          var clonedOption = option.cloneNode(true);
          fragment.appendChild(clonedOption);
          visibleOptions += 1;
          if (clonedOption.value === currentValue) {
            hasValidSelection = true;
          }
        }
      });

      subcategorySelect.innerHTML = "";
      subcategorySelect.appendChild(fragment);
      subcategorySelect.disabled = !selectedCategoryValue || visibleOptions === 0;
      subcategorySelect.value = hasValidSelection ? currentValue : "";
      syncSelect2(subcategorySelect);
    }

    categorySelect.addEventListener("change", rebuildSubcategories);
    if (window.$ && window.$.fn && typeof window.$.fn.select2 !== "undefined") {
      try {
        window.$(categorySelect).on(
          "select2:select select2:unselect select2:clear change.select2",
          rebuildSubcategories
        );
      } catch (error) {}
    }

    subcategorySelect.dataset.kmSubcategoryBound = "1";
    rebuildSubcategories();
  }

  ready(function () {
    var forms = Array.prototype.slice.call(document.querySelectorAll("form"));
    forms.forEach(function (form) {
      var categorySelect = form.querySelector('select[name="category"]');
      var subcategorySelect = form.querySelector('select[name="subcategory"]');
      bindCategorySubcategoryPair(categorySelect, subcategorySelect);
    });

    if (!forms.length) {
      bindCategorySubcategoryPair(
        document.querySelector('select[name="category"]'),
        document.querySelector('select[name="subcategory"]')
      );
    }
  });
})();
