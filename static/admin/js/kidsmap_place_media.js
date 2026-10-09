/* ==========================================================================
   KidsMap admin — place form: main photo and gallery.

   Split out of kidsmap_place_form.js: the page controller owns readiness,
   sections and navigation, this file owns the file inputs, previews, drag &
   drop ordering and the inline formset bookkeeping. Every change that can move
   the "main photo" readiness item dispatches km-place-media-change, which the
   page controller listens for.
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

  function setIcon(node, name) {
    if (!node) return;
    var use = node.tagName && String(node.tagName).toLowerCase() === "use"
      ? node
      : node.querySelector("use");
    if (use) use.setAttribute("href", "#kmi-" + name);
  }

  function mediaText(ru, az, en) {
    if (!document.getElementById('place_form')) return ru;
    return ({ru:ru, az:az, en:en})[document.documentElement.lang.split('-')[0]] || ru;
  }

  function notifyMediaChange() {
    document.dispatchEvent(new CustomEvent("km-place-media-change"));
  }

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
    var mainClearCheckbox = mainInput ? mediaSection.querySelector('input[name="' + mainInput.name + '-clear"]') : null;
    var mainDropzone = mediaSection.querySelector("[data-main-photo-preview-wrap]");
    var mainRoot = mediaSection.querySelector("[data-main-photo-root]");
    var mainState = mediaSection.querySelector("[data-main-photo-state]");

    function setMeta(node, text) {
      if (!node) return;
      node.textContent = text || "";
      node.hidden = !text;
    }

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

      var hasPhoto = !!(showSelected || (!isCleared && mainPreview && mainPreview.getAttribute("data-main-photo-initial-url")));
      if (mainRoot) {
        mainRoot.classList.toggle("has-photo", hasPhoto);
      }
      if (mainState) {
        mainState.classList.toggle("is-filled", hasPhoto);
        setIcon(mainState.querySelector("svg"), hasPhoto ? "check_circle" : "radio_button_unchecked");
        var stateText = mainState.querySelector("span");
        if (stateText) stateText.textContent = hasPhoto ? mediaText('Главное фото загружено','Əsas şəkil yüklənib','Main photo uploaded') : mediaText('Нет главного фото','Əsas şəkil yoxdur','No main photo');
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
        setMeta(mainFileName, selectedFile.name || "");
        setMeta(mainFileSize, formatBytes(selectedFile.size));
      } else {
        if (mainClearCheckbox && isCleared) {
          mainClearCheckbox.checked = true;
        }
        if (!isCleared && mainPreview && mainPreview.getAttribute("data-main-photo-initial-url")) {
          setPreviewImage(mainPreview, mainPreview.getAttribute("data-main-photo-initial-url"));
          setMeta(mainFileName, mainPreview.getAttribute("data-main-photo-initial-name") || "");
          setMeta(mainFileSize, formatBytes(mainPreview.getAttribute("data-main-photo-initial-size")));
          if (mainPlaceholder) {
            mainPlaceholder.hidden = true;
          }
        } else {
          clearPreviewImage(mainPreview);
          if (mainPlaceholder) {
            mainPlaceholder.hidden = false;
          }
          setMeta(mainFileName, "");
          setMeta(mainFileSize, "");
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
      if (mainPreview) {
        mainPreview.removeAttribute("data-main-photo-initial-url");
      }
      syncMainPhotoState();
      notifyMediaChange();
    }

    if (mainInput) {
      mainInput.addEventListener("change", function () {
        if (mainClearCheckbox) {
          mainClearCheckbox.checked = false;
        }
        syncMainPhotoState();
        notifyMediaChange();
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
      mainClearButton.addEventListener("click", function (e) {
        if (e) e.preventDefault();
        var hasPhoto = Boolean(
          (mainInput && mainInput.files && mainInput.files.length) ||
          (mainPreview && mainPreview.getAttribute("data-main-photo-initial-url"))
        );
        if (!hasPhoto) {
          clearMainPhoto();
          return;
        }

        if (window.kmModal) {
          window.kmModal.show({
            icon: "delete",
            iconTone: "danger",
            title: mediaText('Удалить главное фото?','Əsas şəkil silinsin?','Remove main photo?'),
            message: document.getElementById('place_form') ? mediaText('Фотография будет удалена после сохранения. Отсутствие фото не блокирует публикацию.', 'Şəkil saxlandıqdan sonra silinəcək. Şəklin olmaması dərcə mane olmur.', 'The photo will be removed after saving. Its absence does not block publication.') : 'Без главного фото карточка перестанет соответствовать требованиям публикации.',
            actions: [
              { label: mediaText('Отмена','Ləğv et','Cancel'), tone: "quiet" },
              {
                label: mediaText('Удалить фото','Şəkli sil','Remove photo'),
                tone: "danger-filled",
                onClick: function () {
                  clearMainPhoto();
                  if (window.kmToast) window.kmToast.info(mediaText('Главное фото удалено','Əsas şəkil silinmək üçün işarələndi','Main photo marked for removal'));
                }
              }
            ]
          });
        } else {
          clearMainPhoto();
        }
      });
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
    var mediaSection = galleryRoot.closest("[data-place-media-section]") || galleryRoot.closest(".km-gallery-section") || galleryRoot.parentElement;

    var grid = galleryRoot.querySelector("[data-gallery-grid]");
    var emptyState = mediaSection ? mediaSection.querySelector("[data-gallery-empty-state]") : null;
    var galleryCountValue = mediaSection ? mediaSection.querySelector("[data-gallery-count-value]") : null;
    var galleryEmptyCount = mediaSection ? mediaSection.querySelector("[data-gallery-count-empty]") : null;
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

    function getActivePhotosCount() {
      return getCards().filter(function (card) {
        var deleteInput = card.querySelector('input[type="checkbox"][name$="-DELETE"]');
        var previewEl = card.querySelector("[data-gallery-preview]");
        var hasFile = hasAssignedFile(card) || (previewEl ? previewEl.getAttribute("data-gallery-initial-url") : null);
        return !card.hidden && !(deleteInput && deleteInput.checked) && hasFile;
      }).length;
    }

    function updateGalleryCounter() {
      var activeCount = getActivePhotosCount();
      if (galleryCountValue) {
        galleryCountValue.textContent = activeCount + " / 10";
      }
      if (galleryEmptyCount) {
        galleryEmptyCount.textContent = mediaText('Сейчас загружено ','Yüklənib: ','Uploaded: ') + activeCount + mediaText(' из 10 фото',' / 10 şəkil',' of 10 photos');
      }
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
      if (!emptyState) {
        return;
      }
      var visibleCards = getActivePhotosCount();
      emptyState.hidden = visibleCards !== 0;
      updateGalleryCounter();
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
            fileMeta.textContent = mediaText('Файл не выбран','Fayl seçilməyib','No file selected');
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

    function hasSavedImage(card) {
      var preview = card.querySelector("[data-gallery-preview]");
      return !!(preview && preview.getAttribute("data-gallery-initial-url"));
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

      var keyboardHandle = card.querySelector("[data-gallery-drag-handle]");
      if (keyboardHandle) {
        keyboardHandle.tabIndex = 0;
        keyboardHandle.setAttribute("role", "button");
        keyboardHandle.setAttribute("aria-keyshortcuts", "ArrowLeft ArrowRight ArrowUp ArrowDown");
        var orderHelp = {ru: 'Порядок фото: стрелками переместите фото', az: 'Şəkil sırası: oxlarla yerini dəyişin', en: 'Photo order: use arrow keys to move'}[(document.documentElement.lang || 'ru').split('-')[0]] || 'Photo order: use arrow keys to move';
        keyboardHandle.setAttribute("aria-label", orderHelp);
        keyboardHandle.title = orderHelp;
        keyboardHandle.addEventListener("keydown", function (event) {
          var direction = {ArrowLeft: -1, ArrowUp: -1, ArrowRight: 1, ArrowDown: 1}[event.key];
          if (!direction) return;
          event.preventDefault();
          var visible = getCards().filter(function (item) { return !item.hidden; });
          var index = visible.indexOf(card);
          var target = visible[index + direction];
          if (!target) return;
          grid.insertBefore(card, direction < 0 ? target : target.nextSibling);
          renumberVisibleCards();
          keyboardHandle.focus();
        });
      }

      function syncFromInput() {
        var idInput = getPersistedIdInput(card);
        var persisted = hasSavedImage(card) || !!(idInput && String(idInput.value || "").trim());
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
            card.querySelector("[data-gallery-file-meta]").textContent = mediaText('Файл не выбран','Fayl seçilməyib','No file selected');
          }
          setCardHiddenState(card, !persisted);
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
          var persisted = hasSavedImage(card) || !!(idInput && String(idInput.value || "").trim());
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
          if (window.kmToast) {
            window.kmToast.info(mediaText('Фотография удалена из галереи','Şəkil qalereyadan silinmək üçün işarələndi','Gallery photo marked for removal'));
          }
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
          if (!hasSavedImage(card) && (!idInput || !String(idInput.value || "").trim())) {
            return card;
          }
        }
        if (!card.hidden && !hasAssignedFile(card)) {
          var existingId = getPersistedIdInput(card);
          if (!hasSavedImage(card) && (!existingId || !String(existingId.value || "").trim())) {
            return card;
          }
        }
      }
      return null;
    }

    function addFiles(files) {
      var list = Array.prototype.slice.call(files || []);
      var activeCount = getActivePhotosCount();

      var allowedToAdd = 10 - activeCount;
      if (allowedToAdd <= 0) {
        if (window.kmToast) {
          window.kmToast.warning(mediaText('Максимальное количество фотографий — 10.','Ən çox 10 şəkil.','Up to 10 photos.'));
        } else {
          alert(mediaText('Максимальное количество фотографий — 10.','Ən çox 10 şəkil.','Up to 10 photos.'));
        }
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
        if (window.kmToast) {
          window.kmToast.warning(mediaText('Превышен лимит в 10 фотографий. Добавлено только ','10 şəkil həddi aşılıb. Əlavə edildi: ','The 10 photo limit was exceeded. Added: ') + allowedToAdd + mediaText(' шт.',' ədəd.',' photos.'));
        } else {
          alert(mediaText('Превышен лимит в 10 фотографий. Добавлено только ','10 şəkil həddi aşılıb. Əlavə edildi: ','The 10 photo limit was exceeded. Added: ') + allowedToAdd + mediaText(' шт.',' ədəd.',' photos.'));
        }
      }

      renumberVisibleCards();
      updateGalleryEmptyState();
      updateAddCardVisibility();
    }

    function updateAddCardVisibility() {
      var addCard = galleryRoot.querySelector("[data-gallery-add-button-card]");
      var topAddButton = mediaSection ? mediaSection.querySelector("[data-gallery-add-button]") : null;

      var activePhotosCount = getActivePhotosCount();

      if (activePhotosCount >= 10) {
        if (addCard) addCard.hidden = true;
        if (topAddButton) topAddButton.hidden = true;
      } else {
        if (topAddButton) topAddButton.hidden = false;
        if (addCard) {
          if (activePhotosCount === 0) {
            addCard.hidden = true;
          } else {
            addCard.hidden = false;
            grid.appendChild(addCard);
          }
        }
      }
    }

    getCards().forEach(wireCard);
    updateGalleryCounter();

    var addButtons = mediaSection
      ? mediaSection.querySelectorAll("[data-gallery-add-button], [data-gallery-add-button-empty]")
      : galleryRoot.querySelectorAll("[data-gallery-add-button], [data-gallery-add-button-empty]");
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

    function handleEmptyStateDragOver(event) {
      event.preventDefault();
      if (emptyState) {
        emptyState.classList.add("is-dragover");
      }
    }

    function handleEmptyStateDragLeave(event) {
      if (!emptyState) {
        return;
      }
      if (event.relatedTarget && emptyState.contains(event.relatedTarget)) {
        return;
      }
      emptyState.classList.remove("is-dragover");
    }

    function handleEmptyStateDrop(event) {
      var droppedFiles = event.dataTransfer && event.dataTransfer.files ? event.dataTransfer.files : null;
      if (!droppedFiles || !droppedFiles.length) {
        return;
      }
      event.preventDefault();
      if (emptyState) {
        emptyState.classList.remove("is-dragover");
      }
      addFiles(droppedFiles);
    }

    if (emptyState) {
      emptyState.addEventListener("dragover", handleEmptyStateDragOver);
      emptyState.addEventListener("dragleave", handleEmptyStateDragLeave);
      emptyState.addEventListener("drop", handleEmptyStateDrop);
    }

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

  ready(function () {
    var uploadInput = document.querySelector("[data-filepond-gallery-upload]");
    var panel = document.querySelector("[data-filepond-gallery-panel]");
    var meta = document.querySelector("[data-filepond-gallery-meta]");
    if (!uploadInput || !panel || panel.dataset.filepondReady === "1") {
      return;
    }

    function getExistingGalleryCount() {
      var cards = Array.prototype.slice.call(document.querySelectorAll("[data-gallery-card]"));
      return cards.filter(function (card) {
        if (card.hidden) {
          return false;
        }
        var deleteInput = card.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteInput && deleteInput.checked) {
          return false;
        }
        var preview = card.querySelector("[data-gallery-preview]");
        var fileInput = card.querySelector('input[type="file"]');
        return !!(
          (preview && preview.getAttribute("data-gallery-initial-url")) ||
          (fileInput && fileInput.files && fileInput.files.length)
        );
      }).length;
    }

    function updateMeta(count, maxFiles) {
      if (!meta) {
        return;
      }
      if (maxFiles <= 0) {
        meta.textContent = mediaText('Лимит галереи заполнен. Удалите одно фото, чтобы добавить новое.','Qalereya doludur. Yeni şəkil üçün birini silin.','Gallery is full. Remove a photo to add another.');
        return;
      }
      meta.textContent = count
        ? mediaText('Будет добавлено новых фото: ','Yeni şəkillər əlavə ediləcək: ','New photos to add: ') + count + mediaText(' из ',' / ',' of ') + maxFiles + mediaText('. Сохраните карточку, чтобы применить.','. Tətbiq etmək üçün kartı saxlayın.','. Save the listing to apply.')
        : mediaText('Новые фото добавятся в галерею после сохранения карточки. Можно изменить порядок перетаскиванием.','Yeni şəkillər kart saxlandıqdan sonra əlavə ediləcək. Ardıcıllığı sürükləməklə dəyişə bilərsiniz.','New photos are added after saving. Drag to change their order.');
    }

    var maxFiles = Math.max(10 - getExistingGalleryCount(), 0);
    uploadInput.dataset.allowReorder = "true";
    uploadInput.dataset.storeAsFile = "true";
    uploadInput.dataset.maxFiles = String(maxFiles);

    if (!window.FilePond) {
      panel.classList.add("km-filepond-gallery--fallback");
      updateMeta(0, maxFiles);
      return;
    }

    try {
      if (window.FilePondPluginImagePreview) {
        window.FilePond.registerPlugin(window.FilePondPluginImagePreview);
      }
    } catch (error) {}

    var pond = window.FilePond.create(uploadInput, {
      allowMultiple: true,
      allowReorder: true,
      allowImagePreview: true,
      credits: false,
      imagePreviewHeight: 118,
      itemInsertLocation: "after",
      maxFiles: maxFiles || 1,
      storeAsFile: true,
      labelIdle: maxFiles > 0
        ? mediaText('Перетащите фото сюда или <span class="filepond--label-action">выберите файлы</span>', 'Şəkilləri buraya sürükləyin və ya <span class="filepond--label-action">faylları seçin</span>', 'Drag photos here or <span class="filepond--label-action">choose files</span>')
        : mediaText('Лимит галереи заполнен','Qalereya doludur','Gallery is full'),
      labelMaxFileCountExceeded: mediaText('Можно добавить не больше {maxFiles} фото','Ən çox {maxFiles} şəkil əlavə edə bilərsiniz','Add up to {maxFiles} photos'),
      labelMaxFileCount: mediaText('Максимум {maxFiles} фото','Ən çox {maxFiles} şəkil','Up to {maxFiles} photos'),
      labelTapToCancel: mediaText('нажмите для отмены','ləğv etmək üçün basın','press to cancel'),
      labelTapToRetry: mediaText('нажмите для повтора','təkrar üçün basın','press to retry'),
      labelTapToUndo: mediaText('нажмите для отмены','ləğv etmək üçün basın','press to cancel'),
      labelButtonRemoveItem: mediaText('Удалить','Sil','Remove'),
      labelButtonAbortItemLoad: mediaText('Отменить','Ləğv et','Cancel'),
      labelButtonRetryItemLoad: mediaText('Повторить','Təkrar et','Retry'),
      labelButtonAbortItemProcessing: mediaText('Отменить','Ləğv et','Cancel'),
      labelButtonUndoItemProcessing: mediaText('Отменить','Ləğv et','Cancel'),
      labelButtonRetryItemProcessing: mediaText('Повторить','Təkrar et','Retry'),
      labelButtonProcessItem: mediaText('Загрузить','Yüklə','Upload')
    });

    if (maxFiles <= 0) {
      pond.setOptions({ disabled: true });
    }

    pond.on("updatefiles", function (files) {
      updateMeta(files.length, maxFiles);
    });
    panel.dataset.filepondReady = "1";
    updateMeta(0, maxFiles);
  });

})();
