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
        var selectedCategoryText = "";
        if (categorySelect.selectedIndex >= 0) {
          selectedCategoryText = categorySelect.options[categorySelect.selectedIndex].text.trim();
        }
        
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
          
          // Subcategory __str__ format is usually: "Category Name -> Subcategory Name"
          var optionText = option.text.trim();
          var prefix = selectedCategoryText + " -> ";
          
          if (selectedCategoryText && optionText.indexOf(prefix) === 0) {
            var newOption = option.cloneNode(true);
            
            // Clean up the text for better UX (remove category prefix)
            newOption.text = optionText.substring(prefix.length);
            
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
