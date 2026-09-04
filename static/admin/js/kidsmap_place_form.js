/* ==========================================================================
   KidsMap admin — place form page controller.

   Readiness is NOT decided here. The twelve requirements, their labels, their
   messages and their anchors all come from the server
   (catalog.services.place_readiness) through #km-place-progress-config. This
   file only mirrors "is this filled right now?" so the page can react without a
   round trip, and paints the result. If the mirror and the server ever
   disagreed, the server would still be the one refusing to publish — so the
   mirror is deliberately a copy of the same rules, nothing more.

   Photo and gallery behaviour lives in kidsmap_place_media.js.
   ========================================================================== */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn, { once: true });
    } else {
      fn();
    }
  }

  function qs(selector, root) { return (root || document).querySelector(selector); }
  function qsa(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }
  function on(node, type, handler) { if (node) node.addEventListener(type, handler); }

  var SVG_NS = "http://www.w3.org/2000/svg";

  /* Icons are inline SVG from the sprite in _icon_sprite.html. They used to be
     Material Symbols ligatures, but that font build has no ligature table, so
     every icon rendered as its own name in plain text. */
  function iconEl(name, className) {
    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", className ? "km-i " + className : "km-i");
    svg.setAttribute("viewBox", "0 0 960 960");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    var use = document.createElementNS(SVG_NS, "use");
    use.setAttribute("href", "#kmi-" + name);
    svg.appendChild(use);
    return svg;
  }

  function setIcon(node, name) {
    if (!node) return;
    var use = node.tagName && String(node.tagName).toLowerCase() === "use"
      ? node
      : node.querySelector("use");
    if (use) use.setAttribute("href", "#kmi-" + name);
  }

  /* ==========================================================================
     Unified Modal & Toast References (kidsmap_notifications.js)
     ========================================================================== */
  var kmModal = window.kmModal;
  var kmToast = window.kmToast;

  var REDUCED_MOTION = window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
    : false;

  ready(function () {
    var root = qs(".km-pf");
    var form = qs("[data-km-admin-form]") || document.getElementById("place_form");
    if (!root || !form) return;

    var labels = form.dataset;

    /* ----------------------------------------------------------------------
       Sections: collapse, persistence, navigation
       ---------------------------------------------------------------------- */

    var sections = qsa("[data-place-accordion-section]", root);
    var storageKey = "km-place-sections:" + (form.dataset.placeAccordionKey || "default");

    function readStoredState() {
      try {
        var raw = window.localStorage.getItem(storageKey);
        return raw ? JSON.parse(raw) : null;
      } catch (error) {
        return null;
      }
    }

    function writeStoredState() {
      var state = {};
      sections.forEach(function (section) {
        state[section.id] = !section.classList.contains("is-collapsed");
      });
      try {
        window.localStorage.setItem(storageKey, JSON.stringify(state));
      } catch (error) { /* private mode — the page still works */ }
    }

    function sectionHasError(section) {
      return !!section.querySelector(".km-pf-field.is-error, .errorlist, .km-pf-field__error");
    }

    function setExpanded(section, expanded, persist) {
      var toggle = qs("[data-place-section-toggle]", section);
      section.classList.toggle("is-collapsed", !expanded);
      if (toggle) toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
      if (persist !== false) writeStoredState();
    }

    function isExpanded(section) { return !section.classList.contains("is-collapsed"); }

    var stored = readStoredState();
    sections.forEach(function (section) {
      var expanded = true;
      if (stored && Object.prototype.hasOwnProperty.call(stored, section.id)) {
        expanded = !!stored[section.id];
      }
      // A section holding an error is always opened: a hidden error is a dead end.
      if (sectionHasError(section)) expanded = true;
      setExpanded(section, expanded, false);
    });

    sections.forEach(function (section) {
      var toggle = qs("[data-place-section-toggle]", section);
      on(toggle, "click", function () {
        setExpanded(section, !isExpanded(section));
      });
    });

    on(qs("[data-place-accordion-collapse-all]", root), "click", function () {
      sections.forEach(function (section) { setExpanded(section, false, false); });
      writeStoredState();
    });
    on(qs("[data-place-accordion-expand-all]", root), "click", function () {
      sections.forEach(function (section) { setExpanded(section, true, false); });
      writeStoredState();
    });

    /* Sticky navigation ---------------------------------------------------- */

    var navItems = qsa("[data-pf-nav-for]", root);
    var isManualNavClick = false;
    var manualNavTimer = null;

    navItems.forEach(function (item) {
      on(item, "click", function (event) {
        var id = item.dataset.pfNavFor;
        var section = document.getElementById(id);
        if (!section) return;
        event.preventDefault();

        // 1. Immediately highlight clicked item with zero delay
        isManualNavClick = true;
        clearTimeout(manualNavTimer);
        navItems.forEach(function (navItem) {
          var isCur = navItem.dataset.pfNavFor === id;
          navItem.classList.toggle("is-current", isCur);
          navItem.setAttribute("aria-current", isCur ? "step" : "false");
        });

        // 2. Ensure section is expanded and scroll into view
        setExpanded(section, true);
        scrollTo(section);

        // 3. Unlock scrollspy once smooth scroll completes
        manualNavTimer = setTimeout(function () {
          isManualNavClick = false;
          markCurrentSection();
        }, 850);
      });
    });

    function markCurrentSection() {
      if (isManualNavClick) return;

      // When scrolled to the very bottom, activate the last section
      var atBottom = (window.innerHeight + window.scrollY) >= (document.documentElement.scrollHeight - 60);
      if (atBottom && sections.length > 0) {
        var lastSection = sections[sections.length - 1];
        navItems.forEach(function (item) {
          var isCur = item.dataset.pfNavFor === lastSection.id;
          item.classList.toggle("is-current", isCur);
          item.setAttribute("aria-current", isCur ? "step" : "false");
        });
        return;
      }

      // Check if user is actively interacting with an input inside a section
      var activeSec = (document.activeElement && typeof document.activeElement.closest === "function")
        ? document.activeElement.closest("[data-place-accordion-section]")
        : null;

      var current = null;
      if (activeSec && sections.indexOf(activeSec) !== -1) {
        current = activeSec;
      } else {
        var nav = qs("[data-pf-nav]", root);
        var navBottom = nav ? nav.getBoundingClientRect().bottom : 70;
        // Viewport checkpoint: ~30-35% down the window, below the sticky nav
        var checkpoint = Math.max(navBottom + 40, Math.min(window.innerHeight * 0.35, 260));

        sections.forEach(function (section) {
          var box = section.getBoundingClientRect();
          if (box.top <= checkpoint && box.bottom > navBottom + 10) {
            current = section;
          }
        });
      }

      if (!current && sections.length > 0) {
        current = sections[0];
      }

      navItems.forEach(function (item) {
        var isCur = !!current && item.dataset.pfNavFor === current.id;
        item.classList.toggle("is-current", isCur);
        item.setAttribute("aria-current", isCur ? "step" : "false");
      });
    }

    var scrollTicking = false;
    window.addEventListener("scroll", function () {
      if (scrollTicking) return;
      scrollTicking = true;
      window.requestAnimationFrame(function () {
        markCurrentSection();
        scrollTicking = false;
      });
    }, { passive: true });
    root.addEventListener("focusin", function () {
      markCurrentSection();
    });
    markCurrentSection();

    function scrollTo(node) {
      node.scrollIntoView({ behavior: REDUCED_MOTION ? "auto" : "smooth", block: "start" });
    }

    /* ----------------------------------------------------------------------
       Going to a problem: open the section, scroll, highlight, focus
       ---------------------------------------------------------------------- */

    function resolveTarget(anchor) {
      if (!anchor) return null;
      var value = String(anchor);
      if (value.charAt(0) === "#") value = value.slice(1);
      if (!value) return null;
      if (value.charAt(0) === "[" || value.charAt(0) === ".") return qs(value);
      return document.getElementById(value) || qs("#" + CSS.escape(value));
    }

    function focusTarget(anchor, sectionHint) {
      var input = resolveTarget(anchor);
      var scrollNode = null;

      if (input) {
        scrollNode = input.closest(".km-pf-field") || input.closest("[data-pf-group]") || input;
      }
      if (!scrollNode && sectionHint) {
        scrollNode = resolveTarget(sectionHint);
      }
      if (!scrollNode) return;

      var section = scrollNode.closest("[data-place-accordion-section]");
      if (section) setExpanded(section, true);

      var disclosure = scrollNode.closest("details");
      if (disclosure) disclosure.open = true;

      var pane = scrollNode.closest("[data-pf-langpane]");
      if (pane) activateLanguagePane(pane);

      window.setTimeout(function () {
        scrollNode.scrollIntoView({
          behavior: REDUCED_MOTION ? "auto" : "smooth",
          block: "center",
        });
        scrollNode.classList.add("km-pf-highlight");
        window.setTimeout(function () {
          scrollNode.classList.remove("km-pf-highlight");
        }, 700);

        if (input && typeof input.focus === "function" && !input.disabled) {
          window.setTimeout(function () {
            try { input.focus({ preventScroll: true }); } catch (error) { /* ignore */ }
            if (input.classList && input.classList.contains("select2-hidden-accessible") && window.jQuery) {
              try { window.jQuery(input).select2("open"); } catch (error) { /* ignore */ }
            }
          }, REDUCED_MOTION ? 0 : 260);
        }
      }, 0);
    }

    document.addEventListener("click", function (event) {
      var link = event.target.closest("[data-place-error-link]");
      if (!link || !root.contains(link)) return;
      event.preventDefault();
      focusTarget(link.getAttribute("href"), link.dataset.placeErrorSection);
    });

    var errorSummary = qs("[data-place-error-summary]", root);
    if (errorSummary) {
      window.setTimeout(function () {
        errorSummary.scrollIntoView({ behavior: REDUCED_MOTION ? "auto" : "smooth", block: "start" });
        try { errorSummary.focus({ preventScroll: true }); } catch (error) { /* ignore */ }
      }, 60);
    }

    /* ----------------------------------------------------------------------
       Language tabs
       ---------------------------------------------------------------------- */

    function activateLanguagePane(pane) {
      var group = pane.closest("[data-pf-langgroup]") || pane.parentElement;
      if (!group) return;
      var code = pane.dataset.pfLangpane;
      setLanguage(group, code);
    }

    function setLanguage(group, code) {
      qsa("[data-pf-langpane]", group).forEach(function (pane) {
        var active = pane.dataset.pfLangpane === code;
        pane.classList.toggle("is-hidden", !active);
        pane.hidden = !active;
      });
      qsa("[data-pf-langtab]", group).forEach(function (tab) {
        var active = tab.dataset.pfLangtab === code;
        tab.classList.toggle("is-active", active);
        tab.setAttribute("aria-selected", active ? "true" : "false");
      });
    }

    function bindLanguageGroup(group) {
      qsa("[data-pf-langtab]", group).forEach(function (tab) {
        on(tab, "click", function () { setLanguage(group, tab.dataset.pfLangtab); });
      });
      updateLanguageMarks(group);
      qsa("[data-pf-langpane] input, [data-pf-langpane] textarea", group).forEach(function (field) {
        on(field, "input", function () { updateLanguageMarks(group); });
      });
    }

    function updateLanguageMarks(group) {
      qsa("[data-pf-langtab]", group).forEach(function (tab) {
        var pane = qs('[data-pf-langpane="' + tab.dataset.pfLangtab + '"]', group);
        if (!pane) return;
        var fields = qsa("input, textarea", pane);
        var filled = fields.length > 0 && fields.every(function (field) {
          return String(field.value || "").trim() !== "";
        });
        var partial = fields.some(function (field) { return String(field.value || "").trim() !== ""; });
        var hasError = !!pane.querySelector(".km-pf-field.is-error");
        tab.classList.toggle("is-filled", filled);
        tab.classList.toggle("has-error", hasError);
        // Show a mark only when it says something: a filled language, a partly
        // filled one, or an error. An empty tab carries no icon at all.
        var mark = qs("[data-pf-langmark]", tab);
        if (mark) {
          var state = hasError ? "error" : (filled ? "check" : (partial ? "more_horiz" : ""));
          mark.hidden = !state;
          if (state) setIcon(mark, state);
        }
      });
    }

    var mainLangGroup = qs("[data-pf-group='names']", root);
    if (mainLangGroup) bindLanguageGroup(mainLangGroup);
    qsa("[data-pf-langgroup]", root).forEach(bindLanguageGroup);

    /* Description counter -------------------------------------------------- */

    qsa(".km-pf-field__control--counted textarea", root).forEach(function (textarea) {
      var wrap = textarea.parentElement;
      var counter = document.createElement("span");
      counter.className = "km-pf-counter";
      wrap.appendChild(counter);
      var advisory = 120;
      function update() {
        var length = String(textarea.value || "").trim().length;
        counter.textContent = length + " / 1000";
        counter.classList.toggle("is-short", length > 0 && length < advisory);
        counter.title = length > 0 && length < advisory
          ? "Рекомендуем не меньше " + advisory + " символов — на публикацию не влияет"
          : "";
      }
      on(textarea, "input", update);
      update();
    });

    /* ----------------------------------------------------------------------
       Age: dependent fields
       ---------------------------------------------------------------------- */

    var ageBlock = qs("[data-pf-age]", root);
    var ageOpenEnded = document.getElementById("id_age_open_ended");
    var ageTo = document.getElementById("id_age_to");

    function syncAge() {
      if (!ageOpenEnded || !ageTo) return;
      var openEnded = ageOpenEnded.checked;
      ageTo.disabled = openEnded;
      if (openEnded) ageTo.value = "";
      if (ageBlock) ageBlock.classList.toggle("is-open-ended", openEnded);
    }

    on(ageOpenEnded, "change", function () { syncAge(); refreshReadiness(); });
    syncAge();

    /* ----------------------------------------------------------------------
       Phones
       ---------------------------------------------------------------------- */

    function formatAzerbaijanPhone(value) {
      var digits = String(value || "").replace(/\D/g, "");
      var national = digits;
      if (national.slice(0, 3) === "994") {
        national = national.slice(3);
      } else if (national.slice(0, 1) === "0") {
        national = national.slice(1);
      }
      national = national.slice(0, 9);
      if (!national) return "";
      var parts = [];
      [[0, 2], [2, 5], [5, 7], [7, 9]].forEach(function (range) {
        var chunk = national.slice(range[0], range[1]);
        if (chunk) parts.push(chunk);
      });
      return "+994 " + parts.join(" ");
    }

    function syncPhoneInput(input) {
      if (!input) return;
      var formatted = formatAzerbaijanPhone(input.value);
      input.value = formatted;
      var nationalLength = formatted.replace(/\D/g, "").replace(/^994/, "").length;
      input.setCustomValidity(
        !formatted || nationalLength === 9 ? "" : "Введите номер в формате +994 50 123 45 67"
      );
    }

    qsa('input[data-km-az-phone="1"]', root).forEach(function (input) {
      syncPhoneInput(input);
      on(input, "input", function () { syncPhoneInput(input); });
      on(input, "blur", function () { syncPhoneInput(input); });
    });

    var phoneEditor = qs("[data-km-phone-editor]", root);
    if (phoneEditor) {
      var phoneRows = qsa("[data-km-phone-row]", phoneEditor);
      var phoneAdd = qs("[data-km-phone-add]", phoneEditor);

      var updatePhoneAdd = function () {
        if (!phoneAdd) return;
        phoneAdd.hidden = !phoneRows.some(function (row, index) { return index > 0 && row.hidden; });
      };

      on(phoneAdd, "click", function () {
        var next = phoneRows.filter(function (row, index) { return index > 0 && row.hidden; })[0];
        if (!next) return;
        next.hidden = false;
        var input = qs("input", next);
        if (input) input.focus();
        updatePhoneAdd();
      });

      qsa("[data-km-phone-remove]", phoneEditor).forEach(function (button) {
        on(button, "click", function () {
          var row = button.closest("[data-km-phone-row]");
          var input = row ? qs("input", row) : null;
          if (!row || !input) return;
          input.value = "";
          input.setCustomValidity("");
          input.dispatchEvent(new Event("input", { bubbles: true }));
          row.hidden = true;
          updatePhoneAdd();
          refreshReadiness();
        });
      });

      updatePhoneAdd();
    }

    /* ----------------------------------------------------------------------
       Coordinates chip and manual lat/lng
       ---------------------------------------------------------------------- */

    var latInput = document.getElementById("id_lat");
    var lngInput = document.getElementById("id_lng");
    var coordFields = qs("[data-pf-coord-fields]", root);
    var coordChip = qs("[data-pf-coord-chip]", root);
    var headerCoordChip = qs("[data-pf-coords-chip]", root);

    // Reserved for the future "district detected from coordinates" feature: the
    // hint stays hidden until a backend fills it, but the escape hatch works.
    on(qs("[data-pf-district-manual]", root), "click", function () {
      var district = document.getElementById("id_district");
      var hint = qs("[data-pf-district-auto]", root);
      if (hint) hint.hidden = true;
      if (district) {
        district.focus();
        if (window.jQuery && district.classList.contains("select2-hidden-accessible")) {
          try { window.jQuery(district).select2("open"); } catch (error) { /* ignore */ }
        }
      }
    });

    on(qs("[data-pf-coord-manual]", root), "click", function () {
      if (!coordFields) return;
      coordFields.hidden = !coordFields.hidden;
      if (!coordFields.hidden && latInput) latInput.focus();
    });

    function coordsValue() {
      if (!latInput || !lngInput) return null;
      var lat = parseFloat(String(latInput.value || "").trim());
      var lng = parseFloat(String(lngInput.value || "").trim());
      if (isNaN(lat) || isNaN(lng)) return null;
      if (lat < -90 || lat > 90 || lng < -180 || lng > 180) return null;
      return { lat: lat, lng: lng };
    }

    function syncCoordinateChips() {
      var coords = coordsValue();
      if (coordChip) {
        coordChip.classList.toggle("is-filled", !!coords);
        var label = qs("[data-pf-coord-label]", coordChip);
        var value = qs("[data-pf-coord-value]", coordChip);
        var section = qs("[data-km-location-section]", root);
        setIcon(qs("[data-pf-coord-icon]", coordChip), coords ? "check_circle" : "location_off");
        if (label && section) {
          label.textContent = coords
            ? (section.dataset.coordinatesFilledLabel || label.textContent)
            : (section.dataset.coordinatesMissingLabel || label.textContent);
        }
        if (value) value.textContent = coords ? coords.lat.toFixed(4) + ", " + coords.lng.toFixed(4) : "";
      }
      if (headerCoordChip) {
        headerCoordChip.dataset.tone = coords ? "good" : "warn";
        setIcon(qs("[data-pf-coords-chip-icon]", headerCoordChip), coords ? "place" : "location_off");
      }
    }

    [latInput, lngInput].forEach(function (input) {
      if (!input) return;
      on(input, "input", function () { syncCoordinateChips(); refreshReadiness(); });
      on(input, "change", function () { syncCoordinateChips(); refreshReadiness(); });
    });

    /* ----------------------------------------------------------------------
       Management panel conditionals
       ---------------------------------------------------------------------- */

    var statusSelect = document.getElementById("id_status");
    var rejectionRow = qs("[data-place-rejection-row]", root);
    var rejectedValue = form.dataset.rejectedStatus || "rejected";

    function syncRejection() {
      if (!rejectionRow || !statusSelect) return;
      rejectionRow.hidden = statusSelect.value !== rejectedValue;
    }
    on(statusSelect, "change", syncRejection);
    syncRejection();

    var recommendToggle = document.getElementById("id_is_home_recommended");
    var recommendOrder = qs("[data-place-recommendation-order]", root);
    function syncRecommend() {
      if (!recommendOrder || !recommendToggle) return;
      recommendOrder.hidden = !recommendToggle.checked;
    }
    on(recommendToggle, "change", syncRecommend);
    syncRecommend();

    /* ----------------------------------------------------------------------
       Schedule editor: segmented mode control and compact closed rows
       ---------------------------------------------------------------------- */

    var scheduleEditor = qs("[data-km-schedule-editor]", root);
    if (scheduleEditor) {
      var modeSelect = document.getElementById("id_schedule_mode");
      if (modeSelect && modeSelect.options.length > 1 && modeSelect.options.length <= 6) {
        var segmented = document.createElement("div");
        segmented.className = "km-pf-segmented";
        segmented.setAttribute("role", "group");
        Array.prototype.forEach.call(modeSelect.options, function (option) {
          if (!option.value) return;
          var button = document.createElement("button");
          button.type = "button";
          button.className = "km-pf-segmented__item";
          button.textContent = option.textContent;
          button.dataset.value = option.value;
          button.addEventListener("click", function () {
            modeSelect.value = option.value;
            modeSelect.dispatchEvent(new Event("change", { bubbles: true }));
            paintSegmented();
            refreshReadiness();
          });
          segmented.appendChild(button);
        });
        // Jazzmin turns every select into a select2 widget. Park the native
        // control inside a hidden wrapper so the generated container is hidden
        // with it, whichever script runs first.
        var nativeWrap = document.createElement("div");
        nativeWrap.className = "km-pf-native-select";
        nativeWrap.hidden = true;
        modeSelect.parentNode.insertBefore(nativeWrap, modeSelect);
        nativeWrap.appendChild(modeSelect);
        nativeWrap.parentNode.insertBefore(segmented, nativeWrap.nextSibling);

        var paintSegmented = function () {
          qsa(".km-pf-segmented__item", segmented).forEach(function (button) {
            button.classList.toggle("is-active", button.dataset.value === modeSelect.value);
          });
        };
        paintSegmented();
        on(modeSelect, "change", paintSegmented);
      }

      var copyLabel = scheduleEditor.dataset.copyLabel || "Копировать";
      qsa("[data-km-schedule-copy-day]", scheduleEditor).forEach(function (button) {
        button.dataset.pfCopyLabel = copyLabel;
      });

      var paintScheduleRows = function () {
        qsa("[data-km-schedule-row]", scheduleEditor).forEach(function (row) {
          var toggle = qs("[data-km-schedule-open]", row);
          var open = !!(toggle && toggle.checked);
          row.classList.toggle("is-open", open);
          row.classList.toggle("is-closed", !open);
        });
      };

      paintScheduleRows();
      scheduleEditor.addEventListener("change", function () {
        window.setTimeout(function () {
          paintScheduleRows();
          refreshReadiness();
        }, 0);
      });
      scheduleEditor.addEventListener("input", function () {
        window.setTimeout(refreshReadiness, 0);
      });
      scheduleEditor.addEventListener("click", function () {
        window.setTimeout(function () {
          paintScheduleRows();
          refreshReadiness();
        }, 0);
      });
    }

    /* ----------------------------------------------------------------------
       Tariffs: empty state and the computed catalog price
       ---------------------------------------------------------------------- */

    var tariffEditor = qs("[data-tariff-editor]", root);
    var tariffInput = qs("[data-tariff-input]", root);
    var tariffList = qs("[data-tariff-list]", root);
    var tariffEmpty = qs("[data-tariff-empty]", root);
    var tariffComputed = qs("[data-tariff-computed-value]", root);

    function readPlans() {
      if (!tariffInput) return [];
      try {
        var parsed = JSON.parse(tariffInput.value || "[]");
        return Array.isArray(parsed) ? parsed : [];
      } catch (error) {
        return [];
      }
    }

    function planPrices(plan) {
      var kind = plan.price_kind || "exact";
      var numbers = [];
      function push(value) {
        if (value === null || value === undefined || value === "") return;
        var parsed = parseFloat(value);
        if (!isNaN(parsed)) numbers.push(parsed);
      }
      if (kind === "free") return [0];
      if (kind === "exact") push(plan.price);
      if (kind === "from") push(plan.price_min);
      if (kind === "range") { push(plan.price_min); push(plan.price_max); }
      return numbers;
    }

    function syncTariffs() {
      var plans = readPlans();
      if (tariffEmpty) tariffEmpty.hidden = plans.length > 0;
      if (!tariffComputed) return;

      var values = [];
      plans.forEach(function (plan) {
        if (!plan || typeof plan !== "object") return;
        if (plan.is_active === false) return;
        if ((plan.charge_role || "primary") !== "primary") return;
        values = values.concat(planPrices(plan));
      });

      if (!values.length) {
        tariffComputed.textContent = "—";
        return;
      }
      var min = Math.min.apply(null, values);
      var max = Math.max.apply(null, values);
      var format = function (value) { return String(Math.round(value * 100) / 100); };
      tariffComputed.textContent = min === max
        ? format(min) + " ₼"
        : format(min) + "–" + format(max) + " ₼";
    }

    if (tariffList && window.MutationObserver) {
      new MutationObserver(function () {
        syncTariffs();
        refreshReadiness();
      }).observe(tariffList, { childList: true, subtree: true, attributes: true, characterData: true });
    }
    if (tariffEditor) {
      tariffEditor.addEventListener("input", function () {
        window.setTimeout(function () { syncTariffs(); refreshReadiness(); }, 0);
      });
      tariffEditor.addEventListener("change", function () {
        window.setTimeout(function () { syncTariffs(); refreshReadiness(); }, 0);
      });
    }
    syncTariffs();

    /* ----------------------------------------------------------------------
       Readiness mirror
       ---------------------------------------------------------------------- */

    function inputValue(id) {
      var node = document.getElementById(id);
      return node ? String(node.value || "").trim() : "";
    }

    function parseJsonInput(selector) {
      var node = qs(selector);
      if (!node) return null;
      try { return JSON.parse(node.value || "null"); } catch (error) { return null; }
    }

    function hasMainPhoto() {
      var input = document.getElementById("id_photo");
      var preview = qs("[data-main-photo-preview]");
      var clear = document.getElementById("id_photo-clear");
      return !!(
        (input && input.files && input.files.length) ||
        (preview && preview.getAttribute("data-main-photo-initial-url") && !(clear && clear.checked))
      );
    }

    function planHasPublicPrice(plan) {
      if (!plan || typeof plan !== "object") return false;
      if (plan.is_active === false) return false;
      if ((plan.charge_role || "primary") !== "primary") return false;
      var kind = plan.price_kind || "exact";
      if (kind === "exact" || kind === "free") {
        return plan.price !== null && plan.price !== undefined && plan.price !== "";
      }
      if (kind === "from") {
        return plan.price_min !== null && plan.price_min !== undefined && plan.price_min !== "";
      }
      if (kind === "range") {
        return (
          plan.price_min !== null && plan.price_min !== undefined && plan.price_min !== "" &&
          plan.price_max !== null && plan.price_max !== undefined && plan.price_max !== ""
        );
      }
      return false;
    }

    function scheduleIsMeaningful() {
      // The legacy free-text schedule does not count: weekly mode needs at least
      // one open day with a valid interval in the editor.
      var days = parseJsonInput("[data-km-schedule-editor-input]");
      if (!Array.isArray(days)) return false;
      return days.some(function (day) {
        if (!day || typeof day !== "object") return false;
        if (day.is_24_hours) return true;
        return !day.is_closed && Array.isArray(day.intervals) && day.intervals.length > 0;
      });
    }

    var CHECKS = {
      name: function () { return !!inputValue("id_name_az"); },
      description: function () {
        // Length is advice, not a gate: publication only needs a real text.
        return !!inputValue("id_description_az");
      },
      category: function () {
        var node = qs('select[name="category"]');
        return !!(node && node.value);
      },
      subcategory: function () {
        var node = qs('select[name="subcategory"]');
        return !!(node && node.value);
      },
      region: function () {
        var region = document.getElementById("id_region");
        var district = document.getElementById("id_district");
        var value = region ? String(region.value || "").trim() : "";
        if (!value) return false;
        if (value === "baku") return !!(district && String(district.value || "").trim());
        return true;
      },
      address: function () { return !!inputValue("id_address"); },
      coordinates: function () { return !!coordsValue(); },
      age: function () {
        var fromRaw = inputValue("id_age_from");
        if (!fromRaw) return false;
        var openEnded = document.getElementById("id_age_open_ended");
        var toRaw = inputValue("id_age_to");
        if (!toRaw) return !!(openEnded && openEnded.checked);
        return parseInt(toRaw, 10) >= parseInt(fromRaw, 10);
      },
      price: function (config) {
        var modeInput = document.getElementById("id_price_mode");
        var mode = modeInput ? String(modeInput.value || "tariffs").trim() : "tariffs";
        var exemptModes = (config && config.exempt_modes) || [];
        if (exemptModes.indexOf(mode) !== -1) {
          return true;
        }
        var plans = parseJsonInput("[data-tariff-input]");
        if (!Array.isArray(plans)) return false;
        return plans.some(planHasPublicPrice);
      },
      phone: function () { return !!inputValue("id_phone1"); },
      schedule: function (config) {
        var mode = document.getElementById("id_schedule_mode");
        var value = mode ? String(mode.value || "regular") : "regular";
        var exemptModes = (config && config.exempt_modes) || [];
        if (exemptModes.indexOf(value) !== -1) {
          return true;
        }
        return scheduleIsMeaningful();
      },
      photo: function () { return hasMainPhoto(); }
    };

    var CHECKLIST = (function () {
      var node = document.getElementById("km-place-progress-config");
      var items = [];
      if (node) {
        try { items = JSON.parse(node.textContent || "[]"); } catch (error) { items = []; }
      }
      return items.map(function (item) {
        var evaluator = CHECKS[item.check];
        return {
          code: item.code,
          label: item.label,
          message: item.message || "",
          anchor: item.anchor || "",
          section: item.section || "",
          config: item.config || {},
          // Some requirements are satisfied by stored data the browser cannot
          // see (an uploaded cover photo). The server tells us so.
          fallback: !!item.fallback,
          initial: !!item.initial,
          isFilled: function () {
            if (this.fallback) return true;
            return evaluator ? !!evaluator(this.config) : this.initial;
          }
        };
      });
    })();

    var progressBars = qsa("[data-progress-bar]", root);
    var progressPcts = qsa("[data-progress-pct]", root);
    var progressDone = qsa("[data-progress-done]", root);
    var progressTotal = qsa("[data-progress-total]", root);
    var readinessBadges = qsa("[data-progress-readiness]", root);
    var remainingNode = qs("[data-pf-remaining]", root);
    var issuesBox = qs("[data-pf-issues]", root);
    var issuesList = qs("[data-pf-issues-list]", root);
    var readyBanner = qs("[data-pf-ready-banner]", root);
    var publishButtons = qsa("[data-pf-publish]", root);

    function sectionErrorCount(sectionId) {
      var section = document.getElementById(sectionId);
      if (!section) return 0;
      return qsa(".km-pf-field.is-error, .km-pf-field__error", section).length;
    }

    function paintSection(sectionId, done, total) {
      var section = document.getElementById(sectionId);
      var navItem = qs('[data-pf-nav-for="' + sectionId + '"]', root);
      var hasError = sectionErrorCount(sectionId) > 0;
      var state = hasError ? "error" : (total && done >= total ? "done" : (done ? "partial" : "empty"));
      var icons = {
        done: "check_circle",
        partial: "radio_button_checked",
        error: "error",
        empty: "radio_button_unchecked"
      };
      var label = hasError ? (labels.labelError || "Есть ошибка") : (total ? done + " из " + total : "");

      if (section) {
        ["is-done", "is-partial", "is-error", "is-empty"].forEach(function (name) {
          section.classList.remove(name);
        });
        section.classList.add("is-" + state);
        var badge = qs("[data-place-section-state]", section);
        if (badge) {
          var badgeText = qs("[data-place-section-state-text]", badge);
          setIcon(qs("[data-place-section-state-icon]", badge) || qs("svg", badge), icons[state]);
          if (badgeText) badgeText.textContent = label;
        }
      }
      if (navItem) {
        ["is-done", "is-partial", "is-error", "is-empty"].forEach(function (name) {
          navItem.classList.remove(name);
        });
        navItem.classList.add("is-" + state);
        var navSub = qs("[data-pf-nav-sub]", navItem);
        setIcon(qs("[data-pf-nav-icon]", navItem), icons[state]);
        if (navSub) navSub.textContent = label;
      }
    }

    function renderIssues(missing) {
      if (!issuesList || !issuesBox) return;
      issuesBox.hidden = missing.length === 0;
      issuesList.textContent = "";
      missing.forEach(function (item) {
        var link = document.createElement("a");
        link.className = "km-pf-issue";
        link.href = "#" + String(item.anchor || item.section || "").replace(/^#/, "");
        link.setAttribute("data-place-error-link", "");
        link.setAttribute("data-place-error-section", "#" + item.section);
        link.dataset.pfIssueCode = item.code;

        var icon = iconEl("radio_button_unchecked", "km-pf-issue__icon");

        var copy = document.createElement("span");
        copy.className = "km-pf-issue__copy";
        var title = document.createElement("strong");
        title.textContent = item.label;
        var text = document.createElement("span");
        text.textContent = item.message;
        copy.append(title, text);

        var go = document.createElement("span");
        go.className = "km-pf-issue__go";
        go.textContent = "Перейти";
        go.appendChild(iconEl("arrow_forward"));

        link.append(icon, copy, go);
        issuesList.appendChild(link);
      });
    }

    function refreshReadiness() {
      if (!CHECKLIST.length) return;

      var missing = [];
      var perSection = {};
      var done = 0;

      CHECKLIST.forEach(function (item) {
        var filled = item.isFilled();
        if (filled) done += 1; else missing.push(item);
        var bucket = perSection[item.section] || (perSection[item.section] = { done: 0, total: 0 });
        bucket.total += 1;
        if (filled) bucket.done += 1;
      });

      var total = CHECKLIST.length;
      var pct = total ? Math.round((done / total) * 100) : 0;
      // The invariant the whole page rests on: 100% only when nothing is missing.
      if (missing.length) pct = Math.min(pct, 99);

      progressBars.forEach(function (bar) {
        bar.style.width = pct + "%";
        bar.dataset.tone = missing.length ? (pct >= 75 ? "warn" : "error") : "";
        if (!missing.length) bar.removeAttribute("data-tone");
      });
      progressPcts.forEach(function (node) { node.textContent = pct + "%"; });
      progressDone.forEach(function (node) { node.textContent = String(done); });
      progressTotal.forEach(function (node) { node.textContent = String(total); });

      var ready = missing.length === 0;
      readinessBadges.forEach(function (badge) {
        badge.dataset.tone = ready ? "good" : "warn";
        var text = qs("[data-progress-readiness-text]", badge);
        setIcon(qs("[data-progress-readiness-icon]", badge), ready ? "check_circle" : "radio_button_checked");
        if (text) text.textContent = ready ? (labels.labelReady || "") : (labels.labelIncomplete || "");
      });

      if (remainingNode) {
        // A count, not a dump of field names: the full list is the job of the
        // "Проверка" section, which is one click away.
        remainingNode.textContent = ready
          ? (labels.labelAllDone || "")
          : (labels.labelRemaining || "").replace("%(count)s", String(missing.length));
      }

      Object.keys(perSection).forEach(function (sectionId) {
        paintSection(sectionId, perSection[sectionId].done, perSection[sectionId].total);
      });
      paintSection("verification", done, total);

      renderIssues(missing);
      if (readyBanner) readyBanner.hidden = !ready;

      publishButtons.forEach(function (button) {
        button.disabled = !ready;
        if (!ready) {
          button.title = labels.labelPublishBlocked || "";
        } else {
          button.removeAttribute("title");
        }
      });
    }

    // Any change anywhere in the form can move a readiness item.
    form.addEventListener("input", function () { window.setTimeout(refreshReadiness, 0); });
    form.addEventListener("change", function () { window.setTimeout(refreshReadiness, 0); });

    /* ----------------------------------------------------------------------
       Catalog preview card
       ---------------------------------------------------------------------- */

    var taxonomy = (function () {
      var node = document.getElementById("km-place-taxonomy-config");
      if (!node) return { categories: [] };
      try { return JSON.parse(node.textContent || "{}"); } catch (error) { return { categories: [] }; }
    })();

    /* ----------------------------------------------------------------------
       Taxonomy: Searchable Category & Subcategory Dropdown Pickers
       ---------------------------------------------------------------------- */

    function initTaxonomyDropdownPickers() {
      var categorySelect = qs('select[name="category"]', root);
      var subcategorySelect = qs('select[name="subcategory"]', root);
      if (!categorySelect && !subcategorySelect) return;

      var categories = taxonomy.categories || [];
      var subcategories = taxonomy.subcategories || [];

      function createIconElement(item, isSub) {
        var wrap = document.createElement("span");
        wrap.className = "km-pf-picker-icon-wrap";
        if (item && item.color_bg) wrap.style.backgroundColor = item.color_bg;
        if (item && item.color_text) wrap.style.color = item.color_text;

        if (item && item.icon) {
          var img = document.createElement("img");
          img.src = item.icon;
          img.alt = "";
          img.loading = "lazy";
          wrap.appendChild(img);
          return wrap;
        }
        if (item && item.icon_class) {
          var icon = document.createElement("i");
          icon.className = item.icon_class;
          wrap.appendChild(icon);
          return wrap;
        }
        wrap.innerHTML = '<svg class="km-i" viewBox="0 0 960 960"><use href="#kmi-category"></use></svg>';
        return wrap;
      }

      function buildDropdown(options) {
        var select = options.select;
        if (!select) return null;

        var nativeWrap = document.createElement("div");
        nativeWrap.className = "km-pf-native-select";
        nativeWrap.hidden = true;
        select.parentNode.insertBefore(nativeWrap, select);
        nativeWrap.appendChild(select);

        var container = document.createElement("div");
        container.className = "km-pf-picker-wrap";

        var button = document.createElement("button");
        button.type = "button";
        button.className = "km-pf-picker-btn";
        button.setAttribute("aria-haspopup", "listbox");
        button.setAttribute("aria-expanded", "false");

        var iconSlot = document.createElement("span");
        iconSlot.className = "km-pf-picker-btn__icon";
        button.appendChild(iconSlot);

        var labelSlot = document.createElement("span");
        labelSlot.className = "km-pf-picker-btn__label";
        button.appendChild(labelSlot);

        var arrow = document.createElement("span");
        arrow.className = "km-pf-picker-btn__arrow";
        arrow.innerHTML = '<svg class="km-i" viewBox="0 0 960 960"><use href="#kmi-unfold_more"></use></svg>';
        button.appendChild(arrow);

        container.appendChild(button);

        var dropdown = document.createElement("div");
        dropdown.className = "km-pf-picker-dropdown";
        dropdown.hidden = true;

        var searchBox = document.createElement("div");
        searchBox.className = "km-pf-picker-search";
        searchBox.innerHTML = '<svg class="km-i" viewBox="0 0 960 960"><use href="#kmi-search"></use></svg>';
        var searchInput = document.createElement("input");
        searchInput.type = "text";
        searchInput.placeholder = options.searchPlaceholder || "Поиск...";
        searchInput.autocomplete = "off";
        searchBox.appendChild(searchInput);
        dropdown.appendChild(searchBox);

        var listNode = document.createElement("div");
        listNode.className = "km-pf-picker-list";
        listNode.setAttribute("role", "listbox");
        dropdown.appendChild(listNode);

        var footer = document.createElement("span");
        footer.className = "km-pf-picker-footer";
        footer.textContent = "↑ ↓ — выбор, Enter — подтвердить";
        dropdown.appendChild(footer);

        container.appendChild(dropdown);
        nativeWrap.parentNode.insertBefore(container, nativeWrap.nextSibling);

        var focusedIndex = -1;

        function updateButtonDisplay() {
          var val = select.value;
          var selectedItem = null;
          var items = options.getItems();

          if (val) {
            selectedItem = items.filter(function (it) {
              return String(it.code || it.id) === String(val);
            })[0];
          }

          if (selectedItem) {
            iconSlot.innerHTML = "";
            var iconEl = createIconElement(selectedItem, options.isSubcategory);
            iconSlot.appendChild(iconEl);
            iconSlot.hidden = false;
            labelSlot.textContent = selectedItem.label || selectedItem.name || "";
            labelSlot.classList.remove("km-pf-picker-btn__placeholder");
          } else {
            iconSlot.innerHTML = "";
            iconSlot.hidden = true;
            labelSlot.textContent = options.placeholder || "Выберите значение...";
            labelSlot.classList.add("km-pf-picker-btn__placeholder");
          }

          if (options.isDisabled && options.isDisabled()) {
            button.disabled = true;
            if (!val) labelSlot.textContent = options.disabledPlaceholder || options.placeholder;
          } else {
            button.disabled = false;
          }
        }

        function renderList(query) {
          listNode.innerHTML = "";
          focusedIndex = -1;
          var items = options.getItems();
          var filter = (query || "").trim().toLowerCase();

          var filtered = items.filter(function (it) {
            if (!filter) return true;
            var label = (it.label || it.name || "").toLowerCase();
            return label.indexOf(filter) !== -1;
          });

          if (!filtered.length) {
            var empty = document.createElement("div");
            empty.className = "km-pf-picker-empty";
            empty.textContent = options.emptyText || "Ничего не найдено";
            listNode.appendChild(empty);
            return;
          }

          var currentVal = String(select.value || "");

          filtered.forEach(function (it) {
            var itemBtn = document.createElement("button");
            itemBtn.type = "button";
            itemBtn.className = "km-pf-picker-item";
            itemBtn.setAttribute("role", "option");
            itemBtn.dataset.value = it.code || it.id;
            var isSel = String(it.code || it.id) === currentVal;
            if (isSel) {
              itemBtn.classList.add("is-selected");
              itemBtn.setAttribute("aria-selected", "true");
            }

            var iconEl = createIconElement(it, options.isSubcategory);
            iconEl.classList.add("km-pf-picker-item__icon");
            itemBtn.appendChild(iconEl);

            var nameSpan = document.createElement("span");
            nameSpan.className = "km-pf-picker-item__name";
            nameSpan.textContent = it.label || it.name || "";
            itemBtn.appendChild(nameSpan);

            if (it.subcategory_count !== undefined) {
              var countSpan = document.createElement("span");
              countSpan.className = "km-pf-picker-item__count";
              var c = Number(it.subcategory_count || 0);
              countSpan.textContent = c > 0 ? c + " подкатегорий" : "без подкатегорий";
              itemBtn.appendChild(countSpan);
            }

            itemBtn.addEventListener("click", function (e) {
              e.preventDefault();
              selectValue(it.code || it.id);
            });

            listNode.appendChild(itemBtn);
          });
        }

        function selectValue(val) {
          select.value = val;
          select.dispatchEvent(new Event("change", { bubbles: true }));
          closeDropdown();
          updateButtonDisplay();
          if (options.onSelect) options.onSelect(val);
          refreshReadiness();
          refreshPreview();
        }

        function openDropdown() {
          if (button.disabled) return;
          qsa(".km-pf-picker-wrap.is-open").forEach(function (otherWrap) {
            if (otherWrap !== container) {
              otherWrap.classList.remove("is-open");
              var otherBtn = qs(".km-pf-picker-btn", otherWrap);
              if (otherBtn) {
                otherBtn.classList.remove("is-open");
                otherBtn.setAttribute("aria-expanded", "false");
              }
              var otherDropdown = qs(".km-pf-picker-dropdown", otherWrap);
              if (otherDropdown) otherDropdown.hidden = true;
            }
          });

          var section = container.closest(".km-pf-section");
          if (section) section.classList.add("has-open-picker");

          container.classList.add("is-open");
          button.classList.add("is-open");
          button.setAttribute("aria-expanded", "true");
          dropdown.hidden = false;
          searchInput.value = "";
          renderList("");
          window.setTimeout(function () {
            searchInput.focus();
          }, 50);
        }

        function closeDropdown() {
          container.classList.remove("is-open");
          button.classList.remove("is-open");
          button.setAttribute("aria-expanded", "false");
          dropdown.hidden = true;
          var section = container.closest(".km-pf-section");
          if (section) {
            var anyOpen = qs(".km-pf-picker-wrap.is-open", section);
            if (!anyOpen) section.classList.remove("has-open-picker");
          }
        }

        button.addEventListener("click", function (e) {
          e.preventDefault();
          if (dropdown.hidden) openDropdown();
          else closeDropdown();
        });

        searchInput.addEventListener("input", function () {
          renderList(searchInput.value);
        });

        searchInput.addEventListener("keydown", function (e) {
          var items = qsa(".km-pf-picker-item", listNode);
          if (!items.length) return;

          if (e.key === "ArrowDown") {
            e.preventDefault();
            focusedIndex = (focusedIndex + 1) % items.length;
            highlightItem(items);
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            focusedIndex = (focusedIndex - 1 + items.length) % items.length;
            highlightItem(items);
          } else if (e.key === "Enter") {
            e.preventDefault();
            if (focusedIndex >= 0 && items[focusedIndex]) {
              items[focusedIndex].click();
            } else if (items.length === 1) {
              items[0].click();
            }
          } else if (e.key === "Escape") {
            e.preventDefault();
            closeDropdown();
            button.focus();
          }
        });

        function highlightItem(items) {
          items.forEach(function (item, idx) {
            item.classList.toggle("is-focused", idx === focusedIndex);
            if (idx === focusedIndex) {
              item.scrollIntoView({ block: "nearest" });
            }
          });
        }

        document.addEventListener("click", function (e) {
          if (!container.contains(e.target)) {
            closeDropdown();
          }
        });

        select.addEventListener("change", updateButtonDisplay);
        updateButtonDisplay();

        return {
          updateDisplay: updateButtonDisplay,
          refresh: function () {
            updateButtonDisplay();
            if (!dropdown.hidden) renderList(searchInput.value);
          }
        };
      }

      var categoryPicker = buildDropdown({
        select: categorySelect,
        getItems: function () {
          return categories;
        },
        placeholder: "Выберите категорию...",
        searchPlaceholder: "Поиск категории...",
        emptyText: "Категории не найдены",
        onSelect: function (catCode) {
          if (subcategoryPicker) {
            var validSubs = subcategories.filter(function (s) {
              return String(s.category) === String(catCode);
            });
            var curSubVal = subcategorySelect ? subcategorySelect.value : "";
            var stillValid = validSubs.some(function (s) {
              return String(s.id) === String(curSubVal);
            });
            if (!stillValid && subcategorySelect) {
              subcategorySelect.value = "";
              subcategorySelect.dispatchEvent(new Event("change", { bubbles: true }));
            }
            subcategoryPicker.refresh();
          }
        }
      });

      var subcategoryPicker = buildDropdown({
        select: subcategorySelect,
        isSubcategory: true,
        getItems: function () {
          var selCat = categorySelect ? String(categorySelect.value || "") : "";
          var parentCat = categories.filter(function (c) {
            return String(c.code) === selCat;
          })[0];

          var items = subcategories.filter(function (s) {
            if (!selCat) return false;
            return String(s.category) === selCat;
          });

          return items.map(function (s) {
            return {
              id: s.id,
              code: s.id,
              label: s.label,
              icon: s.icon || (parentCat ? parentCat.icon : ""),
              icon_class: s.icon_class || (parentCat ? parentCat.icon_class : ""),
              color_bg: s.color_bg || (parentCat ? parentCat.color_bg : "#E4F0E9"),
              color_text: s.color_text || (parentCat ? parentCat.color_text : "#136F38"),
            };
          });
        },
        placeholder: "Выберите подкатегорию...",
        disabledPlaceholder: "Сначала выберите категорию",
        searchPlaceholder: "Поиск подкатегории...",
        emptyText: "Подкатегории не найдены",
        isDisabled: function () {
          var selCat = categorySelect ? String(categorySelect.value || "") : "";
          if (!selCat) return true;
          var items = subcategories.filter(function (s) {
            return String(s.category) === selCat;
          });
          return items.length === 0;
        }
      });

      categorySelect.addEventListener("change", function () {
        if (subcategoryPicker) subcategoryPicker.refresh();
      });
    }

    initTaxonomyDropdownPickers();

    function refreshPreview() {
      var titleNode = qs("[data-pf-preview-title]", root);
      if (!titleNode) return;

      var name = inputValue("id_name_ru") || inputValue("id_name_az") || inputValue("id_name_en");
      titleNode.textContent = name || titleNode.dataset.pfDefault || titleNode.textContent;

      var categorySelect = qs('select[name="category"]');
      var categoryNode = qs("[data-pf-preview-category]", root);
      if (categorySelect && categoryNode) {
        var option = categorySelect.options[categorySelect.selectedIndex];
        if (option && option.value) {
          categoryNode.textContent = option.textContent;
          var match = (taxonomy.categories || []).filter(function (item) {
            return String(item.code) === String(option.value);
          })[0];
          if (match) {
            categoryNode.style.backgroundColor = match.color_bg || "";
            categoryNode.style.color = match.color_text || "";
          }
        }
      }

      var ageNode = qs("[data-pf-preview-age]", root);
      if (ageNode) {
        var ageFrom = inputValue("id_age_from");
        var ageToValue = inputValue("id_age_to");
        var openEnded = ageOpenEnded && ageOpenEnded.checked;
        ageNode.textContent = ageFrom
          ? (openEnded || !ageToValue ? ageFrom + "+" : ageFrom + "–" + ageToValue)
          : "—";
      }

      var priceNode = qs("[data-pf-preview-price]", root);
      if (priceNode && tariffComputed) priceNode.textContent = tariffComputed.textContent;

      var addressNode = qs("[data-pf-preview-address]", root);
      if (addressNode) {
        var address = inputValue("id_address");
        if (address) addressNode.textContent = address;
      }

      var imgNode = qs("[data-pf-preview-img]", root);
      var imgEmpty = qs("[data-pf-preview-img-empty]", root);
      var mainPreview = qs("[data-main-photo-preview]");
      if (imgNode && imgEmpty) {
        var src = mainPreview && !mainPreview.hidden ? mainPreview.getAttribute("src") : "";
        if (src) {
          imgNode.src = src;
          imgNode.hidden = false;
          imgEmpty.hidden = true;
        } else {
          imgNode.hidden = true;
          imgEmpty.hidden = false;
        }
      }
    }

    form.addEventListener("input", function () { window.setTimeout(refreshPreview, 0); });
    form.addEventListener("change", function () { window.setTimeout(refreshPreview, 0); });

    /* ----------------------------------------------------------------------
       Save state & Dirty Tracker
       ---------------------------------------------------------------------- */

    var saveStates = qsa("[data-pf-savestate]", root);

    function setSaveState(state, text) {
      var icons = { idle: "check_circle", dirty: "edit_note", saving: "progress_activity", saved: "check_circle", error: "error" };
      saveStates.forEach(function (node) {
        node.dataset.state = state;
        var label = qs("[data-pf-savestate-text]", node);
        setIcon(qs("[data-pf-savestate-icon]", node), icons[state] || "edit_note");
        if (label) label.textContent = text;
      });
    }

    function getReadinessStatus() {
      var missing = [];
      var done = 0;
      CHECKLIST.forEach(function (item) {
        if (item.isFilled()) done += 1;
        else missing.push(item);
      });
      return {
        done: done,
        total: CHECKLIST.length,
        missing: missing,
        isReady: missing.length === 0 && CHECKLIST.length > 0
      };
    }

    var initialSnapshot = "";
    var isDirty = false;
    var submitting = false;
    var bypassNavigationPrompt = false;

    function serializeFormState() {
      var elements = form.elements;
      var state = {};
      for (var i = 0; i < elements.length; i++) {
        var el = elements[i];
        if (!el.name || el.disabled || el.type === "submit" || el.type === "button" || el.type === "reset") continue;
        if (el.name === "csrfmiddlewaretoken" || el.name === "initial-photo") continue;
        if (el.dataset && el.dataset.noDirty) continue;

        if (el.type === "checkbox") {
          state[el.name + "__" + (el.value || "")] = el.checked ? "1" : "0";
        } else if (el.type === "radio") {
          if (el.checked) state[el.name] = el.value;
        } else if (el.type === "file") {
          state[el.name] = el.files && el.files.length ? el.files[0].name + ":" + el.files[0].size : "";
        } else {
          state[el.name] = el.value;
        }
      }
      return JSON.stringify(state);
    }

    function syncDirty() {
      if (submitting) return;
      var currentSnapshot = serializeFormState();
      var wasDirty = isDirty;
      isDirty = Boolean(initialSnapshot && currentSnapshot !== initialSnapshot);

      if (isDirty) {
        setSaveState("dirty", "● " + (labels.labelDirty || "Есть несохранённые изменения"));
      } else {
        setSaveState("saved", "✓ " + (labels.labelSaved || "Все изменения сохранены"));
      }
    }

    window.kmDirtyState = {
      isDirty: function () { return isDirty; },
      setInitial: function () {
        initialSnapshot = serializeFormState();
        isDirty = false;
        setSaveState("saved", "✓ " + (labels.labelSaved || "Все изменения сохранены"));
      },
      markDirty: function () {
        isDirty = true;
        setSaveState("dirty", "● " + (labels.labelDirty || "Есть несохранённые изменения"));
      },
      check: syncDirty,
      bypassNext: function () { bypassNavigationPrompt = true; }
    };

    form.addEventListener("input", function (event) {
      if (!event.isTrusted) return;
      syncDirty();
    });
    form.addEventListener("change", function (event) {
      if (!event.isTrusted) return;
      syncDirty();
    });

    form.addEventListener("submit", function () {
      submitting = true;
      setSaveState("saving", labels.labelSaving || "Сохранение…");
    });

    window.addEventListener("beforeunload", function (event) {
      if (!isDirty || submitting || bypassNavigationPrompt) return;
      event.preventDefault();
      event.returnValue = "";
    });

    /* ----------------------------------------------------------------------
       Navigation interception for unsaved changes
       ---------------------------------------------------------------------- */

    document.addEventListener("click", function (e) {
      if (!isDirty || submitting || bypassNavigationPrompt) return;

      var link = e.target.closest("a[href]");
      if (!link) return;

      var href = link.getAttribute("href");
      if (!href || href.startsWith("#") || href.startsWith("javascript:") || href.startsWith("mailto:") || href.startsWith("tel:")) {
        return;
      }
      if (link.target === "_blank" || link.hasAttribute("download")) {
        return;
      }

      var targetUrl = link.href;
      if (!targetUrl || targetUrl === window.location.href || targetUrl === window.location.href + "#") {
        return;
      }

      e.preventDefault();
      e.stopPropagation();

      kmModal.unsavedChanges({
        title: "Есть несохранённые изменения",
        message: "Вы изменили карточку, но ещё не сохранили изменения.",
        stayText: "Остаться",
        saveText: "Сохранить и выйти",
        discardText: "Выйти без сохранения",
        onStay: function () {},
        onSaveAndExit: function () {
          submitting = true;
          setSaveState("saving", labels.labelSaving || "Сохранение…");
          kmToast.info("Сохранение…");

          var formData = new FormData(form);
          if (!formData.has("_continue")) {
            formData.append("_continue", "1");
          }

          fetch(form.action || window.location.href, {
            method: "POST",
            body: formData,
            headers: { "X-Requested-With": "XMLHttpRequest" }
          }).then(function (res) {
            if (res.ok && res.redirected) {
              bypassNavigationPrompt = true;
              window.location.href = targetUrl;
            } else if (res.ok) {
              return res.text().then(function (html) {
                if (html.indexOf("km-pf-field is-error") !== -1 || html.indexOf("km-pf-alert--danger") !== -1 || html.indexOf("errorlist") !== -1) {
                  submitting = false;
                  isDirty = true;
                  setSaveState("error", "Есть ошибка");
                  kmToast.error("Не удалось сохранить карточку", "Исправьте отмеченные поля и попробуйте снова.", {
                    label: "Показать ошибки",
                    onClick: function () {
                      var summary = qs("[data-place-error-summary]");
                      if (summary) summary.scrollIntoView({ behavior: "smooth", block: "start" });
                    }
                  });
                } else {
                  bypassNavigationPrompt = true;
                  window.location.href = targetUrl;
                }
              });
            } else {
              throw new Error("Save failed");
            }
          }).catch(function () {
            submitting = false;
            isDirty = true;
            setSaveState("error", "Ошибка сохранения");
            kmToast.error("Не удалось сохранить карточку", "Проверьте соединение и попробуйте снова.");
          });
        },
        onExitWithoutSaving: function () {
          bypassNavigationPrompt = true;
          isDirty = false;
          window.location.href = targetUrl;
        }
      });
    }, true);

    /* ----------------------------------------------------------------------
       Publish and Unpublish Confirmation Modals
       ---------------------------------------------------------------------- */

    var publishButtons = qsa("[data-pf-publish], button[name='_publish_place']", root);
    publishButtons.forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        if (btn.dataset.confirmed === "1") return;
        e.preventDefault();
        e.stopPropagation();

        var status = getReadinessStatus();
        if (status.isReady) {
          kmModal.show({
            icon: "public",
            iconTone: "success",
            title: "Опубликовать карточку?",
            message: "Карточка станет доступна пользователям сайта.",
            actions: [
              { label: "Отмена", tone: "secondary" },
              {
                label: "Опубликовать",
                tone: "primary",
                onClick: function () {
                  btn.dataset.confirmed = "1";
                  submitting = true;
                  var hidden = document.createElement("input");
                  hidden.type = "hidden";
                  hidden.name = "_publish_place";
                  hidden.value = "1";
                  form.appendChild(hidden);
                  form.submit();
                }
              }
            ]
          });
        } else {
          var missingCount = status.missing.length || (status.total - status.done);
          kmModal.show({
            icon: "warning",
            iconTone: "warning",
            title: "Карточка пока не готова",
            message: "Заполнено " + status.done + " из " + status.total + " обязательных пунктов.",
            actions: [
              {
                label: "Посмотреть " + missingCount + (missingCount === 1 ? " проблему" : (missingCount < 5 ? " проблемы" : " проблем")),
                tone: "primary",
                onClick: function () {
                  var verificationSection = document.getElementById("verification");
                  if (verificationSection) {
                    setExpanded(verificationSection, true, true);
                    verificationSection.scrollIntoView({ behavior: "smooth", block: "start" });
                  }
                }
              },
              { label: "Закрыть", tone: "secondary" }
            ]
          });
        }
      });
    });

    var unpublishButtons = qsa("button[name='_unpublish_place']", root);
    unpublishButtons.forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        if (btn.dataset.confirmed === "1") return;
        e.preventDefault();
        e.stopPropagation();

        kmModal.show({
          icon: "visibility_off",
          iconTone: "warning",
          isAlertDialog: true,
          title: "Снять карточку с публикации?",
          message: "Она перестанет отображаться на сайте и перейдёт в черновики.",
          actions: [
            { label: "Отмена", tone: "secondary" },
            {
              label: "Снять с публикации",
              tone: "danger",
              onClick: function () {
                btn.dataset.confirmed = "1";
                submitting = true;
                var hidden = document.createElement("input");
                hidden.type = "hidden";
                hidden.name = "_unpublish_place";
                hidden.value = "1";
                form.appendChild(hidden);
                form.submit();
              }
            }
          ]
        });
      });
    });

    /* ----------------------------------------------------------------------
       Numeric inputs: keep them numeric without swallowing shortcuts
       ---------------------------------------------------------------------- */

    root.addEventListener("keydown", function (event) {
      var target = event.target;
      if (!target || target.tagName !== "INPUT") return;
      if (target.getAttribute("inputmode") !== "numeric") return;
      var allowed = [46, 8, 9, 27, 13, 35, 36, 37, 38, 39, 40, 190, 110];
      if (allowed.indexOf(event.keyCode) !== -1) return;
      if (event.ctrlKey || event.metaKey) return;
      var isDigit = (event.keyCode >= 48 && event.keyCode <= 57 && !event.shiftKey) ||
        (event.keyCode >= 96 && event.keyCode <= 105);
      if (!isDigit) event.preventDefault();
    });

    /* First paint & listeners ---------------------------------------------- */

    syncCoordinateChips();
    refreshReadiness();
    refreshPreview();

    // The media module loads separately and reports photo changes back here.
    document.addEventListener("km-place-media-change", function () {
      refreshReadiness();
      refreshPreview();
      syncDirty();
    });

    // The map writes lat/lng programmatically, which fires no input event.
    form.addEventListener("km:location-change", function () {
      syncCoordinateChips();
      refreshReadiness();
      refreshPreview();
      syncDirty();
    });

    // Pricing and Schedule custom events
    form.addEventListener("km:pricing-change", function () {
      refreshReadiness();
      refreshPreview();
      syncDirty();
    });

    form.addEventListener("km:schedule-change", function () {
      refreshReadiness();
      refreshPreview();
      syncDirty();
    });

    // Initialize dirty baseline once all plugins/widgets are loaded
    window.setTimeout(function () {
      window.kmDirtyState.setInitial();

      // Check on-page errors or success
      var errorSummary = qs("[data-place-error-summary]", root);
      if (errorSummary) {
        kmToast.error("Не удалось сохранить карточку", "Исправьте отмеченные поля и попробуйте снова.", {
          label: "Показать ошибки",
          onClick: function () {
            errorSummary.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        });
      } else {
        var successBanner = qs(".alert-success, .messagelist .success");
        if (successBanner && successBanner.textContent) {
          kmToast.success("Изменения сохранены");
        }
      }
    }, 200);
  });
})();
