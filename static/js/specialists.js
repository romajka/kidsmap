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
    var filtersForm = document.getElementById("filters-form");
    var categorySelect = page.querySelector('select[name="specialization"]');
    var subjectSelect = page.querySelector('select[name="subject"]');
    if (categorySelect && subjectSelect) {
      categorySelect.addEventListener('change', function () {
        if (categorySelect.value !== 'tutor' && categorySelect.value !== 'exam_prep_tutor') subjectSelect.value = '';
      });
      subjectSelect.addEventListener('change', function () {
        if (!subjectSelect.value || categorySelect.value === 'tutor' || categorySelect.value === 'exam_prep_tutor') return;
        categorySelect.value = 'tutor';
        var custom = categorySelect.closest('.km-custom-select');
        if (custom) {
          custom.querySelectorAll('.km-custom-select__option').forEach(function (option) {
            var selected = option.dataset.value === 'tutor';
            option.classList.toggle('is-selected', selected);
            option.setAttribute('aria-selected', String(selected));
            if (selected) custom.querySelector('.km-custom-select__value').textContent = option.textContent.replace(/\s+/g, ' ').trim();
          });
        }
        categorySelect.dispatchEvent(new Event('change', {bubbles: true}));
      });
    }

    var mobileFilters = window.matchMedia("(max-width: 768px)");
    function drawerFields() {
      return Array.from(drawer.querySelectorAll('button, a[href], input:not([type="hidden"]), select, textarea, [tabindex="0"]')).filter(function (el) {
        return !el.disabled && el.getAttribute("tabindex") !== "-1" && el.getClientRects().length > 0;
      });
    }
    function setDrawer(open, restoreFocus) {
      if (!drawer || !overlay || !openButton) return;
      open = Boolean(open && mobileFilters.matches);
      drawer.classList.toggle("is-open", open);
      drawer.inert = mobileFilters.matches && !open;
      overlay.hidden = !open;
      document.body.classList.toggle("km-filter-lock", open);
      openButton.setAttribute("aria-expanded", String(open));
      if (open) {
        drawer.setAttribute("role", "dialog");
        drawer.setAttribute("aria-modal", "true");
        var firstField = drawerFields()[0];
        if (firstField) firstField.focus();
      } else {
        drawer.removeAttribute("role");
        drawer.removeAttribute("aria-modal");
        drawer.querySelectorAll(".km-custom-select.is-open").forEach(function (cs) {
          cs.classList.remove("is-open");
          cs.querySelector(".km-custom-select__trigger").setAttribute("aria-expanded", "false");
        });
        if (restoreFocus !== false && mobileFilters.matches) openButton.focus();
      }
    }
    setDrawer(false, false);
    mobileFilters.addEventListener("change", function () { setDrawer(false, false); });
    if (openButton) {
      openButton.addEventListener("click", function () { setDrawer(true); });
    }
    closeButtons.forEach(function (button) {
      button.addEventListener("click", function () { setDrawer(false); });
    });
    document.addEventListener("keydown", function (event) {
      if (!drawer || !drawer.classList.contains("is-open")) return;
      if (event.key === "Escape") {
        event.preventDefault();
        setDrawer(false);
      } else if (event.key === "Tab") {
        var fields = drawerFields();
        var first = fields[0], last = fields[fields.length - 1];
        if (event.shiftKey && (document.activeElement === first || !drawer.contains(document.activeElement))) {
          event.preventDefault();
          if (last) last.focus();
        } else if (!event.shiftKey && (document.activeElement === last || !drawer.contains(document.activeElement))) {
          event.preventDefault();
          if (first) first.focus();
        }
      }
    });

    // Sync online/offline layout
    if (formatSelect && locFiltersContainer) {
      function syncFormatLayout() {
        var onlineOnly = formatSelect.value === "online";
        locFiltersContainer.hidden = onlineOnly;
        if (onlineOnly) {
          locFiltersContainer.querySelectorAll("select").forEach(function (select) {
            select.value = "";
          });
          // Also reset custom select display if present
          var regionCs = document.getElementById("custom-select-region");
          if (regionCs) {
            var valSpan = regionCs.querySelector(".km-custom-select__value");
            var firstOpt = regionCs.querySelector(".km-custom-select__option");
            if (valSpan && firstOpt) {
              valSpan.textContent = firstOpt.textContent.trim();
            }
            regionCs.querySelectorAll(".km-custom-select__option").forEach(function (opt, idx) {
              opt.classList.toggle("is-selected", idx === 0);
              opt.setAttribute("aria-selected", idx === 0 ? "true" : "false");
            });
          }
        }
      }
      formatSelect.addEventListener("change", syncFormatLayout);
      syncFormatLayout();
    }

    /* ─── 1. Custom Selects Interactivity ─── */
    var customSelects = page.querySelectorAll(".km-custom-select");
    customSelects.forEach(function (cs) {
      var trigger = cs.querySelector(".km-custom-select__trigger");
      var menu = cs.querySelector(".km-custom-select__menu");
      var valueSpan = cs.querySelector(".km-custom-select__value");
      var options = cs.querySelectorAll(".km-custom-select__option");
      var nativeSelect = cs.querySelector("select");
      if (!trigger || !menu || !options.length) return;

      function closeMenu() {
        cs.classList.remove("is-open");
        trigger.setAttribute("aria-expanded", "false");
      }

      function openMenu() {
        customSelects.forEach(function (other) {
          if (other !== cs) {
            other.classList.remove("is-open");
            var otherTrig = other.querySelector(".km-custom-select__trigger");
            if (otherTrig) otherTrig.setAttribute("aria-expanded", "false");
          }
        });
        cs.classList.add("is-open");
        trigger.setAttribute("aria-expanded", "true");
      }

      trigger.addEventListener("click", function (e) {
        e.stopPropagation();
        if (cs.classList.contains("is-open")) {
          closeMenu();
        } else {
          openMenu();
        }
      });

      options.forEach(function (opt) {
        opt.setAttribute("tabindex", "-1");
        opt.addEventListener("click", function (e) {
          e.stopPropagation();
          var val = opt.getAttribute("data-value") || "";
          var optText = opt.querySelector(".km-custom-select__opt-text");
          var label = optText ? optText.textContent.trim() : opt.textContent.trim();
          var optCount = opt.querySelector(".km-custom-select__opt-count");

          options.forEach(function (o) {
            o.classList.remove("is-selected");
            o.setAttribute("aria-selected", "false");
          });
          opt.classList.add("is-selected");
          opt.setAttribute("aria-selected", "true");

          if (valueSpan) {
            if (optCount && val) {
              valueSpan.textContent = label + " (" + optCount.textContent.trim() + ")";
            } else {
              valueSpan.textContent = label;
            }
          }

          if (nativeSelect) {
            nativeSelect.value = val;
            nativeSelect.dispatchEvent(new Event("change", { bubbles: true }));
          }

          closeMenu();
          trigger.focus();
        });
      });

      // Keyboard support
      trigger.addEventListener("keydown", function (e) {
        if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openMenu();
          var firstOpt = menu.querySelector(".km-custom-select__option.is-selected") || options[0];
          if (firstOpt) firstOpt.focus();
        } else if (e.key === "Escape" && cs.classList.contains("is-open")) {
          e.preventDefault();
          e.stopPropagation();
          closeMenu();
        }
      });

      menu.addEventListener("keydown", function (e) {
        var cur = document.activeElement;
        var curIndex = Array.prototype.indexOf.call(options, cur);
        if (e.key === "ArrowDown") {
          e.preventDefault();
          var nextIndex = curIndex < options.length - 1 ? curIndex + 1 : 0;
          options[nextIndex].focus();
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          var prevIndex = curIndex > 0 ? curIndex - 1 : options.length - 1;
          options[prevIndex].focus();
        } else if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (cur && cur.classList.contains("km-custom-select__option")) {
            cur.click();
          }
        } else if (e.key === "Escape" && cs.classList.contains("is-open")) {
          e.preventDefault();
          e.stopPropagation();
          closeMenu();
          trigger.focus();
        }
      });
    });

    document.addEventListener("click", function (e) {
      if (!e.target.closest(".km-custom-select")) {
        customSelects.forEach(function (cs) {
          cs.classList.remove("is-open");
          var trig = cs.querySelector(".km-custom-select__trigger");
          if (trig) trig.setAttribute("aria-expanded", "false");
        });
      }
    });

    /* ─── 2. Age and price range sliders ─── */
    var rangeRoots = page.querySelectorAll("[data-range]");
    rangeRoots.forEach(function (root) {
      var min = Number(root.dataset.min || 0);
      var max = Number(root.dataset.max || 18);
      var unit = root.dataset.unit || "";
      var isPriceRange = root.classList.contains("filter-price-range");
      var fromInput = root.querySelector("[data-range-from-input]");
      var toInput = root.querySelector("[data-range-to-input]");
      var fromRange = root.querySelector("[data-range-from-range]");
      var toRange = root.querySelector("[data-range-to-range]");
      var caption = root.querySelector("[data-range-caption]");
      if (!fromInput || !toInput || !fromRange || !toRange) return;

      function clamp(v) {
        var n = Number(v);
        if (!Number.isFinite(n)) return min;
        return Math.min(max, Math.max(min, Math.round(n)));
      }

      function updateCaption(a, b) {
        if (!caption) return;
        var openPriceRange = isPriceRange && b >= max;
        caption.textContent = openPriceRange && a > min
          ? (root.dataset.fromLabel || "") + a + " " + unit + (root.dataset.fromSuffix || "")
          : a + "–" + b + (unit ? " " + unit : "");
        if (isPriceRange) {
          toRange.setAttribute("aria-valuetext", openPriceRange ? root.dataset.unlimitedLabel : b + " " + unit);
        }
        var fromPct = max > min ? ((a - min) / (max - min)) * 100 : 0;
        var toPct = max > min ? ((b - min) / (max - min)) * 100 : 100;
        root.style.setProperty("--from-pct", fromPct + "%");
        root.style.setProperty("--to-pct", toPct + "%");
      }

      function syncFromRange() {
        var a = clamp(fromRange.value);
        var b = clamp(toRange.value);
        if (a > b) {
          if (document.activeElement === fromRange) b = a;
          else a = b;
        }
        fromInput.value = a;
        toInput.value = b;
        fromRange.value = a;
        toRange.value = b;
        updateCaption(a, b);
      }

      function syncFromInput() {
        var a = clamp(fromInput.value || fromRange.value);
        var b = clamp(toInput.value || toRange.value);
        if (a > b) b = a;
        fromInput.value = a;
        toInput.value = b;
        fromRange.value = a;
        toRange.value = b;
        updateCaption(a, b);
      }

      ["input", "change"].forEach(function (evt) {
        fromRange.addEventListener(evt, syncFromRange);
        toRange.addEventListener(evt, syncFromRange);
      });

      syncFromInput();
    });

    if (filtersForm) {
      filtersForm.addEventListener("submit", function (event) {
        var data = new FormData(filtersForm);
        var params = new URLSearchParams();
        var priceRange = filtersForm.querySelector(".filter-price-range");
        var ceiling = priceRange ? Number(priceRange.dataset.max) : NaN;
        var upper = String(data.get("price_to") || "").trim();
        var openUpper = !upper || (Number.isFinite(ceiling) && Number(upper) >= ceiling);
        var neutralAge = data.get("age_from") === "0" && data.get("age_to") === "18";
        data.forEach(function (value, key) {
          var clean = String(value || "").trim();
          if (!clean || key === "page" || (key === "sort" && clean === "new")) return;
          if (neutralAge && (key === "age_from" || key === "age_to")) return;
          if (key === "price_to" && openUpper) return;
          if (key === "price_from" && Number(clean) === 0) return;
          params.append(key, clean);
        });
        var url = new URL(filtersForm.getAttribute("action") || window.location.pathname, window.location.origin);
        url.search = params.toString();
        event.preventDefault();
        window.location.assign(url.href);
      });
    }

    /* ─── 3. Rating Pills (matching catalog places) ─── */
    var ratingPills = page.querySelectorAll("[data-select-target='min_rating']");
    var ratingHiddenInput = page.querySelector("input[name='min_rating']");
    if (ratingPills.length && ratingHiddenInput) {
      ratingPills.forEach(function (pill) {
        pill.addEventListener("click", function () {
          var targetVal = pill.getAttribute("data-select-value") || "";
          ratingHiddenInput.value = targetVal;
          ratingPills.forEach(function (p) {
            var val = p.getAttribute("data-select-value") || "";
            p.classList.toggle("is-active", val === targetVal);
          });
        });
      });
    }

    /* ─── Hero search clear button ─── */
    var heroSearchInput = page.querySelector('#specialists-hero-search-input');
    var heroClearBtn = page.querySelector("[data-search-clear][data-search-target='specialists-hero-search-input']");
    if (heroSearchInput && heroClearBtn) {
      function toggleClearBtn() {
        heroClearBtn.hidden = !heroSearchInput.value.trim();
      }
      heroSearchInput.addEventListener('input', toggleClearBtn);
      heroClearBtn.addEventListener('click', function () {
        heroSearchInput.value = '';
        toggleClearBtn();
        heroSearchInput.focus();
      });
    }

    /* ─── 4. Specialization horizontal strip auto-scroll ─── */
    var activeCategoryChip = page.querySelector(".catalog-category-chip.is-active");
    var categoryStrip = page.querySelector(".catalog-category-strip");
    if (activeCategoryChip && categoryStrip && activeCategoryChip.offsetLeft > categoryStrip.clientWidth / 2) {
      categoryStrip.scrollLeft = activeCategoryChip.offsetLeft - 32;
    }
  }

  function initOwnerSpecialistForm() {
    var form = document.querySelector(".km-specialist-owner-form");
    if (!form) return;

    var isUnified = form.classList.contains("km-unified-form");
    var rulesNode = document.getElementById("specialist-readiness-rules");
    var readinessRules = null;
    try { readinessRules = rulesNode ? JSON.parse(rulesNode.textContent) : null; } catch (_) {}

    function fieldHasValue(field) {
      return Boolean(field && field.value.trim());
    }

    function contactValid(field) {
      if (!fieldHasValue(field) || !field.validity.valid) return false;
      if (!readinessRules) return false;
      var value = field.value.trim();
      if (readinessRules.phone_pattern && !(new RegExp(readinessRules.phone_pattern)).test(value)) return false;
      var digits = value.replace(/\D/g, '').length;
      return (!readinessRules.phone_min_digits || digits >= readinessRules.phone_min_digits) &&
        (!readinessRules.phone_max_digits || digits <= readinessRules.phone_max_digits);
    }

    function hasActivePracticeLocation() {
      if (!readinessRules) return false;
      return Array.from(form.querySelectorAll('[data-practice-row]')).some(function (row) {
        var active = row.querySelector('[name$="-is_active"]');
        var deleted = row.querySelector('[name$="-DELETE"]');
        if (!active || !active.checked || (deleted && deleted.checked)) return false;
        var identities = readinessRules.location_identity_fields || [];
        var required = readinessRules.location_required_fields || [];
        return identities.some(function (name) { return fieldHasValue(row.querySelector('[name$="-' + name + '"]')); }) &&
          required.every(function (name) { return fieldHasValue(row.querySelector('[name$="-' + name + '"]')); });
      });
    }

    if (isUnified) {
      // 1. Ensure all unified sections remain visible on one page
      var unifiedSections = Array.from(form.querySelectorAll(".km-unified-section"));
      unifiedSections.forEach(function (sec) { sec.hidden = false; });

      // Desktop sections remain expanded; small screens use a native disclosure.
      var sectionNavigation = form.querySelector(".km-section-navigation");
      var desktopNavigation = window.matchMedia ? window.matchMedia("(min-width: 1024px)") : null;
      if (sectionNavigation && desktopNavigation) {
        var navigationHeading = sectionNavigation.querySelector("summary");
        function syncSectionNavigation() {
          sectionNavigation.open = desktopNavigation.matches;
          navigationHeading.tabIndex = desktopNavigation.matches ? -1 : 0;
        }
        syncSectionNavigation();
        desktopNavigation.addEventListener("change", syncSectionNavigation);
        navigationHeading.addEventListener("click", function (event) {
          if (desktopNavigation.matches) event.preventDefault();
        });
      }

      // 2. TOC Navigation with smooth scrolling and active link tracking
      var tocLinks = Array.from(form.querySelectorAll("[data-toc-target]"));
      tocLinks.forEach(function (link) {
        link.addEventListener("click", function (e) {
          e.preventDefault();
          var targetId = link.getAttribute("data-toc-target");
          var targetSec = document.getElementById(targetId);
          if (targetSec) {
            if (sectionNavigation && desktopNavigation && !desktopNavigation.matches) {
              sectionNavigation.open = false;
              targetSec.setAttribute("tabindex", "-1");
              targetSec.focus({ preventScroll: true });
            }
            targetSec.scrollIntoView({ behavior: "smooth", block: "start" });
            tocLinks.forEach(function (l) { l.classList.remove("is-active"); });
            link.classList.add("is-active");
          }
        });
      });

      if ("IntersectionObserver" in window && unifiedSections.length) {
        var observer = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              var id = entry.target.id;
              tocLinks.forEach(function (link) {
                var isActive = link.getAttribute("data-toc-target") === id;
                link.classList.toggle("is-active", isActive);
              });
            }
          });
        }, { rootMargin: "-15% 0px -55% 0px", threshold: 0 });
        unifiedSections.forEach(function (sec) { observer.observe(sec); });
      }

      // 3. Mandatory Progress Bar & Live Section Checkmarks
      function updateMandatoryProgress() {
        var nameField = form.querySelector("#id_name");
        var hasName = Boolean(nameField && nameField.value.trim().length > 0);

        var specChecked = form.querySelectorAll('input[name="specializations"]:checked');
        var hasSpecs = specChecked.length > 0;
        var needsSubject = false, hasSubject = false;
        var subjectRulesNode = document.getElementById('specialist-subject-rules');
        if (subjectRulesNode) {
          var subjectRules = JSON.parse(subjectRulesNode.textContent);
          var selectedSpecs = Array.from(specChecked).map(function (cb) { return cb.value; });
          var needsSubject = subjectRules.requires.some(function (id) { return selectedSpecs.indexOf(id) !== -1; });
          var hasSubject = subjectRules.subjects.some(function (id) { return selectedSpecs.indexOf(id) !== -1; });
          var subjectPicker = form.querySelector('[data-subject-picker]');
          if (subjectPicker) subjectPicker.hidden = !needsSubject && !hasSubject;
          var requiredMark = form.querySelector('[data-subject-required-mark]');
          if (requiredMark) requiredMark.hidden = !needsSubject;
          var subjectNotice = form.querySelector('[data-subject-required]');
          if (subjectNotice) subjectNotice.hidden = !needsSubject || hasSubject;
        }

        var langChecked = form.querySelector("#id_language_az:checked, #id_language_ru:checked, #id_language_en:checked");
        var hasLangs = Boolean(langChecked);

        var fmtField = form.querySelector("#id_consultation_format");
        var hasFmt = Boolean(fmtField && fmtField.value.trim().length > 0);
        var needsLocation = Boolean(readinessRules && fmtField && readinessRules.location_required_formats.indexOf(fmtField.value) !== -1);
        var hasLocation = !needsLocation || hasActivePracticeLocation();

        var phoneField = form.querySelector("#id_phone");
        var waField = form.querySelector("#id_whatsapp");
        var hasContacts = (contactValid(phoneField) || contactValid(waField)) &&
          (!fieldHasValue(phoneField) || contactValid(phoneField)) &&
          (!fieldHasValue(waField) || contactValid(waField));

        var hasBio = ["az", "ru", "en"].some(function (l) {
          var el = form.querySelector("#id_bio_" + l);
          return Boolean(el && el.value.trim().length > 0);
        });

        var totalReq = 6 + (needsLocation ? 1 : 0) + (needsSubject ? 1 : 0);
        var doneCount = 0;
        if (hasName) doneCount++;
        if (hasSpecs) doneCount++;
        if (needsSubject && hasSubject) doneCount++;
        if (hasLangs) doneCount++;
        if (hasFmt) doneCount++;
        if (hasContacts) doneCount++;
        if (hasBio) doneCount++;
        if (needsLocation && hasLocation) doneCount++;

        var pct = Math.round((doneCount / totalReq) * 100);
        var invalidField = Array.from(form.querySelectorAll('input,select,textarea')).some(function (field) {
          var row = field.closest('[data-practice-row]');
          var deleted = row && row.querySelector('[name$="-DELETE"]');
          return !(deleted && deleted.checked) && field.willValidate && !field.validity.valid;
        });
        var invalidRange = ['age', 'price'].some(function (prefix) {
          var from = form.querySelector('#id_' + prefix + '_from');
          var to = form.querySelector('#id_' + prefix + '_to');
          return from && to && from.value.trim() && to.value.trim() && Number(from.value) > Number(to.value);
        });
        invalidField = invalidField || invalidRange;
        var isAllDone = Boolean(readinessRules) && doneCount === totalReq && !invalidField;

        // Visual field highlight
        if (nameField) nameField.classList.toggle("is-field-filled", hasName);
        if (phoneField) phoneField.classList.toggle("is-field-filled", Boolean(phoneField.value.trim().length > 0));
        if (waField) waField.classList.toggle("is-field-filled", Boolean(waField.value.trim().length > 0));

        // Top Card Elements
        var topFill = form.querySelector("[data-req-progress-fill]");
        var topBadge = form.querySelector("[data-req-badge]");
        var topStatus = form.querySelector("[data-req-status-text]");

        if (topFill) {
          topFill.style.width = pct + "%";
          topFill.classList.toggle("is-low", pct < 50);
          topFill.classList.toggle("is-mid", pct >= 50 && pct < 100);
          topFill.classList.toggle("is-complete", isAllDone);
        }
        if (topBadge) {
          topBadge.textContent = (isAllDone ? "✓ " : "") + doneCount + " / " + totalReq;
          topBadge.classList.toggle("is-complete", isAllDone);
          topBadge.classList.toggle("is-low", pct < 50);
        }
        if (topStatus) {
          var langCode = (document.documentElement.lang || "ru").toLowerCase();
          if (isAllDone) {
            topStatus.textContent = topStatus.getAttribute("data-all-done") || "Все обязательные поля заполнены! Анкету можно отправлять на модерацию.";
            topStatus.classList.add("is-complete");
          } else {
            topStatus.classList.remove("is-complete");
            var remaining = totalReq - doneCount;
            if (invalidField || !readinessRules) {
              topStatus.textContent = langCode === 'az' ? 'Daxil etdiyiniz məlumatların formatını yoxlayın.' :
                langCode === 'en' ? 'Check the format of the entered details.' : 'Проверьте формат введённых данных.';
            } else if (langCode === "az") {
              topStatus.textContent = "Doldurulub: " + doneCount + " / " + totalReq + " (" + pct + "%). Qalıb: " + remaining + ".";
            } else if (langCode === "en") {
              topStatus.textContent = "Completed: " + doneCount + " of " + totalReq + " (" + pct + "%). Remaining: " + remaining + ".";
            } else {
              topStatus.textContent = "Заполнено: " + doneCount + " из " + totalReq + " (" + pct + "%). Осталось: " + remaining + ".";
            }
          }
        }

        // Sidebar Elements
        var sideFill = form.querySelector("[data-req-sidebar-fill]");
        var sideBadge = form.querySelector("[data-req-sidebar-badge]");
        var sideStatus = form.querySelector("[data-req-sidebar-status]");

        if (sideFill) {
          sideFill.style.width = pct + "%";
          sideFill.classList.toggle("is-low", pct < 50);
          sideFill.classList.toggle("is-mid", pct >= 50 && pct < 100);
          sideFill.classList.toggle("is-complete", isAllDone);
        }
        if (sideBadge) {
          sideBadge.textContent = (isAllDone ? "✓ " : "") + doneCount + " / " + totalReq;
          sideBadge.classList.toggle("is-complete", isAllDone);
          sideBadge.classList.toggle("is-low", pct < 50);
        }
        if (sideStatus) {
          var langCode = (document.documentElement.lang || "ru").toLowerCase();
          if (langCode === "az") {
            sideStatus.textContent = "Məcburi: " + doneCount + " / " + totalReq + " (" + pct + "%)";
          } else if (langCode === "en") {
            sideStatus.textContent = "Required: " + doneCount + " of " + totalReq + " (" + pct + "%)";
          } else {
            sideStatus.textContent = "Обязательно: " + doneCount + " из " + totalReq + " (" + pct + "%)";
          }
        }

        // TOC Status Checkmarks
        function setTocStatus(secId, isDone) {
          var statEl = form.querySelector('[data-sec-status="' + secId + '"]');
          if (!statEl) return;
          statEl.classList.toggle("is-done", isDone);
          statEl.innerHTML = isDone
            ? '<span class="material-symbols-rounded toc-done-icon" aria-hidden="true">check_circle</span>'
            : '<span class="toc-req-dot" aria-hidden="true">*</span>';
        }

        setTocStatus("km-sec-basic", hasName);
        setTocStatus("km-sec-directions", hasSpecs && hasLangs && (!needsSubject || hasSubject));
        setTocStatus("km-sec-format-places", hasFmt && hasLocation);
        setTocStatus("km-sec-pricing-contacts", hasContacts);
        setTocStatus("km-sec-bio-experience", hasBio);
      }

      // Mobile action bar: tuck it away while the full actions card is on screen.
      var mobileBar = form.querySelector("[data-mobile-submit-bar]");
      var actionsCard = form.querySelector(".km-unified-actions-card");
      if (mobileBar && actionsCard && "IntersectionObserver" in window) {
        new IntersectionObserver(function (entries) {
          mobileBar.classList.toggle("is-tucked", entries[0].isIntersecting);
        }).observe(actionsCard);
      }

      form.addEventListener("input", updateMandatoryProgress);
      form.addEventListener("change", updateMandatoryProgress);
      setTimeout(updateMandatoryProgress, 50);

      // Scroll to error if any
      var errorSummary = document.querySelector("[data-error-summary]");
      var firstError = form.querySelector(".auth-field-error, .auth-errors, .errorlist");
      if (errorSummary) {
        // Server-side errors: move focus to the summary so screen readers and keyboard users start there.
        setTimeout(function () {
          errorSummary.scrollIntoView({ behavior: "smooth", block: "start" });
          errorSummary.focus({ preventScroll: true });
        }, 120);
        errorSummary.addEventListener("click", function (event) {
          var link = event.target.closest("a[href^='#']");
          if (!link) return;
          var target = document.getElementById(decodeURIComponent(link.getAttribute("href").slice(1)));
          if (!target) return;
          event.preventDefault();
          var section = target.closest("details");
          if (section) section.open = true;
          var focusable = target.matches("input,select,textarea,button") ? target : target.querySelector("input:not([type=hidden]),select,textarea");
          (focusable || target).scrollIntoView({ behavior: "smooth", block: "center" });
          if (focusable) focusable.focus({ preventScroll: true });
        });
      } else if (firstError) {
        var errorTarget = firstError.closest(".km-unified-section") || firstError;
        setTimeout(function () {
          errorTarget.scrollIntoView({ behavior: "smooth", block: "center" });
          var input = errorTarget.querySelector("input:invalid, select:invalid, textarea:invalid, input:not([type=hidden]), select, textarea");
          if (input) input.focus();
        }, 120);
      }
    } else {
      var steps = Array.from(form.querySelectorAll("[data-owner-step]"));
      var navButtons = Array.from(form.querySelectorAll("[data-owner-step-target]"));
      var nextButtons = Array.from(form.querySelectorAll("[data-owner-next]"));
      var prevButtons = Array.from(form.querySelectorAll("[data-owner-prev]"));
      var progressText = form.querySelector("[data-owner-progress-text]");
      var progressBar = form.querySelector("[data-owner-progress-bar]");
      var current = 0;
      steps.forEach(function(step){var heading=step.querySelector("h2");if(heading)heading.tabIndex=-1;});

      function updateStepErrors() {
        steps.forEach(function (step, i) {
          var hasError = step.querySelector(".auth-field-error, .auth-errors, .errorlist") !== null;
          if (navButtons[i]) {
            navButtons[i].classList.toggle("has-error", hasError);
          }
        });
      }

      function showStep(index, scroll) {
        current = Math.max(0, Math.min(index, steps.length - 1));
        steps.forEach(function (step, i) {
          step.hidden = i !== current;
        });
        navButtons.forEach(function (button, i) {
          var isActive = i === current;
          button.classList.toggle("is-active", isActive);
          button.setAttribute("aria-current", isActive ? "step" : "false");
        });

        var currentStep = steps[current];
        var stepName = currentStep ? (currentStep.getAttribute("data-step-name") || "") : "";
        if (progressText) {
          var labelTemplate = progressText.getAttribute("data-label") || "Шаг {current} из {total}: {name}";
          progressText.textContent = labelTemplate
            .replace("{current}", current + 1)
            .replace("{total}", steps.length)
            .replace("{name}", stepName);
        }
        if (progressBar) {
          progressBar.style.width = (((current + 1) / steps.length) * 100) + "%";
        }

        if (scroll) {
          var header = form.querySelector(".km-owner-stepper, .owner-event-stepper, .km-owner-mobile-progress");
          if (header) {
            header.scrollIntoView({ behavior: "smooth", block: "start" });
            var heading=currentStep.querySelector("h2");if(heading)heading.focus({preventScroll:true});
          }
        }
      }

      navButtons.forEach(function (button, index) {
        button.addEventListener("click", function () { showStep(index, true); });
      });
      nextButtons.forEach(function (button) {
        button.addEventListener("click", function () { showStep(current + 1, true); });
      });
      prevButtons.forEach(function (button) {
        button.addEventListener("click", function () { showStep(current - 1, true); });
      });

      // Error Routing: jump directly to the first step containing an error
      updateStepErrors();
      var firstError = form.querySelector(".auth-field-error, .auth-errors, .errorlist");
      if (firstError) {
        var errorStep = firstError.closest("[data-owner-step]");
        var errorIndex = steps.indexOf(errorStep);
        if (errorIndex >= 0) {
          current = errorIndex;
          setTimeout(function () {
            var targetInput = errorStep.querySelector(".auth-field-error, .errorlist")
              ? errorStep.querySelector("input:invalid, select:invalid, textarea:invalid, input:not([type=hidden]), select, textarea")
              : null;
            if (targetInput) targetInput.focus();
          }, 120);
        }
      }
      form.showSpecialistStep=showStep;
      form.addEventListener('click',function(event){var link=event.target.closest('a[href^="#id_"]');if(!link)return;var target=document.getElementById(link.hash.slice(1));if(!target)return;event.preventDefault();var step=target.closest('[data-owner-step]');if(step)showStep(steps.indexOf(step),false);var panel=target.closest('[data-owner-lang-panel]');if(panel){form.querySelectorAll('[data-owner-lang-panel]').forEach(function(p){p.hidden=p!==panel;p.classList.toggle('is-active',p===panel);});form.querySelectorAll('[data-owner-lang-tab]').forEach(function(t){var active=t.dataset.ownerLangTab===panel.dataset.ownerLangPanel;t.setAttribute('aria-selected',String(active));t.classList.toggle('is-active',active);});}var details=target.closest('details');if(details)details.open=true;target.scrollIntoView({block:'center'});target.focus({preventScroll:true});});
      form.querySelectorAll('details').forEach(function(d){if(d.querySelector('.errorlist'))d.open=true;});
      showStep(current, false);
    }

    // Format selection
    var formatSelect = form.querySelector("#id_consultation_format");
    var locationBlock = form.querySelector("[data-owner-location-block]");
    var formatCards = Array.from(form.querySelectorAll("[data-owner-format-card]"));
    function syncFormat() {
      if (!formatSelect) return;
      // No preselected format: nothing is highlighted and no address is asked until the author picks one.
      var value = formatSelect.value || "";
      if (locationBlock) locationBlock.hidden = value !== "offline" && value !== "both";
      formatCards.forEach(function (card) {
        card.classList.toggle("is-selected", card.getAttribute("data-owner-format-card") === value);
        card.setAttribute("aria-pressed",String(card.getAttribute("data-owner-format-card") === value));
      });
    }
    formatCards.forEach(function (card) {
      card.addEventListener("click", function () {
        if (formatSelect) {
          formatSelect.value = card.getAttribute("data-owner-format-card");
          formatSelect.dispatchEvent(new Event("change", { bubbles: true }));
        }
      });
    });
    if (formatSelect) formatSelect.addEventListener("change", syncFormat);
    syncFormat();

    // Specializations: search and selected bar
    var searchInput = form.querySelector("[data-spec-search]");
    var clearSearchBtn = form.querySelector("[data-spec-search-clear]");
    var specGroups = Array.from(form.querySelectorAll("[data-spec-group]"));
    var allChips = Array.from(form.querySelectorAll(".owner-specialist-chip"));
    var specChips = allChips.filter(function (chip) {
      return Boolean(chip.querySelector('input[name="specializations"]'));
    });
    var noResultsNotice = form.querySelector("[data-spec-no-results]");
    var selectedBar = form.querySelector("[data-owner-selected-specs]");
    var selectedChipsBox = form.querySelector("[data-selected-chips]");
    var selectedCountEl = form.querySelector("[data-selected-count]");
    var clearAllSpecsBtn = form.querySelector("[data-clear-specs]");

    function syncSelectedSpecs() {
      if (!selectedBar || !selectedChipsBox) return;
      var checkedBoxes = specChips.map(function (chip) {
        return chip.querySelector("input[type=checkbox]:checked");
      }).filter(Boolean);

      if (selectedCountEl) selectedCountEl.textContent = checkedBoxes.length;
      selectedBar.hidden = checkedBoxes.length === 0;
      selectedChipsBox.innerHTML = "";

      var categoryBoxes = checkedBoxes.filter(function (cb) { return !cb.closest('[data-subject-picker]'); });
      var dropdownPlaceholder = form.querySelector("[data-owner-spec-placeholder]");
      var dropdownBadge = form.querySelector("[data-selected-count-badge]");
      if (dropdownBadge) {
        dropdownBadge.textContent = categoryBoxes.length;
        dropdownBadge.hidden = categoryBoxes.length === 0;
      }
      if (dropdownPlaceholder) {
        var language = (document.documentElement.lang || '').toLowerCase();
        var isAz = language === 'az';
        if (categoryBoxes.length > 0) {
          dropdownPlaceholder.textContent = (isAz ? 'Kateqoriyalar' : language === 'en' ? 'Categories' : 'Категории');
        } else {
          dropdownPlaceholder.textContent = isAz ? 'Kateqoriya seçin: repetitor, loqoped, psixoloq...' : language === 'en' ? 'Choose a category: tutor, speech therapist, psychologist...' : 'Выберите категорию: репетитор, логопед, психолог...';
        }
      }

      checkedBoxes.forEach(function (cb) {
        var labelEl = cb.closest(".owner-specialist-chip");
        var titleText = labelEl ? (labelEl.querySelector(".chip-title") || labelEl).textContent.trim() : "";
        var pill = document.createElement("span");
        pill.className = "selected-chip-pill";
        var title=document.createElement('span');title.className='pill-name';title.textContent=titleText;
        var remove=document.createElement('button');remove.type='button';remove.className='pill-remove';remove.textContent='×';remove.setAttribute('aria-label',(selectedBar.dataset.removeLabel||'Remove')+' '+titleText);pill.append(title,remove);
        pill.querySelector(".pill-remove").addEventListener("click", function () {
          cb.checked = false;
          cb.dispatchEvent(new Event("change", { bubbles: true }));
        });
        selectedChipsBox.appendChild(pill);
      });
    }

    // Dropdown open/close & trigger handlers
    var dropdownRoot = form.querySelector("[data-owner-spec-dropdown]");
    var dropdownTrigger = form.querySelector("[data-owner-spec-dropdown-trigger]");
    var dropdownPanel = form.querySelector("[data-owner-spec-dropdown-panel]");
    var dropdownDoneBtn = form.querySelector("[data-owner-spec-dropdown-done]");

    if (dropdownTrigger && dropdownPanel) {
      dropdownTrigger.addEventListener("click", function (e) {
        e.stopPropagation();
        var isOpen = !dropdownPanel.hidden;
        dropdownPanel.hidden = isOpen;
        dropdownTrigger.setAttribute("aria-expanded", !isOpen ? "true" : "false");
        if (dropdownRoot) dropdownRoot.classList.toggle("is-open", !isOpen);
        if (!isOpen && searchInput) {
          setTimeout(function () { searchInput.focus(); }, 50);
        }
      });

      dropdownTrigger.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          dropdownTrigger.click();
        }
      });

      document.addEventListener("click", function (e) {
        if (dropdownRoot && !dropdownRoot.contains(e.target)) {
          dropdownPanel.hidden = true;
          dropdownTrigger.setAttribute("aria-expanded", "false");
          dropdownRoot.classList.remove("is-open");
        }
      });

      document.addEventListener("keydown", function (e) {
        if (e.key !== "Escape" || dropdownPanel.hidden) return;
        e.preventDefault();
        dropdownPanel.hidden = true;
        dropdownTrigger.setAttribute("aria-expanded", "false");
        if (dropdownRoot) dropdownRoot.classList.remove("is-open");
        dropdownTrigger.focus();
      });

      if (dropdownDoneBtn) {
        dropdownDoneBtn.addEventListener("click", function (e) {
          e.stopPropagation();
          dropdownPanel.hidden = true;
          dropdownTrigger.setAttribute("aria-expanded", "false");
          if (dropdownRoot) dropdownRoot.classList.remove("is-open");
          dropdownTrigger.focus();
        });
      }
    }

    if (clearAllSpecsBtn) {
      clearAllSpecsBtn.addEventListener("click", function () {
        specChips.forEach(function (chip) {
          var cb = chip.querySelector("input[type=checkbox]");
          if (cb) cb.checked = false;
          chip.classList.remove("is-checked");
        });
        syncSelectedSpecs();
        form.dispatchEvent(new Event("change",{bubbles:true}));
      });
    }

    allChips.forEach(function (chip) {
      var cb = chip.querySelector("input[type=checkbox]");
      if (cb) {
        cb.addEventListener("change", function () {
          chip.classList.toggle("is-checked", cb.checked);
          if (cb.name === 'specializations') syncSelectedSpecs();
        });
        chip.classList.toggle("is-checked", cb.checked);
      }
    });
    syncSelectedSpecs();

    if (searchInput) {
      function runSearch() {
        var query = searchInput.value.trim().toLowerCase();
        if (clearSearchBtn) clearSearchBtn.hidden = !query;
        var totalMatches = 0;

        specGroups.forEach(function (group) {
          var chipsInGroup = Array.from(group.querySelectorAll(".owner-specialist-chip"));
          var groupMatches = 0;
          chipsInGroup.forEach(function (chip) {
            var title = chip.getAttribute("data-spec-title") || chip.textContent.toLowerCase();
            var hint = chip.getAttribute("data-spec-hint") || "";
            var matches = !query || title.indexOf(query) !== -1 || hint.indexOf(query) !== -1;
            chip.hidden = !matches;
            if (matches) {
              groupMatches++;
              totalMatches++;
            }
          });
          group.hidden = groupMatches === 0;
        });

        var liveCount=form.querySelector("[data-spec-result-count]");if(liveCount)liveCount.textContent=liveCount.dataset.found+" "+totalMatches;
        if (noResultsNotice) {
          noResultsNotice.hidden = totalMatches > 0;
        }
      }

      searchInput.addEventListener("input", runSearch);
      runSearch();
      if (clearSearchBtn) {
        clearSearchBtn.addEventListener("click", function () {
          searchInput.value = "";
          runSearch();
          searchInput.focus();
        });
      }
    }

    // Bio Language tabs & indicators
    var langTabs = form.querySelectorAll("[data-owner-lang-tab]");
    var langPanels = form.querySelectorAll("[data-owner-lang-panel]");
    function updateBioIndicators() {
      ["az", "ru", "en"].forEach(function (lang) {
        var textarea = form.querySelector("#id_bio_" + lang);
        var indicator = form.querySelector('[data-bio-indicator="' + lang + '"]');
        if (textarea && indicator) {
          var filled = textarea.value.trim().length > 0;
          indicator.textContent = filled ? "✓" : "";
          indicator.classList.toggle("is-filled", filled);
        }
      });
    }

    langTabs.forEach(function(tab,index){
      var lang=tab.dataset.ownerLangTab;tab.id='specialist-bio-tab-'+lang;tab.setAttribute('aria-controls','specialist-bio-panel-'+lang);tab.tabIndex=index===0?0:-1;
      var panel=form.querySelector('[data-owner-lang-panel="'+lang+'"]');panel.id='specialist-bio-panel-'+lang;panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby',tab.id);panel.hidden=index!==0;
      tab.addEventListener('keydown',function(event){var tabs=Array.from(langTabs),target=null;if(event.key==='ArrowRight')target=tabs[(index+1)%tabs.length];if(event.key==='ArrowLeft')target=tabs[(index+tabs.length-1)%tabs.length];if(event.key==='Home')target=tabs[0];if(event.key==='End')target=tabs[tabs.length-1];if(target){event.preventDefault();target.click();target.focus();}});
    });
    langTabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        var lang = tab.getAttribute("data-owner-lang-tab");
        langTabs.forEach(function (item) {
          var isActive = item === tab;
          item.classList.toggle("is-active", isActive);
          item.setAttribute("aria-selected", isActive ? "true" : "false");
          item.tabIndex=isActive?0:-1;
          item.classList.toggle("is-active",isActive);
        });
        langPanels.forEach(function (panel) {
          panel.hidden = panel.getAttribute("data-owner-lang-panel") !== lang;
          panel.classList.toggle("is-active",!panel.hidden);
        });
      });
    });

    var pageLanguage = (document.documentElement.lang || 'az').toLowerCase().split('-')[0];
    var initialBioTab = Array.from(langTabs).find(function (tab) { return tab.dataset.ownerLangTab === pageLanguage; }) || langTabs[0];
    if (initialBioTab) initialBioTab.click();

    // Error links must reveal the target even in the unified (non-wizard) form.
    if (isUnified) form.addEventListener('click', function (event) {
      var link = event.target.closest('a[href^="#id_"]');
      if (!link) return;
      var target = document.getElementById(link.hash.slice(1));
      if (!target) return;
      event.preventDefault();
      if (target.id === 'id_specializations') {
        var subjectNotice = form.querySelector('[data-subject-required]');
        if (subjectNotice && !subjectNotice.hidden) target = form.querySelector('[data-subject-picker] input') || target;
      }
      var panel = target.closest('[data-owner-lang-panel]');
      if (panel) {
        var tab = form.querySelector('[data-owner-lang-tab="' + panel.dataset.ownerLangPanel + '"]');
        if (tab) tab.click();
      }
      var details = target.closest('details');
      if (details) details.open = true;
      var locationPanel = target.closest('[data-location-panel]');
      if (locationPanel) {
        var row = locationPanel.closest('[data-practice-row]');
        var modeButton = row.querySelector('[data-type-target="' + locationPanel.dataset.locationPanel + '"]');
        if (modeButton) modeButton.click();
      }
      target.scrollIntoView({block:'center'});
      target.focus({preventScroll:true});
    });
    form.querySelectorAll('details').forEach(function (details) {
      if (details.querySelector('.auth-field-error, .errorlist')) details.open = true;
    });

    ["az", "ru", "en"].forEach(function (lang) {
      var textarea = form.querySelector("#id_bio_" + lang);
      if (textarea) textarea.addEventListener("input", updateBioIndicators);
    });
    updateBioIndicators();

    // Photo preview and Dropzone
    var photoInput = form.querySelector("#id_photo");
    var photoPreview = form.querySelector("[data-owner-photo-preview]");
    var photoChoose = form.querySelector('[data-specialist-photo-choose]');
    var photoDropzone = form.querySelector('[data-owner-photo-dropzone]');

    if (photoChoose && photoInput) {
      photoChoose.addEventListener('click', function(e) {
        e.stopPropagation();
        photoInput.click();
      });
    }

    if (photoDropzone && photoInput) {
      photoDropzone.addEventListener('click', function(e) {
        if (e.target.closest('[data-specialist-photo-choose]')) return;
        photoInput.click();
      });

      photoDropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        photoDropzone.classList.add('is-dragover');
      });

      photoDropzone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        photoDropzone.classList.remove('is-dragover');
      });

      photoDropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        photoDropzone.classList.remove('is-dragover');
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
          var file = e.dataTransfer.files[0];
          if (file && file.type && file.type.indexOf('image/') === 0) {
            photoInput.files = e.dataTransfer.files;
            photoInput.dispatchEvent(new Event('change', { bubbles: true }));
          }
        }
      });
    }

    var widgetError = form.querySelector('.km-file-input-hidden [data-upload-error]'), visiblePhotoError = form.querySelector('[data-specialist-photo-error]');
    if (widgetError && visiblePhotoError) {
      new MutationObserver(function() {
        visiblePhotoError.textContent = widgetError.textContent;
        visiblePhotoError.hidden = widgetError.hidden;
      }).observe(widgetError, { attributes: true, childList: true, subtree: true });
    }

    if (photoInput && photoPreview) {
      photoInput.addEventListener("change", function () {
        var file = photoInput.files && photoInput.files[0];
        if (!file || !file.type || file.type.indexOf("image/") !== 0) return;
        var reader = new FileReader();
        reader.onload = function (event) {
          photoPreview.innerHTML = '<img src="' + event.target.result + '" alt="Avatar preview">';
        };
        reader.readAsDataURL(file);
      });
    }

    // Step 4: WhatsApp copy & auto-sync
    var phoneInput = form.querySelector("#id_phone");
    var waInput = form.querySelector("#id_whatsapp");
    var syncWaBtn = form.querySelector("[data-sync-wa]");
    var sameWaCheckbox = form.querySelector("[data-wa-same]");

    if (phoneInput && waInput) {
      function syncWaFromPhone() {
        var val = phoneInput.value.trim();
        if (val) {
          waInput.value = val;
          waInput.dispatchEvent(new Event("input", { bubbles: true }));
        }
      }

      if (sameWaCheckbox) {
        if (phoneInput.value.trim() && phoneInput.value.trim() === waInput.value.trim()) {
          sameWaCheckbox.checked = true;
          waInput.readOnly = true;
          waInput.classList.add("is-synced-readonly");
        }

        sameWaCheckbox.addEventListener("change", function () {
          if (sameWaCheckbox.checked) {
            syncWaFromPhone();
            waInput.readOnly = true;
            waInput.classList.add("is-synced-readonly");
          } else {
            waInput.readOnly = false;
            waInput.classList.remove("is-synced-readonly");
            waInput.focus();
          }
        });

        phoneInput.addEventListener("input", function () {
          if (sameWaCheckbox.checked) {
            syncWaFromPhone();
          }
        });
      }

      if (syncWaBtn) {
        syncWaBtn.addEventListener("click", function (e) {
          e.preventDefault();
          if (phoneInput.value.trim()) {
            waInput.value = phoneInput.value.trim();
            waInput.dispatchEvent(new Event("input", { bubbles: true }));
            waInput.focus();
            syncWaBtn.classList.add("is-synced");
            setTimeout(function () { syncWaBtn.classList.remove("is-synced"); }, 1500);
          }
        });
      }
    }


  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initCatalogFilters();
      initOwnerSpecialistForm();
    });
  } else {
    initCatalogFilters();
    initOwnerSpecialistForm();
  }
})();
