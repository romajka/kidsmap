(function () {
  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
      return;
    }
    document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var categorySelects = document.querySelectorAll('select[name="category"]');
    var subcategorySelects = document.querySelectorAll('select[name="subcategory"]');

    if (categorySelects.length === 0 || subcategorySelects.length === 0) {
      return;
    }

    categorySelects.forEach(function (categorySelect, index) {
      // Find matching subcategory select (usually same index)
      // Sometimes there's only one of each on the page
      var subcategorySelect = subcategorySelects.length === 1 ? subcategorySelects[0] : subcategorySelects[index];
      if (!subcategorySelect) return;

      // Store all original subcategory options
      var allOptions = Array.prototype.slice.call(subcategorySelect.options);
      
      function updateSubcategories() {
        var selectedCategoryValue = categorySelect.value;
        
        var currentValue = subcategorySelect.value;
        
        // Clear current options
        subcategorySelect.innerHTML = "";
        
        var hasValidSelection = false;
        
        allOptions.forEach(function (option) {
          // Empty option (---------) is always shown
          if (!option.value) {
            subcategorySelect.appendChild(option.cloneNode(true));
            return;
          }

          if (selectedCategoryValue && option.dataset.category === selectedCategoryValue) {
            var newOption = option.cloneNode(true);
            subcategorySelect.appendChild(newOption);
            
            if (newOption.value === currentValue) {
              hasValidSelection = true;
            }
          }
        });
        
        if (hasValidSelection) {
          subcategorySelect.value = currentValue;
        } else {
          subcategorySelect.value = "";
        }
      }

      categorySelect.addEventListener("change", updateSubcategories);
      
      // Initial trigger to filter on page load
      updateSubcategories();
    });
  });
})();
