/**
 * KidsMap Specialist Admin — Form JavaScript
 * Scoped to: .km-specialist-form-page
 *
 * Responsibilities:
 *  1. Move inlines (locations, documents) into their section slots
 *  2. Section navigation (smooth scroll + active highlighting)
 *  3. Restore active section from sessionStorage
 *  4. Mark nav items with error badges
 *  5. Photo preview on file input change
 *  6. Conditional format hint (online-only notice)
 */

(function () {
  "use strict";

  var PAGE = document.querySelector(".km-specialist-form-page");
  if (!PAGE) return;

  /* ── 1. Move inlines into section slots ─────────────────── */
  function moveInlines() {
    var source = document.getElementById("km-inlines-source");
    if (!source) return;

    var locGroup = source.querySelector("#practice_locations-group");
    var docGroup = source.querySelector("#documents-group");

    var locWrapper = document.getElementById("practice_locations-group-wrapper");
    var docWrapper = document.getElementById("documents-group-wrapper");

    if (locGroup && locWrapper) {
      locGroup.style.display = "";
      locWrapper.appendChild(locGroup);
    }

    if (docGroup && docWrapper) {
      docGroup.style.display = "";
      docWrapper.appendChild(docGroup);
    }

    // Remove the hidden source container
    if (source.children.length === 0) {
      source.remove();
    }
  }

  /* ── 2. Section navigation ──────────────────────────────── */
  function initNav() {
    var navItems = PAGE.querySelectorAll(".km-nav-item");
    var sections = PAGE.querySelectorAll(".km-specialist-section");
    var STORAGE_KEY = "km-spec-active-section";

    // Click: smooth scroll to section
    navItems.forEach(function (item) {
      item.addEventListener("click", function (e) {
        e.preventDefault();
        var targetId = item.getAttribute("data-section");
        var target = document.getElementById(targetId);
        if (target) {
          target.scrollIntoView({ behavior: "smooth", block: "start" });
          setActive(item);
          try { sessionStorage.setItem(STORAGE_KEY, targetId); } catch (_) {}
        }
      });
    });

    // Scroll spy
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var id = entry.target.id;
            var match = PAGE.querySelector('.km-nav-item[data-section="' + id + '"]');
            if (match) setActive(match);
          }
        });
      },
      { rootMargin: "-10% 0px -70% 0px", threshold: 0 }
    );

    sections.forEach(function (sec) { observer.observe(sec); });

    function setActive(activeItem) {
      navItems.forEach(function (i) { i.classList.remove("km-nav-active"); });
      activeItem.classList.add("km-nav-active");
    }

    // Restore from session
    try {
      var saved = sessionStorage.getItem(STORAGE_KEY);
      if (saved) {
        var match = PAGE.querySelector('.km-nav-item[data-section="' + saved + '"]');
        if (match) match.classList.add("km-nav-active");
      }
    } catch (_) {}
  }

  /* ── 3. Error badges on nav items ───────────────────────── */
  function markErrorBadges() {
    // Map section id → which fieldset names / field id prefixes it contains
    var sectionMap = {
      "km-sec-1": ["id_owner", "id_name", "id_name_alt", "id_slug"],
      "km-sec-2": ["id_photo", "id_bio_ru", "id_bio_az", "id_bio_en"],
      "km-sec-3": ["id_specializations"],
      "km-sec-4": ["id_age_from", "id_age_to"],
      "km-sec-5": ["id_language_az", "id_language_ru", "id_language_en"],
      "km-sec-6": ["id_consultation_format"],
      "km-sec-7": ["id_price_from", "id_price_to", "id_duration_minutes"],
      "km-sec-8": ["practice_locations"],
      "km-sec-9": ["id_experience_years", "id_education", "id_experience_info"],
      "km-sec-10": ["documents-"],
      "km-sec-11": ["id_phone", "id_whatsapp", "id_instagram", "id_website"],
      "km-sec-12": ["id_is_verified", "id_is_active", "id_status", "id_rejection_reason"],
    };

    var allErrors = PAGE.querySelectorAll(".km-field-error, .errorlist li, ul.errorlist");

    allErrors.forEach(function (errEl) {
      // Walk up to find containing section
      var sec = errEl.closest(".km-specialist-section");
      if (sec) {
        var navItem = PAGE.querySelector('.km-nav-item[data-section="' + sec.id + '"]');
        if (navItem && !navItem.querySelector(".km-nav-badge")) {
          var badge = document.createElement("span");
          badge.className = "km-nav-badge";
          badge.textContent = "!";
          navItem.appendChild(badge);
          navItem.classList.add("km-nav-has-error");
          // Jump to first error section
          var firstError = PAGE.querySelector(".km-nav-has-error");
          if (firstError && !sessionStorage.getItem("km-spec-active-section")) {
            firstError.click();
          }
        }
      }
    });
  }

  /* ── 4. Photo preview ───────────────────────────────────── */
  function initPhotoPreview() {
    var fileInput = PAGE.querySelector('input[name="photo"]');
    var imgEl = document.getElementById("km-photo-img");
    var emptyEl = document.getElementById("km-photo-empty");

    if (!fileInput || !imgEl) return;

    fileInput.addEventListener("change", function () {
      var file = fileInput.files && fileInput.files[0];
      if (file && file.type.startsWith("image/")) {
        var reader = new FileReader();
        reader.onload = function (e) {
          imgEl.src = e.target.result;
          imgEl.style.display = "block";
          if (emptyEl) emptyEl.style.display = "none";
        };
        reader.readAsDataURL(file);
      }
    });
  }

  /* ── 5. Format/online toggle ────────────────────────────── */
  function initFormatToggle() {
    var formatSelect = PAGE.querySelector('[name="consultation_format"]');
    var onlineNotice = document.getElementById("km-online-only-notice");
    var formatHint = document.getElementById("km-format-hint-online");

    if (!formatSelect) return;

    function update() {
      var val = formatSelect.value;
      var isOnlineOnly = val === "online";
      if (onlineNotice) onlineNotice.style.display = isOnlineOnly ? "" : "none";
      if (formatHint) formatHint.style.display = isOnlineOnly ? "" : "none";
    }

    formatSelect.addEventListener("change", update);
    update();
  }

  /* ── 6. Inline formset: empty state ─────────────────────── */
  function initInlineEmptyState() {
    var locGroup = document.getElementById("practice_locations-group");
    if (!locGroup) return;

    function checkEmpty() {
      var rows = locGroup.querySelectorAll("tr.dynamic-practice_locations:not(.empty-form)");
      var existing = locGroup.querySelector("tr.has_original");
      var hasRows = rows.length > 0 || existing;
      var notice = locGroup.querySelector(".km-inline-empty-notice");

      if (!hasRows) {
        if (!notice) {
          notice = document.createElement("p");
          notice.className = "km-notice km-notice--info km-inline-empty-notice";
          notice.style.margin = "12px 0 0";
          notice.textContent = "Мест приёма пока нет. Нажмите «Добавить место приёма».";
          var tbl = locGroup.querySelector("table");
          if (tbl) tbl.parentNode.insertBefore(notice, tbl.nextSibling);
        }
      } else {
        if (notice) notice.remove();
      }
    }

    // Watch for add-row clicks
    var addRow = locGroup.querySelector(".add-row a");
    if (addRow) addRow.addEventListener("click", function () { setTimeout(checkEmpty, 50); });

    checkEmpty();
  }

  /* ── Init ────────────────────────────────────────────────── */
  document.addEventListener("DOMContentLoaded", function () {
    moveInlines();
    initNav();
    markErrorBadges();
    initPhotoPreview();
    initFormatToggle();
    initInlineEmptyState();
  });
})();
