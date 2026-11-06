// Home page section behaviour, moved out of home.html (cached between visits).
  (function () {
    document.querySelectorAll("[data-review-stars]").forEach(function (picker) {
      const input = picker.parentElement.querySelector("[data-rating-input]");
      if (!input) return;
      const stars = Array.from(picker.querySelectorAll(".review-star"));

      function paint(value) {
        stars.forEach((star, idx) => {
          star.classList.toggle("active", idx < value);
        });
      }

      stars.forEach((star) => {
        const value = Number(star.dataset.value || 0);
        star.addEventListener("mouseenter", function () {
          paint(value);
        });
        star.addEventListener("click", function () {
          input.value = String(value);
          paint(value);
        });
      });

      picker.addEventListener("mouseleave", function () {
        paint(Number(input.value || 0));
      });

      paint(Number(input.value || 0));
    });
  })();

  (function () {
    function initLocationTreeSelect() {
      const container = document.querySelector('[data-tree-select="district"]');
      if (!container) return;
      const trigger = container.querySelector('.km-tree-trigger');
      const triggerText = container.querySelector('.km-tree-trigger-text');
      const dropdown = container.querySelector('.km-tree-dropdown');
      const targetSelect = document.querySelector('select[name="district"]');
      if (!trigger || !dropdown || !targetSelect) return;

      const currentLang = (document.documentElement.lang || 'az').split('-')[0].toLowerCase();

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
        return Array.from(targetSelect.options).map(function (opt) {
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

        row.addEventListener('click', function (e) {
          if (hasChildren && e.target.closest('.km-tree-chevron')) {
            e.stopPropagation();
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

      dropdown.addEventListener('keydown', function (e) {
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

      trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        toggleDropdown();
      });

      trigger.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openDropdown();
        }
      });

      document.addEventListener('click', function (e) {
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
          let defaultLabel = 'Region / район';
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

    function initCategorySelect() {
      const container = document.querySelector('[data-category-select]');
      if (!container) return;
      const trigger = container.querySelector('.km-category-trigger');
      const triggerIcon = container.querySelector('[data-category-trigger-icon]');
      const triggerText = container.querySelector('[data-category-trigger-text]');
      const dropdown = container.querySelector('.km-category-dropdown');
      const targetSelect = document.querySelector('select[name="category"]');
      if (!trigger || !dropdown || !targetSelect) return;

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
        const activeOpt = dropdown.querySelector('.km-category-option.is-active') || dropdown.querySelector('.km-category-option');
        if (activeOpt) {
          activeOpt.setAttribute('tabindex', '0');
          activeOpt.focus();
        }
      }

      function closeDropdown() {
        dropdown.hidden = true;
        trigger.setAttribute('aria-expanded', 'false');
        trigger.focus();
      }

      dropdown.querySelectorAll('.km-category-option').forEach(option => {
        option.setAttribute('tabindex', '-1');
        option.addEventListener('click', function (e) {
          const value = option.dataset.value;
          selectValue(value);
        });
      });

      function selectValue(value) {
        targetSelect.value = value;
        targetSelect.dispatchEvent(new Event('change', { bubbles: true }));
        closeDropdown();
      }

      function updateTrigger() {
        const selectedVal = targetSelect.value;
        dropdown.querySelectorAll('.km-category-option').forEach(opt => {
          if (opt.dataset.value === selectedVal) {
            opt.classList.add('is-active');
            opt.setAttribute('aria-selected', 'true');
          } else {
            opt.classList.remove('is-active');
            opt.setAttribute('aria-selected', 'false');
          }
        });

        const activeOpt = dropdown.querySelector(`.km-category-option[data-value="${selectedVal}"]`) || dropdown.querySelector('.km-category-option[data-value=""]');
        if (activeOpt) {
          triggerText.textContent = activeOpt.querySelector('.km-category-option-text').textContent.trim();
          triggerIcon.innerHTML = activeOpt.querySelector('.km-category-option-icon').innerHTML;
          if (selectedVal !== '') {
            container.classList.add('is-active');
          } else {
            container.classList.remove('is-active');
          }
        }
      }

      trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        toggleDropdown();
      });

      trigger.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openDropdown();
        }
      });

      dropdown.addEventListener('keydown', function (e) {
        const active = document.activeElement;
        if (!active || !active.classList.contains('km-category-option')) return;
        const options = Array.from(dropdown.querySelectorAll('.km-category-option'));
        const index = options.indexOf(active);

        switch (e.key) {
          case 'ArrowDown':
            e.preventDefault();
            if (index < options.length - 1) {
              options.forEach(opt => opt.setAttribute('tabindex', '-1'));
              options[index + 1].setAttribute('tabindex', '0');
              options[index + 1].focus();
            }
            break;
          case 'ArrowUp':
            e.preventDefault();
            if (index > 0) {
              options.forEach(opt => opt.setAttribute('tabindex', '-1'));
              options[index - 1].setAttribute('tabindex', '0');
              options[index - 1].focus();
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
        }
      });

      document.addEventListener('click', function (e) {
        if (!container.contains(e.target)) {
          dropdown.hidden = true;
          trigger.setAttribute('aria-expanded', 'false');
        }
      });

      targetSelect.addEventListener('change', updateTrigger);
      updateTrigger();
    }

    initCategorySelect();

    function initAgeSelect() {
      const container = document.querySelector('[data-age-select]');
      if (!container) return;
      const trigger = container.querySelector('.km-age-trigger');
      const triggerText = container.querySelector('[data-age-value-text]');
      const dropdown = container.querySelector('.km-age-dropdown');
      const inputFrom = container.querySelector('input[name="age_from"]');
      const inputTo = container.querySelector('input[name="age_to"]');
      const applyBtn = container.querySelector('[data-age-apply-btn]');
      const presetItems = container.querySelectorAll('.km-age-preset-item');
      if (!trigger || !dropdown || !inputFrom || !inputTo) return;

      const allLabel = container.dataset.allLabel || 'Все возрасты';
      const unit = container.dataset.unit || 'лет';

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
        container.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');
        const activeItem = dropdown.querySelector('.km-age-preset-item.is-active') || dropdown.querySelector('.km-age-preset-item');
        if (activeItem) {
          activeItem.setAttribute('tabindex', '0');
          activeItem.focus();
        }
      }

      function closeDropdown() {
        dropdown.hidden = true;
        container.classList.remove('is-open');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.focus();
      }

      function updateTriggerLabel() {
        const from = inputFrom.value.trim();
        const to = inputTo.value.trim();

        presetItems.forEach(item => {
          const match = (item.dataset.from || '') === from && (item.dataset.to || '') === to;
          item.classList.toggle('is-active', match);
          item.setAttribute('aria-selected', match ? 'true' : 'false');
        });

        if (!from && !to) {
          triggerText.textContent = allLabel;
          container.classList.remove('is-active');
        } else if (from && to) {
          if (from === to) {
            triggerText.textContent = from + ' ' + unit;
          } else {
            triggerText.textContent = from + '–' + to + ' ' + unit;
          }
          container.classList.add('is-active');
        } else if (from) {
          triggerText.textContent = from + '+ ' + unit;
          container.classList.add('is-active');
        } else if (to) {
          triggerText.textContent = to + ' ' + unit + ' max';
          container.classList.add('is-active');
        }
      }

      presetItems.forEach(item => {
        item.setAttribute('tabindex', '-1');
        item.addEventListener('click', function (e) {
          e.preventDefault();
          const from = item.dataset.from || '';
          const to = item.dataset.to || '';
          inputFrom.value = from;
          inputTo.value = to;
          inputFrom.dispatchEvent(new Event('input', { bubbles: true }));
          inputFrom.dispatchEvent(new Event('change', { bubbles: true }));
          inputTo.dispatchEvent(new Event('input', { bubbles: true }));
          inputTo.dispatchEvent(new Event('change', { bubbles: true }));
          updateTriggerLabel();
          closeDropdown();
        });
      });

      if (applyBtn) {
        applyBtn.addEventListener('click', function (e) {
          e.preventDefault();
          inputFrom.dispatchEvent(new Event('input', { bubbles: true }));
          inputFrom.dispatchEvent(new Event('change', { bubbles: true }));
          inputTo.dispatchEvent(new Event('input', { bubbles: true }));
          inputTo.dispatchEvent(new Event('change', { bubbles: true }));
          updateTriggerLabel();
          closeDropdown();
        });
      }

      [inputFrom, inputTo].forEach(input => {
        input.addEventListener('keydown', function (e) {
          if (e.key === 'Enter') {
            e.preventDefault();
            if (applyBtn) applyBtn.click();
            else {
              updateTriggerLabel();
              closeDropdown();
            }
          }
        });
      });

      trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        toggleDropdown();
      });

      trigger.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openDropdown();
        }
      });

      dropdown.addEventListener('keydown', function (e) {
        const active = document.activeElement;
        if (!active || !active.classList.contains('km-age-preset-item')) return;
        const items = Array.from(presetItems);
        const index = items.indexOf(active);

        switch (e.key) {
          case 'ArrowDown':
            e.preventDefault();
            if (index < items.length - 1) {
              items.forEach(opt => opt.setAttribute('tabindex', '-1'));
              items[index + 1].setAttribute('tabindex', '0');
              items[index + 1].focus();
            }
            break;
          case 'ArrowUp':
            e.preventDefault();
            if (index > 0) {
              items.forEach(opt => opt.setAttribute('tabindex', '-1'));
              items[index - 1].setAttribute('tabindex', '0');
              items[index - 1].focus();
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
        }
      });

      document.addEventListener('click', function (e) {
        if (!container.contains(e.target)) {
          dropdown.hidden = true;
          container.classList.remove('is-open');
          trigger.setAttribute('aria-expanded', 'false');
        }
      });

      inputFrom.addEventListener('change', updateTriggerLabel);
      inputTo.addEventListener('change', updateTriggerLabel);
      inputFrom.addEventListener('input', updateTriggerLabel);
      inputTo.addEventListener('input', updateTriggerLabel);

      const resetBtn = document.querySelector('[data-home-search-reset]');
      if (resetBtn) {
        resetBtn.addEventListener('click', function () {
          window.setTimeout(updateTriggerLabel, 60);
        });
      }
      updateTriggerLabel();
    }

    initAgeSelect();

    function initAgeChips() {
      const form = document.querySelector('[data-home-map-filter-form]');
      if (!form) return;
      const ageInput = form.querySelector('input[name="age"]');
      const chips = form.querySelectorAll('[data-home-age-chip]');
      if (!ageInput || !chips.length) return;

      function syncChips() {
        const val = (ageInput.value || '').trim();
        chips.forEach(chip => {
          const chipVal = (chip.dataset.ageValue || '').trim();
          const isActive = chipVal !== '' && chipVal === val;
          chip.classList.toggle('is-active', isActive);
          chip.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        });
      }

      chips.forEach(chip => {
        chip.addEventListener('click', function (e) {
          e.preventDefault();
          const chipVal = (chip.dataset.ageValue || '').trim();
          const currentVal = (ageInput.value || '').trim();
          ageInput.value = (currentVal === chipVal) ? '' : chipVal;
          syncChips();
          ageInput.dispatchEvent(new Event('change', { bubbles: true }));
        });
      });

      ageInput.addEventListener('change', syncChips);
      syncChips();
    }

    initAgeChips();

    // Scroll reveal logic
    function initScrollReveal() {
      const revealElements = document.querySelectorAll('.km-reveal, .km-reveal-up');
      if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries, observer) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              entry.target.classList.add('is-visible');
              observer.unobserve(entry.target);
            }
          });
        }, {
          threshold: 0.1,
          rootMargin: '0px 0px -40px 0px'
        });
        revealElements.forEach(el => observer.observe(el));
      } else {
        revealElements.forEach(el => el.classList.add('is-visible'));
      }
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initScrollReveal);
    } else {
      initScrollReveal();
    }
  })();
