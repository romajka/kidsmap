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
        } else if (e.key === "Escape") {
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
        } else if (e.key === "Escape") {
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

    /* ─── 2. Age Range Slider (matching catalog places) ─── */
    var rangeRoots = page.querySelectorAll("[data-range]");
    rangeRoots.forEach(function (root) {
      var min = Number(root.dataset.min || 0);
      var max = Number(root.dataset.max || 18);
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
        var lang = (document.documentElement.lang || "ru").toLowerCase();
        var suffix = lang === "az" ? "yaş" : (lang === "en" ? "years" : "лет");
        caption.textContent = a + "–" + b + " " + suffix;
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
        var header = form.querySelector(".owner-event-stepper, .km-owner-mobile-progress");
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

    // Format selection
    var formatSelect = form.querySelector("#id_consultation_format");
    var locationBlock = form.querySelector("[data-owner-location-block]");
    var formatCards = Array.from(form.querySelectorAll("[data-owner-format-card]"));
    function syncFormat() {
      if (!formatSelect) return;
      var value = formatSelect.value || "online";
      if (locationBlock) locationBlock.hidden = value === "online";
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
    var specChips = Array.from(form.querySelectorAll(".owner-specialist-chip"));
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

    if (clearAllSpecsBtn) {
      clearAllSpecsBtn.addEventListener("click", function () {
        specChips.forEach(function (chip) {
          var cb = chip.querySelector("input[type=checkbox]");
          if (cb) cb.checked = false;
        });
        syncSelectedSpecs();
        form.dispatchEvent(new Event("change",{bubbles:true}));
      });
    }

    specChips.forEach(function (chip) {
      var cb = chip.querySelector("input[type=checkbox]");
      if (cb) {
        cb.addEventListener("change", function () {
          chip.classList.toggle("is-checked", cb.checked);
          syncSelectedSpecs();
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

    ["az", "ru", "en"].forEach(function (lang) {
      var textarea = form.querySelector("#id_bio_" + lang);
      if (textarea) textarea.addEventListener("input", updateBioIndicators);
    });
    updateBioIndicators();

    // Photo preview
    var photoInput = form.querySelector("#id_photo");
    var photoPreview = form.querySelector("[data-owner-photo-preview]");
    var photoChoose=form.querySelector('[data-specialist-photo-choose]');
    if(photoChoose&&photoInput)photoChoose.addEventListener('click',function(){photoInput.click();});
    var widgetError=form.querySelector('.km-file-input-hidden [data-upload-error]'),visiblePhotoError=form.querySelector('[data-specialist-photo-error]');
    if(widgetError&&visiblePhotoError){new MutationObserver(function(){visiblePhotoError.textContent=widgetError.textContent;visiblePhotoError.hidden=widgetError.hidden;}).observe(widgetError,{attributes:true,childList:true,subtree:true});}
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
