(function () {
  const form = document.querySelector("[data-owner-wizard]");
  if (!form) return;

  const steps = Array.from(form.querySelectorAll("[data-owner-step]"));
  const tabs = Array.from(form.querySelectorAll("[data-owner-step-target]"));
  const progressCurrent = form.querySelector("[data-owner-progress-current]");
  const progressTitle = form.querySelector("[data-owner-progress-title]");
  const progressBar = form.querySelector("[data-owner-progress-bar]");
  const locationRequiredMessage = form.dataset.ownerLocationRequiredMessage || "";
  const stepLabel = form.dataset.stepLabel || "";
  const ofLabel = form.dataset.ofLabel || "/";
  const warningLabel = form.dataset.ownerStepWarningLabel || "!";
  const completeLabel = form.dataset.ownerStepCompleteLabel || "✓";
  const neutralLabel = form.dataset.ownerStepNeutralLabel || "";
  const unsavedChangesMessage = form.dataset.ownerUnsavedChangesMessage || "";
  const draftKey = form.dataset.ownerDraftKey || "";
  const draftStatus = form.querySelector("[data-owner-draft-status]");
  const draftRestoredMessage = form.dataset.ownerDraftRestoredMessage || "";
  const draftSavedMessage = form.dataset.ownerDraftSavedMessage || "";
  const draftOfflineMessage = form.dataset.ownerDraftOfflineMessage || "";
  const draftOnlineMessage = form.dataset.ownerDraftOnlineMessage || "";
  const draftFilesMessage = form.dataset.ownerDraftFilesMessage || "";
  const hasServerErrors = !!form.querySelector(".auth-field-error, .auth-errors");
  const leaveGuard = form.querySelector("[data-owner-leave-guard]");
  const leaveGuardSave = leaveGuard ? leaveGuard.querySelector("[data-owner-leave-save]") : null;
  const leaveGuardCancel = leaveGuard ? leaveGuard.querySelector("[data-owner-leave-cancel]") : null;
  const leaveGuardDiscard = leaveGuard ? leaveGuard.querySelector("[data-owner-leave-discard]") : null;
  let currentStep = 1;
  let allowNavigation = false;
  let pendingNavigationUrl = "";
  let leaveGuardLastFocus = null;
  let draftSaveTimer = null;
  let isRestoringDraft = false;
  let restoredStep = null;
  const requiresTypeChoice = form.dataset.ownerRequiresTypeChoice === "1";
  let listingTypeChosen = !requiresTypeChoice
    || form.dataset.ownerMode === "temporary"
    || form.dataset.ownerMode === "permanent"
    || hasServerErrors;

  function currentListingMode() {
    if (requiresTypeChoice && !listingTypeChosen) return "";
    const temporaryCheckbox = form.querySelector('[name="is_temporary"]');
    return temporaryCheckbox && temporaryCheckbox.checked ? "temporary" : "permanent";
  }

  function getDraftStorage() {
    if (!draftKey || typeof window === "undefined" || !window.localStorage) return null;
    try {
      const probeKey = "__owner_wizard_draft_probe__";
      window.localStorage.setItem(probeKey, "1");
      window.localStorage.removeItem(probeKey);
      return window.localStorage;
    } catch (error) {
      return null;
    }
  }

  const draftStorage = getDraftStorage();

  function showDraftStatus(message, mode) {
    if (!draftStatus || !message) return;
    draftStatus.textContent = message;
    draftStatus.hidden = false;
    draftStatus.classList.remove("is-restored", "is-saved", "is-offline", "is-saving");
    if (mode) {
      draftStatus.classList.add("is-" + mode);
    }
  }

  function serializeField(field) {
    if (!field || !field.name || field.disabled) return "";
    if (field.type === "file") {
      const files = Array.from(field.files || []).map(function (file) {
        return [file.name, file.size, file.lastModified].join(":");
      });
      return field.name + "::file::" + files.join("|");
    }
    if (field.type === "checkbox" || field.type === "radio") {
      return field.name + "::check::" + (field.checked ? "1" : "0");
    }
    return field.name + "::value::" + String(field.value || "");
  }

  function captureFormSnapshot() {
    return Array.from(form.elements || [])
      .filter(function (field) {
        return !!field.name && !field.disabled && field.type !== "submit" && field.type !== "button" && field.type !== "reset";
      })
      .map(serializeField)
      .sort()
      .join("\n");
  }

  const initialSnapshot = captureFormSnapshot();

  function hasUnsavedChanges() {
    return captureFormSnapshot() !== initialSnapshot;
  }

  function escapeSelectorValue(value) {
    if (typeof CSS !== "undefined" && typeof CSS.escape === "function") {
      return CSS.escape(String(value));
    }
    return String(value).replace(/["\\]/g, "\\$&");
  }

  function listRestorableFields() {
    return Array.from(form.elements || []).filter(function (field) {
      return !!field.name
        && field.name !== "csrfmiddlewaretoken"
        && !field.disabled
        && field.type !== "file"
        && field.type !== "submit"
        && field.type !== "button"
        && field.type !== "reset";
    });
  }

  function collectDraftState() {
    const detailsState = Array.from(form.querySelectorAll("details.owner-form-details")).map(function (details) {
      return !!details.open;
    });
    const fields = {};

    listRestorableFields().forEach(function (field) {
      if (field.type === "checkbox") {
        fields[field.name] = !!field.checked;
        return;
      }
      if (field.type === "radio") {
        if (field.checked) {
          fields[field.name] = field.value;
        }
        return;
      }
      fields[field.name] = field.value;
    });

    return {
      version: 1,
      step: currentStep,
      fields: fields,
      detailsOpen: detailsState,
      hasPendingFiles: Array.from(form.querySelectorAll('input[type="file"]')).some(function (field) {
        return !!(field.files && field.files.length);
      }),
      savedAt: Date.now(),
    };
  }

  function clearDraftStatus() {
    if (!draftStatus) return;
    draftStatus.hidden = true;
    draftStatus.textContent = "";
    draftStatus.classList.remove("is-restored", "is-saved", "is-offline", "is-saving");
  }

  function saveDraftNow() {
    if (!draftStorage || isRestoringDraft) return;
    try {
      if (!hasUnsavedChanges()) {
        draftStorage.removeItem(draftKey);
        clearDraftStatus();
        return;
      }
      draftStorage.setItem(draftKey, JSON.stringify(collectDraftState()));
      if (navigator.onLine) {
        showDraftStatus(draftSavedMessage, "saved");
      }
    } catch (error) {
      // Ignore storage quota or privacy-mode failures and keep the form usable.
    }
  }

  function scheduleDraftSave() {
    if (!draftStorage || isRestoringDraft) return;
    window.clearTimeout(draftSaveTimer);
    const lang = document.documentElement.lang || "ru";
    const savingText = lang === "az" ? "Yadda saxlanılır..." : (lang === "en" ? "Saving..." : "Сохранение...");
    showDraftStatus(savingText, "saving");
    draftSaveTimer = window.setTimeout(saveDraftNow, 250);
  }

  function restoreDraftState() {
    if (!draftStorage || hasServerErrors) return;
    let rawState = null;
    try {
      rawState = draftStorage.getItem(draftKey);
    } catch (error) {
      return;
    }
    if (!rawState) return;

    let state = null;
    try {
      state = JSON.parse(rawState);
    } catch (error) {
      draftStorage.removeItem(draftKey);
      return;
    }
    if (!state || !state.fields || typeof state.fields !== "object") return;

    isRestoringDraft = true;
    if (requiresTypeChoice && Object.prototype.hasOwnProperty.call(state.fields, "is_temporary")) {
      listingTypeChosen = true;
    }
    Object.keys(state.fields).forEach(function (name) {
      const field = getField(name);
      if (!field || field.disabled) return;
      if (field.type === "checkbox") {
        field.checked = !!state.fields[name];
        return;
      }
      if (field.type === "radio") {
        const radio = form.querySelector('[name="' + name + '"][value="' + escapeSelectorValue(state.fields[name]) + '"]');
        if (radio) radio.checked = true;
        return;
      }
      field.value = state.fields[name];
    });

    syncListingMode();
    syncTemporaryRequiredState();
    syncOptionalDetailsState();
    syncLocationCascading();
    syncLanguagePanels();

    if (Array.isArray(state.detailsOpen)) {
      Array.from(form.querySelectorAll("details.owner-form-details")).forEach(function (details, index) {
        details.open = !!state.detailsOpen[index] || details.open;
      });
    }

    updateCompletion();
    updateFinalSummary();
    restoredStep = Number(state.step || 1);
    updateWizard(restoredStep);
    isRestoringDraft = false;

    const restoredMessage = state.hasPendingFiles
      ? [draftRestoredMessage, draftFilesMessage].filter(Boolean).join(" ")
      : draftRestoredMessage;
    showDraftStatus(restoredMessage, "restored");
  }

  function hasFieldValue(field) {
    if (!field || field.disabled) return false;
    if (field.type === "checkbox" || field.type === "radio") {
      return !!field.checked;
    }
    if (field.type === "file") {
      return getSelectedFiles(field).length > 0;
    }
    return !!String(field.value || "").trim();
  }

  function getSelectedFiles(input) {
    if (!input) return [];
    if (input.multiple && input._accumulatedFiles) {
      return Array.from(input._accumulatedFiles.files || []);
    }
    return Array.from(input.files || []);
  }

  function parseList(value) {
    return String(value || "")
      .split(",")
      .map(function (item) { return item.trim(); })
      .filter(Boolean);
  }

  function parseGroups(value) {
    return String(value || "")
      .split(",")
      .map(function (item) {
        return item
          .split("|")
          .map(function (name) { return name.trim(); })
          .filter(Boolean);
      })
      .filter(function (group) { return group.length; });
  }

  function getField(name) {
    return form.querySelector('[name="' + name + '"]');
  }

  function getFieldLabel(name) {
    if (name === "structured_schedule") {
      const lang = document.documentElement.lang || "ru";
      return lang === "az" ? "İş qrafiki" : (lang === "en" ? "Opening hours" : "Расписание работы");
    }
    const field = getField(name);
    if (!field) return "";
    const wrapper = field.closest(".owner-form-field, .owner-form-toggle-field, .owner-form-file-field");
    const label = wrapper ? wrapper.querySelector(".owner-form-label") : null;
    if (!label) return name;
    return label.textContent.replace(/\*/g, "").replace(/\s+/g, " ").trim();
  }

  function isPhotoFieldFilled(field) {
    if (!field) return false;
    if (getSelectedFiles(field).length) return true;
    const uploader = field.closest("[data-file-uploader]");
    if (!uploader) return false;
    const clearCheckbox = uploader.querySelector(".owner-image-clear-checkbox");
    const hasCurrentPreview = !!uploader.querySelector(".owner-file-uploader-current-preview");
    return hasCurrentPreview && !(clearCheckbox && clearCheckbox.checked);
  }

  function isFieldFilledByName(name) {
    const field = getField(name);
    if (!field) return null;
    if (name === "structured_schedule") {
      return isStructuredScheduleFilled(field);
    }
    if (name === "photo") {
      return isPhotoFieldFilled(field);
    }
    if (name === "gallery_images") {
      return getSelectedFiles(field).length > 0;
    }
    return hasFieldValue(field);
  }

  function isStructuredScheduleFilled(field) {
    let days = [];
    try {
      const parsed = JSON.parse(field.value || "[]");
      days = Array.isArray(parsed) ? parsed : (parsed && Array.isArray(parsed.days) ? parsed.days : []);
    } catch (error) {
      return false;
    }
    return days.some(function (day) {
      if (!day || day.is_closed) return false;
      if (day.is_24_hours) return true;
      return Array.isArray(day.intervals) && day.intervals.some(function (interval) {
        return String(interval.start || "").trim() && String(interval.end || "").trim();
      });
    });
  }

  function evaluateFields(names) {
    let total = 0;
    let filled = 0;
    const missing = [];

    names.forEach(function (name) {
      const state = isFieldFilledByName(name);
      if (state === null) return;
      total += 1;
      if (state) {
        filled += 1;
      } else {
        missing.push(getFieldLabel(name));
      }
    });

    return { total: total, filled: filled, missing: missing };
  }

  function evaluateGroups(groups, labels) {
    let total = 0;
    let filled = 0;
    const missing = [];

    groups.forEach(function (group) {
      const states = group
        .map(function (name) { return { name: name, state: isFieldFilledByName(name) }; })
        .filter(function (item) { return item.state !== null; });
      if (!states.length) return;
      total += 1;
      if (states.some(function (item) { return item.state; })) {
        filled += 1;
      } else {
        const key = group.join("|");
        missing.push(labels[key] || states.map(function (item) { return getFieldLabel(item.name); }).join(" / "));
      }
    });

    return { total: total, filled: filled, missing: missing };
  }

  function buildTip(prefix, suffix, missing, fallbackText) {
    if (!missing.length) return fallbackText;
    return [prefix, missing[0], suffix].filter(Boolean).join(" ").replace(/\s+\./g, ".").trim();
  }

  function syncOptionalDetailsState(scope) {
    const root = scope || form;
    root.querySelectorAll("details.owner-form-details").forEach(function (details) {
      if (details.hidden) return;
      const hasErrors = !!details.querySelector(".auth-field-error, .auth-errors");
      const hasValues = Array.from(details.querySelectorAll("input, select, textarea")).some(hasFieldValue);
      details.open = hasErrors || hasValues || details.hasAttribute("data-owner-force-open");
    });
  }

  function syncListingMode() {
    const mode = currentListingMode();
    const waitingForType = requiresTypeChoice && !listingTypeChosen;
    form.dataset.ownerMode = mode;
    form.classList.toggle("is-awaiting-listing-type", waitingForType);

    if (form.dataset.ownerPermanentRequiredFields || form.dataset.ownerTemporaryRequiredFields) {
      form.dataset.ownerRequiredFields = waitingForType
        ? ""
        : mode === "temporary"
          ? (form.dataset.ownerTemporaryRequiredFields || form.dataset.ownerRequiredFields || "")
          : (form.dataset.ownerPermanentRequiredFields || form.dataset.ownerRequiredFields || "");
    }
    if (form.dataset.ownerPermanentRequiredGroups || form.dataset.ownerTemporaryRequiredGroups) {
      form.dataset.ownerRequiredGroups = waitingForType
        ? ""
        : mode === "temporary"
          ? (form.dataset.ownerTemporaryRequiredGroups || form.dataset.ownerRequiredGroups || "")
          : (form.dataset.ownerPermanentRequiredGroups || form.dataset.ownerRequiredGroups || "");
    }

    steps.forEach(function (step) {
      const fieldKey = mode === "temporary" ? "ownerStepTemporaryRequiredFields" : "ownerStepPermanentRequiredFields";
      const groupKey = mode === "temporary" ? "ownerStepTemporaryRequiredGroups" : "ownerStepPermanentRequiredGroups";
      if (waitingForType) {
        step.dataset.ownerStepRequiredFields = "";
        step.dataset.ownerStepRequiredGroups = "";
      } else if (step.dataset[fieldKey] !== undefined) {
        step.dataset.ownerStepRequiredFields = step.dataset[fieldKey] || "";
      }
      if (!waitingForType && step.dataset[groupKey] !== undefined) {
        step.dataset.ownerStepRequiredGroups = step.dataset[groupKey] || "";
      }
    });

    const wizardHead = form.querySelector(".owner-wizard-head");
    const wizardStage = form.querySelector("[data-owner-stage]");
    if (wizardHead) wizardHead.hidden = waitingForType;
    if (wizardStage) wizardStage.hidden = waitingForType;

    form.querySelectorAll("[data-owner-listing-type]").forEach(function (card) {
      const active = card.dataset.ownerListingType === mode;
      card.classList.toggle("is-active", active);
      card.setAttribute("aria-pressed", active ? "true" : "false");
    });

    form.querySelectorAll("[data-owner-mode-panel]").forEach(function (panel) {
      const visible = panel.dataset.ownerModePanel === mode;
      panel.hidden = !visible;
      panel.querySelectorAll("input, select, textarea, button").forEach(function (field) {
        if (field.name === "is_temporary") return;
        field.disabled = !visible;
      });
      if (!visible && panel.tagName === "DETAILS") {
        panel.open = false;
      }
    });
  }

  function syncTemporaryRequiredState() {
    const temporaryCheckbox = form.querySelector('[name="is_temporary"]');
    const startInput = form.querySelector('[name="temporary_start"]');
    const endInput = form.querySelector('[name="temporary_end"]');
    const marks = form.querySelectorAll(".owner-temp-required-mark");
    const tempPanel = form.querySelector("[data-temp-panel]");
    if (!temporaryCheckbox || !startInput || !endInput) return;

    const isTemporary = !!temporaryCheckbox.checked;
    [startInput, endInput].forEach(function (field) {
      field.required = isTemporary && !field.disabled;
      field.setAttribute("aria-required", isTemporary ? "true" : "false");
    });
    marks.forEach(function (mark) {
      mark.hidden = !isTemporary;
    });
    if (tempPanel) {
      tempPanel.hidden = !isTemporary && !startInput.value && !endInput.value && !startInput.validationMessage && !endInput.validationMessage;
    }
  }

  function activateLanguagePanel(root, language) {
    if (!root) return;
    root.querySelectorAll("[data-owner-lang-tab]").forEach(function (tab) {
      const active = tab.dataset.ownerLangTab === language;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
    root.querySelectorAll("[data-owner-lang-panel]").forEach(function (panel) {
      const active = panel.dataset.ownerLangPanel === language;
      panel.classList.toggle("is-active", active);
      panel.hidden = !active;
    });
  }

  function syncLanguagePanels() {
    form.querySelectorAll("[data-owner-lang-tabs]").forEach(function (tabsRoot) {
      const hasAz = !!tabsRoot.querySelector('[data-owner-lang-panel="az"]');
      let preferred = ["ru", "en", "az"].find(function (language) {
        const panel = tabsRoot.querySelector('[data-owner-lang-panel="' + language + '"]');
        if (!panel) return false;
        return !!panel.querySelector(".auth-field-error");
      });

      if (!preferred) {
        preferred = ["ru", "en"].find(function (language) {
          const panel = tabsRoot.querySelector('[data-owner-lang-panel="' + language + '"]');
          if (!panel) return false;
          return Array.from(panel.querySelectorAll("input, textarea")).some(hasFieldValue);
        });
      }

      if (!preferred) {
        preferred = hasAz ? "az" : "ru";
      }

      activateLanguagePanel(tabsRoot, preferred);
    });
  }

  function updateCompletion() {
    const completion = form.querySelector("[data-owner-completion]");
    if (!completion) return;

    const requiredFields = evaluateFields(parseList(form.dataset.ownerRequiredFields));
    const optionalFields = evaluateFields(parseList(form.dataset.ownerOptionalFields));
    const requiredGroups = evaluateGroups(parseGroups(form.dataset.ownerRequiredGroups), {
      "district|metro": form.dataset.ownerLocationGroupLabel || "Район или метро",
    });
    const optionalGroups = evaluateGroups(parseGroups(form.dataset.ownerOptionalGroups), {
      "lat|lng": form.dataset.ownerMapGroupLabel || "Точка на карте",
    });

    const requiredTotal = requiredFields.total + requiredGroups.total;
    const requiredFilled = requiredFields.filled + requiredGroups.filled;
    const requiredPercent = requiredTotal ? Math.round((requiredFilled / requiredTotal) * 100) : 0;
    const requiredMissing = requiredFields.missing.concat(requiredGroups.missing);

    const overallTotal = requiredTotal + optionalFields.total + optionalGroups.total;
    const overallFilled = requiredFilled + optionalFields.filled + optionalGroups.filled;
    const overallPercent = overallTotal ? Math.round((overallFilled / overallTotal) * 100) : 0;
    const overallMissing = optionalFields.missing.concat(optionalGroups.missing);

    const requiredPercentNode = completion.querySelector('[data-owner-completion-percent="required"]');
    const requiredCountNode = completion.querySelector('[data-owner-completion-count="required"]');
    const requiredBar = completion.querySelector('[data-owner-completion-bar="required"]');
    const requiredTip = completion.querySelector('[data-owner-completion-tip="required"]');
    const nextStepBlock = completion.querySelector('[data-owner-next-step-block]');
    const overallPercentNode = completion.querySelector('[data-owner-completion-percent="overall"]');
    const overallCountNode = completion.querySelector('[data-owner-completion-count="overall"]');
    const overallBar = completion.querySelector('[data-owner-completion-bar="overall"]');
    const overallTip = completion.querySelector('[data-owner-completion-tip="overall"]');

    if (requiredPercentNode) requiredPercentNode.textContent = requiredPercent + "%";
    if (requiredCountNode) requiredCountNode.textContent = requiredFilled + "/" + requiredTotal;
    if (requiredBar) requiredBar.style.width = requiredPercent + "%";
    if (requiredTip) {
      requiredTip.textContent = buildTip(
        form.dataset.ownerRequiredTipPrefix || "",
        form.dataset.ownerRequiredTipSuffix || "",
        requiredMissing,
        form.dataset.ownerRequiredDoneText || ""
      );
    }
    if (nextStepBlock) {
      nextStepBlock.style.display = requiredMissing.length ? "flex" : "none";
    }

    if (overallPercentNode) overallPercentNode.textContent = overallPercent + "%";
    if (overallCountNode) overallCountNode.textContent = overallFilled + "/" + overallTotal;
    if (overallBar) overallBar.style.width = overallPercent + "%";
    if (overallTip) {
      overallTip.textContent = buildTip(
        form.dataset.ownerOverallTipPrefix || "",
        form.dataset.ownerOverallTipSuffix || "",
        overallMissing,
        form.dataset.ownerOverallDoneText || ""
      );
    }

    // Update SVG ring arcs (circumference of r=15.9 circle ≈ 99.9)
    var CIRC = 99.9;
    completion.querySelectorAll('[data-owner-completion-ring]').forEach(function(ring) {
      var kind = ring.getAttribute('data-owner-completion-ring');
      var pct = kind === 'required' ? requiredPercent : overallPercent;
      ring.setAttribute('stroke-dasharray', (CIRC * pct / 100).toFixed(1) + ' ' + CIRC);
    });
  }

  function updateTodoList() {
    const listEl = document.getElementById("km-verification-todo-list");
    const blockEl = document.getElementById("km-verification-todo-block");
    if (!listEl) return;

    listEl.innerHTML = "";
    const missingItems = [];
    const lang = document.documentElement.lang || "ru";
    const locationLabels = {
      region: lang === "az" ? "Region" : (lang === "en" ? "Region" : "Город / регион"),
      district: lang === "az" ? "Rayon" : (lang === "en" ? "District" : "Район"),
      metro: lang === "az" ? "Metro" : (lang === "en" ? "Metro" : "Метро"),
    };

    for (let i = 0; i < 4; i++) {
      const step = steps[i];
      if (!step) continue;

      const requiredList = parseList(step.dataset.ownerStepRequiredFields);
      requiredList.forEach(function (name) {
        if (!isFieldFilledByName(name)) {
          const field = getField(name);
          const wrapper = field ? field.closest(".owner-form-field") : null;
          const labelEl = wrapper ? wrapper.querySelector(".owner-form-label") : null;
          let labelText = labelEl ? labelEl.textContent.trim().replace(/\*$/, "").trim() : name;
          labelText = locationLabels[name] || labelText;
          if (!labelText) labelText = name;
          missingItems.push({ name: name, label: labelText, stepIndex: i + 1 });
        }
      });

      const requiredGroups = parseGroups(step.dataset.ownerStepRequiredGroups);
      requiredGroups.forEach(function (groupNames) {
        let isAnyFilled = false;
        groupNames.forEach(function (name) {
          if (isFieldFilledByName(name)) {
            isAnyFilled = true;
          }
        });
        if (!isAnyFilled) {
          const labelText = form.dataset.ownerLocationGroupLabel || (document.documentElement.lang === "az" ? "Rayon və ya metro" : (document.documentElement.lang === "en" ? "District or Metro" : "Район или метро"));
          missingItems.push({ name: groupNames.join("|"), label: labelText, stepIndex: i + 1 });
        }
      });
    }

    if (missingItems.length > 0) {
      if (blockEl) blockEl.style.display = "block";
      missingItems.forEach(function (item) {
        const li = document.createElement("li");
        li.className = "km-verification-todo-item";
        
        const link = document.createElement("a");
        link.href = "#";
        link.textContent = item.label;
        link.addEventListener("click", function (e) {
          e.preventDefault();
          updateWizard(item.stepIndex);
        });

        li.appendChild(link);
        listEl.appendChild(li);
      });
    } else {
      if (blockEl) blockEl.style.display = "none";
    }
  }

  function updateFinalSummary() {
    const photoSummary = form.querySelector("[data-owner-summary-photo]");
    const gallerySummary = form.querySelector("[data-owner-summary-gallery]");
    const noteSummary = form.querySelector("[data-owner-summary-note]");
    const photoField = getField("photo");
    const galleryField = getField("gallery_images");
    const noteField = getField("moderation_note");

    if (photoSummary) {
      if (photoField && photoField.files && photoField.files.length) {
        photoSummary.textContent = (form.dataset.ownerSummaryPhotoSelected || "") + " " + photoField.files[0].name;
      } else if (isPhotoFieldFilled(photoField)) {
        photoSummary.textContent = form.dataset.ownerSummaryPhotoReady || "";
      } else {
        photoSummary.textContent = form.dataset.ownerSummaryPhotoEmpty || "";
      }
    }

    if (gallerySummary) {
      const count = getSelectedFiles(galleryField).length;
      if (count === 1) {
        gallerySummary.textContent = form.dataset.ownerSummaryGalleryOne || "";
      } else if (count > 1) {
        gallerySummary.textContent = (form.dataset.ownerSummaryGalleryManyPrefix || "") + " " + count;
      } else {
        gallerySummary.textContent = form.dataset.ownerSummaryGalleryEmpty || "";
      }
    }

    if (noteSummary) {
      noteSummary.textContent = noteField && String(noteField.value || "").trim()
        ? (form.dataset.ownerSummaryNoteFilled || "Comment added")
        : (form.dataset.ownerSummaryNoteEmpty || "");
    }

    // Update Step 5 Card Preview
    const previewImgEl = document.getElementById("km-preview-image");
    const previewPlaceholderEl = document.getElementById("km-preview-image-placeholder");

    if (previewImgEl) {
      if (previewImgEl._tempUrl) {
        URL.revokeObjectURL(previewImgEl._tempUrl);
        previewImgEl._tempUrl = null;
      }
      const files = getSelectedFiles(photoField);
      if (files.length && files[0].type.startsWith("image/")) {
        const url = URL.createObjectURL(files[0]);
        previewImgEl._tempUrl = url;
        previewImgEl.src = url;
        previewImgEl.style.display = "block";
        if (previewPlaceholderEl) previewPlaceholderEl.style.display = "none";
      } else {
        const uploader = photoField ? photoField.closest("[data-file-uploader]") : null;
        const currentPreview = uploader ? uploader.querySelector(".owner-file-uploader-current-preview img") : null;
        if (currentPreview && currentPreview.src) {
          previewImgEl.src = currentPreview.src;
          previewImgEl.style.display = "block";
          if (previewPlaceholderEl) previewPlaceholderEl.style.display = "none";
        } else {
          previewImgEl.style.display = "none";
          if (previewPlaceholderEl) previewPlaceholderEl.style.display = "flex";
        }
      }
    }

    const catEl = document.getElementById("km-preview-cat");
    if (catEl) {
      const categorySelect = getField("category");
      const categoryText = categorySelect ? categorySelect.options[categorySelect.selectedIndex]?.text : "";
      catEl.textContent = categoryText || "-";
    }

    const titleEl = document.getElementById("km-preview-title");
    if (titleEl) {
      const lang = document.documentElement.lang || "ru";
      const nameField = getField("name_" + lang) || getField("name_az") || getField("name_ru") || getField("name_en");
      titleEl.textContent = (nameField ? nameField.value : "") || "-";
    }

    const ageEl = document.getElementById("km-preview-age");
    if (ageEl) {
      const ageFrom = getField("age_from")?.value;
      const ageTo = getField("age_to")?.value;
      if (ageFrom && ageTo) {
        const label = document.documentElement.lang === "az" ? "yaş" : (document.documentElement.lang === "en" ? "years" : "лет");
        ageEl.textContent = `${ageFrom}-${ageTo} ${label}`;
      } else if (ageFrom) {
        const label = document.documentElement.lang === "az" ? "yaşdan" : (document.documentElement.lang === "en" ? "years+" : "лет+");
        ageEl.textContent = `${ageFrom} ${label}`;
      } else {
        ageEl.textContent = "-";
      }
    }

    const priceEl = document.getElementById("km-preview-price");
    if (priceEl) {
      const priceFrom = getField("price_from")?.value;
      const priceTo = getField("price_to")?.value;
      if (priceFrom && priceTo) {
        priceEl.textContent = `${priceFrom}-${priceTo} AZN`;
      } else if (priceFrom) {
        priceEl.textContent = `${priceFrom} AZN`;
      } else {
        priceEl.textContent = "-";
      }
    }

    const locEl = document.getElementById("km-preview-loc-text");
    if (locEl) {
      const address = getField("address")?.value;
      locEl.textContent = address || "-";
    }

    const phoneContainer = document.getElementById("km-preview-phone");
    const phoneText = document.getElementById("km-preview-phone-text");
    if (phoneContainer && phoneText) {
      const phone = getField("phone1")?.value || getField("phone2")?.value;
      if (phone) {
        phoneText.textContent = phone;
        phoneContainer.style.display = "block";
      } else {
        phoneContainer.style.display = "none";
      }
    }

    // Verification badges
    const badgeCoords = document.getElementById("km-status-badge-coords");
    const badgePhotos = document.getElementById("km-status-badge-photos");
    const lang = document.documentElement.lang || "ru";

    if (badgeCoords) {
      const latVal = getField("lat")?.value;
      const lngVal = getField("lng")?.value;
      const addressVal = getField("address")?.value;

      badgeCoords.className = "km-verification-badge";
      if (latVal && lngVal && addressVal) {
        badgeCoords.classList.add("is-success");
        badgeCoords.textContent = lang === "az" ? "Doldurulub" : (lang === "en" ? "Filled" : "Заполнено");
      } else if (addressVal) {
        badgeCoords.classList.add("is-warning");
        badgeCoords.textContent = lang === "az" ? "Xəritədə tap" : (lang === "en" ? "Find on map" : "Найти на карте");
      } else if (latVal && lngVal) {
        badgeCoords.classList.add("is-warning");
        badgeCoords.textContent = lang === "az" ? "Ünvan yoxdur" : (lang === "en" ? "No address" : "Нужен адрес");
      } else {
        badgeCoords.classList.add("is-error");
        badgeCoords.textContent = lang === "az" ? "Boşdur" : (lang === "en" ? "Empty" : "Не заполнено");
      }
    }

    if (badgePhotos) {
      badgePhotos.className = "km-verification-badge";
      if (isPhotoFieldFilled(photoField)) {
        badgePhotos.classList.add("is-success");
        badgePhotos.textContent = lang === "az" ? "Əlavə edilib" : (lang === "en" ? "Added" : "Добавлено");
      } else {
        badgePhotos.classList.add("is-error");
        badgePhotos.textContent = lang === "az" ? "Əsas şəkil yoxdur" : (lang === "en" ? "No main photo" : "Нет главного фото");
      }
    }

    // Remaining fields checklist
    updateTodoList();
  }

  function syncLocationCascading() {
    const regionSelect = form.querySelector('[name="region"]');
    const districtSelect = form.querySelector('[name="district"]');
    const metroSelect = form.querySelector('[name="metro"]');
    if (!regionSelect) return;

    const isBaku = regionSelect.value === "baku";

    // Show/hide district
    const districtWrapper = districtSelect ? districtSelect.closest(".owner-form-field") : null;
    if (districtWrapper) {
      districtWrapper.style.display = isBaku ? "" : "none";
      if (districtSelect) {
        districtSelect.disabled = !isBaku;
        if (!isBaku) {
          districtSelect.value = "";
        }
      }
    }

    // Show/hide metro
    const metroWrapper = metroSelect ? metroSelect.closest(".owner-form-field") : null;
    if (metroWrapper) {
      metroWrapper.style.display = isBaku ? "" : "none";
      if (metroSelect) {
        metroSelect.disabled = !isBaku;
        if (!isBaku) {
          metroSelect.value = "";
        }
      }
    }

    // Dynamically adjust step 3's required groups
    const step3 = steps.find(s => s.dataset.ownerStep === "3");
    if (step3) {
      if (isBaku) {
        step3.dataset.ownerStepRequiredGroups = "district|metro";
        step3.dataset.ownerStepPermanentRequiredGroups = "district|metro";
        step3.dataset.ownerStepTemporaryRequiredGroups = "district|metro";
      } else {
        step3.dataset.ownerStepRequiredGroups = "";
        step3.dataset.ownerStepPermanentRequiredGroups = "";
        step3.dataset.ownerStepTemporaryRequiredGroups = "";
      }
    }

    // Also update form's top-level dataset properties so updateCompletion reads the correct values
    if (isBaku) {
      form.dataset.ownerRequiredGroups = "district|metro";
      form.dataset.ownerPermanentRequiredGroups = "district|metro";
      form.dataset.ownerTemporaryRequiredGroups = "district|metro";
    } else {
      form.dataset.ownerRequiredGroups = "";
      form.dataset.ownerPermanentRequiredGroups = "";
      form.dataset.ownerTemporaryRequiredGroups = "";
    }

    setLocationValidity();
  }

  function setLocationValidity() {
    const region = form.querySelector('[name="region"]');
    const district = form.querySelector('[name="district"]');
    const metro = form.querySelector('[name="metro"]');
    if (!region) return;

    if (!region.value) {
      region.setCustomValidity(locationRequiredMessage || "Выберите регион");
      if (district) district.setCustomValidity("");
      if (metro) metro.setCustomValidity("");
      return;
    }
    region.setCustomValidity("");

    if (region.value === "baku") {
      if ((district && district.value) || (metro && metro.value)) {
        if (district) district.setCustomValidity("");
        if (metro) metro.setCustomValidity("");
      } else {
        const msg = form.dataset.ownerBakuLocationRequiredMessage || "Для Баку выберите район или метро";
        if (district) district.setCustomValidity(msg);
        if (metro) metro.setCustomValidity(msg);
      }
    } else {
      if (district) district.setCustomValidity("");
      if (metro) metro.setCustomValidity("");
    }
  }

  function getStepState(step) {
    const requiredFields = evaluateFields(parseList(step.dataset.ownerStepRequiredFields));
    const requiredGroups = evaluateGroups(parseGroups(step.dataset.ownerStepRequiredGroups), {
      "district|metro": form.dataset.ownerLocationGroupLabel || "Район или метро",
    });
    const total = requiredFields.total + requiredGroups.total;
    const filled = requiredFields.filled + requiredGroups.filled;
    const hasErrors = !!step.querySelector(".auth-field-error, .auth-errors");
    const complete = total ? filled === total : true;
    const touched = step.dataset.ownerStepTouched === "true";
    const attempted = step.dataset.ownerStepAttempted === "true";
    const warning = !complete && (hasErrors || touched || attempted);

    return {
      total: total,
      filled: filled,
      complete: complete,
      hasErrors: hasErrors,
      touched: touched,
      attempted: attempted,
      warning: warning,
    };
  }

  function maxReachableStep() {
    let reachable = 1;
    for (let index = 0; index < steps.length; index += 1) {
      const step = steps[index];
      const state = getStepState(step);
      if (!state.complete) {
        return index + 1;
      }
      reachable = index + 2;
    }
    return Math.min(reachable, steps.length);
  }

  function alignStepperTrack() {
    const stepper = form.querySelector(".wz-stepper");
    const track = form.querySelector(".wz-stepper-track");
    const dots = Array.from(form.querySelectorAll(".wz-step .wz-dot"));
    if (!stepper || !track || dots.length < 2) return;

    const firstDot = dots[0];
    const lastDot = dots[dots.length - 1];

    const stepperRect = stepper.getBoundingClientRect();
    const firstRect = firstDot.getBoundingClientRect();
    const lastRect = lastDot.getBoundingClientRect();

    if (firstRect.width === 0 || lastRect.width === 0) {
      return;
    }

    const leftOffset = (firstRect.left + firstRect.width / 2) - stepperRect.left;
    const rightOffset = stepperRect.right - (lastRect.left + lastRect.width / 2);
    const verticalCenter = (firstRect.top + firstRect.height / 2) - stepperRect.top;

    track.style.left = leftOffset + "px";
    track.style.right = rightOffset + "px";
    track.style.top = verticalCenter + "px";
    track.style.transform = "translateY(-50%)";
  }

  function updateWizard(stepNumber) {
    const reachableStep = maxReachableStep();
    currentStep = Math.max(1, Math.min(stepNumber, steps.length));

    steps.forEach(function (step, index) {
      const stepIndex = index + 1;
      const isActive = stepIndex === currentStep;
      step.hidden = !isActive;
      step.classList.toggle("is-active", isActive);
    });

    tabs.forEach(function (tab) {
      const target = Number(tab.dataset.ownerStepTarget || "1");
      const step = steps[target - 1];
      const state = getStepState(step);
      const isUnlocked = target <= reachableStep || target === steps.length;
      const indicator = tab.querySelector("[data-owner-step-indicator]");

      tab.classList.toggle("is-active", target === currentStep);
      tab.classList.toggle("is-complete", state.complete);
      tab.classList.toggle("is-warning", state.warning);
      tab.classList.toggle("is-locked", !isUnlocked);
      tab.setAttribute("aria-current", target === currentStep ? "step" : "false");
      tab.setAttribute("aria-disabled", isUnlocked ? "false" : "true");
      tab.disabled = !isUnlocked;

      if (indicator) {
        var isWzDot = indicator.classList.contains('wz-dot');
        if (isWzDot) {
          indicator.textContent = state.complete ? '' : state.warning ? warningLabel : String(target);
        } else {
          indicator.textContent = state.complete ? completeLabel : state.warning ? warningLabel : String(target);
        }
        indicator.setAttribute("aria-label", state.complete ? completeLabel : state.warning ? warningLabel : neutralLabel);
      }
    });

    if (progressCurrent) {
      progressCurrent.textContent = ofLabel === "/"
        ? stepLabel + " " + currentStep + "/" + steps.length
        : stepLabel + " " + currentStep + " " + ofLabel + " " + steps.length;
    }
    if (progressTitle) {
      progressTitle.textContent = steps[currentStep - 1].dataset.ownerStepTitle || "";
    }
    if (progressBar) {
      const fillPercent = steps.length > 1 ? ((currentStep - 1) / (steps.length - 1) * 100).toFixed(2) : 0;
      progressBar.style.width = fillPercent + "%";
    }
    alignStepperTrack();
    if (currentStep === 3 && window.kidsMapRefreshOwnerMapPickers) {
      window.setTimeout(window.kidsMapRefreshOwnerMapPickers, 40);
    }
  }

  function openContainingDetails(element) {
    let parent = element ? element.parentElement : null;
    while (parent) {
      if (parent.tagName === "DETAILS") {
        parent.open = true;
      }
      parent = parent.parentElement;
    }
  }

  function getCustomValidationMessage(field) {
    const lang = document.documentElement.lang || "ru";
    
    // Check if it's the category field
    if (field.name === "category") {
      if (lang === "az") return "Zəhmət olmasa kateqoriya seçin";
      if (lang === "en") return "Please select a category";
      return "Пожалуйста, выберите категорию";
    }
    
    // Check if empty required field
    if (field.validity && field.validity.valueMissing) {
      if (lang === "az") return "Zəhmət olmasa bu sahəni doldurun";
      if (lang === "en") return "Please fill in this field";
      return "Пожалуйста, заполните это поле";
    }
    
    // Check if email error
    if (field.type === "email" && field.validity && field.validity.typeMismatch) {
      if (lang === "az") return "Zəhmət olmasa düzgün e-poçt ünvanı daxil edin";
      if (lang === "en") return "Please enter a valid email address";
      return "Пожалуйста, введите корректный адрес электронной почты";
    }

    // Default message
    return field.validationMessage || "Некорректное значение";
  }

  function showFieldError(field) {
    const wrapper = field.closest(".owner-form-field, .owner-form-toggle-field, .owner-form-file-field") || field.parentElement;
    if (!wrapper) return;
    
    if (field.name === "category") {
      const customPicker = wrapper.parentElement.querySelector(".km-taxonomy-picker");
      if (customPicker) {
        customPicker.classList.add("has-client-error");
        let errorMsg = customPicker.querySelector(".client-side-error");
        if (!errorMsg) {
          errorMsg = document.createElement("small");
          errorMsg.className = "auth-field-error client-side-error";
          customPicker.appendChild(errorMsg);
        }
        errorMsg.textContent = getCustomValidationMessage(field);
        errorMsg.style.display = "block";
        return;
      }
    }

    wrapper.classList.add("has-client-error");
    
    // Check if there is already a client error displayed
    let errorMsg = wrapper.querySelector(".client-side-error");
    if (!errorMsg) {
      errorMsg = document.createElement("small");
      errorMsg.className = "auth-field-error client-side-error";
      wrapper.appendChild(errorMsg);
    }
    errorMsg.textContent = getCustomValidationMessage(field);
    errorMsg.style.display = "block";
  }

  function clearFieldError(field) {
    const wrapper = field.closest(".owner-form-field, .owner-form-toggle-field, .owner-form-file-field") || field.parentElement;
    if (!wrapper) return;
    
    if (field.name === "category") {
      const customPicker = wrapper.parentElement.querySelector(".km-taxonomy-picker");
      if (customPicker) {
        customPicker.classList.remove("has-client-error");
        const errorMsg = customPicker.querySelector(".client-side-error");
        if (errorMsg) {
          errorMsg.style.display = "none";
          errorMsg.textContent = "";
        }
      }
    }

    wrapper.classList.remove("has-client-error");
    const errorMsg = wrapper.querySelector(".client-side-error");
    if (errorMsg) {
      errorMsg.style.display = "none";
      errorMsg.textContent = "";
    }
    
    // Also hide server-side errors if the field is now valid
    wrapper.querySelectorAll(".auth-field-error:not(.client-side-error)").forEach(function (srvErr) {
      srvErr.style.display = "none";
    });
  }

  function setScheduleClientError(show) {
    const editor = form.querySelector("[data-km-schedule-editor]");
    if (!editor) return;
    let error = editor.querySelector(".km-schedule-client-error");
    if (!show) {
      if (error) error.remove();
      editor.classList.remove("has-client-error");
      return;
    }
    if (!error) {
      error = document.createElement("small");
      error.className = "auth-field-error km-schedule-client-error";
      editor.appendChild(error);
    }
    const lang = document.documentElement.lang || "ru";
    error.textContent = lang === "az"
      ? "Məkanın nə vaxt işlədiyini seçin."
      : (lang === "en" ? "Select when this place is open." : "Выберите, когда место работает.");
    editor.classList.add("has-client-error");
  }

  function focusFirstProblem(step) {
    const invalidField = Array.from(step.querySelectorAll("input, select, textarea")).find(function (field) {
      return typeof field.checkValidity === "function" && !field.checkValidity();
    });
    const errorField = invalidField || step.querySelector(".auth-field-error, .auth-errors");
    const target = invalidField || (errorField && errorField.closest(".owner-form-field, .owner-form-toggle-field, .owner-form-file-field"));
    if (!target) return;
    openContainingDetails(target);
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    if (invalidField && typeof invalidField.focus === "function") {
      invalidField.focus({ preventScroll: true });
    }
  }

  function validateCurrentStep() {
    const activeStep = steps[currentStep - 1];
    if (!activeStep) return true;

    activeStep.dataset.ownerStepAttempted = "true";
    setLocationValidity();

    const fields = Array.from(activeStep.querySelectorAll("input, select, textarea")).filter(function (field) {
      return field.type !== "hidden" && !field.disabled;
    });

    let firstInvalid = null;
    
    // Clear previous client errors on this step
    fields.forEach(clearFieldError);

    for (const field of fields) {
      if (typeof field.checkValidity === "function" && !field.checkValidity()) {
        showFieldError(field);
        if (!firstInvalid) {
          firstInvalid = field;
        }
      }
    }

    if (firstInvalid) {
      focusFirstProblem(activeStep);
      return false;
    }

    const stepState = getStepState(activeStep);
    if (!stepState.complete) {
      if (
        parseList(activeStep.dataset.ownerStepRequiredFields).includes("structured_schedule")
        && !isFieldFilledByName("structured_schedule")
      ) {
        setScheduleClientError(true);
      }
      focusFirstProblem(activeStep);
      return false;
    }

    return true;
  }

  function firstErrorStep() {
    const stepIndex = steps.findIndex(function (step) {
      return !!step.querySelector(".auth-field-error, .auth-errors");
    });
    return stepIndex >= 0 ? stepIndex + 1 : 1;
  }

  function markStepTouched(field) {
    const step = field.closest("[data-owner-step]");
    if (step) {
      step.dataset.ownerStepTouched = "true";
    }
  }

  function formatFileSize(size) {
    const value = Number(size || 0);
    if (!value) return "0 KB";
    if (value >= 1024 * 1024) return (value / (1024 * 1024)).toFixed(1) + " MB";
    return Math.max(1, Math.round(value / 1024)) + " KB";
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderUploaderState(uploader) {
    const input = uploader.querySelector("[data-upload-input]");
    const meta = uploader.querySelector("[data-upload-meta]");
    const list = uploader.querySelector("[data-upload-list]");
    const countEl = uploader.querySelector("[data-upload-count]");
    const errorEl = uploader.querySelector("[data-upload-error]");
    if (!input || !meta) return;

    const emptyMessage = uploader.dataset.uploadEmpty || "";
    const summaryLabel = uploader.dataset.uploadSummary || "";
    const pendingMessage = uploader.dataset.uploadPending || "";
    const cropNote = uploader.dataset.uploadCropNote || "";
    const files = getSelectedFiles(input);
    const isSingleUploader = uploader.dataset.uploadMode === "single";
    const maxFiles = Number(uploader.dataset.uploadMaxFiles || (isSingleUploader ? 1 : 10));

    const hasCurrentPreview = !!uploader.querySelector(".owner-file-uploader-current-preview");
    const clearCheckbox = uploader.querySelector(".owner-image-clear-checkbox");
    const hasInitial = hasCurrentPreview && !(clearCheckbox && clearCheckbox.checked);
    if (countEl) {
      countEl.textContent = files.length + " / " + maxFiles;
      countEl.classList.toggle("is-full", files.length >= maxFiles);
    }
    if (errorEl && !uploader.dataset.uploadErrorActive) {
      errorEl.hidden = true;
      errorEl.textContent = "";
    }

    if (!files.length) {
      meta.textContent = emptyMessage;
      uploader.classList.remove("is-selected");
      if (list) {
        if (!hasInitial) {
          list.hidden = false;
          list.classList.add("is-empty");
          const lang = document.documentElement.lang || "ru";
          const emptyText = lang === "az" ? "Şəkillər əlavə olunmayıb" : (lang === "en" ? "No photos added yet" : "Фотографии не добавлены");
          list.innerHTML = '<div class="owner-file-uploader-empty-state">' +
            '<svg viewBox="0 0 24 24" fill="none" style="width:24px;height:24px;color:#a0aeb1;margin-bottom:4px;"><path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>' +
            '<span>' + emptyText + '</span>' +
          '</div>';
        } else {
          list.hidden = true;
          list.innerHTML = "";
          list.classList.remove("is-empty");
        }
        list.classList.remove("owner-file-uploader-list--single");
      }
      return;
    }
    if (list) {
      list.classList.remove("is-empty");
    }

    uploader.classList.add("is-selected");
    if (files.length === 1) {
      meta.textContent = [summaryLabel + " " + files[0].name + " (" + formatFileSize(files[0].size) + ").", pendingMessage].filter(Boolean).join(" ");
    } else {
      meta.textContent = [summaryLabel + " " + files.length + ".", pendingMessage].filter(Boolean).join(" ");
    }

    if (!list) return;
    list.classList.toggle("owner-file-uploader-list--single", isSingleUploader);

    if (list._previewUrls) {
      list._previewUrls.forEach(function (url) {
        URL.revokeObjectURL(url);
      });
    }
    list._previewUrls = [];

    list.hidden = false;
    if (isSingleUploader && files.length === 1) {
      const file = files[0];
      let previewHtml = "";
      if (file.type && file.type.indexOf("image/") === 0) {
        const url = URL.createObjectURL(file);
        list._previewUrls.push(url);
        previewHtml = '<img src="' + url + '" alt="" class="owner-file-uploader-square-preview" />';
      }
      list.innerHTML =
        '<div class="owner-file-uploader-preview-card" data-filename="' + escapeHtml(file.name) + '">' +
          previewHtml +
          '<div class="owner-file-uploader-preview-copy">' +
            '<strong class="owner-file-uploader-preview-name">' + escapeHtml(file.name) + '</strong>' +
            '<span class="owner-file-uploader-preview-meta">' + escapeHtml(formatFileSize(file.size)) + '</span>' +
            (cropNote ? '<span class="owner-file-uploader-preview-note">' + escapeHtml(cropNote) + '</span>' : '') +
          '</div>' +
          '<button type="button" class="owner-file-uploader-preview-remove" data-remove-file aria-label="Remove file">&times;</button>' +
        '</div>';
      return;
    }

    list.innerHTML = files.map(function (file) {
      let previewHtml = '';
      if (file.type && file.type.indexOf('image/') === 0) {
        const url = URL.createObjectURL(file);
        list._previewUrls.push(url);
        previewHtml = '<a href="' + url + '" target="_blank" title="' + escapeHtml(file.name) + '" style="display:block; overflow:hidden; border-radius:6px;"><img src="' + url + '" alt="" class="owner-file-uploader-mini-preview" /></a>';
      }
      const removeBtn = '<button type="button" class="owner-file-uploader-item-remove" data-remove-file aria-label="Remove file">&times;</button>';
      return '<span class="owner-file-uploader-item" data-filename="' + escapeHtml(file.name) + '">' + previewHtml + '<span class="owner-file-uploader-item-name">' + escapeHtml(file.name) + ' <em>' + escapeHtml(formatFileSize(file.size)) + '</em></span>' + removeBtn + '</span>';
    }).join("");
  }

  function setUploaderError(uploader, messages) {
    const errorEl = uploader.querySelector("[data-upload-error]");
    const cleanMessages = Array.from(new Set((messages || []).filter(Boolean)));
    uploader.dataset.uploadErrorActive = cleanMessages.length ? "1" : "";
    if (!errorEl) return;
    if (!cleanMessages.length) {
      errorEl.hidden = true;
      errorEl.textContent = "";
      return;
    }
    errorEl.hidden = false;
    errorEl.textContent = cleanMessages.join(" ");
  }

  function fileKey(file) {
    return [file.name, file.size, file.lastModified].join(":");
  }

  function filterUploaderFiles(uploader, incomingFiles, existingFiles) {
    const input = uploader.querySelector("[data-upload-input]");
    const isSingle = uploader.dataset.uploadMode === "single";
    const maxFiles = Number(uploader.dataset.uploadMaxFiles || (isSingle ? 1 : 10));
    const maxSize = Number(uploader.dataset.uploadMaxSize || 0);
    const accepted = new DataTransfer();
    const errors = [];
    const seen = new Set();

    function tryAdd(file) {
      if (!file) return;
      if (file.type && file.type.indexOf("image/") !== 0) {
        errors.push(uploader.dataset.uploadBadType || "");
        return;
      }
      if (maxSize && file.size > maxSize) {
        errors.push(uploader.dataset.uploadTooLarge || "");
        return;
      }
      if (seen.has(fileKey(file))) return;
      if (accepted.files.length >= maxFiles) {
        errors.push(uploader.dataset.uploadTooMany || "");
        return;
      }
      accepted.items.add(file);
      seen.add(fileKey(file));
    }

    if (!isSingle) {
      Array.from(existingFiles || []).forEach(tryAdd);
    }
    Array.from(incomingFiles || []).forEach(tryAdd);

    if (isSingle && accepted.files.length > 1) {
      errors.push(uploader.dataset.uploadTooMany || "");
      while (accepted.items.length > 1) {
        accepted.items.remove(1);
      }
    }

    if (input && input.multiple) {
      input._accumulatedFiles = accepted;
      input.value = "";
    } else if (input) {
      input.files = accepted.files;
    }
    setUploaderError(uploader, errors);
    return accepted.files;
  }

  function shouldBypassNavigationWarning(target) {
    if (!target) return true;
    if (target.hasAttribute("download")) return true;
    const href = target.getAttribute("href") || "";
    if (!href || href.charAt(0) === "#") return true;
    if (href.indexOf("javascript:") === 0) return true;
    if ((target.getAttribute("target") || "").toLowerCase() === "_blank") return true;
    return false;
  }

  function isPlainPrimaryClick(event) {
    return event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey;
  }

  function openLeaveGuard(url) {
    if (!leaveGuard) return false;
    pendingNavigationUrl = url || "";
    leaveGuardLastFocus = document.activeElement;
    leaveGuard.hidden = false;
    document.documentElement.classList.add("owner-leave-guard-open");
    if (leaveGuardSave) {
      leaveGuardSave.focus({ preventScroll: true });
    }
    return true;
  }

  function closeLeaveGuard() {
    if (!leaveGuard) return;
    leaveGuard.hidden = true;
    document.documentElement.classList.remove("owner-leave-guard-open");
    pendingNavigationUrl = "";
    if (leaveGuardLastFocus && typeof leaveGuardLastFocus.focus === "function") {
      leaveGuardLastFocus.focus({ preventScroll: true });
    }
  }

  function submitDraftAndExit() {
    const button = document.createElement("button");
    button.type = "submit";
    button.name = "form_action";
    button.value = "save_draft_exit";
    button.formNoValidate = true;
    button.hidden = true;
    button.setAttribute("data-loading-button", "");
    form.appendChild(button);
    if (typeof form.requestSubmit === "function") {
      form.requestSubmit(button);
    } else {
      button.click();
    }
  }

  window.addEventListener("beforeunload", function (event) {
    saveDraftNow();
    if (allowNavigation || !hasUnsavedChanges()) return;
    event.preventDefault();
    event.returnValue = unsavedChangesMessage;
  });

  window.addEventListener("offline", function () {
    saveDraftNow();
    showDraftStatus(draftOfflineMessage, "offline");
  });

  window.addEventListener("online", function () {
    if (hasUnsavedChanges()) {
      showDraftStatus(draftOnlineMessage, "saved");
    }
  });

  window.addEventListener("pagehide", function () {
    saveDraftNow();
  });

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") {
      saveDraftNow();
    }
  });

  document.addEventListener("click", function (event) {
    const link = event.target.closest("a[href]");
    if (!isPlainPrimaryClick(event)) return;
    if (!link || shouldBypassNavigationWarning(link)) return;
    if (allowNavigation || !hasUnsavedChanges()) return;
    event.preventDefault();
    if (openLeaveGuard(link.href)) {
      return;
    }
    if (window.confirm(unsavedChangesMessage)) {
      allowNavigation = true;
      window.location.href = link.href;
      return;
    }
  });

  if (leaveGuardSave) {
    leaveGuardSave.addEventListener("click", function () {
      allowNavigation = true;
      window.clearTimeout(draftSaveTimer);
      saveDraftNow();
      submitDraftAndExit();
    });
  }

  if (leaveGuardCancel) {
    leaveGuardCancel.addEventListener("click", function () {
      closeLeaveGuard();
    });
  }

  if (leaveGuardDiscard) {
    leaveGuardDiscard.addEventListener("click", function () {
      allowNavigation = true;
      const targetUrl = pendingNavigationUrl || "/";
      closeLeaveGuard();
      window.location.href = targetUrl;
    });
  }

  if (leaveGuard) {
    leaveGuard.addEventListener("click", function (event) {
      if (event.target === leaveGuard) {
        closeLeaveGuard();
      }
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && leaveGuard && !leaveGuard.hidden) {
      event.preventDefault();
      closeLeaveGuard();
    }
  });

  form.addEventListener("submit", function (event) {
    const submitter = event.submitter || document.activeElement;
    const isDraft = submitter && (
      submitter.value === "save_draft"
      || submitter.value === "save_draft_exit"
      || (submitter.name === "form_action" && (submitter.value === "save_draft" || submitter.value === "save_draft_exit"))
    );
    
    if (!isDraft) {
      for (let i = 1; i <= 4; i++) {
        const step = steps[i - 1];
        const state = getStepState(step);
        if (!state.complete) {
          event.preventDefault();
          updateWizard(i);
          focusFirstProblem(step);
          return;
        }
      }
    }

    form.querySelectorAll('input[type="file"][multiple]').forEach(function (input) {
      if (input._accumulatedFiles) {
        input.files = input._accumulatedFiles.files;
      }
    });
    allowNavigation = true;
    window.clearTimeout(draftSaveTimer);
    saveDraftNow();
  });

  form.addEventListener("click", function (event) {
    const nextButton = event.target.closest("[data-owner-next]");
    const prevButton = event.target.closest("[data-owner-prev]");
    const stepTab = event.target.closest("[data-owner-step-target]");
    const langTab = event.target.closest("[data-owner-lang-tab]");
    const listingType = event.target.closest("[data-owner-listing-type]");
    const gotoNext = event.target.closest("[data-owner-goto-next]");
    const removeFileBtn = event.target.closest("[data-remove-file]");
    const uploadTrigger = event.target.closest("[data-upload-trigger]");
    const findOnMapBtn = event.target.closest("[data-action-find-on-map]");

    if (uploadTrigger) {
      event.preventDefault();
      const uploader = uploadTrigger.closest("[data-file-uploader]");
      const input = uploader ? uploader.querySelector("[data-upload-input]") : null;
      if (input) {
        input.click();
      }
      return;
    }

    if (findOnMapBtn) {
      event.preventDefault();
      const mapPicker = form.querySelector("[data-owner-map-picker]");
      const searchInput = mapPicker ? mapPicker.querySelector("[data-map-search-input]") : null;
      const searchBtn = mapPicker ? mapPicker.querySelector("[data-map-search]") : null;
      const addressInput = getField("address");
      if (searchInput && addressInput) {
        searchInput.value = addressInput.value || searchInput.value || "";
      }
      if (window.kidsMapRefreshOwnerMapPickers) {
        window.kidsMapRefreshOwnerMapPickers();
      }
      if (searchBtn) {
        searchBtn.click();
      }
      if (mapPicker) {
        mapPicker.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      return;
    }

    if (removeFileBtn) {
      event.preventDefault();
      const item = removeFileBtn.closest(".owner-file-uploader-item");
      const previewCard = removeFileBtn.closest(".owner-file-uploader-preview-card");
      const filename = (item || previewCard).dataset.filename;
      const uploader = removeFileBtn.closest("[data-file-uploader]");
      const input = uploader.querySelector("[data-upload-input]");
      
      const dt = new DataTransfer();
      const currentFiles = input._accumulatedFiles ? input._accumulatedFiles.files : input.files;
      Array.from(currentFiles).forEach(f => {
        if (f.name !== filename) dt.items.add(f);
      });
      if (input.multiple) {
        input._accumulatedFiles = dt;
        input.value = "";
      } else {
        input.files = dt.files;
      }
      
      renderUploaderState(uploader);
      updateCompletion();
      updateFinalSummary();
      updateWizard(currentStep);
      scheduleDraftSave();
      return;
    }

    if (gotoNext) {
      event.preventDefault();
      const requiredNames = parseList(form.dataset.ownerRequiredFields);
      for (let i = 0; i < requiredNames.length; i++) {
        if (!isFieldFilledByName(requiredNames[i])) {
          const field = getField(requiredNames[i]);
          if (field) {
            const step = field.closest("[data-owner-step]");
            if (step) {
              const target = Number(step.dataset.ownerStep || "1");
              if (target <= maxReachableStep()) {
                updateWizard(target);
              }
            }
            openContainingDetails(field);
            const targetEl = field.closest('.owner-form-field') || field;
            targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
            if (typeof field.focus === "function") {
               field.focus({ preventScroll: true });
            }
            break;
          }
        }
      }
      return;
    }

    if (listingType) {
      event.preventDefault();
      const temporaryCheckbox = form.querySelector('[name="is_temporary"]');
      listingTypeChosen = true;
      if (temporaryCheckbox) {
        temporaryCheckbox.checked = listingType.dataset.ownerListingType === "temporary";
      }
      syncListingMode();
      syncTemporaryRequiredState();
      syncOptionalDetailsState();
      updateCompletion();
      updateFinalSummary();
      updateWizard(currentStep);
      scheduleDraftSave();
      return;
    }

    if (langTab) {
      event.preventDefault();
      activateLanguagePanel(langTab.closest("[data-owner-lang-tabs]"), langTab.dataset.ownerLangTab);
      return;
    }

    if (stepTab) {
      event.preventDefault();
      const target = Number(stepTab.dataset.ownerStepTarget || "1");
      if (target <= maxReachableStep() || target === steps.length) {
        updateWizard(target);
        scheduleDraftSave();
      }
      return;
    }

    if (prevButton) {
      event.preventDefault();
      updateWizard(currentStep - 1);
      scheduleDraftSave();
      return;
    }

    if (nextButton) {
      event.preventDefault();
      if (!validateCurrentStep()) {
        updateCompletion();
        updateWizard(currentStep);
        return;
      }
      updateCompletion();
      updateWizard(currentStep + 1);
      scheduleDraftSave();
    }
  });

  form.addEventListener("change", function (event) {
    if (event.target.type === "file" && event.target.multiple) {
      const input = event.target;
      const uploader = input.closest("[data-file-uploader]");
      if (uploader) {
        filterUploaderFiles(uploader, input.files, input._accumulatedFiles ? input._accumulatedFiles.files : []);
      }
    } else if (event.target.type === "file") {
      const input = event.target;
      const uploader = input.closest("[data-file-uploader]");
      if (uploader) {
        filterUploaderFiles(uploader, input.files, []);
      }
    }

    markStepTouched(event.target);
    if (event.target.matches('[name="region"]')) {
      syncLocationCascading();
    }
    if (event.target.matches('[name="district"], [name="metro"]')) {
      setLocationValidity();
    }
    if (event.target.matches('[name="is_temporary"]')) {
      syncListingMode();
      syncTemporaryRequiredState();
    }
    if (event.target.closest("details.owner-form-details")) {
      syncOptionalDetailsState(event.target.closest("details.owner-form-details"));
    }
    const uploader = event.target.closest("[data-file-uploader]");
    if (uploader) {
      renderUploaderState(uploader);
    }
    if (event.target && typeof event.target.checkValidity === "function" && event.target.checkValidity()) {
      clearFieldError(event.target);
    }
    updateCompletion();
    updateFinalSummary();
    updateWizard(currentStep);
    scheduleDraftSave();
  });

  form.addEventListener("input", function (event) {
    markStepTouched(event.target);
    if (event.target && typeof event.target.checkValidity === "function" && event.target.checkValidity()) {
      clearFieldError(event.target);
    }
    updateCompletion();
    updateFinalSummary();
    updateWizard(currentStep);
    scheduleDraftSave();
  });

  form.addEventListener("km:schedule-change", function () {
    const scheduleField = getField("structured_schedule");
    if (scheduleField) {
      markStepTouched(scheduleField);
      setScheduleClientError(!isStructuredScheduleFilled(scheduleField));
    }
    updateCompletion();
    updateFinalSummary();
    updateWizard(currentStep);
    scheduleDraftSave();
  });

  form.addEventListener("toggle", function (event) {
    if (!event.target.matches("details.owner-form-details")) return;
    scheduleDraftSave();
  }, true);

  form.addEventListener("invalid", function (event) {
    event.preventDefault();
    if (event.target) {
      showFieldError(event.target);
    }
  }, true);

  function initDragAndDrop(uploader) {
    const dropZone = uploader.querySelector(".owner-file-uploader-drop");
    const input = uploader.querySelector("[data-upload-input]");
    if (!dropZone || !input) return;

    ["dragenter", "dragover"].forEach(function (eventName) {
      dropZone.addEventListener(eventName, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add("is-dragover");
      }, false);
    });

    ["dragleave", "drop"].forEach(function (eventName) {
      dropZone.addEventListener(eventName, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("is-dragover");
      }, false);
    });

    dropZone.addEventListener("drop", function (e) {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (!files || !files.length) return;

      if (input.multiple) {
        filterUploaderFiles(uploader, files, input._accumulatedFiles ? input._accumulatedFiles.files : input.files);
      } else {
        filterUploaderFiles(uploader, files, []);
      }

      renderUploaderState(uploader);
      updateCompletion();
      updateFinalSummary();
      updateWizard(currentStep);
      scheduleDraftSave();
    }, false);
  }

  Array.from(document.querySelectorAll("[data-file-uploader]")).forEach(function (uploader) {
    renderUploaderState(uploader);
    initDragAndDrop(uploader);
  });

  restoreDraftState();

  // Set up Azerbaijani phone format: +994 50 123 45 67
  const phoneInputs = form.querySelectorAll('[data-km-az-phone], input[type="tel"], input[name="phone1"], input[name="phone2"]');
  function formatAzerbaijanPhone(value, keepPrefix) {
    let digits = String(value || "").replace(/\D/g, "");
    if (digits.startsWith("994")) {
      digits = digits.slice(3);
    }
    if (digits.startsWith("0")) {
      digits = digits.slice(1);
    }
    digits = digits.slice(0, 9);

    const chunks = [];
    [[0, 2], [2, 5], [5, 7], [7, 9]].forEach(function (range) {
      const part = digits.slice(range[0], range[1]);
      if (part) {
        chunks.push(part);
      }
    });

    if (!chunks.length) {
      return keepPrefix ? "+994 " : "";
    }
    return "+994 " + chunks.join(" ");
  }
  phoneInputs.forEach(function(input) {
    input.setAttribute("autocomplete", "tel");
    input.setAttribute("inputmode", "tel");
    input.setAttribute("maxlength", "20");
    if (input.value) {
      input.value = formatAzerbaijanPhone(input.value, false);
    }
    input.addEventListener("input", function() {
      input.value = formatAzerbaijanPhone(input.value, true);
    });
    input.addEventListener("focus", function() {
      if (!input.value) {
        input.value = "+994 ";
      }
    });
    input.addEventListener("blur", function() {
      if (!String(input.value || "").replace(/\D/g, "").replace(/^994/, "")) {
        input.value = "";
      } else {
        input.value = formatAzerbaijanPhone(input.value, false);
      }
    });
  });

  // Set up Price Free Checkbox
  const priceFreeCheckbox = document.getElementById("km-price-free-checkbox");
  if (priceFreeCheckbox) {
    const priceFromInput = form.querySelector('[name="price_from"]');
    const priceToInput = form.querySelector('[name="price_to"]');
    const priceGrid = form.querySelector('[data-price-inputs-grid]');

    function updatePriceGridVisibility() {
      const isFree = priceFreeCheckbox.checked;
      if (priceGrid) {
        priceGrid.style.display = isFree ? "none" : "";
      }
      if (isFree) {
        if (priceFromInput) {
          priceFromInput.value = "0";
          priceFromInput.dispatchEvent(new Event("input", { bubbles: true }));
        }
        if (priceToInput) {
          priceToInput.value = "0";
          priceToInput.dispatchEvent(new Event("input", { bubbles: true }));
        }
      }
    }

    // Initialize state
    if (priceFromInput && priceToInput) {
      if (priceFromInput.value === "0" && priceToInput.value === "0") {
        priceFreeCheckbox.checked = true;
      }
      updatePriceGridVisibility();
    } else if (priceFromInput) {
      if (priceFromInput.value === "0") {
        priceFreeCheckbox.checked = true;
      }
      updatePriceGridVisibility();
    }

    priceFreeCheckbox.addEventListener("change", function () {
      if (priceFreeCheckbox.checked) {
        updatePriceGridVisibility();
      } else {
        if (priceFromInput) {
          priceFromInput.value = "";
          priceFromInput.dispatchEvent(new Event("input", { bubbles: true }));
        }
        if (priceToInput) {
          priceToInput.value = "";
          priceToInput.dispatchEvent(new Event("input", { bubbles: true }));
        }
        updatePriceGridVisibility();
      }
      updateCompletion();
      updateFinalSummary();
    });
  }


  steps.forEach(function (step) {
    if (step.querySelector(".auth-field-error, .auth-errors")) {
      step.dataset.ownerStepAttempted = "true";
      step.dataset.ownerStepTouched = "true";
    }
  });

  document.addEventListener("keydown", function (e) {
    var target = e.target;
    if (target && target.tagName === "INPUT" && target.getAttribute("inputmode") === "numeric") {
      if (
        [46, 8, 9, 27, 13].indexOf(e.keyCode) !== -1 ||
        (e.keyCode === 65 && (e.ctrlKey === true || e.metaKey === true)) ||
        (e.keyCode === 67 && (e.ctrlKey === true || e.metaKey === true)) ||
        (e.keyCode === 86 && (e.ctrlKey === true || e.metaKey === true)) ||
        (e.keyCode === 88 && (e.ctrlKey === true || e.metaKey === true)) ||
        (e.keyCode >= 35 && e.keyCode <= 40)
      ) {
        return;
      }
      if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
        e.preventDefault();
      }
    }
  });

  document.addEventListener("input", function (e) {
    var target = e.target;
    if (target && target.tagName === "INPUT" && target.getAttribute("inputmode") === "numeric") {
      var val = target.value;
      var clean = val.replace(/\D/g, "");
      if (val !== clean) {
        target.value = clean;
      }
    }
  });

  window.addEventListener("resize", alignStepperTrack);
  window.addEventListener("load", alignStepperTrack);

  syncListingMode();
  syncTemporaryRequiredState();
  syncOptionalDetailsState();
  syncLocationCascading();
  syncLanguagePanels();
  updateCompletion();
  updateFinalSummary();
  updateWizard(restoredStep || firstErrorStep());
})();
