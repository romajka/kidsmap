    (function () {
      function initCatalogRange(root) {
        const min = Number(root.dataset.min || 0);
        const max = Number(root.dataset.max || 100);
        const unit = root.dataset.unit || "";
        const fromInput = root.querySelector("[data-range-from-input]");
        const toInput = root.querySelector("[data-range-to-input]");
        const fromRange = root.querySelector("[data-range-from-range]");
        const toRange = root.querySelector("[data-range-to-range]");
        const caption = root.querySelector("[data-range-caption]");
        if (!fromInput || !toInput || !fromRange || !toRange) return;

        function clamp(v) {
          const n = Number(v);
          if (!Number.isFinite(n)) return min;
          return Math.min(max, Math.max(min, n));
        }

        function updateCaption(a, b) {
          if (!caption) return;
          const openPriceRange = root.hasAttribute("data-price-range") && a > min && b >= max;
          caption.textContent = openPriceRange
            ? `${root.dataset.fromLabel || ""}${a} ${unit}${root.dataset.fromSuffix || ""}`
            : (unit ? `${a}–${b} ${unit}` : `${a}–${b}`);
          if (root.hasAttribute("data-price-range")) {
            toRange.setAttribute("aria-valuetext", openPriceRange ? caption.textContent : `${b} ${unit}`);
          }
          const fromPct = max > min ? ((a - min) / (max - min)) * 100 : 0;
          const toPct = max > min ? ((b - min) / (max - min)) * 100 : 100;
          root.style.setProperty("--from-pct", fromPct + "%");
          root.style.setProperty("--to-pct", toPct + "%");
        }

        function syncFromInput() {
          let a = clamp(fromInput.value || fromRange.value);
          let b = clamp(toInput.value || toRange.value);
          if (a > b) b = a;
          fromInput.value = a;
          toInput.value = b;
          fromRange.value = a;
          toRange.value = b;
          updateCaption(a, b);
        }

        function syncFromRange() {
          let a = clamp(fromRange.value);
          let b = clamp(toRange.value);
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

        ["input", "change"].forEach((evt) => {
          fromInput.addEventListener(evt, syncFromInput);
          toInput.addEventListener(evt, syncFromInput);
          fromRange.addEventListener(evt, syncFromRange);
          toRange.addEventListener(evt, syncFromRange);
        });

        syncFromInput();
      }
      document.querySelectorAll("[data-range]").forEach(initCatalogRange);
      window.kidsMapInitCatalogRange = initCatalogRange;
    })();

    /* ─── Unified Custom Selects Interactivity ─── */
    (function () {
      function closeAllCustomSelects(except) {
        document.querySelectorAll('.km-custom-select.is-open').forEach(function (other) {
          if (other !== except) {
            other.classList.remove('is-open');
            const otherTrig = other.querySelector('.km-custom-select__trigger');
            if (otherTrig) otherTrig.setAttribute('aria-expanded', 'false');
          }
        });
      }

      function initCustomSelect(cs) {
        if (!cs || cs.dataset.customSelectInit === "true") return;
        cs.dataset.customSelectInit = "true";

        const trigger = cs.querySelector('.km-custom-select__trigger');
        const menu = cs.querySelector('.km-custom-select__menu');
        const valueSpan = cs.querySelector('.km-custom-select__value');
        const options = Array.from(cs.querySelectorAll('.km-custom-select__option'));
        const nativeSelect = cs.querySelector('select');
        if (!trigger || !menu || !options.length) return;

        function closeMenu() {
          cs.classList.remove('is-open');
          trigger.setAttribute('aria-expanded', 'false');
        }

        function openMenu() {
          closeAllCustomSelects(cs);
          cs.classList.add('is-open');
          trigger.setAttribute('aria-expanded', 'true');
        }

        trigger.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          if (cs.classList.contains('is-open')) {
            closeMenu();
          } else {
            openMenu();
          }
        });

        options.forEach(function (opt) {
          opt.tabIndex = -1;
          opt.addEventListener('click', function (e) {
            const val = opt.getAttribute('data-select-value') || opt.getAttribute('data-value') || '';
            const optText = opt.querySelector('.km-custom-select__opt-text');
            const label = optText ? optText.textContent.trim() : opt.textContent.trim();
            const optCount = opt.querySelector('.km-custom-select__opt-count');

            options.forEach(function (o) {
              const isSel = (o === opt);
              o.classList.toggle('is-selected', isSel);
              o.classList.toggle('is-active', isSel);
              o.setAttribute('aria-selected', isSel ? 'true' : 'false');
            });

            if (valueSpan) {
              const optIcon = opt.querySelector('.km-custom-select__opt-icon');
              if (optIcon && val) {
                valueSpan.innerHTML = '<span class="km-custom-select__opt-icon km-custom-select__trigger-icon" style="' + (optIcon.getAttribute('style') || '') + '">' + optIcon.innerHTML + '</span>' +
                  '<span class="km-custom-select__trigger-text">' + label + '</span>' +
                  (optCount ? '<span class="km-custom-select__opt-count">' + optCount.textContent.trim() + '</span>' : '');
              } else if (optCount && val) {
                valueSpan.textContent = label + ' (' + optCount.textContent.trim() + ')';
              } else {
                valueSpan.textContent = label;
              }
            }

            if (nativeSelect) {
              nativeSelect.value = val;
              if (!opt.hasAttribute('data-select-target')) {
                nativeSelect.dispatchEvent(new Event('change', { bubbles: true }));
              }
            }

            closeMenu();
            trigger.focus();
          });
        });

        function focusOption(option) {
          let attempts = 0;
          function focusWhenVisible() {
            if (!cs.classList.contains('is-open')) return;
            if (document.activeElement !== trigger && !menu.contains(document.activeElement)) return;
            option.focus();
            if (document.activeElement !== option && ++attempts < 30) {
              window.requestAnimationFrame(focusWhenVisible);
            }
          }
          focusWhenVisible();
        }

        // Keyboard navigation
        trigger.addEventListener('keydown', function (e) {
          if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            openMenu();
            const firstOpt = menu.querySelector('.km-custom-select__option.is-selected') || options[0];
            if (firstOpt) focusOption(firstOpt);
          } else if (e.key === 'Escape' && cs.classList.contains('is-open')) {
            e.preventDefault();
            e.stopPropagation();
            closeMenu();
          }
        });

        menu.addEventListener('keydown', function (e) {
          const cur = document.activeElement;
          const curIndex = options.indexOf(cur);
          if (e.key === 'ArrowDown') {
            e.preventDefault();
            const nextIndex = curIndex < options.length - 1 ? curIndex + 1 : 0;
            options[nextIndex].focus();
          } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prevIndex = curIndex > 0 ? curIndex - 1 : options.length - 1;
            options[prevIndex].focus();
          } else if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (cur && cur.classList.contains('km-custom-select__option')) {
              cur.click();
            }
          } else if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            closeMenu();
            trigger.focus();
          }
        });

        // Sync when native select changes
        if (nativeSelect) {
          nativeSelect.addEventListener('change', function () {
            const curVal = nativeSelect.value || '';
            let matched = null;
            options.forEach(function (opt) {
              const v = opt.getAttribute('data-select-value') || opt.getAttribute('data-value') || '';
              const isMatch = (v === curVal);
              opt.classList.toggle('is-selected', isMatch);
              opt.classList.toggle('is-active', isMatch);
              opt.setAttribute('aria-selected', isMatch ? 'true' : 'false');
              if (isMatch) matched = opt;
            });
            if (matched && valueSpan) {
              const optText = matched.querySelector('.km-custom-select__opt-text');
              const label = optText ? optText.textContent.trim() : matched.textContent.trim();
              const optCount = matched.querySelector('.km-custom-select__opt-count');
              if (optCount && curVal) {
                valueSpan.textContent = label + ' (' + optCount.textContent.trim() + ')';
              } else {
                valueSpan.textContent = label;
              }
            }
          });
        }
      }

      function initCustomSelects(root) {
        (root || document).querySelectorAll('.km-custom-select').forEach(initCustomSelect);
      }

      window.kidsMapInitCustomSelects = initCustomSelects;
      initCustomSelects(document);

      // Delegated fallback for dynamic nodes
      document.addEventListener('click', function (e) {
        const trigger = e.target.closest('.km-custom-select__trigger');
        if (trigger) {
          const cs = trigger.closest('.km-custom-select');
          if (cs && cs.dataset.customSelectInit !== "true") {
            initCustomSelect(cs);
            trigger.click();
            return;
          }
        }
        if (!e.target.closest('.km-custom-select')) {
          closeAllCustomSelects();
        }
      });
    })();


    (function () {
      const quickMenuButtons = Array.from(document.querySelectorAll("[data-quick-filter-toggle]"));
      const quickMenus = Array.from(document.querySelectorAll("[data-quick-menu]"));
      if (!quickMenuButtons.length || !quickMenus.length) return;
      let activeQuickMenuButton = null;

      function setQuickMenuState(activeName) {
        quickMenus.forEach(function (menu) {
          menu.hidden = menu.dataset.quickMenu !== activeName;
        });
        quickMenuButtons.forEach(function (button) {
          const isActive = button.dataset.quickMenuTarget === activeName;
          button.setAttribute("aria-expanded", isActive ? "true" : "false");
        });
      }

      function closeQuickMenus(restoreFocus) {
        setQuickMenuState("");
        if (restoreFocus && activeQuickMenuButton) {
          activeQuickMenuButton.focus();
        }
        activeQuickMenuButton = null;
      }

      function submitMobileFilters() {
        const filtersForm = document.getElementById("filters-form");
        if (!filtersForm) return;
        filtersForm.requestSubmit ? filtersForm.requestSubmit() : filtersForm.submit();
      }

      window.kidsMapCloseQuickMenus = closeQuickMenus;
      window.kidsMapSubmitMobileFilters = submitMobileFilters;

      document.addEventListener("click", function (event) {
        const toggleButton = event.target.closest("[data-quick-filter-toggle]");
        if (toggleButton) {
          event.preventDefault();
          const targetName = toggleButton.dataset.quickMenuTarget || "";
          const isOpen = toggleButton.getAttribute("aria-expanded") === "true";
          activeQuickMenuButton = isOpen ? null : toggleButton;
          setQuickMenuState(isOpen ? "" : targetName);
          return;
        }

        if (event.target.closest("[data-quick-menu-close]")) {
          event.preventDefault();
          closeQuickMenus(true);
          return;
        }

        if (event.target.closest("[data-quick-menu]")) {
          return;
        }

        closeQuickMenus();
      });

      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          closeQuickMenus(true);
        }
      });
    })();

    (function () {
      const openButtons = Array.from(document.querySelectorAll("[data-filters-open]"));
      const closeBtn = document.querySelector("[data-filters-close]");
      const backdrop = document.querySelector("[data-filters-backdrop]");
      const drawer = document.querySelector("[data-filters-drawer]");

      if (!openButtons.length || !closeBtn || !backdrop || !drawer) return;

      const mobileMedia = window.matchMedia("(max-width: 820px)");
      let pendingFilterFocus = "";
      let activeOpenButton = null;
      let drawerOpen = false;
      let lastDrawerFocus = null;
      const backgroundState = new Map();

      function isolateBackground(isolate) {
        if (!isolate) {
          backgroundState.forEach(function (value, element) {
            if (value === null) element.removeAttribute("inert");
            else element.setAttribute("inert", value);
          });
          backgroundState.clear();
          return;
        }
        // Keep the form's ancestor chain and its clickable backdrop active.
        for (let branch = drawer; branch.parentElement; branch = branch.parentElement) {
          Array.from(branch.parentElement.children).forEach(function (element) {
            if (element === branch || element === backdrop || backgroundState.has(element)) return;
            backgroundState.set(element, element.getAttribute("inert"));
            element.inert = true;
          });
          if (branch.parentElement === document.body) break;
        }
      }

      function focusDrawer() {
        let attempts = 0;
        function focusWhenVisible() {
          if (!drawerOpen || drawer.contains(document.activeElement)) return;
          closeBtn.focus({ preventScroll: true });
          if (document.activeElement !== closeBtn && ++attempts < 60) {
            window.requestAnimationFrame(focusWhenVisible);
          }
        }
        window.requestAnimationFrame(focusWhenVisible);
      }

      function setDrawerOpen(isOpen, restoreFocus) {
        drawerOpen = isOpen && mobileMedia.matches;
        isOpen = drawerOpen;
        drawer.inert = mobileMedia.matches && !isOpen;
        isolateBackground(isOpen);
        if (isOpen) {
          drawer.setAttribute("role", "dialog");
          drawer.setAttribute("aria-modal", "true");
          drawer.setAttribute("aria-labelledby", "mobile-filters-title");
        } else {
          drawer.removeAttribute("role");
          drawer.removeAttribute("aria-modal");
          drawer.removeAttribute("aria-labelledby");
        }
        document.body.classList.toggle("filters-drawer-open", isOpen);
        openButtons.forEach(function (button) {
          button.setAttribute("aria-expanded", isOpen ? "true" : "false");
        });
        drawer.setAttribute("aria-hidden", isOpen || !mobileMedia.matches ? "false" : "true");
        backdrop.hidden = !isOpen;
        if (isOpen) {
          focusDrawer();
        } else if (restoreFocus && activeOpenButton) {
          activeOpenButton.focus();
          activeOpenButton = null;
        }
        if (isOpen && pendingFilterFocus) {
          window.setTimeout(function () {
            const target = drawer.querySelector(`[data-mobile-filter-section="${pendingFilterFocus}"]`) ||
              drawer.querySelector(`.filter-${pendingFilterFocus}`) ||
              drawer.querySelector(`.filter-${pendingFilterFocus}-range`) ||
              drawer.querySelector(`[name="${pendingFilterFocus}"]`);
            if (target && typeof target.scrollIntoView === "function") {
              target.scrollIntoView({ block: "start", behavior: "smooth" });
            }
            pendingFilterFocus = "";
          }, 80);
        }
      }

      document.addEventListener("click", function (event) {
        const openTrigger = event.target.closest("[data-filters-open]");
        if (openTrigger) {
          event.preventDefault();
          if (window.kidsMapCloseQuickMenus) {
            window.kidsMapCloseQuickMenus();
          }
          pendingFilterFocus = openTrigger.dataset.filterFocus || "";
          activeOpenButton = openTrigger;
          setDrawerOpen(true);
          return;
        }

        if (event.target.closest("[data-filters-close]") || event.target.closest("[data-filters-backdrop]")) {
          event.preventDefault();
          setDrawerOpen(false, true);
        }
      });

      document.addEventListener("focusin", function (event) {
        lastDrawerFocus = drawer.contains(event.target) ? event.target : null;
        if (drawerOpen && !drawer.contains(event.target)) focusDrawer();
      });

      function drawerControls() {
        return Array.from(drawer.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]'
        )).filter(function (element) {
          return element.tabIndex >= 0 && !element.matches(":disabled") &&
            !element.closest("[inert]") && element.getClientRects().length > 0 &&
            window.getComputedStyle(element).visibility !== "hidden";
        });
      }

      document.addEventListener("keydown", function (event) {
        if (!drawerOpen) return;
        if (event.key === "Escape") {
          event.preventDefault();
          setDrawerOpen(false, true);
          return;
        }
        if (event.key !== "Tab") return;
        const controls = drawerControls();
        const first = controls[0] || closeBtn;
        const last = controls[controls.length - 1] || closeBtn;
        if (!drawer.contains(document.activeElement) ||
            (event.shiftKey && document.activeElement === first) ||
            (!event.shiftKey && document.activeElement === last)) {
          event.preventDefault();
          (event.shiftKey ? last : first).focus();
        }
      });

      function handleViewportChange() {
        // A media change can hide the focused control before this callback;
        // Chromium then focuses BODY without another focusin event.
        const focusWasInside = drawer.contains(document.activeElement) ||
          (document.activeElement === document.body && lastDrawerFocus !== null);
        setDrawerOpen(false);
        if (focusWasInside) {
          const target = mobileMedia.matches ? openButtons.find(function (button) {
            return button.getClientRects().length > 0;
          }) : drawerControls()[0];
          if (target) target.focus({ preventScroll: true });
        }
        activeOpenButton = null;
      }

      if (typeof mobileMedia.addEventListener === "function") {
        mobileMedia.addEventListener("change", handleViewportChange);
      } else if (typeof mobileMedia.addListener === "function") {
        mobileMedia.addListener(handleViewportChange);
      }

      if (mobileMedia.matches) {
        setDrawerOpen(false);
      } else {
        drawer.setAttribute("aria-hidden", "false");
      }
    })();

    (function () {
      document.querySelectorAll(".event-type-filter").forEach(function (group) {
        const sync = function () {
          group.querySelectorAll(".event-type-option").forEach(function (option) {
            const input = option.querySelector('input[type="radio"]');
            option.classList.toggle("is-active", !!(input && input.checked));
          });
        };
        group.addEventListener("change", sync);
        sync();
      });
    })();

    (function () {
      const selectInputs = Array.from(document.querySelectorAll("[data-option-search-for]"));

      const optionCache = new Map();

      function normalize(text) {
        const translitMap = {
          "ə": "e",
          "Ə": "e",
          "ı": "i",
          "I": "i",
          "İ": "i",
          "ö": "o",
          "Ö": "o",
          "ü": "u",
          "Ü": "u",
          "ş": "s",
          "Ş": "s",
          "ç": "c",
          "Ç": "c",
          "ğ": "g",
          "Ğ": "g"
        };
        return String(text || "")
          .replace(/[ƏəIİıÖöÜüŞşÇçĞğ]/g, function (char) {
            return translitMap[char] || char;
          })
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "");
      }

      function getSelect(name) {
        return document.querySelector(`select[name="${name}"]`);
      }

      function getFilterField(name) {
        return getSelect(name) || document.querySelector(`input[name="${name}"]`);
      }

      function syncTargetButtons(targetName, targetValue) {
        document.querySelectorAll(`[data-select-target="${targetName}"]`).forEach(function (item) {
          const isActive = (item.dataset.selectValue || "") === targetValue;
          item.classList.toggle("is-active", isActive);
          if (item.classList.contains("km-custom-select__option")) {
            item.classList.toggle("is-selected", isActive);
            item.setAttribute("aria-selected", isActive ? "true" : "false");
            if (isActive) {
              const cs = item.closest(".km-custom-select");
              const valueSpan = cs ? cs.querySelector(".km-custom-select__value") : null;
              if (valueSpan) {
                const optText = item.querySelector(".km-custom-select__opt-text");
                const label = optText ? optText.textContent.trim() : item.textContent.trim();
                const optCount = item.querySelector(".km-custom-select__opt-count");
                const optIcon = item.querySelector(".km-custom-select__opt-icon");
                if (optIcon && targetValue) {
                  valueSpan.innerHTML = '<span class="km-custom-select__opt-icon km-custom-select__trigger-icon" style="' + (optIcon.getAttribute('style') || '') + '">' + optIcon.innerHTML + '</span>' +
                    '<span class="km-custom-select__trigger-text">' + label + '</span>' +
                    (optCount ? '<span class="km-custom-select__opt-count">' + optCount.textContent.trim() + '</span>' : '');
                } else if (optCount && targetValue) {
                  valueSpan.textContent = label + ' (' + optCount.textContent.trim() + ')';
                } else {
                  valueSpan.textContent = label;
                }
              }
            }
          }
        });
      }

      function cacheSelectOptions(select) {
        if (!select || optionCache.has(select)) return;
        optionCache.set(
          select,
          Array.from(select.options).map(function (option) {
            return {
              value: option.value,
              label: option.textContent,
              selected: option.selected,
            };
          })
        );
      }

      function rebuildOptions(select, query) {
        const originalOptions = optionCache.get(select);
        if (!originalOptions) return;

        const selectedValue = select.value;
        const cleanQuery = normalize(query);
        const matchingOptions = originalOptions.filter(function (item, index) {
          if (index === 0) return true;
          return !cleanQuery || normalize(item.label).includes(cleanQuery);
        });

        select.innerHTML = "";
        matchingOptions.forEach(function (item) {
          const option = document.createElement("option");
          option.value = item.value;
          option.textContent = item.label;
          select.appendChild(option);
        });

        const currentOptionExists = matchingOptions.some(function (item) {
          return item.value === selectedValue;
        });

        if (selectedValue && !currentOptionExists) {
          const currentOption = originalOptions.find(function (item) {
            return item.value === selectedValue;
          });
          if (currentOption) {
            const option = document.createElement("option");
            option.value = currentOption.value;
            option.textContent = currentOption.label;
            select.appendChild(option);
          }
        }

        select.value = selectedValue && Array.from(select.options).some(function (option) { return option.value === selectedValue; }) ? selectedValue : "";
      }

      function initFilterAutocomplete(input) {
        const targetName = input.dataset.optionSearchFor;
        if (targetName !== "district" && targetName !== "metro") return;

        const container = input.closest(`[data-autocomplete="${targetName}"]`);
        const targetSelect = getSelect(targetName);
        const dropdown = container ? container.querySelector("[data-autocomplete-dropdown]") : null;
        const chip = container ? container.querySelector("[data-autocomplete-chip]") : null;
        const chipLabel = container ? container.querySelector("[data-autocomplete-chip-label]") : null;
        const clearButton = container ? container.querySelector("[data-autocomplete-clear]") : null;
        const popularOptions = container ? container.parentElement.querySelector(".filter-popular-options") : null;
        if (!container || !targetSelect || !dropdown) return;

        const emptyLabel = container.dataset.emptyLabel || "No results found";
        const options = Array.from(targetSelect.options)
          .filter(function (option, index) {
            return index > 0 && option.value;
          })
          .map(function (option) {
            return {
              value: option.value,
              label: option.dataset.labelCurrent || option.textContent.trim(),
              searchTerms: normalize([
                option.value,
                option.textContent,
                option.dataset.labelCurrent,
                option.dataset.labelAz,
                option.dataset.labelRu,
                option.dataset.labelEn,
              ].join(" ")),
            };
          });

        let activeIndex = -1;
        let filteredOptions = options.slice();

        function getSelectedOption() {
          return options.find(function (item) {
            return item.value === targetSelect.value;
          }) || null;
        }

        function setExpandedState(isExpanded) {
          input.setAttribute("aria-expanded", isExpanded ? "true" : "false");
        }

        function hideDropdown() {
          dropdown.hidden = true;
          dropdown.innerHTML = "";
          activeIndex = -1;
          setExpandedState(false);
        }

        function updateChip() {
          const selected = getSelectedOption();
          if (!chip || !chipLabel) return;
          if (!selected) {
            chip.hidden = true;
            if (popularOptions) {
              popularOptions.hidden = false;
            }
            return;
          }
          chipLabel.textContent = selected.label;
          chip.hidden = false;
          if (popularOptions) {
            popularOptions.hidden = true;
          }
        }

        function renderDropdown() {
          dropdown.innerHTML = "";
          if (!filteredOptions.length) {
            const emptyState = document.createElement("div");
            emptyState.className = "filter-autocomplete-empty";
            emptyState.textContent = emptyLabel;
            dropdown.appendChild(emptyState);
            dropdown.hidden = false;
            setExpandedState(true);
            return;
          }

          filteredOptions.forEach(function (item, index) {
            const optionButton = document.createElement("button");
            optionButton.type = "button";
            optionButton.className = "filter-autocomplete-option";
            optionButton.textContent = item.label;
            optionButton.setAttribute("role", "option");
            optionButton.dataset.value = item.value;
            optionButton.classList.toggle("is-active", index === activeIndex);
            optionButton.addEventListener("mousedown", function (event) {
              event.preventDefault();
            });
            optionButton.addEventListener("click", function () {
              applySelection(item.value);
            });
            dropdown.appendChild(optionButton);
          });

          dropdown.hidden = false;
          setExpandedState(true);
        }

        function filterOptions() {
          const cleanQuery = normalize(input.value);
          filteredOptions = options.filter(function (item) {
            return !cleanQuery || item.searchTerms.includes(cleanQuery);
          });
          activeIndex = filteredOptions.length ? 0 : -1;
          renderDropdown();
        }

        function applySelection(value) {
          const selected = options.find(function (item) {
            return item.value === value;
          }) || null;
          targetSelect.value = selected ? selected.value : "";
          input.value = selected ? selected.label : "";
          syncTargetButtons(targetName, targetSelect.value);
          updateChip();
          targetSelect.dispatchEvent(new Event("change", { bubbles: true }));
          hideDropdown();
        }

        function clearSelection() {
          targetSelect.value = "";
          input.value = "";
          syncTargetButtons(targetName, "");
          updateChip();
          targetSelect.dispatchEvent(new Event("change", { bubbles: true }));
          filterOptions();
        }

        input.addEventListener("focus", function () {
          filterOptions();
        });

        input.addEventListener("input", function () {
          if (!input.value.trim()) {
            targetSelect.value = "";
            syncTargetButtons(targetName, "");
            updateChip();
          }
          filterOptions();
        });

        input.addEventListener("keydown", function (event) {
          if (dropdown.hidden && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
            filterOptions();
            return;
          }
          if (event.key === "ArrowDown") {
            event.preventDefault();
            if (!filteredOptions.length) return;
            activeIndex = Math.min(activeIndex + 1, filteredOptions.length - 1);
            renderDropdown();
            return;
          }
          if (event.key === "ArrowUp") {
            event.preventDefault();
            if (!filteredOptions.length) return;
            activeIndex = Math.max(activeIndex - 1, 0);
            renderDropdown();
            return;
          }
          if (event.key === "Enter" && !dropdown.hidden && activeIndex >= 0 && filteredOptions[activeIndex]) {
            event.preventDefault();
            applySelection(filteredOptions[activeIndex].value);
            return;
          }
          if (event.key === "Escape") {
            hideDropdown();
          }
        });

        targetSelect.addEventListener("change", function () {
          const selected = getSelectedOption();
          if (selected && document.activeElement !== input) {
            input.value = selected.label;
          }
          if (!selected && document.activeElement !== input) {
            input.value = "";
          }
          syncTargetButtons(targetName, targetSelect.value);
          updateChip();
        });

        if (clearButton) {
          clearButton.addEventListener("click", function () {
            clearSelection();
            input.focus();
          });
        }

        document.addEventListener("click", function (event) {
          if (!container.contains(event.target)) {
            hideDropdown();
          }
        });

        const initiallySelected = getSelectedOption();
        if (initiallySelected) {
          input.value = initiallySelected.label;
        }
        updateChip();
        syncTargetButtons(targetName, targetSelect.value);
      }

      selectInputs.forEach(function (input) {
        const targetName = input.dataset.optionSearchFor;
        const targetSelect = getSelect(targetName);
        if (!targetSelect) return;
        if (targetName === "district" || targetName === "metro") {
          initFilterAutocomplete(input);
          return;
        }
        cacheSelectOptions(targetSelect);

        input.addEventListener("input", function () {
          rebuildOptions(targetSelect, input.value);
        });
      });

      // Список подкатегорий строится от выбранной категории, поэтому при её
      // смене старое значение обнуляем: иначе фильтр ушёл бы в запрос вместе
      // с новой категорией и выдача оказалась бы пустой.
      function resetSubcategoryField() {
        const subField = getFilterField("subcategory");
        if (!subField || !subField.value) return;
        subField.value = "";
        syncTargetButtons("subcategory", "");
      }

      const categorySelectField = getSelect("category");
      if (categorySelectField) {
        categorySelectField.addEventListener("change", resetSubcategoryField);
      }

      // Блок подкатегорий пересобирается при AJAX-фильтрации, поэтому привязку
      // вынесли в функцию: новые кнопки нужно подключать заново, а старые —
      // не по второму разу (отсюда флаг selectBound).
      function bindSelectTargetButtons(root) {
        (root || document).querySelectorAll("[data-select-target]").forEach(function (button) {
        if (button.dataset.selectBound === "true") return;
        button.dataset.selectBound = "true";
        button.addEventListener("click", function () {
          const targetName = button.dataset.selectTarget;
          const targetValue = button.dataset.selectValue || "";
          const targetSelect = getSelect(targetName);
          const targetField = getFilterField(targetName);
          const targetInput = document.querySelector(`[data-option-search-for="${targetName}"]`);
          if (!targetField) return;

          if (targetSelect) {
            cacheSelectOptions(targetSelect);
          }
          if (targetInput) {
            targetInput.value = "";
          }
          if (targetSelect) {
            rebuildOptions(targetSelect, "");
          }
          targetField.value = targetValue;
          if (targetName === "category") {
            resetSubcategoryField();
          }
          targetField.dispatchEvent(new Event("change", { bubbles: true }));
          syncTargetButtons(targetName, targetValue);
          if (targetName === "category" && window.matchMedia("(max-width: 820px)").matches) {
            const filtersForm = document.getElementById("filters-form");
            if (filtersForm) {
              if (window.kidsMapBuildCatalogFiltersUrl) {
                window.location.href = window.kidsMapBuildCatalogFiltersUrl(filtersForm).href;
              } else {
                filtersForm.requestSubmit ? filtersForm.requestSubmit() : filtersForm.submit();
              }
            }
            return;
          }
          if (button.closest("[data-quick-menu]")) {
            if (window.kidsMapCloseQuickMenus) {
              window.kidsMapCloseQuickMenus();
            }
            if (window.kidsMapSubmitMobileFilters) {
              window.kidsMapSubmitMobileFilters();
            }
          }
        });
        });
      }

      bindSelectTargetButtons(document);
      window.kidsMapBindSelectTargets = bindSelectTargetButtons;

    })();

    (function() {
      const filtersForm = document.getElementById("filters-form");
      let resultsGrid = document.querySelector(".grid");
      const isListMode = document.body.classList.contains("results-list-mode") || (resultsGrid && resultsGrid.classList.contains("results-list-mode"));
      const mobileMedia = window.matchMedia("(max-width: 820px)");
      let activeRequest = null;
      let requestSequence = 0;

      const phoneCards = window.matchMedia("(max-width: 820px)");
      const cardMotion = window.matchMedia("(max-width: 820px) and (prefers-reduced-motion: no-preference)");
      const revealObserver = "IntersectionObserver" in window && new IntersectionObserver((entries, observer) => {
        for (const entry of entries) {
          if (entry.intersectionRatio >= 0.15) {
            entry.target.classList.add("is-revealed");
            observer.unobserve(entry.target);
          }
        }
      }, { threshold: 0.15 });

      function observePlaceCards(root) {
        if (!revealObserver) return;
        revealObserver.disconnect();
        if (cardMotion.matches) {
          root.querySelectorAll(".grid > .place-card:not(.is-revealed)").forEach(card => revealObserver.observe(card));
        }
      }
      observePlaceCards(document);
      cardMotion.addEventListener("change", () => observePlaceCards(document));

      // On touch, :active can arrive on release. Give feedback as soon as the finger lands.
      function updateDetailsPress(event) {
        if (!event.isPrimary || event.pointerType !== "touch") return;
        const link = event.target.closest(".place-card .card-go-btn");
        if (link) link.classList.toggle("is-touch-pressed", event.type === "pointerdown");
      }
      for (const type of ["pointerdown", "pointerup", "pointercancel", "lostpointercapture"]) {
        document.addEventListener(type, updateDetailsPress, { passive: true });
      }

      function syncOfferDetails(root) {
        root.querySelectorAll(".card-offer-details").forEach(function (details) {
          details.open = !phoneCards.matches;
          details.querySelector("summary").hidden = !phoneCards.matches;
        });
      }
      syncOfferDetails(document);
      phoneCards.addEventListener("change", () => syncOfferDetails(document));

      document.addEventListener("focusin", function (event) {
        if (event.target.matches(".active-filter-chip:focus-visible")) {
          event.target.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "instant" });
        }
      });

      function buildFormUrl(form) {
        const formData = new FormData(form);
        const params = new URLSearchParams();
        const neutralAgeRange = formData.get("age_from") === "0" && formData.get("age_to") === "18";
        const priceRange = form.querySelector(".filter-price-range");
        const priceMax = priceRange ? Number(priceRange.dataset.max) : NaN;
        const priceTo = String(formData.get("price_to") || "").trim();
        const openPriceRange = !priceTo || (Number.isFinite(priceMax) && Number(priceTo) >= priceMax);
        const neutralPriceRange = (!formData.get("price_from") || Number(formData.get("price_from")) === 0) && openPriceRange;

        formData.forEach(function (value, key) {
          const cleanValue = String(value || "").trim();
          if (!cleanValue || key === "page" || (key === "sort" && cleanValue === "new")) return;
          if (neutralAgeRange && (key === "age_from" || key === "age_to")) return;
          if (neutralPriceRange && (key === "price_from" || key === "price_to")) return;
          if (openPriceRange && key === "price_to") return;
          params.append(key, cleanValue);
        });

        const action = form.getAttribute("action") || window.location.pathname;
        const url = new URL(action, window.location.origin);
        url.search = params.toString();
        return url;
      }

      function buildFiltersUrl() {
        return buildFormUrl(filtersForm);
      }

      window.kidsMapBuildCatalogFiltersUrl = buildFormUrl;

      function showResultsLoading() {
        const grid = document.querySelector(".grid");
        if (!grid || isListMode) return;
        const skeletonHtml = Array(6).fill().map(function() {
          return '<div class="skeleton-card">' +
                   '<div class="skeleton-img"></div>' +
                   '<div class="skeleton-text"></div>' +
                   '<div class="skeleton-text short"></div>' +
                 '</div>';
        }).join("");
        grid.innerHTML = skeletonHtml;
      }

      function syncSubcategoryFilter(nextDocument) {
        const current = document.querySelector("[data-subcategory-filter]");
        const next = nextDocument.querySelector("[data-subcategory-filter]");

        if (current && next) {
          current.replaceWith(next);
        } else if (current) {
          current.remove();          // категорию сняли — подкатегориям неоткуда взяться
          return;
        } else if (next) {
          const categoryBlock = document.querySelector(".filter-item.filter-category");
          if (!categoryBlock) return;
          categoryBlock.insertAdjacentElement("afterend", next);
        } else {
          return;
        }

        const block = document.querySelector("[data-subcategory-filter]");
        if (block) {
          if (window.kidsMapInitCustomSelects) {
            window.kidsMapInitCustomSelects(block);
          }
          if (window.kidsMapBindSelectTargets) {
            window.kidsMapBindSelectTargets(block);
          }
        }
        // Значение из чипа попадает в select, а отправляет форму именно его
        // change — у свежевставленного узла слушателя ещё нет.
        const select = block && block.querySelector(".filter-select");
        if (select && select.dataset.submitBound !== "true") {
          select.dataset.submitBound = "true";
          select.addEventListener("change", triggerSubmit);
        }
      }

      function replaceCatalogFragment(nextDocument, scrollTop, url) {
        const currentTopStack = document.querySelector(".catalog-top-stack");
        const nextTopStack = nextDocument.querySelector(".catalog-top-stack");
        const currentMainColumn = document.querySelector(".catalog-main-column");
        const nextMainColumn = nextDocument.querySelector(".catalog-main-column");
        const wasMapOpen = !!document.querySelector("[data-catalog-map-panel]:not([hidden])");

        if (!currentTopStack || !nextTopStack || !currentMainColumn || !nextMainColumn) {
          window.location.href = url.href;
          return;
        }

        // Keep the Google canvas and its camera/markers alive across AJAX.
        const currentMapPanel = currentMainColumn.querySelector('[data-catalog-map-panel]');
        const nextMapPanel = nextMainColumn.querySelector('[data-catalog-map-panel]');
        if (currentMapPanel && nextMapPanel) {
          ['.catalog-map-meta', '[data-map-pagination]'].forEach(selector => {
            const current = currentMapPanel.querySelector(selector);
            const next = nextMapPanel.querySelector(selector);
            if (current && next) current.replaceWith(next);
          });
          nextMapPanel.replaceWith(currentMapPanel);
        }
        currentTopStack.replaceWith(nextTopStack);
        currentMainColumn.replaceWith(nextMainColumn);
        observePlaceCards(nextMainColumn);
        syncOfferDetails(nextMainColumn);
        window.kidsMapBindSelectTargets(nextTopStack);
        if (window.kidsMapInitCategoryStrip) window.kidsMapInitCategoryStrip();

        const priceQuickFilter = document.querySelector('.mobile-quick-filter[data-filter-focus="price"]');
        const nextPriceQuickFilter = nextDocument.querySelector('.mobile-quick-filter[data-filter-focus="price"]');
        if (priceQuickFilter && nextPriceQuickFilter) {
          priceQuickFilter.hidden = nextPriceQuickFilter.hidden;
          priceQuickFilter.classList.toggle("is-active", nextPriceQuickFilter.classList.contains("is-active"));
        }

        // Сайдбар при AJAX-фильтрации не переписывается, а список подкатегорий
        // зависит от выбранной категории — иначе после её смены в блоке
        // остались бы подкатегории прошлой категории.
        syncSubcategoryFilter(nextDocument);
        const priceSlot = filtersForm.querySelector("[data-price-filter-slot]");
        const nextSlot = nextDocument.querySelector("[data-price-filter-slot]");
        if (priceSlot && nextSlot) {
          const current = priceSlot.querySelector("[data-price-range]");
          const next = nextSlot.querySelector("[data-price-range]");
          if (current && next && current.dataset.max === next.dataset.max && current.dataset.step === next.dataset.step) {
            const upper = current.querySelector("[data-range-to-range]");
            current.querySelector("[data-range-from-range]").value = next.querySelector("[name=price_from]").value;
            upper.value = next.querySelector("[name=price_to]").value;
            upper.dispatchEvent(new Event("input", {bubbles: true}));
          } else if (current || next) {
            priceSlot.replaceWith(nextSlot);
            if (next) window.kidsMapInitCatalogRange(next);
          }
        }

        const currentHeroSearch = document.getElementById("catalog-hero-search-input");
        const nextHeroSearch = nextDocument.getElementById("catalog-hero-search-input");
        const currentTopSearch = document.querySelector('.top-search-field[name="q"]');
        const nextTopSearch = nextDocument.querySelector('.top-search-field[name="q"]');
        if (currentHeroSearch && nextHeroSearch) {
          currentHeroSearch.value = nextHeroSearch.value;
          syncSearchClearButton(currentHeroSearch);
        }
        if (currentTopSearch && nextTopSearch) {
          currentTopSearch.value = nextTopSearch.value;
        }
        const currentHeroHeading = document.querySelector(".hero-text h1");
        const nextHeroHeading = nextDocument.querySelector(".hero-text h1");
        const currentHeroIntro = document.querySelector(".hero-text > p");
        const nextHeroIntro = nextDocument.querySelector(".hero-text > p");
        if (currentHeroHeading && nextHeroHeading) {
          currentHeroHeading.textContent = nextHeroHeading.textContent;
        }
        if (currentHeroIntro && nextHeroIntro) {
          currentHeroIntro.textContent = nextHeroIntro.textContent;
        }
        if (nextDocument.title) {
          document.title = nextDocument.title;
        }

        if (wasMapOpen) {
          const panel = document.querySelector("[data-catalog-map-panel]");
          if (panel) panel.hidden = false;
        }

        resultsGrid = document.querySelector(".grid");
        bindDynamicCatalogControls();
        window.history.pushState({ catalogUrl: url.href }, "", url.href);
        if (window.kidsMapRefreshCatalogResultsMap) {
          window.kidsMapRefreshCatalogResultsMap();
        }
        requestAnimationFrame(function () {
          window.scrollTo(0, scrollTop);
        });
      }

      function submitFiltersAjax(urlOverride) {
        if (!filtersForm || mobileMedia.matches) return false;
        const url = urlOverride || buildFiltersUrl();
        const scrollTop = window.scrollY;

        if (activeRequest) {
          activeRequest.abort();
        }
        const requestId = ++requestSequence;
        const controller = new AbortController();
        activeRequest = controller;
        if (window.kidsMapCancelCatalogMapTransition) window.kidsMapCancelCatalogMapTransition();
        showResultsLoading();

        fetch(url.href, {
          headers: { "X-Requested-With": "XMLHttpRequest" },
          signal: controller.signal,
        })
          .then(function (response) {
            if (!response.ok) throw new Error("Filter request failed");
            return response.text();
          })
          .then(function (html) {
            if (requestId !== requestSequence || controller.signal.aborted) return;
            const nextDocument = new DOMParser().parseFromString(html, "text/html");
            replaceCatalogFragment(nextDocument, scrollTop, url);
          })
          .catch(function (error) {
            if (error.name === "AbortError" || requestId !== requestSequence) return;
            window.location.href = url.href;
          })
          .finally(function () {
            if (requestId === requestSequence) activeRequest = null;
          });

        return true;
      }

      function triggerSubmit() {
        if (filtersForm && !mobileMedia.matches) {
          if (!submitFiltersAjax()) {
            filtersForm.requestSubmit ? filtersForm.requestSubmit() : filtersForm.submit();
          }
        }
      }

      function initCustomSortDropdown() {
        document.querySelectorAll("[data-catalog-sort-wrap]").forEach(function (wrap) {
          if (wrap.dataset.sortInit === "true") return;
          wrap.dataset.sortInit = "true";

          const trigger = wrap.querySelector("[data-sort-trigger]");
          const menu = wrap.querySelector("[data-sort-menu]");
          const label = wrap.querySelector("[data-sort-label]");
          const select = wrap.querySelector("select[name='sort']");
          const options = wrap.querySelectorAll("[data-sort-value]");
          if (!trigger || !menu || !select) return;

          function toggleSortMenu(open) {
            const shouldOpen = typeof open === "boolean" ? open : !wrap.classList.contains("is-open");
            wrap.classList.toggle("is-open", shouldOpen);
            trigger.setAttribute("aria-expanded", shouldOpen ? "true" : "false");
          }

          trigger.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            toggleSortMenu();
          });

          options.forEach(function (opt) {
            opt.addEventListener("click", function (e) {
              e.preventDefault();
              e.stopPropagation();
              const val = opt.getAttribute("data-sort-value");
              const textNode = opt.querySelector(".km-sort-option-text");
              const text = textNode ? textNode.textContent.trim() : opt.textContent.trim();

              label.textContent = text;
              options.forEach(function (o) {
                const isSel = o === opt;
                o.classList.toggle("is-selected", isSel);
                o.setAttribute("aria-selected", isSel ? "true" : "false");
              });

              select.value = val;
              toggleSortMenu(false);
              select.dispatchEvent(new Event("change", { bubbles: true }));
            });
          });

          document.addEventListener("click", function (e) {
            if (wrap.classList.contains("is-open") && !wrap.contains(e.target)) {
              toggleSortMenu(false);
            }
          });

          wrap.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && wrap.classList.contains("is-open")) {
              e.preventDefault();
              toggleSortMenu(false);
              trigger.focus();
            }
          });
        });
      }

      function bindDynamicCatalogControls() {
        document.querySelectorAll("[data-sort-submit]").forEach(function (select) {
          if (select.dataset.ajaxBound === "true") return;
          select.dataset.ajaxBound = "true";
          select.addEventListener("change", function () {
            if (filtersForm && !submitFiltersAjax()) {
              filtersForm.requestSubmit ? filtersForm.requestSubmit() : filtersForm.submit();
            }
          });
        });

        initCustomSortDropdown();
        if (window.kidsMapInitCustomSelects) {
          window.kidsMapInitCustomSelects(document);
        }
      }

      if (filtersForm) {
        filtersForm.addEventListener("submit", function (event) {
          event.preventDefault();
          if (!submitFiltersAjax()) {
            window.location.assign(buildFiltersUrl().href);
          }
        });
        // Desktop: every filter applies as soon as it changes (no "Apply"
        // step); the phone drawer keeps its explicit button.
        let liveFilterTimer = null;
        function syncLiveFilterMode() {
          filtersForm.classList.toggle("is-live-filters", !mobileMedia.matches);
        }
        syncLiveFilterMode();
        mobileMedia.addEventListener("change", syncLiveFilterMode);
        filtersForm.addEventListener("change", function (event) {
          if (mobileMedia.matches) return;
          if (event.target && event.target.name === "q") return;
          window.clearTimeout(liveFilterTimer);
          liveFilterTimer = window.setTimeout(triggerSubmit, 220);
        });
      }

      const heroSearchForm = document.querySelector(".catalog-hero-search");
      if (heroSearchForm) {
        heroSearchForm.addEventListener("submit", function (event) {
          if (mobileMedia.matches || !filtersForm) return;
          const heroQuery = heroSearchForm.querySelector('[name="q"]');
          const filtersQuery = document.querySelector('.top-search-field[name="q"][form="filters-form"]');
          if (heroQuery && filtersQuery) {
            filtersQuery.value = heroQuery.value;
          }
          if (submitFiltersAjax(buildFormUrl(heroSearchForm))) {
            event.preventDefault();
          }
        });
      }

      function syncSearchClearButton(input) {
        if (!input || !input.id) return;
        const button = document.querySelector('[data-search-clear][data-search-target="' + input.id + '"]');
        if (button) {
          button.hidden = !input.value;
        }
      }

      document.querySelectorAll("[data-search-input]").forEach(syncSearchClearButton);

      document.addEventListener("input", function (event) {
        if (event.target.matches("[data-search-input]")) {
          syncSearchClearButton(event.target);
        }
      });

      document.addEventListener("click", function (event) {
        const button = event.target.closest("[data-search-clear]");
        if (!button) return;

        const input = document.getElementById(button.dataset.searchTarget);
        if (!input) return;

        input.value = "";
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.focus();

        const form = input.form || button.closest("form");
        if (form) {
          if (form.classList.contains("mobile-catalog-search")) {
            window.location.href = buildFormUrl(form).href;
            return;
          }
          form.requestSubmit ? form.requestSubmit() : form.submit();
        }
      });

      function initLocationTreeSelect() {
        const container = document.querySelector('[data-tree-select="district"]');
        if (!container) return;
        const trigger = container.querySelector('.km-tree-trigger');
        const triggerText = container.querySelector('.km-tree-trigger-text');
        const dropdown = container.querySelector('.km-tree-dropdown');
        const targetSelect = document.querySelector('select[name="district"]');
        if (!trigger || !dropdown || !targetSelect) return;

        const currentLang = document.documentElement.lang || 'az';

        function getBütünBakıRayonlarıLabel() {
          if (currentLang === 'az') return 'Bütün Bakı rayonları';
          if (currentLang === 'en') return 'All Baku districts';
          return 'Все районы Баку';
        }

        function cleanDistrictLabel(label) {
          if (label && label.includes(':')) {
            return label.split(':')[1].trim();
          }
          return label;
        }

        function getOptions() {
          return Array.from(targetSelect.options).map(function(opt) {
            const label = opt.dataset.labelCurrent || opt.textContent.trim();
            const labelWithCount = opt.textContent.trim();
            return {
              value: opt.value,
              label: label,
              labelWithCount: labelWithCount,
              count: opt.value ? parseInt(labelWithCount.split('—')[1] || '0') : null
            };
          });
        }

        function createNodeRow(value, label, labelWithCount, hasChildren, isChild, isBakuAll, isLastChild) {
          const row = document.createElement('div');
          row.className = 'km-tree-row';
          row.setAttribute('role', 'treeitem');
          row.setAttribute('tabindex', '-1');
          row.dataset.value = value;

          if (isChild) {
            row.classList.add('km-tree-row--child');
            if (isBakuAll) {
              row.classList.add('km-tree-row--baku-all');
            }
            if (isLastChild) {
              row.classList.add('km-tree-row--last-child');
            }
          }

          let isSelected = false;
          if (value === 'baku') {
            if (targetSelect.value === 'baku' && isBakuAll) {
              isSelected = true;
            }
          } else {
            if (targetSelect.value === value) {
              isSelected = true;
            }
          }

          if (isSelected) {
            row.classList.add('is-selected');
            row.setAttribute('aria-selected', 'true');
          } else {
            row.setAttribute('aria-selected', 'false');
          }

          if (hasChildren) {
            const toggle = document.createElement('button');
            toggle.type = 'button';
            toggle.className = 'km-tree-chevron';
            toggle.setAttribute('aria-label', 'Toggle');
            toggle.setAttribute('tabindex', '-1');
            toggle.innerHTML = `
              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" class="km-tree-chevron-icon">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            `;
            row.appendChild(toggle);
          } else if (!isChild) {
            const spacer = document.createElement('div');
            spacer.className = 'km-tree-spacer';
            row.appendChild(spacer);
          }

          if (isChild) {
            const branch = document.createElement('div');
            branch.className = 'km-tree-branch';
            row.appendChild(branch);
          }

          const labelSpan = document.createElement('span');
          labelSpan.className = 'km-tree-label';

          const text = label;
          const countPart = labelWithCount ? (labelWithCount.split('—')[1] || '').trim() : '';
          labelSpan.innerHTML = text + (countPart ? ` <span class="km-tree-count">— ${countPart}</span>` : '');
          row.appendChild(labelSpan);

          row.addEventListener('click', function(e) {
            if (hasChildren) {
              toggleNode(row);
            } else {
              selectValue(value);
            }
          });

          return row;
        }

        function toggleNode(row) {
          const parentNode = row.closest('.km-tree-node');
          if (!parentNode) return;
          const children = parentNode.querySelector('.km-tree-children');
          if (!children) return;

          const isExpanded = row.getAttribute('aria-expanded') === 'true';
          row.setAttribute('aria-expanded', isExpanded ? 'false' : 'true');
          children.hidden = isExpanded;
        }

        function selectValue(value) {
          targetSelect.value = value;
          targetSelect.dispatchEvent(new Event('change', { bubbles: true }));
          closeDropdown();
        }

        function buildTreeHTML() {
          dropdown.innerHTML = '';
          const options = getOptions();

          const bakuOption = options.find(o => o.value === 'baku');
          const bakuDistricts = options.filter(o => o.value.startsWith('baku_'));
          const otherRegions = options.filter(o => o.value && o.value !== 'baku' && !o.value.startsWith('baku_'));

          if (bakuOption) {
            const bakuNode = document.createElement('div');
            bakuNode.className = 'km-tree-node km-tree-parent';

            const hasChildren = bakuDistricts.length > 0;
            const bakuRow = createNodeRow(bakuOption.value, bakuOption.label, bakuOption.labelWithCount, hasChildren);
            bakuNode.appendChild(bakuRow);

            if (hasChildren) {
              const childrenContainer = document.createElement('div');
              childrenContainer.className = 'km-tree-children';
              childrenContainer.setAttribute('role', 'group');

              const isBakuSelected = targetSelect.value === 'baku' || targetSelect.value.startsWith('baku_');
              bakuRow.setAttribute('aria-expanded', isBakuSelected ? 'true' : 'false');
              childrenContainer.hidden = !isBakuSelected;

              const bakuCountPart = bakuOption.labelWithCount.split('—')[1] || '';
              const allBakuLabel = getBütünBakıRayonlarıLabel() + (bakuCountPart ? ' — ' + bakuCountPart : '');
              const allBakuRow = createNodeRow('baku', getBütünBakıRayonlarıLabel(), allBakuLabel, false, true, true);
              childrenContainer.appendChild(allBakuRow);

              bakuDistricts.forEach((dist, idx) => {
                const isLast = idx === bakuDistricts.length - 1;
                const distRow = createNodeRow(dist.value, cleanDistrictLabel(dist.label), cleanDistrictLabel(dist.labelWithCount), false, true, false, isLast);
                childrenContainer.appendChild(distRow);
              });

              bakuNode.appendChild(childrenContainer);
            }
            dropdown.appendChild(bakuNode);
          }

          otherRegions.forEach(reg => {
            const regRow = createNodeRow(reg.value, reg.label, reg.labelWithCount, false);
            dropdown.appendChild(regRow);
          });
        }

        function toggleDropdown() {
          const isHidden = dropdown.hidden;
          if (isHidden) {
            openDropdown();
          } else {
            closeDropdown();
          }
        }

        function openDropdown() {
          dropdown.hidden = false;
          trigger.setAttribute('aria-expanded', 'true');
          buildTreeHTML();

          const firstItem = dropdown.querySelector('.km-tree-row');
          if (firstItem) {
            focusItem(firstItem);
          }
        }

        function closeDropdown() {
          dropdown.hidden = true;
          trigger.setAttribute('aria-expanded', 'false');
          trigger.focus();
        }

        function getVisibleItems() {
          const items = [];
          const rows = Array.from(dropdown.querySelectorAll('.km-tree-row'));
          rows.forEach(row => {
            const parentChildren = row.closest('.km-tree-children');
            if (!parentChildren || !parentChildren.hidden) {
              items.push(row);
            }
          });
          return items;
        }

        function focusItem(item) {
          if (!item) return;
          const allRows = dropdown.querySelectorAll('.km-tree-row');
          allRows.forEach(row => {
            row.setAttribute('tabindex', '-1');
          });
          item.setAttribute('tabindex', '0');
          item.focus();
        }

        dropdown.addEventListener('keydown', function(e) {
          const active = document.activeElement;
          if (!active || !active.classList.contains('km-tree-row')) return;

          const visibleItems = getVisibleItems();
          const index = visibleItems.indexOf(active);

          switch (e.key) {
            case 'ArrowDown':
              e.preventDefault();
              if (index < visibleItems.length - 1) {
                focusItem(visibleItems[index + 1]);
              }
              break;
            case 'ArrowUp':
              e.preventDefault();
              if (index > 0) {
                focusItem(visibleItems[index - 1]);
              }
              break;
            case 'ArrowRight':
              e.preventDefault();
              if (active.querySelector('.km-tree-chevron')) {
                const isExpanded = active.getAttribute('aria-expanded') === 'true';
                if (!isExpanded) {
                  toggleNode(active);
                } else {
                  if (index < visibleItems.length - 1) {
                    focusItem(visibleItems[index + 1]);
                  }
                }
              }
              break;
            case 'ArrowLeft':
              e.preventDefault();
              if (active.querySelector('.km-tree-chevron')) {
                const isExpanded = active.getAttribute('aria-expanded') === 'true';
                if (isExpanded) {
                  toggleNode(active);
                }
              } else if (active.classList.contains('km-tree-row--child')) {
                const parentRow = dropdown.querySelector('.km-tree-node > .km-tree-row');
                if (parentRow) {
                  focusItem(parentRow);
                }
              }
              break;
            case 'Enter':
            case ' ':
              e.preventDefault();
              active.click();
              break;
            case 'Escape':
              e.preventDefault();
              closeDropdown();
              break;
            case 'Home':
              e.preventDefault();
              if (visibleItems.length > 0) {
                focusItem(visibleItems[0]);
              }
              break;
            case 'End':
              e.preventDefault();
              if (visibleItems.length > 0) {
                focusItem(visibleItems[visibleItems.length - 1]);
              }
              break;
          }
        });

        trigger.addEventListener('click', function(e) {
          e.stopPropagation();
          toggleDropdown();
        });

        trigger.addEventListener('keydown', function(e) {
          if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            openDropdown();
          }
        });

        document.addEventListener('click', function(e) {
          if (!container.contains(e.target)) {
            dropdown.hidden = true;
            trigger.setAttribute('aria-expanded', 'false');
          }
        });

        function updateTriggerLabel() {
          const selectedVal = targetSelect.value;
          const options = getOptions();
          const selectedOpt = options.find(o => o.value === selectedVal);
          if (selectedOpt && selectedVal !== '') {
            if (selectedVal.startsWith('baku_')) {
              const bakuOpt = options.find(o => o.value === 'baku');
              const bakuLabel = bakuOpt ? bakuOpt.label : 'Bakı';
              triggerText.textContent = `${bakuLabel} · ${cleanDistrictLabel(selectedOpt.label)}`;
            } else {
              triggerText.textContent = selectedOpt.label;
            }
            container.classList.add('is-active');
          } else {
            let defaultLabel = 'Region / rayon';
            if (currentLang === 'az') defaultLabel = 'Region / rayon';
            else if (currentLang === 'en') defaultLabel = 'Region / district';
            else defaultLabel = 'Регион / район';
            triggerText.textContent = defaultLabel;
            container.classList.remove('is-active');
          }
        }

        targetSelect.addEventListener('change', updateTriggerLabel);
        updateTriggerLabel();
      }

      initLocationTreeSelect();

      bindDynamicCatalogControls();

      document.querySelectorAll("[data-category-overflow]").forEach(function(section) {
        const extras = Array.from(section.querySelectorAll(".is-category-extra"));
        const toggle = section.querySelector("[data-category-overflow-toggle]");
        if (!extras.length || !toggle) return;

        let expanded = extras.some(function(item) {
          return item.classList.contains("is-active");
        });
        const label = toggle.querySelector("[data-category-overflow-label]");

        function renderCategoryOverflow() {
          extras.forEach(function(item) {
            item.hidden = !expanded;
          });
          toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
          toggle.classList.toggle("is-expanded", expanded);
          if (label) {
            label.textContent = expanded ? toggle.dataset.lessLabel : toggle.dataset.moreLabel;
          }
        }

        toggle.addEventListener("click", function() {
          expanded = !expanded;
          renderCategoryOverflow();
        });
        renderCategoryOverflow();
      });

      document.querySelectorAll(".event-type-filter input[type='radio']").forEach(function(radio) {
        radio.addEventListener("change", triggerSubmit);
      });

      document.querySelectorAll(".filter-select:not([data-sort-submit])").forEach(function(select) {
        select.addEventListener("change", triggerSubmit);
      });

      document.querySelectorAll("[data-age-from][data-age-to]").forEach(function(btn) {
        btn.addEventListener("click", triggerSubmit);
      });
    })();
    /* ── Card contact toggle ── */
    (function () {
      document.addEventListener("click", function (e) {
        var btn = e.target.closest("[data-contact-toggle]");
        if (!btn) return;
        var stack = btn.closest(".card-action-stack");
        if (!stack) return;
        var drawer = stack.querySelector("[data-contact-drawer]");
        if (!drawer) return;
        var open = drawer.hidden;
        drawer.hidden = !open;
        btn.setAttribute("aria-expanded", open ? "true" : "false");
      });
      document.addEventListener("keydown", function (e) {
        if (e.key !== "Escape") return;
        document.querySelectorAll("[data-contact-toggle][aria-expanded='true']").forEach(function (btn) {
          const stack = btn.closest(".card-action-stack");
          const drawer = stack && stack.querySelector("[data-contact-drawer]");
          if (drawer) drawer.hidden = true;
          btn.setAttribute("aria-expanded", "false");
          btn.focus();
        });
      });
    })();

      (function () {
        const heroInput = document.getElementById("catalog-hero-search-input");
        const heroForm = document.getElementById("catalog-hero-search-form");
        document.querySelectorAll("[data-search-preset]").forEach(function (btn) {
          btn.addEventListener("click", function () {
            if (heroInput) {
              heroInput.value = btn.dataset.searchPreset;
              heroInput.dispatchEvent(new Event("input", { bubbles: true }));
              if (heroForm) {
                if (window.matchMedia("(max-width: 760px)").matches) {
                  heroForm.submit();
                } else {
                  const filtersQ = document.getElementById("filters-form-q");
                  if (filtersQ) filtersQ.value = heroInput.value;
                  heroForm.requestSubmit ? heroForm.requestSubmit() : heroForm.submit();
                }
              }
            }
          });
        });
      })();


      /* ── Age & Price Presets Handler ── */
      (function () {
        function syncAgePresets() {
          const fromInput = document.querySelector('.filter-age-range [data-range-from-input]');
          const toInput = document.querySelector('.filter-age-range [data-range-to-input]');
          if (!fromInput || !toInput) return;

          const currentFrom = fromInput.value;
          const currentTo = toInput.value;

          document.querySelectorAll('.age-preset-chip').forEach(function (chip) {
            const pFrom = chip.dataset.agePresetFrom;
            const pTo = chip.dataset.agePresetTo;
            const isMatch = (currentFrom === pFrom && currentTo === pTo) ||
                            (!currentFrom && !currentTo && pFrom === '0' && pTo === '18') ||
                            (currentFrom === '0' && currentTo === '18' && pFrom === '0' && pTo === '18');
            chip.classList.toggle('is-active', isMatch);
          });
        }

        document.addEventListener('click', function (e) {
          const ageChip = e.target.closest('.age-preset-chip');
          if (ageChip) {
            const fromInput = document.querySelector('.filter-age-range [data-range-from-input]');
            const toInput = document.querySelector('.filter-age-range [data-range-to-input]');
            const fromRange = document.querySelector('.filter-age-range [data-range-from-range]');
            const toRange = document.querySelector('.filter-age-range [data-range-to-range]');
            if (!fromInput || !toInput || !fromRange || !toRange) return;

            const pFrom = ageChip.dataset.agePresetFrom || '0';
            const pTo = ageChip.dataset.agePresetTo || '18';

            fromInput.value = pFrom;
            toInput.value = pTo;
            fromRange.value = pFrom;
            toRange.value = pTo;
            fromInput.dispatchEvent(new Event('input', { bubbles: true }));
            toInput.dispatchEvent(new Event('input', { bubbles: true }));
            toInput.dispatchEvent(new Event('change', { bubbles: true }));
            syncAgePresets();
            return;
          }

        });
      })();
