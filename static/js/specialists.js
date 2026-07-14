(function () {
  "use strict";

  function initCatalogFilters() {
    var page = document.querySelector(".km-specialists-page");
    if (!page) return;

    var drawer = document.getElementById("km-specialists-filters");
    var overlay = page.querySelector(".km-filter-overlay");
    var openButton = page.querySelector("[data-km-filter-open]");
    var closeButtons = page.querySelectorAll("[data-km-filter-close]");
    var formatSelect = document.getElementById("filter-format");
    var locFiltersContainer = document.getElementById("location-filters-container");
    var regionSelect = document.getElementById("filter-region");
    var districtSelect = document.getElementById("filter-district");

    function setDrawer(open) {
      if (!drawer || !overlay || !openButton) return;
      drawer.classList.toggle("is-open", open);
      overlay.hidden = !open;
      document.body.classList.toggle("km-filter-lock", open);
      openButton.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) {
        var firstField = drawer.querySelector("input, select, button, a");
        if (firstField) firstField.focus();
      } else {
        openButton.focus();
      }
    }

    if (openButton) {
      openButton.addEventListener("click", function () { setDrawer(true); });
    }
    closeButtons.forEach(function (button) {
      button.addEventListener("click", function () { setDrawer(false); });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && drawer && drawer.classList.contains("is-open")) {
        setDrawer(false);
      }
    });

    if (formatSelect && locFiltersContainer) {
      function syncFormatLayout() {
        var onlineOnly = formatSelect.value === "online";
        locFiltersContainer.hidden = onlineOnly;
        if (onlineOnly) {
          locFiltersContainer.querySelectorAll("select").forEach(function (select) {
            select.value = "";
          });
        }
      }
      formatSelect.addEventListener("change", syncFormatLayout);
      syncFormatLayout();
    }

    if (regionSelect && districtSelect) {
      var allDistricts = Array.from(districtSelect.querySelectorAll("option"));
      function filterDistricts() {
        var selectedRegion = regionSelect.value;
        districtSelect.innerHTML = "";
        allDistricts.forEach(function (option) {
          if (!option.value || !selectedRegion || option.getAttribute("data-region") === selectedRegion) {
            districtSelect.appendChild(option);
          }
        });
      }
      regionSelect.addEventListener("change", filterDistricts);
      filterDistricts();
    }
  }

  function initOwnerSpecialistForm() {
    var form = document.querySelector(".km-specialist-owner-form");
    if (!form) return;

    var steps = Array.from(form.querySelectorAll("[data-owner-step]"));
    var navButtons = Array.from(form.querySelectorAll("[data-owner-step-target]"));
    var nextButtons = Array.from(form.querySelectorAll("[data-owner-next]"));
    var prevButtons = Array.from(form.querySelectorAll("[data-owner-prev]"));
    var progressText = form.querySelector("[data-owner-progress-text]");
    var progressBar = form.querySelector("[data-owner-progress-bar]");
    var current = 0;

    function showStep(index) {
      current = Math.max(0, Math.min(index, steps.length - 1));
      steps.forEach(function (step, i) {
        step.hidden = i !== current;
      });
      navButtons.forEach(function (button, i) {
        button.classList.toggle("is-active", i === current);
        button.setAttribute("aria-current", i === current ? "step" : "false");
      });
      if (progressText) {
        progressText.textContent = progressText.getAttribute("data-label").replace("{current}", current + 1).replace("{total}", steps.length);
      }
      if (progressBar) {
        progressBar.style.width = (((current + 1) / steps.length) * 100) + "%";
      }
    }

    navButtons.forEach(function (button, index) {
      button.addEventListener("click", function () { showStep(index); });
    });
    nextButtons.forEach(function (button) {
      button.addEventListener("click", function () { showStep(current + 1); });
    });
    prevButtons.forEach(function (button) {
      button.addEventListener("click", function () { showStep(current - 1); });
    });

    var firstError = form.querySelector(".auth-field-error, .auth-errors, .errorlist");
    if (firstError) {
      var errorStep = firstError.closest("[data-owner-step]");
      var errorIndex = steps.indexOf(errorStep);
      if (errorIndex >= 0) current = errorIndex;
    }
    showStep(current);

    var formatSelect = form.querySelector("#id_consultation_format");
    var locationBlock = form.querySelector("[data-owner-location-block]");
    var formatCards = Array.from(form.querySelectorAll("[data-owner-format-card]"));
    function syncFormat() {
      if (!formatSelect) return;
      var value = formatSelect.value;
      if (locationBlock) locationBlock.hidden = value === "online";
      formatCards.forEach(function (card) {
        card.classList.toggle("is-selected", card.getAttribute("data-owner-format-card") === value);
      });
    }
    formatCards.forEach(function (card) {
      card.addEventListener("click", function () {
        if (formatSelect) {
          formatSelect.value = card.getAttribute("data-owner-format-card");
          formatSelect.dispatchEvent(new Event("change", { bubbles: true }));
        }
      });
      card.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          card.click();
        }
      });
    });
    if (formatSelect) formatSelect.addEventListener("change", syncFormat);
    syncFormat();

    var tabs = form.querySelectorAll("[data-owner-lang-tab]");
    var panels = form.querySelectorAll("[data-owner-lang-panel]");
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        var lang = tab.getAttribute("data-owner-lang-tab");
        tabs.forEach(function (item) {
          item.classList.toggle("is-active", item === tab);
          item.setAttribute("aria-selected", item === tab ? "true" : "false");
        });
        panels.forEach(function (panel) {
          panel.hidden = panel.getAttribute("data-owner-lang-panel") !== lang;
        });
      });
    });

    var photoInput = form.querySelector("#id_photo");
    var photoPreview = form.querySelector("[data-owner-photo-preview]");
    if (photoInput && photoPreview) {
      photoInput.addEventListener("change", function () {
        var file = photoInput.files && photoInput.files[0];
        if (!file || !file.type || file.type.indexOf("image/") !== 0) return;
        var reader = new FileReader();
        reader.onload = function (event) {
          photoPreview.innerHTML = '<img src="' + event.target.result + '" alt="">';
        };
        reader.readAsDataURL(file);
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initCatalogFilters();
    initOwnerSpecialistForm();
  });
})();
