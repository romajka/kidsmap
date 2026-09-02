(function () {
  'use strict';

  function ready(fn) {
    if (document.readyState !== 'loading') {
      fn();
      return;
    }
    document.addEventListener('DOMContentLoaded', fn);
  }

  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  ready(function () {
    // Jazzmin applies its own typography with an important rule.  Put the
    // Material face directly on icon spans so ligature names never leak into
    // the interface as visible text.
    Array.prototype.slice.call(document.querySelectorAll('.ms, .material-symbols-rounded')).forEach(function (icon) {
      icon.style.setProperty('font-family', 'Material Symbols Rounded', 'important');
      icon.style.setProperty('font-weight', '400', 'important');
      icon.style.setProperty('font-style', 'normal', 'important');
      icon.style.setProperty('font-variation-settings', "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 20", 'important');
    });

    var form = document.getElementById('changelist-form');
    var bulkBar = document.getElementById('km-bulk-bar');
    var bulkCountLabel = document.getElementById('km-bulk-count-label');
    var readinessPopover = document.getElementById('km-readiness-popover');
    var rowActionsDropdown = document.getElementById('km-row-actions-dropdown');
    var toast = document.getElementById('km-toast');
    var toastText = document.getElementById('km-toast-text');
    var toastUndo = document.getElementById('km-toast-undo');
    var toggleFiltersBtn = document.getElementById('km-toggle-filters-btn');
    var filtersDrawer = document.getElementById('km-filters-drawer');
    var toastTimer = null;
    var lastUndoAction = null;
    var activePopoverTrigger = null;
    var activeMoreBtn = null;
    var i18nNode = document.getElementById('km-changelist-i18n');
    var labels = (i18nNode && i18nNode.dataset) || {};

    var csrftoken = getCookie('csrftoken') || (document.querySelector('input[name="csrfmiddlewaretoken"]') || {}).value;

    function showTableSkeleton() {
      var tbody = document.querySelector('.km-table-container #result_list tbody');
      if (!tbody || tbody.dataset.loading === '1') return;
      tbody.dataset.loading = '1';
      var columns = Math.max(1, document.querySelectorAll('.km-table-container #result_list thead th').length);
      var cells = [];
      for (var i = 0; i < columns; i++) {
        var cls = i === 1 ? ' km-skeleton--thumb' : (i === columns - 1 ? ' km-skeleton--short' : '');
        cells.push('<td><div class="km-skeleton' + cls + '"></div></td>');
      }
      tbody.innerHTML = '<tr class="km-skeleton-row">' + cells.join('') + '</tr>'.repeat(5);
    }

    /* --------------------------------------------------------------------------
       1. Filter Drawer Toggle (1f)
       -------------------------------------------------------------------------- */
    if (toggleFiltersBtn && filtersDrawer) {
      var toolbar = toggleFiltersBtn.closest('.km-toolbar');
      toggleFiltersBtn.addEventListener('click', function (e) {
        e.preventDefault();
        var isHidden = filtersDrawer.hidden;
        filtersDrawer.hidden = !isHidden;
        toggleFiltersBtn.classList.toggle('is-open', isHidden);
        if (toolbar) {
          toolbar.classList.toggle('is-filters-open', isHidden);
        }
        toggleFiltersBtn.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
      });

      var applyBtn = document.getElementById('km-apply-filters-btn');
      if (applyBtn) {
        applyBtn.addEventListener('click', function () {
          var activeSelect = filtersDrawer.querySelector('select[data-filter-select]');
          if (activeSelect && activeSelect.value) {
            showTableSkeleton();
            window.location.href = activeSelect.value;
          } else {
            filtersDrawer.hidden = true;
            toggleFiltersBtn.classList.remove('is-open');
            if (toolbar) toolbar.classList.remove('is-filters-open');
          }
        });
      }
    }

    // Auto submit on select change inside filter drawer
    Array.prototype.slice.call(document.querySelectorAll('[data-filter-select]')).forEach(function (select) {
      select.addEventListener('change', function () {
        if (select.value) {
          showTableSkeleton();
          window.location.href = select.value;
        }
      });
    });

    var changelistSearch = document.getElementById('changelist-search');
    if (changelistSearch) {
      changelistSearch.addEventListener('submit', showTableSkeleton);
    }

    /* --------------------------------------------------------------------------
       2. Selection & Floating Bulk Bar (1c)
       -------------------------------------------------------------------------- */
    if (form && bulkBar) {
      var rowCheckboxes = Array.prototype.slice.call(form.querySelectorAll('input.action-select'));
      var masterCheckbox = document.getElementById('action-toggle');

      function updateSelectionState() {
        var selectedCount = 0;
        rowCheckboxes.forEach(function (cb) {
          var tr = cb.closest('tr');
          if (cb.checked) {
            selectedCount++;
            if (tr) tr.classList.add('selected');
          } else {
            if (tr) tr.classList.remove('selected');
          }
        });

        if (masterCheckbox) {
          if (selectedCount === 0) {
            masterCheckbox.checked = false;
            masterCheckbox.indeterminate = false;
          } else if (selectedCount === rowCheckboxes.length) {
            masterCheckbox.checked = true;
            masterCheckbox.indeterminate = false;
          } else {
            masterCheckbox.checked = false;
            masterCheckbox.indeterminate = true;
          }
        }

        if (selectedCount > 0) {
          bulkBar.hidden = false;
          if (bulkCountLabel) {
            bulkCountLabel.textContent = (labels.selectedLabel || 'Выбрано') + ' ' + selectedCount;
          }
        } else {
          bulkBar.hidden = true;
        }
      }

      rowCheckboxes.forEach(function (cb) {
        cb.addEventListener('change', updateSelectionState);
      });

      if (masterCheckbox) {
        masterCheckbox.addEventListener('change', function () {
          var checked = masterCheckbox.checked;
          rowCheckboxes.forEach(function (cb) {
            cb.checked = checked;
          });
          updateSelectionState();
        });
      }

      bulkBar.addEventListener('click', function (e) {
        var actionBtn = e.target.closest('[data-bulk-action]');
        if (actionBtn) {
          var actionType = actionBtn.dataset.bulkAction;
          if (actionType === 'select-all') {
            rowCheckboxes.forEach(function (cb) { cb.checked = true; });
            if (masterCheckbox) masterCheckbox.checked = true;
            updateSelectionState();
          } else if (actionType === 'clear-all') {
            rowCheckboxes.forEach(function (cb) { cb.checked = false; });
            if (masterCheckbox) masterCheckbox.checked = false;
            updateSelectionState();
          }
          return;
        }

        var submitBtn = e.target.closest('[data-bulk-submit]');
        if (submitBtn) {
          var actionName = submitBtn.dataset.bulkSubmit;
          var actionSelect = form.querySelector('select[name="action"]');
          if (actionSelect) {
            actionSelect.value = actionName;
          } else {
            var hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'action';
            hidden.value = actionName;
            form.appendChild(hidden);
          }
          form.submit();
        }
      });

      updateSelectionState();
    }

    /* --------------------------------------------------------------------------
       3. Readiness Popover (1d)
       -------------------------------------------------------------------------- */
    function closePopover() {
      if (readinessPopover) {
        readinessPopover.hidden = true;
        activePopoverTrigger = null;
      }
    }

    document.addEventListener('click', function (e) {
      var trigger = e.target.closest('[data-readiness-trigger]');
      if (trigger) {
        e.preventDefault();
        e.stopPropagation();

        if (activePopoverTrigger === trigger && !readinessPopover.hidden) {
          closePopover();
          return;
        }

        activePopoverTrigger = trigger;
        var score = parseInt(trigger.dataset.score || '0', 10);
        var hasCoords = trigger.dataset.hasCoords === '1';
        var hasPrice = trigger.dataset.hasPrice === '1';
        var photosCount = parseInt(trigger.dataset.photosCount || '0', 10);
        var hasDesc = trigger.dataset.hasDesc === '1';
        var hasCat = trigger.dataset.hasCat === '1';
        var editUrl = trigger.dataset.editUrl || '#';

        // Count items done
        var doneCount = (hasCoords ? 1 : 0) + (hasPrice ? 1 : 0) + (photosCount >= 3 ? 1 : 0) + (hasDesc ? 1 : 0) + (hasCat ? 1 : 0);

        var scoreLabel = document.getElementById('km-pop-score-label');
        if (scoreLabel) scoreLabel.textContent = (labels.readinessLabel || 'Готовность') + ' ' + score + '%';

        var itemsCount = document.getElementById('km-pop-items-count');
        if (itemsCount) itemsCount.textContent = doneCount + ' ' + (labels.itemsLabel || 'из 5 пунктов');

        var popBar = document.getElementById('km-pop-bar');
        if (popBar) {
          popBar.style.width = score + '%';
          popBar.style.background = score < 60 ? '#A98A3C' : '#4A5750';
        }

        var editLink = document.getElementById('km-pop-edit-link');
        if (editLink) editLink.href = editUrl;

        // Update items
        var itemsConfig = [
          { key: 'coords', done: hasCoords, label: hasCoords ? 'Точка на карте есть' : 'Точка на карте — нет координат' },
          { key: 'price', done: hasPrice, label: hasPrice ? 'Цена указана' : 'Цена: «от» или тариф' },
          { key: 'photos', done: photosCount >= 3, label: photosCount >= 3 ? 'Фото: ' + photosCount : 'Фото: минимум 3' },
          { key: 'desc', done: hasDesc, label: 'Описание RU / AZ' },
          { key: 'cat', done: hasCat, label: 'Категория и подкатегория' }
        ];

        itemsConfig.forEach(function (cfg) {
          var el = readinessPopover.querySelector('[data-item="' + cfg.key + '"]');
          if (el) {
            el.classList.toggle('is-done', cfg.done);
            var icon = el.querySelector('.ms');
            if (icon) icon.textContent = cfg.done ? 'check' : 'radio_button_unchecked';
            var text = el.querySelector('span:last-child');
            if (text) text.textContent = cfg.label;
          }
        });

        // Position popover
        var rect = trigger.getBoundingClientRect();
        readinessPopover.style.position = 'fixed';
        readinessPopover.style.top = (rect.bottom + 8) + 'px';
        readinessPopover.style.left = Math.max(16, rect.left - 100) + 'px';
        readinessPopover.hidden = false;
        return;
      }

      if (readinessPopover && !readinessPopover.contains(e.target)) {
        closePopover();
      }
    });

    /* --------------------------------------------------------------------------
       4. Row Actions Menu ⋯ (1e) & Quick Actions
       -------------------------------------------------------------------------- */
    function closeRowActions() {
      if (rowActionsDropdown) {
        rowActionsDropdown.hidden = true;
        activeMoreBtn = null;
      }
    }

    function showToast(message, onUndo) {
      if (!toast || !toastText) return;
      if (toastTimer) clearTimeout(toastTimer);

      toastText.textContent = message;
      lastUndoAction = onUndo || null;
      toastUndo.hidden = !onUndo;
      toast.hidden = false;

      toastTimer = setTimeout(function () {
        toast.hidden = true;
        lastUndoAction = null;
      }, 4000);
    }

    function updatePublicationRow(button, data) {
      var row = button.closest('tr');
      if (!row) return;
      var state = row.querySelector('.km-col-state');
      var icon = row.querySelector('.km-state-visibility');
      var dot = row.querySelector('.km-state-dot');
      var label = row.querySelector('.km-state-label');
      var published = data.status === 'published' && data.is_active;
      button.dataset.status = data.status;
      button.dataset.isActive = data.is_active ? '1' : '0';
      if (state) {
        state.dataset.state = published ? 'published' : 'draft';
        state.classList.remove('km-col-state--draft', 'km-col-state--draft-incomplete', 'km-col-state--published', 'km-col-state--published-incomplete');
        state.classList.add(published ? 'km-col-state--published' : 'km-col-state--draft');
      }
      if (icon) {
        icon.textContent = published ? 'public' : 'edit_note';
        icon.classList.remove('km-state-pop');
        window.requestAnimationFrame(function () { icon.classList.add('km-state-pop'); });
      }
      if (dot) {
        dot.classList.remove('km-dot--draft');
        dot.classList.toggle('km-dot--published', published);
        if (!published) dot.classList.add('km-dot--draft');
      }
      if (label) label.textContent = published ? (labels.publishedLabel || 'Опубликовано') : (labels.draftLabel || 'Черновик');
      row.classList.remove('km-row-flash');
      window.requestAnimationFrame(function () { row.classList.add('km-row-flash'); });
    }

    if (toastUndo) {
      toastUndo.addEventListener('click', function () {
        if (typeof lastUndoAction === 'function') {
          var undoFn = lastUndoAction;
          lastUndoAction = null;
          toast.hidden = true;
          undoFn();
        }
      });
    }

    document.addEventListener('click', function (e) {
      var moreBtn = e.target.closest('[data-more-actions-btn]');
      if (moreBtn) {
        e.preventDefault();
        e.stopPropagation();

        if (activeMoreBtn === moreBtn && !rowActionsDropdown.hidden) {
          closeRowActions();
          return;
        }

        activeMoreBtn = moreBtn;
        var placeId = moreBtn.dataset.placeId;
        var status = moreBtn.dataset.status;
        var isActive = moreBtn.dataset.isActive === '1';
        var isHome = moreBtn.dataset.isHome === '1';
        var hasCoords = moreBtn.dataset.hasCoords === '1';
        var isDeleted = moreBtn.dataset.isDeleted === '1';
        var isPublished = status === 'published' && isActive;
        var viewUrl = moreBtn.dataset.viewUrl || '#';

        var pubBtn = document.getElementById('km-row-act-pub') || rowActionsDropdown.querySelector('[data-row-action="toggle_pub"]');
        var pubIcon = document.getElementById('km-row-act-pub-icon');
        var pubLabel = document.getElementById('km-row-act-pub-label');
        var viewLink = document.getElementById('km-row-act-view-link');
        var restoreBtn = document.getElementById('km-row-act-restore');
        var deleteBtn = document.getElementById('km-row-act-delete');
        var divider = document.getElementById('km-row-act-divider');

        if (pubBtn && pubIcon && pubLabel) {
          pubBtn.hidden = isDeleted;
          if (isPublished) {
            pubIcon.textContent = 'visibility_off';
            pubLabel.textContent = 'Снять с публикации';
            pubBtn.disabled = false;
            pubBtn.title = '';
            pubBtn.removeAttribute('aria-disabled');
          } else {
            var cannotPublish = !hasCoords;
            pubIcon.textContent = 'campaign';
            pubLabel.textContent = 'Опубликовать';
            pubBtn.disabled = cannotPublish;
            pubBtn.title = cannotPublish ? (labels.publishError || 'Нельзя опубликовать: заполните обязательные данные.') : '';
            pubBtn.setAttribute('aria-disabled', cannotPublish ? 'true' : 'false');
          }
        }

        if (viewLink) {
          viewLink.href = viewUrl;
          viewLink.hidden = isDeleted;
        }

        if (restoreBtn) {
          restoreBtn.hidden = !isDeleted;
        }

        if (deleteBtn) {
          deleteBtn.hidden = isDeleted;
        }

        if (divider) {
          divider.hidden = isDeleted;
        }

        var rect = moreBtn.getBoundingClientRect();
        rowActionsDropdown.style.position = 'fixed';
        rowActionsDropdown.style.top = (rect.bottom + 6) + 'px';
        rowActionsDropdown.style.left = Math.max(16, rect.right - 232) + 'px';
        rowActionsDropdown.hidden = false;
        return;
      }

      if (rowActionsDropdown && !rowActionsDropdown.contains(e.target)) {
        closeRowActions();
      }
    });

    // Handle clicks inside row actions dropdown
    if (rowActionsDropdown) {
      rowActionsDropdown.addEventListener('click', function (e) {
        var item = e.target.closest('[data-row-action]');
        if (!item || !activeMoreBtn) return;

        if (item.disabled || item.getAttribute('aria-disabled') === 'true') {
          e.preventDefault();
          item.classList.remove('km-action-shake');
          window.requestAnimationFrame(function () { item.classList.add('km-action-shake'); });
          showToast(item.title || labels.actionError || 'Действие недоступно');
          return;
        }

        e.preventDefault();
        var trigger = activeMoreBtn;
        var action = item.dataset.rowAction;
        var placeId = trigger.dataset.placeId;
        var placeName = trigger.dataset.placeName || ('Место #' + placeId);
        var togglePubUrl = trigger.dataset.togglePublicationUrl || ('/admin/catalog/place/' + placeId + '/toggle-publication/');
        var quickActionUrl = trigger.dataset.quickActionUrl || ('/admin/catalog/place/' + placeId + '/quick-action/');
        var isPublished = trigger.dataset.status === 'published' && trigger.dataset.isActive === '1';
        closeRowActions();

        function escapeHtml(str) {
          if (!str) return '';
          return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
        }

        function executeTogglePublication(unpublish) {
          var triggerIcon = trigger.querySelector('.ms');
          var previousIcon = triggerIcon ? triggerIcon.textContent : '';
          var triggerRow = trigger.closest('tr');

          trigger.disabled = true;
          trigger.setAttribute('aria-busy', 'true');
          trigger.classList.add('km-is-busy');
          if (triggerRow) triggerRow.classList.add('km-row--loading');
          if (triggerIcon) triggerIcon.textContent = 'progress_activity';

          if (typeof Swal !== 'undefined') {
            Swal.fire({
              title: unpublish ? 'Снятие с публикации...' : 'Публикация карточки...',
              html: (unpublish ? 'Снимаем карточку' : 'Проверяем и публикуем карточку') + ' <strong>«' + escapeHtml(placeName) + '»</strong>...',
              allowOutsideClick: false,
              allowEscapeKey: false,
              showConfirmButton: false,
              didOpen: function () {
                Swal.showLoading();
              }
            });
          }

          fetch(togglePubUrl, {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrftoken,
              'X-Requested-With': 'XMLHttpRequest',
              'Accept': 'application/json'
            }
          })
            .then(function (res) { return res.json(); })
            .then(function (data) {
              if (data.ok) {
                updatePublicationRow(trigger, data);
                if (typeof Swal !== 'undefined') {
                  Swal.fire({
                    icon: 'success',
                    title: unpublish ? 'Снято с публикации' : 'Успешно опубликовано!',
                    html: 'Карточка <strong>«' + escapeHtml(placeName) + '»</strong> ' + (unpublish ? 'переведена в черновики.' : 'теперь опубликована и видна на сайте.'),
                    timer: 2000,
                    timerProgressBar: true,
                    showConfirmButton: false
                  });
                } else {
                  showToast(data.message);
                }
              } else {
                trigger.classList.add('km-action-shake');
                if (typeof Swal !== 'undefined') {
                  Swal.fire({
                    icon: 'error',
                    title: 'Не удалось опубликовать',
                    text: data.message || labels.publishError || 'Нельзя опубликовать: заполните обязательные данные.',
                    confirmButtonColor: '#136F38',
                    confirmButtonText: 'Понятно'
                  });
                } else {
                  showToast(data.message || labels.publishError || 'Нельзя опубликовать: заполните обязательные данные.');
                }
              }
            })
            .catch(function () {
              if (typeof Swal !== 'undefined') {
                Swal.fire({
                  icon: 'error',
                  title: 'Ошибка соединения',
                  text: labels.toastError || 'Не удалось связаться с сервером.',
                  confirmButtonColor: '#136F38'
                });
              } else {
                showToast(labels.toastError || 'Ошибка выполнения действия');
              }
            })
            .finally(function () {
              trigger.disabled = false;
              trigger.removeAttribute('aria-busy');
              trigger.classList.remove('km-is-busy');
              if (triggerRow) triggerRow.classList.remove('km-row--loading');
              if (triggerIcon) triggerIcon.textContent = previousIcon;
            });
        }

        function executeQuickAction(act) {
          var body = new URLSearchParams();
          body.append('action', act);

          if (typeof Swal !== 'undefined') {
            Swal.fire({
              title: 'Выполняется...',
              allowOutsideClick: false,
              allowEscapeKey: false,
              showConfirmButton: false,
              didOpen: function () {
                Swal.showLoading();
              }
            });
          }

          fetch(quickActionUrl, {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrftoken,
              'X-Requested-With': 'XMLHttpRequest',
              'Accept': 'application/json'
            },
            body: body
          })
            .then(function (res) { return res.json(); })
            .then(function (data) {
              if (data.ok) {
                if (typeof Swal !== 'undefined') {
                  Swal.fire({
                    icon: 'success',
                    title: data.message || 'Готово',
                    timer: 1400,
                    showConfirmButton: false
                  });
                }
                setTimeout(function () { window.location.reload(); }, 1200);
              } else {
                if (typeof Swal !== 'undefined') {
                  Swal.fire({
                    icon: 'error',
                    title: 'Ошибка',
                    text: data.message || 'Действие недоступно',
                    confirmButtonColor: '#136F38'
                  });
                } else {
                  showToast(data.message || 'Действие недоступно');
                }
              }
            })
            .catch(function () {
              window.location.reload();
            });
        }

        if (action === 'toggle_pub') {
          if (isPublished) {
            // Confirmation modal before unpublishing
            if (typeof Swal !== 'undefined') {
              Swal.fire({
                title: 'Снять с публикации?',
                html: 'Карточка <strong>«' + escapeHtml(placeName) + '»</strong> перестанет отображаться на сайте и перейдёт в черновики.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#DC3838',
                cancelButtonColor: '#7C867F',
                confirmButtonText: 'Да, снять',
                cancelButtonText: 'Отмена',
                reverseButtons: true,
                focusCancel: true
              }).then(function (result) {
                if (result.isConfirmed) {
                  executeTogglePublication(true);
                }
              });
            } else if (window.confirm('Снять карточку «' + placeName + '» с публикации?')) {
              executeTogglePublication(true);
            }
          } else {
            // Publishing: execute directly with loader popup + success notification
            executeTogglePublication(false);
          }
          return;
        }

        if (action === 'soft_delete') {
          if (typeof Swal !== 'undefined') {
            Swal.fire({
              title: 'Переместить в удалённые?',
              html: 'Карточка <strong>«' + escapeHtml(placeName) + '»</strong> будет скрыта и перемещена в раздел «В удалённых».',
              icon: 'warning',
              showCancelButton: true,
              confirmButtonColor: '#DC3838',
              cancelButtonColor: '#7C867F',
              confirmButtonText: 'Да, удалить',
              cancelButtonText: 'Отмена',
              reverseButtons: true,
              focusCancel: true
            }).then(function (result) {
              if (result.isConfirmed) {
                executeQuickAction('soft_delete');
              }
            });
            return;
          }
        }

        // Other quick actions (e.g. restore)
        executeQuickAction(action);
      });

      var viewLink = document.getElementById('km-row-act-view-link');
      if (viewLink) {
        viewLink.addEventListener('click', function () {
          closeRowActions();
        });
      }
    }

    // Suggestions autocomplete for searchbar
    var searchBox = document.querySelector('[data-search-suggest-root]');
    if (searchBox) {
      var input = searchBox.querySelector('.km-search-input');
      var suggestionsUrl = searchBox.dataset.suggestionsUrl;
      var emptyLabel = searchBox.dataset.suggestionsEmpty || 'Ничего не найдено';
      var dropdown = searchBox.querySelector('[data-search-suggestions]');
      var timer = null;

      if (input && suggestionsUrl && dropdown) {
        input.addEventListener('input', function () {
          if (timer) clearTimeout(timer);
          var q = input.value.trim();
          if (q.length < 2) {
            dropdown.hidden = true;
            return;
          }

          timer = setTimeout(function () {
            fetch(suggestionsUrl + '?q=' + encodeURIComponent(q), {
              headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
              .then(function (res) { return res.json(); })
              .then(function (data) {
                var results = data.results || [];
                if (!results.length) {
                  dropdown.innerHTML = '<div class="place-admin-dashboard__search-suggestion-empty">' + emptyLabel + '</div>';
                } else {
                  dropdown.innerHTML = results.map(function (item) {
                    var safeVal = String(item.value || '').replace(/"/g, '&quot;');
                    var safeLabel = String(item.label || '');
                    var safeMeta = String(item.meta || '');
                    return '<button type="button" class="place-admin-dashboard__search-suggestion" data-val="' + safeVal + '">' +
                      '<span class="place-admin-dashboard__search-suggestion-title">' + safeLabel + '</span>' +
                      (safeMeta ? '<span class="place-admin-dashboard__search-suggestion-meta">' + safeMeta + '</span>' : '') +
                      '</button>';
                  }).join('');
                }
                dropdown.hidden = false;
              });
          }, 150);
        });

        dropdown.addEventListener('click', function (e) {
          var item = e.target.closest('[data-val]');
          if (item) {
            input.value = item.dataset.val;
            dropdown.hidden = true;
            form.submit();
          }
        });

        document.addEventListener('click', function (e) {
          if (!searchBox.contains(e.target)) {
            dropdown.hidden = true;
          }
        });
      }
    }

    /* --------------------------------------------------------------------------
       8. Column Visibility Toggler (1a)
       -------------------------------------------------------------------------- */
    var columnCheckboxes = Array.prototype.slice.call(document.querySelectorAll('[data-toggle-col]'));
    if (columnCheckboxes.length) {
      var savedHidden = [];
      try {
        savedHidden = JSON.parse(localStorage.getItem('km_hidden_columns') || '[]');
      } catch (err) {
        savedHidden = [];
      }

      function applyColumnVisibility(colName, isVisible) {
        var th = document.querySelector('th.' + colName);
        var fieldName = colName.replace('column-', 'field-');
        var tds = Array.prototype.slice.call(document.querySelectorAll('td.' + fieldName));

        if (th) {
          th.classList.toggle('is-hidden-column', !isVisible);
        }
        tds.forEach(function (td) {
          td.classList.toggle('is-hidden-column', !isVisible);
        });
      }

      // Restore saved preferences
      columnCheckboxes.forEach(function (cb) {
        var colName = cb.getAttribute('data-toggle-col');
        if (savedHidden.indexOf(colName) !== -1) {
          cb.checked = false;
          applyColumnVisibility(colName, false);
        }

        cb.addEventListener('change', function () {
          var isChecked = cb.checked;
          applyColumnVisibility(colName, isChecked);

          var currentHidden = [];
          columnCheckboxes.forEach(function (c) {
            if (!c.checked) {
              currentHidden.push(c.getAttribute('data-toggle-col'));
            }
          });
          try {
            localStorage.setItem('km_hidden_columns', JSON.stringify(currentHidden));
          } catch (e) {}
        });
      });
    }
  });
})();
