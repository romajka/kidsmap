/**
 * KidsMap - Site Registered Users Management
 * Modern UX/UI interactions, mass actions, filter drawer, column toggles
 */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', initUsersDashboard);

  function initUsersDashboard() {
    normalizeTableHeaders();
    initBulkActions();
    initFiltersDrawer();
    initColumnVisibility();
    initQuickToggleActive();
    initDropdownAutoClose();
  }

  function normalizeTableHeaders() {
    var table = document.getElementById('result_list');
    if (!table) return;
    var colMap = [
      'action-checkbox',
      'user_profile_card',
      'user_phone',
      'user_gender',
      'user_status',
      'user_date_joined',
      'user_last_login',
      'user_activity',
      'user_actions'
    ];
    var ths = table.querySelectorAll('thead th');
    for (var i = 0; i < ths.length && i < colMap.length; i++) {
      ths[i].classList.add('column-' + colMap[i]);
    }
  }

  /* --------------------------------------------------------------------------
     1. Bulk Actions & Floating Bar
     -------------------------------------------------------------------------- */
  function initBulkActions() {
    var bulkBar = document.getElementById('km-users-bulk-bar');
    var countElem = document.getElementById('km-users-bulk-count');
    var clearBtn = document.getElementById('km-users-bulk-clear');
    var table = document.getElementById('result_list');
    var changelistForm = document.getElementById('changelist-form');
    var masterCheckbox = document.getElementById('action-toggle');

    if (!bulkBar || !table) return;

    function getSelectedCheckboxes() {
      return table.querySelectorAll('tbody input.action-select:checked');
    }

    function getAllCheckboxes() {
      return table.querySelectorAll('tbody input.action-select');
    }

    function updateBulkState() {
      var selected = getSelectedCheckboxes();
      var count = selected.length;

      if (countElem) {
        countElem.textContent = count;
      }

      if (count > 0) {
        bulkBar.classList.add('is-visible');
        bulkBar.setAttribute('aria-hidden', 'false');
      } else {
        bulkBar.classList.remove('is-visible');
        bulkBar.setAttribute('aria-hidden', 'true');
      }

      // Update row selection styling
      var all = getAllCheckboxes();
      for (var i = 0; i < all.length; i++) {
        var tr = all[i].closest('tr');
        if (tr) {
          if (all[i].checked) {
            tr.classList.add('selected');
          } else {
            tr.classList.remove('selected');
          }
        }
      }
    }

    // Listen to changes in table
    table.addEventListener('change', function (e) {
      if (e.target.classList.contains('action-select') || e.target === masterCheckbox) {
        setTimeout(updateBulkState, 10);
      }
    });

    // Clear selection
    if (clearBtn) {
      clearBtn.addEventListener('click', function (e) {
        e.preventDefault();
        var all = getAllCheckboxes();
        for (var i = 0; i < all.length; i++) {
          all[i].checked = false;
        }
        if (masterCheckbox) masterCheckbox.checked = false;
        updateBulkState();
      });
    }

    // Handle bulk action submissions
    var actionButtons = bulkBar.querySelectorAll('[data-bulk-action]');
    for (var i = 0; i < actionButtons.length; i++) {
      actionButtons[i].addEventListener('click', function (e) {
        e.preventDefault();
        var actionName = this.getAttribute('data-bulk-action');
        var count = getSelectedCheckboxes().length;

        if (count === 0) return;

        if (actionName === 'deactivate_users') {
          showConfirmationModal({
            title: 'Деактивировать выбранных пользователей?',
            desc: 'Выбрано: ' + count + '. Пользователи больше не смогут входить в аккаунты.',
            confirmText: 'Деактивировать',
            isDanger: true,
            onConfirm: function () {
              submitNativeAction(actionName);
            }
          });
        } else if (actionName === 'delete_selected') {
          showConfirmationModal({
            title: 'Удалить выбранных пользователей?',
            desc: 'Выбрано: ' + count + '. Это действие удалит пользователей без возможности восстановления.',
            confirmText: 'Удалить',
            isDanger: true,
            onConfirm: function () {
              submitNativeAction(actionName);
            }
          });
        } else {
          submitNativeAction(actionName);
        }
      });
    }

    function submitNativeAction(actionName) {
      if (!changelistForm) return;

      var actionSelect = changelistForm.querySelector('select[name="action"]');
      if (!actionSelect) {
        // Create hidden input if select not found
        var hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'action';
        hidden.value = actionName;
        changelistForm.appendChild(hidden);
      } else {
        actionSelect.value = actionName;
      }

      changelistForm.submit();
    }

    // Initial state
    updateBulkState();
  }

  /* --------------------------------------------------------------------------
     2. Confirmation Modal System
     -------------------------------------------------------------------------- */
  function showConfirmationModal(options) {
    var modalBackdrop = document.getElementById('km-users-confirm-modal');
    var modalTitle = document.getElementById('km-users-modal-title');
    var modalDesc = document.getElementById('km-users-modal-desc');
    var cancelBtn = document.getElementById('km-users-modal-cancel');
    var confirmBtn = document.getElementById('km-users-modal-confirm');
    var iconBox = document.getElementById('km-users-modal-icon-box');

    if (!modalBackdrop) return;

    if (modalTitle) modalTitle.textContent = options.title || 'Подтверждение';
    if (modalDesc) modalDesc.textContent = options.desc || '';
    if (confirmBtn) {
      confirmBtn.textContent = options.confirmText || 'Подтвердить';
      if (options.isDanger) {
        confirmBtn.className = 'km-u-btn km-u-btn--danger';
        if (iconBox) iconBox.className = 'km-u-modal__icon-box km-u-modal__icon-box--danger';
      } else {
        confirmBtn.className = 'km-u-btn km-u-btn--primary';
        if (iconBox) iconBox.className = 'km-u-modal__icon-box km-u-modal__icon-box--warn';
      }
    }

    modalBackdrop.hidden = false;

    function closeModal() {
      modalBackdrop.hidden = true;
      confirmBtn.removeEventListener('click', onConfirmClick);
      cancelBtn.removeEventListener('click', closeModal);
    }

    function onConfirmClick() {
      closeModal();
      if (typeof options.onConfirm === 'function') {
        options.onConfirm();
      }
    }

    cancelBtn.addEventListener('click', closeModal);
    confirmBtn.addEventListener('click', onConfirmClick);

    modalBackdrop.addEventListener('click', function (e) {
      if (e.target === modalBackdrop) {
        closeModal();
      }
    });
  }

  /* --------------------------------------------------------------------------
     3. Filters Drawer
     -------------------------------------------------------------------------- */
  function initFiltersDrawer() {
    var toggleBtn = document.getElementById('km-users-filter-toggle');
    var drawer = document.getElementById('km-users-filter-drawer');
    var backdrop = document.getElementById('km-users-drawer-backdrop');
    var closeBtn = document.getElementById('km-users-drawer-close');

    if (!drawer || !toggleBtn) return;

    function openDrawer() {
      drawer.classList.add('is-open');
      drawer.setAttribute('aria-hidden', 'false');
      if (backdrop) backdrop.hidden = false;
      toggleBtn.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    }

    function closeDrawer() {
      drawer.classList.remove('is-open');
      drawer.setAttribute('aria-hidden', 'true');
      if (backdrop) backdrop.hidden = true;
      toggleBtn.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }

    toggleBtn.addEventListener('click', function (e) {
      e.preventDefault();
      if (drawer.classList.contains('is-open')) {
        closeDrawer();
      } else {
        openDrawer();
      }
    });

    if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
    if (backdrop) backdrop.addEventListener('click', closeDrawer);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-open')) {
        closeDrawer();
      }
    });
  }

  /* --------------------------------------------------------------------------
     4. Column Visibility (Saved in localStorage)
     -------------------------------------------------------------------------- */
  function initColumnVisibility() {
    var storageKey = 'km_site_users_columns_v1';
    var options = document.querySelectorAll('.km-u-col-option input[data-col]');
    var table = document.getElementById('result_list');

    if (!table || options.length === 0) return;

    var savedConfig = {};
    try {
      var stored = localStorage.getItem(storageKey);
      if (stored) savedConfig = JSON.parse(stored);
    } catch (err) {
      savedConfig = {};
    }

    function applyColumn(colName, isVisible) {
      var thList = table.querySelectorAll('thead th.column-' + colName);
      var tdList = table.querySelectorAll('tbody td.field-' + colName + ', tbody th.field-' + colName);

      for (var i = 0; i < thList.length; i++) {
        thList[i].style.display = isVisible ? '' : 'none';
      }
      for (var j = 0; j < tdList.length; j++) {
        tdList[j].style.display = isVisible ? '' : 'none';
      }
    }

    // Apply saved or default
    for (var i = 0; i < options.length; i++) {
      var opt = options[i];
      var col = opt.getAttribute('data-col');
      if (col in savedConfig) {
        opt.checked = savedConfig[col];
      }
      applyColumn(col, opt.checked);

      opt.addEventListener('change', function () {
        var c = this.getAttribute('data-col');
        applyColumn(c, this.checked);
        savedConfig[c] = this.checked;
        try {
          localStorage.setItem(storageKey, JSON.stringify(savedConfig));
        } catch (e) {}
      });
    }
  }

  /* --------------------------------------------------------------------------
     5. Single User Quick Toggle Active (with confirmation & live update)
     -------------------------------------------------------------------------- */
  function initQuickToggleActive() {
    document.addEventListener('click', function (e) {
      var target = e.target.closest('.js-km-toggle-active');
      if (!target) return;

      e.preventDefault();
      var url = target.getAttribute('href');
      var userId = target.getAttribute('data-user-id');
      var userName = target.getAttribute('data-user-name') || 'пользователя';
      var isActive = target.getAttribute('data-active') === '1';

      if (isActive) {
        showConfirmationModal({
          title: 'Деактивировать ' + userName + '?',
          desc: 'Пользователь больше не сможет войти в аккаунт KidsMap.',
          confirmText: 'Деактивировать',
          isDanger: true,
          onConfirm: function () {
            executeToggle(url, target, userId);
          }
        });
      } else {
        executeToggle(url, target, userId);
      }
    });

    function executeToggle(url, triggerLink, userId) {
      fetch(url, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        }
      })
        .then(function (res) {
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return res.json();
        })
        .then(function (data) {
          if (data && data.success) {
            // Find row
            var tr = triggerLink.closest('tr');
            if (tr) {
              var statusCell = tr.querySelector('.field-user_status');
              if (statusCell) {
                if (data.is_active) {
                  statusCell.innerHTML = '<span class="km-u-status km-u-status--active"><span class="km-u-status-dot" aria-hidden="true"></span><span>' + (data.status_label || 'Активен') + '</span></span>';
                } else {
                  statusCell.innerHTML = '<span class="km-u-status km-u-status--inactive"><span class="km-u-status-dot" aria-hidden="true"></span><span>' + (data.status_label || 'Неактивен') + '</span></span>';
                }
              }

              // Update link inside dropdown
              triggerLink.setAttribute('data-active', data.is_active ? '1' : '0');
              var iconUse = triggerLink.querySelector('use');
              var span = triggerLink.querySelector('span');

              if (data.is_active) {
                triggerLink.className = 'km-u-dropdown-item js-km-toggle-active is-deactivate';
                if (iconUse) iconUse.setAttribute('href', '#kmi-block');
                if (span) span.textContent = 'Деактивировать';
              } else {
                triggerLink.className = 'km-u-dropdown-item js-km-toggle-active is-activate';
                if (iconUse) iconUse.setAttribute('href', '#kmi-check_circle');
                if (span) span.textContent = 'Активировать';
              }
            }

            // Show feedback notification
            if (window.KidsMapNotifications && typeof window.KidsMapNotifications.show === 'function') {
              window.KidsMapNotifications.show({
                type: data.is_active ? 'success' : 'warning',
                message: data.message || 'Статус пользователя обновлён'
              });
            }

            // Close the details menu
            var details = triggerLink.closest('details');
            if (details) details.removeAttribute('open');
          } else {
            window.location.reload();
          }
        })
        .catch(function () {
          // Fallback to standard navigation
          window.location.href = url;
        });
    }
  }

  /* --------------------------------------------------------------------------
     6. Dropdown Auto Close on Click Outside
     -------------------------------------------------------------------------- */
  function initDropdownAutoClose() {
    document.addEventListener('click', function (e) {
      var allDetails = document.querySelectorAll('details.km-u-dropdown[open], details.km-u-dropdown-wrap[open]');
      for (var i = 0; i < allDetails.length; i++) {
        if (!allDetails[i].contains(e.target)) {
          allDetails[i].removeAttribute('open');
        }
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        var allDetails = document.querySelectorAll('details.km-u-dropdown[open], details.km-u-dropdown-wrap[open]');
        for (var i = 0; i < allDetails.length; i++) {
          allDetails[i].removeAttribute('open');
        }
      }
    });
  }

})();
