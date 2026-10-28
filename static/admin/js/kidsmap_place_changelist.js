(function () {

  var SVG_NS = "http://www.w3.org/2000/svg";

  /* Icons are inline SVG from the shared sprite. The Material Symbols build in
     static/fonts has no ligature table, so name-based icon text never rendered
     as a glyph. */
  function iconEl(name, className) {
    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", className ? "km-i " + className : "km-i");
    svg.setAttribute("viewBox", "0 0 960 960");
    svg.setAttribute("aria-hidden", "true");
    var use = document.createElementNS(SVG_NS, "use");
    use.setAttribute("href", "#kmi-" + name);
    svg.appendChild(use);
    return svg;
  }

  function setIcon(node, name) {
    if (!node) return;
    var use = node.tagName && String(node.tagName).toLowerCase() === "use" ? node : node.querySelector("use");
    if (use) use.setAttribute("href", "#kmi-" + name);
  }
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

    // Row menus must escape table clipping and remain inside the viewport.
    var rowMenuAnchors = new WeakMap();
    function positionRowMenu(panel, trigger) {
      var margin = 12;
      var rect = trigger.getBoundingClientRect();
      rowMenuAnchors.set(panel, {trigger: trigger, left: rect.left, top: rect.top});
      panel.hidden = false;
      panel.style.setProperty('position', 'fixed', 'important');
      panel.style.setProperty('right', 'auto', 'important');
      panel.style.setProperty('max-width', (window.innerWidth - margin * 2) + 'px', 'important');
      panel.style.setProperty('max-height', (window.innerHeight - margin * 2) + 'px', 'important');
      panel.style.setProperty('overflow-y', 'auto');
      var size = panel.getBoundingClientRect();
      var top = rect.bottom + 6;
      if (top + size.height > window.innerHeight - margin) top = rect.top - size.height - 6;
      top = Math.max(margin, Math.min(top, window.innerHeight - size.height - margin));
      var left = Math.max(margin, Math.min(rect.right - size.width, window.innerWidth - size.width - margin));
      panel.style.setProperty('top', top + 'px', 'important');
      panel.style.setProperty('left', left + 'px', 'important');
    }

    var portaledActionMenu = null;
    function closePortaledActionMenu(restoreFocus) {
      if (!portaledActionMenu) return;
      var current = portaledActionMenu;
      portaledActionMenu = null;
      current.details.open = false;
      current.details.appendChild(current.panel);
      if (current.style === null) current.panel.removeAttribute('style');
      else current.panel.setAttribute('style', current.style);
      if (restoreFocus) current.trigger.focus({preventScroll: true});
    }

    document.addEventListener('toggle', function (event) {
      var details = event.target;
      if (!details.matches || !details.matches('details.km-admin-action-menu') || !details.closest('.km-event-changelist')) return;
      if (!details.open) {
        if (portaledActionMenu && portaledActionMenu.details === details) closePortaledActionMenu(false);
        return;
      }
      if (portaledActionMenu && portaledActionMenu.details === details) return;
      closePortaledActionMenu(false);
      var panel = details.querySelector('.km-admin-action-menu__panel');
      var trigger = details.querySelector('summary');
      if (!panel || !trigger) return;
      portaledActionMenu = { details: details, panel: panel, trigger: trigger, style: panel.getAttribute('style') };
      document.body.appendChild(panel);
      positionRowMenu(panel, trigger);
      var firstLink = panel.querySelector('a[href], button:not([disabled])');
      if (firstLink) firstLink.focus({preventScroll: true});
    }, true);

    document.addEventListener('click', function (event) {
      if (portaledActionMenu && !portaledActionMenu.panel.contains(event.target) && !portaledActionMenu.trigger.contains(event.target)) closePortaledActionMenu(false);
    });
    document.addEventListener('focusin', function (event) {
      if (portaledActionMenu && !portaledActionMenu.panel.contains(event.target) && !portaledActionMenu.trigger.contains(event.target)) closePortaledActionMenu(false);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') return;
      if (portaledActionMenu) {
        event.preventDefault();
        closePortaledActionMenu(true);
      }
      if (activeMoreBtn && rowActionsDropdown && !rowActionsDropdown.hidden) {
        event.preventDefault();
        var trigger = activeMoreBtn;
        closeRowActions();
        trigger.focus({preventScroll: true});
      }
    });
    function unchangedAnchorScroll(panel, event) {
      if (!event || event.type !== 'scroll') return false;
      var anchor = rowMenuAnchors.get(panel);
      if (!anchor) return false;
      var rect = anchor.trigger.getBoundingClientRect();
      return Math.abs(rect.left - anchor.left) < 0.5 && Math.abs(rect.top - anchor.top) < 0.5;
    }
    function dismissRowMenus(event) {
      if (portaledActionMenu && !unchangedAnchorScroll(portaledActionMenu.panel, event) && (!event || !(event.target instanceof Node) || !portaledActionMenu.panel.contains(event.target))) closePortaledActionMenu(false);
      if (rowActionsDropdown && !rowActionsDropdown.hidden && !unchangedAnchorScroll(rowActionsDropdown, event) && (!event || !(event.target instanceof Node) || !rowActionsDropdown.contains(event.target))) closeRowActions();
    }
    window.addEventListener('resize', dismissRowMenus);
    window.addEventListener('scroll', dismissRowMenus, true);

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
          if (submitBtn.dataset.confirm) {
            var count = form.querySelectorAll('tbody input.action-select:checked').length;
            var confirmMsg = submitBtn.dataset.confirm.replace('{count}', count);
            if (!window.confirm(confirmMsg)) {
              return;
            }
          }
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
       2b. Quick Review Actions (1-click Approve / Reject / Hide)
       -------------------------------------------------------------------------- */
    document.addEventListener('click', function (e) {
      var reviewActionBtn = e.target.closest('[data-review-action]');
      if (!reviewActionBtn) return;

      var action = reviewActionBtn.getAttribute('data-review-action');
      var reviewId = reviewActionBtn.getAttribute('data-review-id');
      if (!action || !reviewId) return;

      if (action === 'approve_selected' || action === 'reject_selected' || action === 'hide_selected') {
        var form = document.getElementById('changelist-form');
        if (!form) return;

        var targetCb = form.querySelector('tbody input.action-select[value="' + reviewId + '"]');
        if (!targetCb) return;

        if (action === 'reject_selected') {
          if (!window.confirm('Вы уверены, что хотите отклонить этот отзыв?')) {
            return;
          }
        } else if (action === 'hide_selected') {
          if (!window.confirm('Вы уверены, что хотите скрыть этот отзыв с сайта?')) {
            return;
          }
        }

        e.preventDefault();

        var allCheckboxes = form.querySelectorAll('tbody input.action-select');
        Array.prototype.slice.call(allCheckboxes).forEach(function (cb) {
          cb.checked = false;
        });

        targetCb.checked = true;

        var actionSelect = form.querySelector('select[name="action"]');
        if (actionSelect) {
          actionSelect.value = action;
        } else {
          var hidden = document.createElement('input');
          hidden.type = 'hidden';
          hidden.name = 'action';
          hidden.value = action;
          form.appendChild(hidden);
        }

        form.submit();
      }
    });

    /* --------------------------------------------------------------------------
       2c. Quick Specialist Actions (1-click Publish / Reject / Draft)
       -------------------------------------------------------------------------- */
    document.addEventListener('click', function (e) {
      var specActionBtn = e.target.closest('[data-specialist-action]');
      if (!specActionBtn) return;

      var action = specActionBtn.getAttribute('data-specialist-action');
      var specId = specActionBtn.getAttribute('data-specialist-id');
      if (!action || !specId) return;

      if (action === 'mark_published' || action === 'mark_rejected' || action === 'mark_draft') {
        var form = document.getElementById('changelist-form');
        if (!form) return;

        var targetCb = form.querySelector('tbody input.action-select[value="' + specId + '"]');
        if (!targetCb) return;

        if (action === 'mark_rejected') {
          if (!window.confirm('Отклонить профиль этого специалиста?')) {
            return;
          }
        } else if (action === 'mark_draft') {
          if (!window.confirm('Снять этого специалиста с публикации и перевести в черновик?')) {
            return;
          }
        }

        e.preventDefault();

        var allCheckboxes = form.querySelectorAll('tbody input.action-select');
        Array.prototype.slice.call(allCheckboxes).forEach(function (cb) {
          cb.checked = false;
        });

        targetCb.checked = true;

        var actionSelect = form.querySelector('select[name="action"]');
        if (actionSelect) {
          actionSelect.value = action;
        } else {
          var hidden = document.createElement('input');
          hidden.type = 'hidden';
          hidden.name = 'action';
          hidden.value = action;
          form.appendChild(hidden);
        }

        form.submit();
      }
    });

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
        var editUrl = trigger.dataset.editUrl || '#';
        var total = parseInt(trigger.dataset.total || '0', 10);
        var done = parseInt(trigger.dataset.done || '0', 10);

        // The twelve items come straight from catalog.services.place_readiness
        // via the row payload. The popover never decides completion itself, so
        // it can never disagree with the edit form or the publish gate.
        var items = [];
        try {
          items = JSON.parse(trigger.dataset.readiness || '[]');
        } catch (err) {
          items = [];
        }
        if (!Array.isArray(items)) items = [];

        var scoreLabel = document.getElementById('km-pop-score-label');
        if (scoreLabel) scoreLabel.textContent = (labels.readinessLabel || 'Готовность') + ' ' + score + '%';

        var itemsCount = document.getElementById('km-pop-items-count');
        if (itemsCount) {
          itemsCount.textContent = done + ' / ' + total + ' ' + (labels.itemsLabel || 'пунктов');
        }

        var popBar = document.getElementById('km-pop-bar');
        if (popBar) {
          popBar.style.width = score + '%';
          popBar.style.background = done >= total ? '#136F38' : (score < 60 ? '#A98A3C' : '#136F38');
        }

        var editLink = document.getElementById('km-pop-edit-link');
        if (editLink) editLink.href = editUrl;

        var list = document.getElementById('km-pop-list');
        if (list) {
          list.textContent = '';
          // Missing items first: the popover exists to answer "what is left?".
          items.slice().sort(function (a, b) {
            return (a.done === b.done) ? 0 : (a.done ? 1 : -1);
          }).forEach(function (item) {
            var anchor = String(item.anchor || '');
            var hash = anchor && anchor.charAt(0) !== '[' && anchor.charAt(0) !== '.'
              ? '#' + anchor
              : '#' + (item.section || '');

            var row = document.createElement('a');
            row.className = 'km-readiness-popover__item' + (item.done ? ' is-done' : '');
            row.href = editUrl + hash;
            row.dataset.item = item.code;

            var icon = iconEl(item.done ? 'check' : 'radio_button_unchecked', 'km-pop-icon');

            var text = document.createElement('span');
            text.className = 'km-pop-text';
            text.textContent = item.label;
            if (!item.done && item.message) {
              var hint = document.createElement('small');
              hint.className = 'km-pop-hint';
              hint.textContent = item.message;
              text.appendChild(hint);
            }

            var arrow = iconEl('arrow_forward', 'km-readiness-popover__item-arrow');

            row.append(icon, text, arrow);
            list.appendChild(row);
          });

          if (done >= total && total > 0) {
            var allDone = document.createElement('p');
            allDone.className = 'km-pop-alldone';
            allDone.textContent = labels.allDoneLabel || 'Все обязательные пункты заполнены';
            list.insertBefore(allDone, list.firstChild);
          }
        }

        // Position it: measure first, then flip above the row when the full
        // twelve-item list would run off the bottom of the viewport.
        readinessPopover.style.position = 'fixed';
        readinessPopover.style.visibility = 'hidden';
        readinessPopover.hidden = false;

        var rect = trigger.getBoundingClientRect();
        var size = readinessPopover.getBoundingClientRect();
        var margin = 12;
        var top = rect.bottom + 8;
        if (top + size.height > window.innerHeight - margin) {
          var above = rect.top - size.height - 8;
          top = above >= margin ? above : Math.max(margin, window.innerHeight - size.height - margin);
        }
        var left = rect.left - 100;
        left = Math.min(Math.max(margin, left), window.innerWidth - size.width - margin);

        readinessPopover.style.top = top + 'px';
        readinessPopover.style.left = left + 'px';
        readinessPopover.style.visibility = '';
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
            setIcon(pubIcon, "visibility_off");
            pubLabel.textContent = 'Снять с публикации';
            pubBtn.disabled = moreBtn.dataset.canTogglePublication !== '1';
            pubBtn.title = pubBtn.disabled ? (moreBtn.dataset.publicationReason || '') : '';
            pubBtn.setAttribute('aria-disabled', pubBtn.disabled ? 'true' : 'false');
          } else {
            var cannotPublish = moreBtn.dataset.canTogglePublication !== '1';
            setIcon(pubIcon, "campaign");
            pubLabel.textContent = 'Опубликовать';
            pubBtn.disabled = cannotPublish;
            pubBtn.title = cannotPublish ? (moreBtn.dataset.publicationReason || labels.publishError || 'Нельзя опубликовать: заполните обязательные данные.') : '';
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

        positionRowMenu(rowActionsDropdown, moreBtn);
        var firstAction = rowActionsDropdown.querySelector('button:not([hidden]):not([disabled]), a[href]:not([hidden])');
        if (firstAction) firstAction.focus({preventScroll: true});
        return;
      }

      if (rowActionsDropdown && !rowActionsDropdown.contains(e.target)) {
        closeRowActions();
      }
    });

    // Handle clicks inside row actions dropdown
    if (rowActionsDropdown) {
      function handleRowAction(e) {
        var direct = e.target.closest('[data-publication-action]');
        var item = direct || e.target.closest('[data-row-action]');
        if (!item || (!direct && !activeMoreBtn)) return;

        if (item.disabled || item.getAttribute('aria-disabled') === 'true') {
          e.preventDefault();
          item.classList.remove('km-action-shake');
          window.requestAnimationFrame(function () { item.classList.add('km-action-shake'); });
          showToast(item.title || labels.actionError || 'Действие недоступно');
          return;
        }

        e.preventDefault();
        var trigger = direct || activeMoreBtn;
        if (trigger.disabled || trigger.getAttribute('aria-busy') === 'true') return;
        var action = direct ? direct.dataset.publicationAction : item.dataset.rowAction;
        var placeId = trigger.dataset.placeId;
        var placeName = trigger.dataset.placeName || ('Место #' + placeId);
        var togglePubUrl = trigger.dataset.togglePublicationUrl || ('/admin/catalog/place/' + placeId + '/toggle-publication/');
        var quickActionUrl = trigger.dataset.quickActionUrl || ('/admin/catalog/place/' + placeId + '/quick-action/');
        var isPublished = trigger.dataset.status === 'published' && trigger.dataset.isActive === '1';
        closeRowActions();
        trigger.focus({preventScroll: true});

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
          if (triggerIcon) setIcon(triggerIcon, "progress_activity");

          var _loadingToast = window.kmToast
            ? window.kmToast.info(unpublish ? (labels.publicationUnpublishLoading || 'Снятие с публикации...') : (labels.publicationPublishLoading || 'Публикация карточки...'), { duration: 0 })
            : null;

          var publicationCommitted = false;
          fetch(togglePubUrl, {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrftoken,
              'X-Requested-With': 'XMLHttpRequest',
              'Accept': 'application/json'
            },
            body: new URLSearchParams({intent: unpublish ? 'unpublish' : 'publish'})
          })
            .then(function (res) { return res.json(); })
            .then(function (data) {
              if (_loadingToast && window.kmToast) window.kmToast.dismiss(_loadingToast);
              if (data.ok) {
                publicationCommitted = true;
                // Reload the current filter so counts, visibility, readiness and actions
                // all come from the committed server state.
                window.setTimeout(function () { window.location.reload(); }, 350);
                if (window.kmToast) {
                  if (unpublish) {
                    window.kmToast.warning((labels.publicationUnpublishSuccess || '«%(name)s» переведена в черновики.').replace('%(name)s', function () { return placeName; }));
                  } else {
                    window.kmToast.success((labels.publicationPublishSuccess || '«%(name)s» опубликована и видна на сайте.').replace('%(name)s', function () { return placeName; }));
                  }
                } else {
                  showToast(data.message);
                }
              } else {
                trigger.classList.add('km-action-shake');
                if (window.kmToast) {
                  window.kmToast.error(data.message || labels.publishError || 'Нельзя опубликовать: заполните обязательные данные.');
                } else {
                  showToast(data.message || labels.publishError || 'Нельзя опубликовать: заполните обязательные данные.');
                }
              }
            })
            .catch(function () {
              if (_loadingToast && window.kmToast) window.kmToast.dismiss(_loadingToast);
              if (window.kmToast) {
                window.kmToast.error(labels.toastError || 'Не удалось связаться с сервером.');
              } else {
                showToast(labels.toastError || 'Ошибка выполнения действия');
              }
            })
            .finally(function () {
              if (publicationCommitted) return;
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

          var _quickToast = window.kmToast
            ? window.kmToast.info('Выполняется...', { duration: 0 })
            : null;

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
              if (_quickToast && window.kmToast) window.kmToast.dismiss(_quickToast);
              if (data.ok) {
                if (window.kmToast) {
                  window.kmToast.success(data.message || 'Готово');
                }
                setTimeout(function () { window.location.reload(); }, 1200);
              } else {
                if (window.kmToast) {
                  window.kmToast.error(data.message || 'Действие недоступно');
                } else {
                  showToast(data.message || 'Действие недоступно');
                }
              }
            })
            .catch(function () {
              if (_quickToast && window.kmToast) window.kmToast.dismiss(_quickToast);
              window.location.reload();
            });
        }

        if (action === 'toggle_pub') {
          if (isPublished) {
            // Confirmation modal before unpublishing
            if (window.kmModal) {
              window.kmModal.confirm({
                title: labels.unpublishTitle || 'Снять с публикации?',
                message: (labels.unpublishMessage || 'Карточка «%(name)s» перестанет отображаться на сайте и перейдёт в черновики.').replace('%(name)s', function () { return placeName; }),
                iconTone: 'warning',
                confirmText: labels.unpublishConfirm || 'Да, снять',
                cancelText: labels.unpublishCancel || 'Отмена',
                isAlertDialog: true
              }).then(function (confirmed) {
                if (confirmed) {
                  executeTogglePublication(true);
                }
              });
            } else if (window.confirm((labels.unpublishFallback || 'Снять карточку «%(name)s» с публикации?').replace('%(name)s', function () { return placeName; }))) {
              executeTogglePublication(true);
            }
          } else {
            // Publishing: execute directly with loader popup + success notification
            executeTogglePublication(false);
          }
          return;
        }

        if (action === 'soft_delete') {
          if (window.kmModal) {
            window.kmModal.confirm({
              title: 'Переместить в удалённые?',
              message: 'Карточка «' + placeName + '» будет скрыта и перемещена в раздел «В удалённых».',
              iconTone: 'danger',
              confirmText: 'Да, удалить',
              cancelText: 'Отмена',
              isAlertDialog: true
            }).then(function (confirmed) {
              if (confirmed) {
                executeQuickAction('soft_delete');
              }
            });
          } else {
            executeQuickAction('soft_delete');
          }
          return;
        }

        // Other quick actions (e.g. restore)
        executeQuickAction(action);
      }
      rowActionsDropdown.addEventListener('click', handleRowAction);
      document.addEventListener('click', function (event) {
        if (event.target.closest('[data-publication-action]')) handleRowAction(event);
      });

      var viewLink = document.getElementById('km-row-act-view-link');
      if (viewLink) {
        viewLink.addEventListener('click', function () {
          closeRowActions();
        });
      }
    }

    // --------------------------------------------------------------------------
    // Suggestions autocomplete for searchbar (Changelist & Global)
    // --------------------------------------------------------------------------
    function escapeSuggestHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function highlightSuggestMatch(text, query) {
      if (!text || !query) return escapeSuggestHtml(text || '');
      var escapedText = escapeSuggestHtml(text);
      var safeQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      var regex = new RegExp('(' + safeQuery + ')', 'gi');
      return escapedText.replace(regex, '<mark class="km-search-highlight">$1</mark>');
    }

    var searchBoxes = document.querySelectorAll('[data-search-suggest-root]');
    searchBoxes.forEach(function (searchBox) {
      if (searchBox.dataset.suggestBound === 'true') return;
      searchBox.dataset.suggestBound = 'true';
      var input = searchBox.querySelector('.km-search-input');
      var suggestionsUrl = searchBox.dataset.suggestionsUrl;
      var emptyLabel = searchBox.dataset.suggestionsEmpty || 'Ничего не найдено';
      var dropdown = searchBox.querySelector('[data-search-suggestions]');
      var timer = null;
      var activeIndex = -1;

      if (!input || !suggestionsUrl || !dropdown) return;

      var parentForm = input.closest('form') || form;

      function updateActiveItem(items) {
        items.forEach(function (el, idx) {
          el.classList.toggle('is-selected', idx === activeIndex);
          el.setAttribute('aria-selected', idx === activeIndex ? 'true' : 'false');
        });
        if (activeIndex >= 0 && items[activeIndex]) {
          items[activeIndex].scrollIntoView({ block: 'nearest' });
        }
      }

      function selectItem(item) {
        if (!item) return;
        input.value = item.dataset.val || '';
        dropdown.hidden = true;
        activeIndex = -1;
        if (parentForm) {
          parentForm.submit();
        }
      }

      input.addEventListener('input', function () {
        if (timer) clearTimeout(timer);
        var q = input.value.trim();
        if (q.length < 2) {
          dropdown.hidden = true;
          dropdown.innerHTML = '';
          activeIndex = -1;
          return;
        }

        timer = setTimeout(function () {
          fetch(suggestionsUrl + '?q=' + encodeURIComponent(q), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
          })
            .then(function (res) { return res.json(); })
            .then(function (data) {
              var results = data.results || [];
              var suggestLabels = data.labels || {};
              activeIndex = -1;
              if (!results.length) {
                dropdown.innerHTML = '<div class="place-admin-dashboard__search-suggestion-empty km-search-suggest-empty">' +
                  '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true" focusable="false"><use href="#kmi-search"></use></svg>' +
                  '<span>' + escapeSuggestHtml(emptyLabel) + '</span>' +
                  '</div>';
              } else {
                var itemsHtml = results.map(function (item) {
                  var safeVal = escapeSuggestHtml(item.value || item.label || '');
                  var safeLabel = item.label || item.value || '';
                  var highlightedTitle = highlightSuggestMatch(safeLabel, q);
                  var safeChangeUrl = item.change_url ? escapeSuggestHtml(item.change_url) : '';
                  var safeCategory = item.category ? escapeSuggestHtml(item.category) : '';
                  var safeStatusLabel = item.status_label ? escapeSuggestHtml(item.status_label) : '';
                  var safeStatusTone = item.status_tone ? escapeSuggestHtml(item.status_tone) : 'muted';
                  var safeDistrict = item.district ? escapeSuggestHtml(item.district) : '';
                  var safeAddress = item.address ? escapeSuggestHtml(item.address) : '';
                  var safePhone = item.phone ? escapeSuggestHtml(item.phone) : '';
                  var safeOwner = item.owner ? escapeSuggestHtml(item.owner) : '';
                  var safeMeta = escapeSuggestHtml(item.meta || '');

                  var badgeHtml = safeStatusLabel
                    ? '<span class="km-search-suggest-badge km-search-suggest-badge--' + safeStatusTone + '">' + safeStatusLabel + '</span>'
                    : '';

                  var categoryHtml = safeCategory
                    ? '<span class="km-search-suggest-cat">' + safeCategory + '</span>'
                    : '';

                  var metaPartsHtml = '';
                  var locText = safeDistrict ? (safeDistrict + (safeAddress ? ', ' + safeAddress : '')) : safeAddress;
                  if (locText) {
                    metaPartsHtml += '<span class="km-search-suggest-loc"><svg class="km-i" viewBox="0 0 960 960" aria-hidden="true" focusable="false"><use href="#kmi-place"></use></svg>' + locText + '</span>';
                  }
                  if (safePhone) {
                    metaPartsHtml += '<span class="km-search-suggest-phone"><svg class="km-i" viewBox="0 0 960 960" aria-hidden="true" focusable="false"><use href="#kmi-call"></use></svg>' + safePhone + '</span>';
                  }
                  if (safeOwner) {
                    metaPartsHtml += '<span class="km-search-suggest-owner"><svg class="km-i" viewBox="0 0 960 960" aria-hidden="true" focusable="false"><use href="#kmi-person"></use></svg>' + safeOwner + '</span>';
                  }
                  if (!metaPartsHtml && safeMeta) {
                    metaPartsHtml = '<span class="km-search-suggest-meta-raw">' + safeMeta + '</span>';
                  }

                  return '<div class="place-admin-dashboard__search-suggestion km-search-suggest-item" role="option" data-val="' + safeVal + '" data-url="' + safeChangeUrl + '">' +
                    '<div class="km-search-suggest-item__main">' +
                      '<div class="km-search-suggest-item__head">' +
                        '<span class="place-admin-dashboard__search-suggestion-title km-search-suggest-item__title">' + highlightedTitle + '</span>' +
                        badgeHtml +
                        categoryHtml +
                      '</div>' +
                      '<div class="place-admin-dashboard__search-suggestion-meta km-search-suggest-item__meta">' +
                        metaPartsHtml +
                      '</div>' +
                    '</div>' +
                    (safeChangeUrl ? '<div class="km-search-suggest-item__actions">' +
                      '<a href="' + safeChangeUrl + '" class="km-search-suggest-btn" title="' + escapeSuggestHtml(suggestLabels.edit || '') + '" aria-label="' + escapeSuggestHtml(suggestLabels.edit || '') + '">' +
                        '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true" focusable="false"><use href="#kmi-edit"></use></svg>' +
                      '</a>' +
                    '</div>' : '') +
                  '</div>';
                }).join('');

                var footerHtml = '<div class="km-search-suggest-footer">' +
                  '<span aria-hidden="true">↑ ↓ · Enter</span>' +
                  '<span class="km-search-suggest-count">' + escapeSuggestHtml(suggestLabels.found || '') + ': ' + results.length + '</span>' +
                '</div>';

                dropdown.innerHTML = itemsHtml + footerHtml;
              }
              dropdown.hidden = false;
            })
            .catch(function () {
              dropdown.hidden = true;
            });
        }, 120);
      });

      input.addEventListener('keydown', function (e) {
        if (dropdown.hidden) return;
        var items = dropdown.querySelectorAll('.km-search-suggest-item');
        if (!items.length) return;

        if (e.key === 'ArrowDown') {
          e.preventDefault();
          activeIndex = Math.min(activeIndex + 1, items.length - 1);
          updateActiveItem(items);
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          activeIndex = Math.max(activeIndex - 1, 0);
          updateActiveItem(items);
        } else if (e.key === 'Enter' && activeIndex >= 0 && items[activeIndex]) {
          e.preventDefault();
          selectItem(items[activeIndex]);
        } else if (e.key === 'Escape') {
          dropdown.hidden = true;
          activeIndex = -1;
        }
      });

      dropdown.addEventListener('click', function (e) {
        if (e.target.closest('.km-search-suggest-btn')) return;
        var item = e.target.closest('[data-val]');
        if (item) {
          selectItem(item);
        }
      });

      document.addEventListener('click', function (e) {
        if (!searchBox.contains(e.target)) {
          dropdown.hidden = true;
          activeIndex = -1;
        }
      });
    });

    /* --------------------------------------------------------------------------
       8. Column Visibility Toggler (1a)
       -------------------------------------------------------------------------- */
    var columnCheckboxes = Array.prototype.slice.call(document.querySelectorAll('[data-toggle-col]'));
    var columnsMenu = document.getElementById('km-columns-menu');
    var columnsTable = document.getElementById('result_list');
    if (columnCheckboxes.length && columnsMenu && columnsTable && columnsTable.tHead) {
      var storageKey = columnsMenu.getAttribute('data-storage-key') || 'km_hidden_columns';
      var savedHidden;
      try {
        var savedColumns = localStorage.getItem(storageKey);
        savedHidden = savedColumns ? JSON.parse(savedColumns) :
          (document.body.classList.contains('km-organization-changelist') ? ['column-programs_count_badge', 'column-display_phone'] : []);
        if (!Array.isArray(savedHidden)) savedHidden = [];
      } catch (err) {
        savedHidden = [];
      }

      var validColumns = columnCheckboxes.filter(function (cb) {
        var index = Number(cb.getAttribute('data-column-index'));
        return Number.isInteger(index) && index >= 0 &&
          columnsTable.tHead.rows[0].cells[index];
      });

      function applyColumnVisibility(cb) {
        var index = Number(cb.getAttribute('data-column-index'));
        Array.prototype.forEach.call(columnsTable.rows, function (row) {
          if (row.cells[index]) {
            row.cells[index].classList.toggle('is-hidden-column', !cb.checked);
          }
        });
      }

      // Restore saved preferences
      validColumns.forEach(function (cb) {
        cb.checked = cb.disabled || savedHidden.indexOf(cb.getAttribute('data-toggle-col')) === -1;
        applyColumnVisibility(cb);

        cb.addEventListener('change', function () {
          if (cb.disabled) cb.checked = true;
          applyColumnVisibility(cb);

          var currentHidden = validColumns.filter(function (c) {
            return !c.disabled && !c.checked;
          }).map(function (c) {
            return c.getAttribute('data-toggle-col');
          });
          try {
            localStorage.setItem(storageKey, JSON.stringify(currentHidden));
          } catch (e) {}
        });
      });
    }

    /* --------------------------------------------------------------------------
       Click outside to close open details menus (sort, columns)
       -------------------------------------------------------------------------- */
    document.addEventListener('click', function (e) {
      var sortMenu = document.getElementById('km-sort-menu');
      if (sortMenu && sortMenu.open && !sortMenu.contains(e.target)) {
        sortMenu.removeAttribute('open');
      }
      var columnsMenu = document.getElementById('km-columns-menu');
      if (columnsMenu && columnsMenu.open && !columnsMenu.contains(e.target)) {
        columnsMenu.removeAttribute('open');
      }
    });
  });
})();
