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
  let currentStep = 1;
  let allowNavigation = false;
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
    draftStatus.classList.remove("is-restored", "is-saved", "is-offline");
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
    draftStatus.classList.remove("is-restored", "is-saved", "is-offline");
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
      return !!(field.files && field.files.length);
    }
    return !!String(field.value || "").trim();
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
    const field = getField(name);
    if (!field) return "";
    const wrapper = field.closest(".owner-form-field, .owner-form-toggle-field, .owner-form-file-field");
    const label = wrapper ? wrapper.querySelector(".owner-form-label") : null;
    if (!label) return name;
    return label.textContent.replace(/\*/g, "").replace(/\s+/g, " ").trim();
  }

  function isPhotoFieldFilled(field) {
    if (!field) return false;
    if (field.files && field.files.length) return true;
    const uploader = field.closest("[data-file-uploader]");
    if (!uploader) return false;
    const clearCheckbox = uploader.querySelector(".owner-image-clear-checkbox");
    const hasCurrentPreview = !!uploader.querySelector(".owner-file-uploader-current-preview");
    return hasCurrentPreview && !(clearCheckbox && clearCheckbox.checked);
  }

  function isFieldFilledByName(name) {
    const field = getField(name);
    if (!field) return null;
    if (name === "photo") {
      return isPhotoFieldFilled(field);
    }
    if (name === "gallery_images") {
      return !!(field.files && field.files.length);
    }
    return hasFieldValue(field);
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
      const preferred = ["ru", "en"].find(function (language) {
        const panel = tabsRoot.querySelector('[data-owner-lang-panel="' + language + '"]');
        if (!panel) return false;
        return !!panel.querySelector(".auth-field-error") || Array.from(panel.querySelectorAll("input, textarea")).some(hasFieldValue);
      }) || "ru";
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
      const count = galleryField && galleryField.files ? galleryField.files.length : 0;
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
  }

  function setLocationValidity() {
    const district = form.querySelector('[name="district"]');
    const metro = form.querySelector('[name="metro"]');
    if (!district || !metro) return;
    if ((district.value || "").trim() || (metro.value || "").trim()) {
      district.setCustomValidity("");
      metro.setCustomValidity("");
      return;
    }
    district.setCustomValidity(locationRequiredMessage);
    metro.setCustomValidity(locationRequiredMessage);
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
      const isUnlocked = target <= reachableStep;
      const indicator = tab.querySelector("[data-owner-step-indicator]");

      tab.classList.toggle("is-active", target === currentStep);
      tab.classList.toggle("is-complete", state.complete);
      tab.classList.toggle("is-warning", state.warning);
      tab.classList.toggle("is-locked", !isUnlocked);
      tab.setAttribute("aria-current", target === currentStep ? "step" : "false");
      tab.setAttribute("aria-disabled", isUnlocked ? "false" : "true");
      tab.disabled = !isUnlocked;

      if (indicator) {
        indicator.textContent = state.complete ? completeLabel : state.warning ? warningLabel : String(target);
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
      progressBar.style.width = ((currentStep / steps.length) * 100).toFixed(2) + "%";
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
      invalidField.reportValidity();
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

    for (const field of fields) {
      if (typeof field.checkValidity === "function" && !field.checkValidity()) {
        focusFirstProblem(activeStep);
        return false;
      }
    }

    const stepState = getStepState(activeStep);
    if (!stepState.complete) {
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
    if (!input || !meta) return;

    const emptyMessage = uploader.dataset.uploadEmpty || "";
    const summaryLabel = uploader.dataset.uploadSummary || "";
    const pendingMessage = uploader.dataset.uploadPending || "";
    const files = Array.from(input.files || []);

    if (!files.length) {
      meta.textContent = emptyMessage;
      uploader.classList.remove("is-selected");
      if (list) {
        list.hidden = true;
        list.innerHTML = "";
      }
      return;
    }

    uploader.classList.add("is-selected");
    if (files.length === 1) {
      meta.textContent = summaryLabel + " " + files[0].name + " (" + formatFileSize(files[0].size) + "). " + pendingMessage;
    } else {
      meta.textContent = summaryLabel + " " + files.length + ". " + pendingMessage;
    }

    if (!list) return;
    list.hidden = false;
    list.innerHTML = files.map(function (file) {
      return '<span class="owner-file-uploader-item">' + escapeHtml(file.name) + '<em>' + escapeHtml(formatFileSize(file.size)) + "</em></span>";
    }).join("");
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
    if (!link || shouldBypassNavigationWarning(link)) return;
    if (allowNavigation || !hasUnsavedChanges()) return;
    if (window.confirm(unsavedChangesMessage)) {
      allowNavigation = true;
      return;
    }
    event.preventDefault();
  });

  form.addEventListener("submit", function () {
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
      if (target <= maxReachableStep()) {
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
    markStepTouched(event.target);
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
    updateCompletion();
    updateFinalSummary();
    updateWizard(currentStep);
    scheduleDraftSave();
  });

  form.addEventListener("input", function (event) {
    markStepTouched(event.target);
    updateCompletion();
    updateFinalSummary();
    updateWizard(currentStep);
    scheduleDraftSave();
  });

  form.addEventListener("toggle", function (event) {
    if (!event.target.matches("details.owner-form-details")) return;
    scheduleDraftSave();
  }, true);

  Array.from(document.querySelectorAll("[data-file-uploader]")).forEach(function (uploader) {
    renderUploaderState(uploader);
  });

  restoreDraftState();

  steps.forEach(function (step) {
    if (step.querySelector(".auth-field-error, .auth-errors")) {
      step.dataset.ownerStepAttempted = "true";
      step.dataset.ownerStepTouched = "true";
    }
  });

  syncListingMode();
  syncTemporaryRequiredState();
  syncOptionalDetailsState();
  syncLanguagePanels();
  updateCompletion();
  updateFinalSummary();
  updateWizard(restoredStep || firstErrorStep());
})();
