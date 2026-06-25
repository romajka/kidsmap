(function () {
  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
      return;
    }
    document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var sectionNodes = Array.prototype.slice.call(
      document.querySelectorAll("[data-km-admin-section], [data-place-section]")
    );
    var stepLinks = Array.prototype.slice.call(
      document.querySelectorAll("[data-km-admin-step-link], [data-place-step-link]")
    );

    function activateCurrentStep() {
      if (!sectionNodes.length || !stepLinks.length) {
        return;
      }

      var current = sectionNodes[0];
      sectionNodes.forEach(function (section) {
        var rect = section.getBoundingClientRect();
        if (rect.top <= 180 && rect.bottom > 180) {
          current = section;
        }
      });

      stepLinks.forEach(function (link) {
        var targetId = (link.getAttribute("href") || "").replace("#", "");
        link.classList.toggle("is-active", targetId === current.id);
      });
    }

    activateCurrentStep();
    window.addEventListener("scroll", activateCurrentStep, { passive: true });
    window.addEventListener("resize", activateCurrentStep);
  });

  ready(function () {
    var form = document.querySelector("[data-km-admin-form]") || document.getElementById("place_form");
    var checkbox = document.getElementById("id_is_temporary");
    var statusSelect = document.getElementById("id_status");
    if (!form) {
      return;
    }

    var startRow = document.querySelector(".field-temporary_start");
    var endRow = document.querySelector(".field-temporary_end");
    var rejectionRow = document.querySelector(".field-rejection_reason");

    function syncTemporaryRows() {
      if (!checkbox) {
        return;
      }
      var visible = checkbox.checked;
      [startRow, endRow].forEach(function (row) {
        if (!row) {
          return;
        }
        var hasErrors = !!row.querySelector(".errorlist");
        row.style.display = visible || hasErrors ? "" : "none";
      });
    }

    function syncRejectedReason() {
      if (!statusSelect || !rejectionRow) {
        return;
      }
      var rejectedValue = form.dataset.rejectedStatus || "rejected";
      var hasErrors = !!rejectionRow.querySelector(".errorlist");
      rejectionRow.style.display =
        statusSelect.value === rejectedValue || hasErrors ? "" : "none";
    }

    if (checkbox) {
      checkbox.addEventListener("change", syncTemporaryRows);
    }
    if (statusSelect) {
      statusSelect.addEventListener("change", syncRejectedReason);
    }
    syncTemporaryRows();
    syncRejectedReason();
  });

  ready(function () {
    var form = document.querySelector("[data-km-admin-form]") || document.getElementById("place_form");
    var configNode =
      document.getElementById("km-admin-progress-config") ||
      document.getElementById("km-place-progress-config");
    if (!form || !configNode) {
      return;
    }

    var checklistItems = [];
    try {
      checklistItems = JSON.parse(configNode.textContent || "[]");
    } catch (error) {
      checklistItems = [];
    }
    if (!checklistItems.length) {
      return;
    }

    var pctNodes = Array.prototype.slice.call(
      document.querySelectorAll("[data-progress-pct]")
    );
    var doneNodes = Array.prototype.slice.call(
      document.querySelectorAll("[data-progress-done]")
    );
    var totalNodes = Array.prototype.slice.call(
      document.querySelectorAll("[data-progress-total]")
    );
    var ringNode = document.querySelector("[data-progress-ring]");
    var barNode = document.querySelector("[data-progress-bar]");
    var readinessNode = document.querySelector("[data-progress-readiness]");
    var missingListNode = document.querySelector("[data-progress-missing-list]");
    var emptyNode = document.querySelector("[data-progress-empty]");

    function hasFieldValue(item) {
      var input = document.getElementById(item.input_id);
      if (!input) {
        return !!item.initial;
      }

      if (input.type === "file") {
        var clearCheckbox = document.getElementById(item.input_id + "-clear");
        var hasSelectedFile = !!(input.files && input.files.length);
        if (clearCheckbox && clearCheckbox.checked) {
          return hasSelectedFile;
        }
        return hasSelectedFile || !!item.initial;
      }

      if (input.type === "checkbox" || input.type === "radio") {
        return !!input.checked;
      }

      if (input.tagName === "SELECT") {
        return !!(input.value || "").trim();
      }

      return !!(input.value || "").trim();
    }

    function setReadinessTone(tone) {
      if (!readinessNode) {
        return;
      }
      readinessNode.classList.remove("km-place-sidebar-badge--good");
      readinessNode.classList.remove("km-place-sidebar-badge--warn");
      readinessNode.classList.remove("km-place-sidebar-badge--muted");
      readinessNode.classList.add("km-place-sidebar-badge--" + tone);
    }

    function renderMissingItems(missing) {
      if (!missingListNode || !emptyNode) {
        return;
      }

      missingListNode.innerHTML = "";
      missing.slice(0, 5).forEach(function (label) {
        var itemNode = document.createElement("li");
        itemNode.textContent = label;
        missingListNode.appendChild(itemNode);
      });

      var hasMissing = missing.length > 0;
      missingListNode.hidden = !hasMissing;
      emptyNode.hidden = hasMissing;
      if (!hasMissing) {
        emptyNode.textContent = form.dataset.progressEmptyText || "";
      }
    }

    function updateProgress() {
      var completed = 0;
      var missing = [];
      var total = checklistItems.length;

      checklistItems.forEach(function (item) {
        if (hasFieldValue(item)) {
          completed += 1;
          return;
        }
        missing.push(item.label);
      });

      var pct = total ? Math.round((completed / total) * 100) : 0;
      pctNodes.forEach(function (node) {
        node.textContent = pct + "%";
      });
      doneNodes.forEach(function (node) {
        node.textContent = String(completed);
      });
      totalNodes.forEach(function (node) {
        node.textContent = String(total);
      });

      if (ringNode) {
        ringNode.style.setProperty("--km-place-progress", String(pct));
      }
      if (barNode) {
        barNode.style.width = pct + "%";
      }

      if (readinessNode) {
        var isComplete = missing.length === 0;
        readinessNode.textContent = isComplete
          ? form.dataset.progressCompleteLabel || ""
          : form.dataset.progressIncompleteLabel || "";
        setReadinessTone(
          isComplete
            ? form.dataset.progressCompleteTone || "good"
            : form.dataset.progressIncompleteTone || "warn"
        );
      }

      renderMissingItems(missing);
    }

    form.addEventListener("input", updateProgress);
    form.addEventListener("change", updateProgress);
    updateProgress();
  });

  ready(function () {
    var azRow = document.querySelector('.form-group.field-name_az.field-description_az');
    var ruRow = document.querySelector('.form-group.field-name_ru.field-description_ru');
    var enRow = document.querySelector('.form-group.field-name_en.field-description_en');

    if (!azRow || !ruRow || !enRow) {
      return;
    }

    var tabsContainer = document.createElement('div');
    tabsContainer.className = 'km-lang-tabs';

    var tabs = [
      { id: 'az', label: 'Азербайджанский (Основной)', element: azRow },
      { id: 'ru', label: 'Русский', element: ruRow },
      { id: 'en', label: 'English', element: enRow }
    ];

    var tabButtons = {};

    tabs.forEach(function (tab) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'km-lang-tab-btn';
      btn.textContent = tab.label;
      
      var hasErrors = !!tab.element.querySelector('.errorlist');
      if (hasErrors) {
        btn.classList.add('has-error');
        var badge = document.createElement('span');
        badge.className = 'error-badge';
        badge.textContent = '!';
        btn.appendChild(badge);
      }

      btn.addEventListener('click', function () {
        setActiveTab(tab.id);
      });

      tabsContainer.appendChild(btn);
      tabButtons[tab.id] = btn;
    });

    azRow.parentNode.insertBefore(tabsContainer, azRow);

    function setActiveTab(activeId) {
      tabs.forEach(function (tab) {
        var isActive = tab.id === activeId;
        tab.element.style.display = isActive ? '' : 'none';
        
        var btn = tabButtons[tab.id];
        if (isActive) {
          btn.classList.add('is-active');
        } else {
          btn.classList.remove('is-active');
        }
      });
    }

    // Если есть ошибка в каком-то табе, делаем его активным по умолчанию, иначе AZ
    var activeDefault = 'az';
    if (ruRow.querySelector('.errorlist')) {
      activeDefault = 'ru';
    } else if (enRow.querySelector('.errorlist')) {
      activeDefault = 'en';
    }

    setActiveTab(activeDefault);
  });

  ready(function () {
    // 0. Автоматически переносим все лейблы внутрь соответствующих .fieldBox
    document.querySelectorAll('.km-place-section .form-group, .km-place-secondary .form-group').forEach(function (formGroup) {
      var row = formGroup.querySelector('.row');
      if (!row) return;

      var fieldBoxes = row.querySelectorAll('.fieldBox');
      fieldBoxes.forEach(function (fb) {
        var label = null;
        var input = fb.querySelector('input, select, textarea');
        if (input && input.id) {
          label = row.querySelector('label[for="' + input.id + '"]');
        }
        
        // Если лейбл не найден по ID (например, readonly поле), ищем предшествующий лейбл
        if (!label) {
          var prev = fb.previousElementSibling;
          while (prev) {
            if (prev.tagName === 'LABEL') {
              label = prev;
              break;
            }
            if (prev.classList.contains('fieldBox')) {
              break;
            }
            prev = prev.previousElementSibling;
          }
        }

        if (label) {
          fb.insertBefore(label, fb.firstChild);
        }
      });
    });

    // 1. Добавляем суффиксы к полям
    var suffixMap = [
      { id: 'id_age_from', text: 'лет' },
      { id: 'id_age_to', text: 'лет' },
      { id: 'id_lesson_duration_minutes', text: 'мин' },
      { id: 'id_price_from', text: '₼' },
      { id: 'id_price_to', text: '₼' },
      { id: 'id_price_per_lesson', text: '₼' },
      { id: 'id_price_per_month', text: '₼' },
      { id: 'id_price_per_8_lessons', text: '₼' }
    ];

    suffixMap.forEach(function (item) {
      var input = document.getElementById(item.id);
      if (!input) {
        return;
      }
      
      if (input.parentNode.classList.contains('km-input-wrapper')) {
        return;
      }

      var wrapper = document.createElement('div');
      wrapper.className = 'km-input-wrapper';

      input.parentNode.insertBefore(wrapper, input);
      wrapper.appendChild(input);

      var suffix = document.createElement('span');
      suffix.className = 'km-input-suffix';
      suffix.textContent = item.text;
      wrapper.appendChild(suffix);
    });

    // 2. Объединяем "Возраст от" и "Возраст до" в один блок диапазона
    var ageFromInput = document.getElementById('id_age_from');
    var ageToInput = document.getElementById('id_age_to');
    
    if (ageFromInput && ageToInput) {
      var fromBox = ageFromInput.closest('.fieldBox');
      var toBox = ageToInput.closest('.fieldBox');
      
      if (fromBox && toBox) {
        var row = fromBox.parentNode;
        
        var ageGroup = document.createElement('div');
        ageGroup.className = 'col-auto fieldBox km-range-fieldbox';
        
        var label = document.createElement('label');
        label.textContent = 'Возраст (от — до)';
        ageGroup.appendChild(label);
        
        var rangeContainer = document.createElement('div');
        rangeContainer.className = 'km-range-container';
        
        var fromInputWrap = fromBox.querySelector('.km-input-wrapper') || ageFromInput;
        var toInputWrap = toBox.querySelector('.km-input-wrapper') || ageToInput;
        
        rangeContainer.appendChild(fromInputWrap);
        
        var sep = document.createElement('span');
        sep.className = 'km-range-separator';
        sep.textContent = '—';
        rangeContainer.appendChild(sep);
        
        rangeContainer.appendChild(toInputWrap);
        ageGroup.appendChild(rangeContainer);
        
        // Копируем ошибки, если они есть
        var errorList = fromBox.querySelector('.errorlist') || toBox.querySelector('.errorlist');
        if (errorList) {
          ageGroup.appendChild(errorList.cloneNode(true));
          ageGroup.classList.add('errors');
        }
        
        row.insertBefore(ageGroup, fromBox);
        
        row.removeChild(fromBox);
        row.removeChild(toBox);
      }
    }

    // 3. Объединяем "Цена от" и "Цена до" в один блок диапазона
    var priceFromInput = document.getElementById('id_price_from');
    var priceToInput = document.getElementById('id_price_to');
    
    if (priceFromInput && priceToInput) {
      var fromBox = priceFromInput.closest('.fieldBox');
      var toBox = priceToInput.closest('.fieldBox');
      
      if (fromBox && toBox) {
        var row = fromBox.parentNode;
        
        var priceGroup = document.createElement('div');
        priceGroup.className = 'col-auto fieldBox km-range-fieldbox';
        
        var label = document.createElement('label');
        label.textContent = 'Цена (от — до)';
        priceGroup.appendChild(label);
        
        var rangeContainer = document.createElement('div');
        rangeContainer.className = 'km-range-container';
        
        var fromInputWrap = fromBox.querySelector('.km-input-wrapper') || priceFromInput;
        var toInputWrap = toBox.querySelector('.km-input-wrapper') || priceToInput;
        
        rangeContainer.appendChild(fromInputWrap);
        
        var sep = document.createElement('span');
        sep.className = 'km-range-separator';
        sep.textContent = '—';
        rangeContainer.appendChild(sep);
        
        rangeContainer.appendChild(toInputWrap);
        priceGroup.appendChild(rangeContainer);
        
        // Копируем ошибки, если они есть
        var errorList = fromBox.querySelector('.errorlist') || toBox.querySelector('.errorlist');
        if (errorList) {
          priceGroup.appendChild(errorList.cloneNode(true));
          priceGroup.classList.add('errors');
        }
        
        row.insertBefore(priceGroup, fromBox);
        
        row.removeChild(fromBox);
        row.removeChild(toBox);
      }
    }

    // 4. Скрываем пустые readonly-слаги на форме добавления и делаем соседние поля на всю ширину
    var slugReadonly = document.querySelector('.field-slug .readonly');
    if (slugReadonly) {
      var slugText = slugReadonly.textContent.trim();
      if (slugText === '-' || slugText === '') {
        var slugBox = slugReadonly.closest('.fieldBox');
        if (slugBox) {
          slugBox.style.display = 'none';
        }
      }
    }

    // 5. Если в строке остался только один видимый блок .fieldBox, расширяем его на всю ширину
    document.querySelectorAll('.km-place-section .form-group > .row, .km-place-secondary .form-group > .row').forEach(function(row) {
      var visibleBoxes = Array.from(row.querySelectorAll('.fieldBox')).filter(function(fb) {
        return window.getComputedStyle(fb).display !== 'none';
      });
      if (visibleBoxes.length === 1) {
        visibleBoxes[0].style.gridColumn = '1 / -1';
      }
    });
  });

  ready(function () {
    var locationSection = document.querySelector("[data-km-location-section]");
    if (!locationSection) return;

    var latInput = document.getElementById('id_lat');
    var lngInput = document.getElementById('id_lng');
    var coordBadge = locationSection.querySelector("[data-location-coordinates-badge]");
    var coordFilledLabel = coordBadge ? coordBadge.getAttribute("data-location-coordinates-label-filled") || "Координаты заполнены" : "";
    var coordMissingLabel = coordBadge ? coordBadge.getAttribute("data-location-coordinates-label-missing") || "Нужны координаты" : "";

    function syncCoordBadge() {
      if (!coordBadge) return;
      var hasLat = !!(latInput && latInput.value.trim());
      var hasLng = !!(lngInput && lngInput.value.trim());
      var hasCoordinates = hasLat && hasLng;
      coordBadge.className = "km-location-badge km-location-badge--" + (hasCoordinates ? "good" : "warn");
      coordBadge.textContent = hasCoordinates ? coordFilledLabel : coordMissingLabel;
    }

    if (latInput) latInput.addEventListener('input', syncCoordBadge);
    if (lngInput) lngInput.addEventListener('input', syncCoordBadge);
    syncCoordBadge();
  });

  ready(function () {
    var mediaSection = document.querySelector("[data-place-media-section]");
    if (!mediaSection) {
      return;
    }

    var mainInput = document.getElementById("id_photo");
    var mainPreview = mediaSection.querySelector("[data-main-photo-preview]");
    var mainPlaceholder = mediaSection.querySelector("[data-main-photo-placeholder]");
    var mainPickButton = mediaSection.querySelector("[data-main-photo-pick]");
    var mainClearButton = mediaSection.querySelector("[data-main-photo-clear]");
    var mainFileName = mediaSection.querySelector("[data-main-photo-file-name]");
    var mainFileSize = mediaSection.querySelector("[data-main-photo-file-size]");
    var mainClearCheckbox = mainInput && mainInput.id ? document.getElementById(mainInput.id + "-clear") : null;
    var mainDropzone = mediaSection.querySelector("[data-main-photo-preview-wrap]");
    var mainRoot = mediaSection.querySelector("[data-main-photo-root]");

    function formatBytes(bytes) {
      var size = Number(bytes || 0);
      if (!size) {
        return "";
      }
      var units = ["B", "KB", "MB", "GB"];
      var unitIndex = 0;
      while (size >= 1024 && unitIndex < units.length - 1) {
        size = size / 1024;
        unitIndex += 1;
      }
      return (unitIndex === 0 ? Math.round(size) : size.toFixed(size >= 10 ? 0 : 1)) + " " + units[unitIndex];
    }

    function clearPreviewImage(img) {
      if (!img) {
        return;
      }
      img.removeAttribute("src");
      img.hidden = true;
    }

    function setPreviewImage(img, url) {
      if (!img) {
        return;
      }
      img.hidden = false;
      img.src = url;
    }

    function syncMainPhotoState() {
      if (!mainInput) {
        return;
      }

      var selectedFile = mainInput.files && mainInput.files.length ? mainInput.files[0] : null;
      var isCleared = !!(mainClearCheckbox && mainClearCheckbox.checked);
      var showSelected = !!selectedFile && !isCleared;

      if (mainRoot) {
        var hasPhoto = !!(showSelected || (!isCleared && mainPreview && mainPreview.getAttribute("data-main-photo-initial-url")));
        mainRoot.classList.toggle("has-photo", hasPhoto);
      }

      if (showSelected) {
        if (mainPlaceholder) {
          mainPlaceholder.hidden = true;
        }
        var previewUrl = window.URL ? window.URL.createObjectURL(selectedFile) : "";
        if (previewUrl) {
          setPreviewImage(mainPreview, previewUrl);
          mainPreview.onload = function () {
            if (previewUrl && window.URL) {
              window.URL.revokeObjectURL(previewUrl);
            }
          };
        }
        if (mainFileName) {
          mainFileName.textContent = selectedFile.name || "";
        }
        if (mainFileSize) {
          mainFileSize.textContent = formatBytes(selectedFile.size);
        }
      } else {
        if (mainClearCheckbox && isCleared) {
          mainClearCheckbox.checked = true;
        }
        if (!isCleared && mainPreview && mainPreview.getAttribute("data-main-photo-initial-url")) {
          setPreviewImage(mainPreview, mainPreview.getAttribute("data-main-photo-initial-url"));
          if (mainFileName) {
            mainFileName.textContent = mainPreview.getAttribute("data-main-photo-initial-name") || "";
          }
          if (mainFileSize) {
            mainFileSize.textContent = formatBytes(mainPreview.getAttribute("data-main-photo-initial-size"));
          }
          if (mainPlaceholder) {
            mainPlaceholder.hidden = true;
          }
        } else {
          clearPreviewImage(mainPreview);
          if (mainPlaceholder) {
            mainPlaceholder.hidden = false;
          }
          if (mainFileName) {
            mainFileName.textContent = "Файл не выбран";
          }
          if (mainFileSize) {
            mainFileSize.textContent = "";
          }
        }
      }
    }

    function clearMainPhoto() {
      if (mainInput) {
        mainInput.value = "";
      }
      if (mainClearCheckbox) {
        mainClearCheckbox.checked = true;
      }
      syncMainPhotoState();
    }

    if (mainInput) {
      mainInput.addEventListener("change", function () {
        if (mainClearCheckbox) {
          mainClearCheckbox.checked = false;
        }
        syncMainPhotoState();
      });
    }
    if (mainClearCheckbox) {
      mainClearCheckbox.addEventListener("change", syncMainPhotoState);
    }
    if (mainPickButton && mainInput) {
      mainPickButton.addEventListener("click", function () {
        mainInput.click();
      });
    }
    if (mainClearButton) {
      mainClearButton.addEventListener("click", clearMainPhoto);
    }
    if (mainDropzone && mainInput) {
      mainDropzone.addEventListener("click", function (event) {
        if (event.target && event.target.closest && event.target.closest("[data-main-photo-clear], [data-main-photo-pick]")) {
          return;
        }
        mainInput.click();
      });
      mainDropzone.addEventListener("dragover", function (event) {
        event.preventDefault();
        mainDropzone.classList.add("is-dragover");
      });
      mainDropzone.addEventListener("dragleave", function () {
        mainDropzone.classList.remove("is-dragover");
      });
      mainDropzone.addEventListener("drop", function (event) {
        var file = event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files[0] : null;
        if (!file) {
          return;
        }
        event.preventDefault();
        mainDropzone.classList.remove("is-dragover");
        if (typeof DataTransfer !== "undefined") {
          var transfer = new DataTransfer();
          transfer.items.add(file);
          mainInput.files = transfer.files;
          mainInput.dispatchEvent(new Event("change", { bubbles: true }));
        }
      });
    }

    syncMainPhotoState();
  });

  ready(function () {
    var galleryRoot = document.querySelector("[data-gallery-root]");
    if (!galleryRoot) {
      return;
    }

    var grid = galleryRoot.querySelector("[data-gallery-grid]");
    var addButton = galleryRoot.querySelector("[data-gallery-add-button]");
    var totalFormsInput = galleryRoot.querySelector('input[name$="-TOTAL_FORMS"]');
    var template = galleryRoot.querySelector("[data-gallery-empty-template]");
    var uploadPicker = document.createElement("input");
    var nextIndex = totalFormsInput ? parseInt(totalFormsInput.value, 10) || 0 : 0;

    uploadPicker.type = "file";
    uploadPicker.accept = "image/*";
    uploadPicker.multiple = true;
    uploadPicker.hidden = true;
    galleryRoot.appendChild(uploadPicker);

    function formatBytes(bytes) {
      var size = Number(bytes || 0);
      if (!size) {
        return "";
      }
      var units = ["B", "KB", "MB", "GB"];
      var unitIndex = 0;
      while (size >= 1024 && unitIndex < units.length - 1) {
        size = size / 1024;
        unitIndex += 1;
      }
      return (unitIndex === 0 ? Math.round(size) : size.toFixed(size >= 10 ? 0 : 1)) + " " + units[unitIndex];
    }

    function getFileNameOnly(path) {
      if (!path) return "";
      return path.substring(path.lastIndexOf('/') + 1).substring(path.lastIndexOf('\\') + 1);
    }

    function updateTotalFormsCount() {
      if (totalFormsInput) {
        totalFormsInput.value = String(nextIndex);
      }
    }

    function getCards() {
      return Array.prototype.slice.call(grid.querySelectorAll("[data-gallery-card]"));
    }

    function renumberVisibleCards() {
      var order = 1;
      getCards().forEach(function (card) {
        if (card.hidden) {
          return;
        }
        var orderInput = card.querySelector('input[type="number"][name$="-order"]');
        if (orderInput) {
          orderInput.value = String(order);
        }
        order += 1;
      });
    }

    function updateGalleryEmptyState() {
      var emptyState = galleryRoot.querySelector("[data-gallery-empty-state]");
      if (!emptyState) {
        return;
      }
      var visibleCards = getCards().filter(function (card) {
        var deleteInput = card.querySelector('input[type="checkbox"][name$="-DELETE"]');
        var previewEl = card.querySelector("[data-gallery-preview]");
        var hasFile = hasAssignedFile(card) || (previewEl ? previewEl.getAttribute("data-gallery-initial-url") : null);
        return !card.hidden && !(deleteInput && deleteInput.checked) && hasFile;
      });
      if (visibleCards.length === 0) {
        emptyState.style.display = "block";
      } else {
        emptyState.style.display = "none";
      }
    }

    function setCardPreview(card, file, url) {
      var preview = card.querySelector("[data-gallery-preview]");
      var placeholder = card.querySelector("[data-gallery-placeholder]");
      var fileMeta = card.querySelector("[data-gallery-file-meta]");
      if (!preview) {
        return;
      }

      if (url) {
        preview.hidden = false;
        preview.src = url;
        preview.onload = function () {
          if (url && window.URL) {
            window.URL.revokeObjectURL(url);
          }
        };
        if (placeholder) {
          placeholder.hidden = true;
        }
        if (fileMeta) {
          fileMeta.textContent = file.name ? getFileNameOnly(file.name) : "";
        }
      } else {
        var initialUrl = preview.getAttribute("data-gallery-initial-url");
        if (initialUrl) {
          preview.hidden = false;
          preview.src = initialUrl;
          if (placeholder) {
            placeholder.hidden = true;
          }
          if (fileMeta) {
            var initialName = preview.getAttribute("data-gallery-initial-name") || "";
            fileMeta.textContent = getFileNameOnly(initialName);
          }
        } else {
          preview.removeAttribute("src");
          preview.hidden = true;
          if (placeholder) {
            placeholder.hidden = false;
          }
          if (fileMeta) {
            fileMeta.textContent = "Файл не выбран";
          }
        }
      }
      if (fileMeta && file && file.size) {
        fileMeta.textContent = getFileNameOnly(file.name || "") + (file.name ? " · " : "") + formatBytes(file.size);
      }
    }

    function getPersistedIdInput(card) {
      return card.querySelector('input[type="hidden"][name$="-id"]');
    }

    function hasAssignedFile(card) {
      var input = card.querySelector('input[type="file"]');
      return !!(input && input.files && input.files.length);
    }

    function assignFileToCard(card, file) {
      var input = card.querySelector('input[type="file"]');
      if (!input || !file) {
        return false;
      }
      if (typeof DataTransfer === "undefined") {
        return false;
      }
      var transfer = new DataTransfer();
      transfer.items.add(file);
      input.files = transfer.files;
      input.dispatchEvent(new Event("change", { bubbles: true }));
      return true;
    }

    function setCardHiddenState(card, hidden) {
      card.hidden = !!hidden;
      card.classList.toggle("is-hidden", !!hidden);
    }

    function wireCard(card) {
      var input = card.querySelector('input[type="file"]');
      var dropzone = card.querySelector("[data-gallery-dropzone]");
      var removeButton = card.querySelector("[data-gallery-remove]");
      var deleteInput = card.querySelector('input[type="checkbox"][name$="-DELETE"]');
      var orderInput = card.querySelector('input[type="number"][name$="-order"]');
      var preview = card.querySelector("[data-gallery-preview]");
      var placeholder = card.querySelector("[data-gallery-placeholder]");

      function syncFromInput() {
        if (deleteInput && deleteInput.checked) {
          setCardHiddenState(card, true);
          return;
        }
        var file = input && input.files && input.files.length ? input.files[0] : null;
        if (file) {
          card.dataset.galleryCardState = "filled";
          setCardHiddenState(card, false);
          if (deleteInput) {
            deleteInput.checked = false;
          }
          if (placeholder) {
            placeholder.hidden = true;
          }
          setCardPreview(card, file, window.URL ? window.URL.createObjectURL(file) : "");
          return;
        }

        if (preview && preview.getAttribute("data-gallery-initial-url")) {
          card.dataset.galleryCardState = "filled";
          preview.hidden = false;
          preview.src = preview.getAttribute("data-gallery-initial-url");
          if (placeholder) {
            placeholder.hidden = true;
          }
          if (card.querySelector("[data-gallery-file-meta]")) {
            var initialName = preview.getAttribute("data-gallery-initial-name") || "";
            var initialSize = preview.getAttribute("data-gallery-initial-size");
            var sizeStr = initialSize ? " · " + formatBytes(initialSize) : "";
            card.querySelector("[data-gallery-file-meta]").textContent = getFileNameOnly(initialName) + sizeStr;
          }
        } else {
          card.dataset.galleryCardState = "empty";
          if (preview) {
            preview.removeAttribute("src");
            preview.hidden = true;
          }
          if (placeholder) {
            placeholder.hidden = false;
          }
          if (card.querySelector("[data-gallery-file-meta]")) {
            card.querySelector("[data-gallery-file-meta]").textContent = "Файл не выбран";
          }
        }
      }

      if (input) {
        input.addEventListener("change", function () {
          if (deleteInput) {
            deleteInput.checked = false;
          }
          syncFromInput();
          renumberVisibleCards();
          updateGalleryEmptyState();
        });
      }

      if (dropzone) {
        dropzone.addEventListener("click", function (event) {
          if (event.target && event.target.closest && event.target.closest("[data-gallery-remove], [data-gallery-drag-handle]")) {
            return;
          }
          var isReplace = event.target.closest("[data-gallery-replace-trigger]");
          if ((card.dataset.galleryCardState === "empty" || isReplace) && input) {
            input.click();
          }
        });
        dropzone.addEventListener("dragover", function (event) {
          event.preventDefault();
          card.classList.add("is-dragover");
        });
        dropzone.addEventListener("dragleave", function () {
          card.classList.remove("is-dragover");
        });
        dropzone.addEventListener("drop", function (event) {
          var file = event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files[0] : null;
          if (!file) {
            return;
          }
          event.preventDefault();
          event.stopPropagation();
          card.classList.remove("is-dragover");
          assignFileToCard(card, file);
        });
      }

      if (removeButton) {
        removeButton.addEventListener("click", function () {
          var idInput = getPersistedIdInput(card);
          var persisted = !!(idInput && String(idInput.value || "").trim());
          if (persisted && deleteInput) {
            deleteInput.checked = true;
            setCardHiddenState(card, true);
          } else {
            if (input) {
              input.value = "";
            }
            if (deleteInput) {
              deleteInput.checked = false;
            }
            setCardHiddenState(card, true);
          }
          syncFromInput();
          renumberVisibleCards();
          updateGalleryEmptyState();
          updateAddCardVisibility();
        });
      }

      if (orderInput) {
        orderInput.addEventListener("change", function () {
          renumberVisibleCards();
          updateGalleryEmptyState();
          updateAddCardVisibility();
        });
      }

      syncFromInput();
    }

    function createCardFromTemplate() {
      if (!template) {
        return null;
      }

      var container = document.createElement("div");
      container.innerHTML = template.innerHTML.replace(/__prefix__/g, String(nextIndex));
      nextIndex += 1;
      updateTotalFormsCount();
      var card = container.firstElementChild;
      if (!card) {
        return null;
      }
      grid.appendChild(card);
      wireCard(card);
      renumberVisibleCards();
      return card;
    }

    function findReusableCard() {
      var cards = getCards();
      for (var i = 0; i < cards.length; i += 1) {
        var card = cards[i];
        if (card.hidden) {
          var idInput = getPersistedIdInput(card);
          if (!idInput || !String(idInput.value || "").trim()) {
            return card;
          }
        }
        if (!card.hidden && !hasAssignedFile(card)) {
          var existingId = getPersistedIdInput(card);
          if (!existingId || !String(existingId.value || "").trim()) {
            return card;
          }
        }
      }
      return null;
    }

    function addFiles(files) {
      var list = Array.prototype.slice.call(files || []);
      var activeCount = getCards().filter(function (c) {
        var deleteInput = c.querySelector('input[type="checkbox"][name$="-DELETE"]');
        var previewEl = c.querySelector("[data-gallery-preview]");
        var hasFile = hasAssignedFile(c) || (previewEl ? previewEl.getAttribute("data-gallery-initial-url") : null);
        return !c.hidden && !(deleteInput && deleteInput.checked) && hasFile;
      }).length;

      var allowedToAdd = 10 - activeCount;
      if (allowedToAdd <= 0) {
        alert("Максимальное количество фотографий — 10.");
        return;
      }

      var addedAny = false;
      list.slice(0, allowedToAdd).forEach(function (file) {
        if (!file || !file.type || file.type.indexOf("image/") !== 0) {
          return;
        }
        var card = findReusableCard();
        if (!card) {
          card = createCardFromTemplate();
        } else {
          setCardHiddenState(card, false);
        }
        if (!card) {
          return;
        }
        assignFileToCard(card, file);
        addedAny = true;
      });

      if (list.length > allowedToAdd) {
        alert("Превышен лимит в 10 фотографий. Добавлено только " + allowedToAdd + " шт.");
      }

      renumberVisibleCards();
      updateGalleryEmptyState();
      updateAddCardVisibility();
    }

    function updateAddCardVisibility() {
      var addCard = galleryRoot.querySelector("[data-gallery-add-button-card]");
      var topAddButton = galleryRoot.querySelector("[data-gallery-add-button]");
      
      var activePhotosCount = getCards().filter(function (c) {
        var deleteInput = c.querySelector('input[type="checkbox"][name$="-DELETE"]');
        var previewEl = c.querySelector("[data-gallery-preview]");
        var hasFile = hasAssignedFile(c) || (previewEl ? previewEl.getAttribute("data-gallery-initial-url") : null);
        return !c.hidden && !(deleteInput && deleteInput.checked) && hasFile;
      }).length;

      if (activePhotosCount >= 10) {
        if (addCard) addCard.style.display = "none";
        if (topAddButton) topAddButton.style.display = "none";
      } else {
        if (topAddButton) topAddButton.style.display = "inline-flex";
        if (addCard) {
          if (activePhotosCount === 0) {
            addCard.style.display = "none";
          } else {
            addCard.style.display = "flex";
            grid.appendChild(addCard);
          }
        }
      }
    }

    getCards().forEach(wireCard);

    var addButtons = galleryRoot.querySelectorAll("[data-gallery-add-button], [data-gallery-add-button-empty]");
    addButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        uploadPicker.value = "";
        uploadPicker.click();
      });
    });

    var addCard = galleryRoot.querySelector("[data-gallery-add-button-card]");
    if (addCard) {
      addCard.addEventListener("click", function () {
        uploadPicker.value = "";
        uploadPicker.click();
      });
    }

    uploadPicker.addEventListener("change", function () {
      addFiles(uploadPicker.files);
      uploadPicker.value = "";
    });

    grid.addEventListener("dragover", function (event) {
      event.preventDefault();
    });

    grid.addEventListener("drop", function (event) {
      var droppedFiles = event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files : null;
      if (!droppedFiles || !droppedFiles.length) {
        return;
      }
      event.preventDefault();
      addFiles(droppedFiles);
    });

    // Drag & Drop sorting implementation
    var dragSrcEl = null;

    function handleDragStart(e) {
      if (e.target.closest('[data-gallery-remove]') || e.target.closest('[data-gallery-replace-trigger]') || e.target.closest('[data-gallery-add-button-card]')) {
        e.preventDefault();
        return;
      }
      var card = e.target.closest('[data-gallery-card]');
      if (!card) {
        return;
      }
      dragSrcEl = card;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', ''); // Required for Firefox
      card.classList.add('is-dragging');
    }

    function handleDragOver(e) {
      if (e.preventDefault) {
        e.preventDefault();
      }
      e.dataTransfer.dropEffect = 'move';
      
      var card = e.target.closest('[data-gallery-card], [data-gallery-add-button-card]');
      if (card && card !== dragSrcEl) {
        if (card.hasAttribute('data-gallery-add-button-card')) {
          grid.insertBefore(dragSrcEl, card);
        } else {
          var rect = card.getBoundingClientRect();
          var next = (e.clientX - rect.left) / (rect.right - rect.left) > 0.5;
          grid.insertBefore(dragSrcEl, next ? card.nextSibling : card);
        }
      }
      return false;
    }

    function handleDragEnd(e) {
      var cards = getCards();
      cards.forEach(function (card) {
        card.classList.remove('is-dragging');
      });
      dragSrcEl = null;
      renumberVisibleCards();
      updateGalleryEmptyState();
      updateAddCardVisibility();
    }

    grid.addEventListener('dragstart', handleDragStart);
    grid.addEventListener('dragover', handleDragOver);
    grid.addEventListener('dragend', handleDragEnd);

    renumberVisibleCards();
    updateGalleryEmptyState();
    updateAddCardVisibility();
  });

})();
