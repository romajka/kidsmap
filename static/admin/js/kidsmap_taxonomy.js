/* static/admin/js/kidsmap_taxonomy.js */
document.addEventListener("DOMContentLoaded", function () {
  const expanders = document.querySelectorAll(".km-tax-expander");
  const expandAllBtn = document.getElementById("km-tax-expand-all");
  const listContainer = document.querySelector(".km-tax-list");
  
  // Toggle individual category
  expanders.forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.stopPropagation(); // prevent bubbling if row is clickable
      const group = btn.closest(".km-tax-group");
      const children = group.querySelector(".km-tax-children");
      const isExpanded = btn.getAttribute("aria-expanded") === "true";
      
      if (isExpanded) {
        btn.setAttribute("aria-expanded", "false");
        children.style.display = "none";
      } else {
        btn.setAttribute("aria-expanded", "true");
        children.style.display = "block";
      }
    });
  });

  // Also allow clicking the parent row to toggle
  const parentRows = document.querySelectorAll(".km-tax-row-parent");
  parentRows.forEach(function (row) {
    row.addEventListener("click", function (e) {
      // Don't toggle if clicking a button or link
      if (e.target.closest("button") || e.target.closest("a")) {
        return;
      }
      const expander = row.querySelector(".km-tax-expander");
      if (expander) {
        expander.click();
      }
    });
  });

  // Expand all / Collapse all
  if (expandAllBtn) {
    expandAllBtn.addEventListener("click", function () {
      const isExpanding = expandAllBtn.querySelector("span").textContent.trim() === "Развернуть все";
      
      expanders.forEach(function (btn) {
        const group = btn.closest(".km-tax-group");
        const children = group.querySelector(".km-tax-children");
        
        if (isExpanding) {
          btn.setAttribute("aria-expanded", "true");
          children.style.display = "block";
        } else {
          btn.setAttribute("aria-expanded", "false");
          children.style.display = "none";
        }
      });

      if (isExpanding) {
        expandAllBtn.querySelector("span").textContent = "Свернуть все";
      } else {
        expandAllBtn.querySelector("span").textContent = "Развернуть все";
      }
    });
  }

  // Auto-expand if search is active
  if (listContainer && listContainer.getAttribute("data-search-active") === "true") {
    if (expandAllBtn) expandAllBtn.click();
  }

  // Dropdown Menus
  const menuBtns = document.querySelectorAll(".km-tax-menu-btn");
  menuBtns.forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const container = btn.closest(".km-tax-dropdown-container");
      const isOpen = container.classList.contains("open");
      
      // Close all others
      document.querySelectorAll(".km-tax-dropdown-container").forEach(function (c) {
        c.classList.remove("open");
      });
      
      if (!isOpen) {
        container.classList.add("open");
      }
    });
  });

  // Close dropdowns when clicking outside
  document.addEventListener("click", function () {
    document.querySelectorAll(".km-tax-dropdown-container").forEach(function (c) {
      c.classList.remove("open");
    });
  });

  // Delete Confirmation Popup
  const deleteLinks = document.querySelectorAll(".km-text-danger");
  const deleteForm = document.getElementById("km-delete-form");

  deleteLinks.forEach(function (link) {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const confirmed = confirm("Вы уверены, что хотите удалить этот объект? Это действие нельзя отменить.");
      if (confirmed && deleteForm) {
        deleteForm.action = link.href;
        deleteForm.submit();
      }
    });
  });

  // Toggle Active/Inactive
  const toggleBtns = document.querySelectorAll(".km-tax-toggle-btn");
  toggleBtns.forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      
      const objType = btn.getAttribute("data-type");
      const objId = btn.getAttribute("data-id");
      const url = btn.getAttribute("data-url");
      
      if (!deleteForm) return;
      
      const csrfToken = deleteForm.querySelector("input[name='csrfmiddlewaretoken']").value;
      
      const formData = new FormData();
      formData.append("obj_type", objType);
      formData.append("obj_id", objId);
      formData.append("csrfmiddlewaretoken", csrfToken);
      
      fetch(url, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === "success") {
          window.location.reload();
        } else {
          alert("Ошибка при изменении статуса: " + (data.error || "Неизвестная ошибка"));
        }
      })
      .catch(err => {
        alert("Ошибка сети при запросе.");
        console.error(err);
      });
    });
  });

  // Client-side status filtering
  const statusFilterContainer = document.getElementById("km-tax-status-filter");
  if (statusFilterContainer) {
    const statusBtnText = statusFilterContainer.querySelector(".km-current-status");
    const statusItems = statusFilterContainer.querySelectorAll(".km-tax-dropdown-item");

    statusItems.forEach(item => {
      item.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();

        const selectedStatus = this.getAttribute("data-status");
        
        // Update active class in dropdown
        statusItems.forEach(i => i.classList.remove("active"));
        this.classList.add("active");

        // Update button text
        if (statusBtnText) {
          statusBtnText.textContent = this.textContent.trim();
        }

        // Close dropdown
        statusFilterContainer.classList.remove("open");

        // Apply filtering
        filterRows(selectedStatus);
      });
    });
  }

  function filterRows(status) {
    const groups = document.querySelectorAll(".km-tax-group");
    
    groups.forEach(group => {
      const isGroupActive = group.getAttribute("data-status") === "active";
      const childRows = group.querySelectorAll(".km-tax-row-child:not(.km-tax-row-empty)");
      const emptyRow = group.querySelector(".km-tax-row-empty");
      
      let hasVisibleChildren = false;
      let activeChildrenCount = 0;
      let inactiveChildrenCount = 0;

      childRows.forEach(child => {
        const isChildActive = child.getAttribute("data-status") === "active";
        if (isChildActive) activeChildrenCount++;
        else inactiveChildrenCount++;

        if (status === "all") {
          child.style.display = "";
          hasVisibleChildren = true;
        } else if (status === "active") {
          if (isChildActive) {
            child.style.display = "";
            hasVisibleChildren = true;
          } else {
            child.style.display = "none";
          }
        } else if (status === "inactive") {
          if (!isChildActive) {
            child.style.display = "";
            hasVisibleChildren = true;
          } else {
            child.style.display = "none";
          }
        }
      });

      // Handle empty placeholder
      if (emptyRow) {
        if (status === "all") {
          emptyRow.style.display = "";
        } else {
          emptyRow.style.display = "none";
        }
      }

      // Determine visibility of parent group
      let showGroup = false;
      if (status === "all") {
        showGroup = true;
      } else if (status === "active") {
        showGroup = isGroupActive;
      } else if (status === "inactive") {
        showGroup = (!isGroupActive) || (inactiveChildrenCount > 0);
      }

      if (showGroup) {
        group.style.display = "";
        // If status filter is active, auto-expand categories that have matching subcategories
        const expanderBtn = group.querySelector(".km-tax-expander");
        const childrenContainer = group.querySelector(".km-tax-children");
        if (status !== "all" && hasVisibleChildren) {
          if (expanderBtn) expanderBtn.setAttribute("aria-expanded", "true");
          if (childrenContainer) childrenContainer.style.display = "block";
        }
      } else {
        group.style.display = "none";
      }
    });
  }
});
