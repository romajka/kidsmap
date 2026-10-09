(() => {
  const lang = (document.documentElement.lang || 'az').slice(0, 2);
  const copy = {
    az: {
      browser: 'Qaralama bu brauzerdə saxlanıb',
      saving: 'Saxlanır…',
      saved: 'Serverdə saxlanıb',
      conflict: 'Konflikt: daxil etdiyiniz məlumat saxlanılıb. Səhifəni yeniləyib müqayisə edin.',
      failed: 'Serverdə saxlamaq mümkün olmadı; daxil etdiyiniz məlumat qalıb.',
      invited: 'Dəvət göndərildi',
      inviteFailed: 'Dəvət göndərilmədi; icazə və sahəni yoxlayın.',
      inviting: "Dəvət göndərilir…",
      invitedListFailed: "Dəvət göndərildi. Siyahını yeniləmək mümkün olmadı; təkrar göndərməzdən əvvəl onu yeniləyin.",
      inviteConflict: "Dəvət artıq mövcuddur. Təkrar göndərməzdən əvvəl siyahını yoxlayın.",
      inviteUncertain: "Serverdən cavab almaq mümkün olmadı. Təkrar göndərməzdən əvvəl siyahını yoxlayın.",
      listRefreshing: "Dəvət siyahısı yenilənir…",
      listUpdated: "Dəvət siyahısı yeniləndi.",
      listFailed: "Dəvət siyahısını yeniləmək mümkün olmadı. Yenidən cəhd edin.",
      showing: 'Göstərilir',
      from: '/',
      prev: '← Əvvəlki',
      next: 'Növbəti →',
      noBranchesFound: 'Axtarışa uyğun filial tapılmadı'
    },
    ru: {
      browser: 'Черновик сохранён в этом браузере',
      saving: 'Сохраняем…',
      saved: 'Сохранено на сервере',
      conflict: 'Конфликт: ваш ввод сохранён. Обновите страницу и сравните версии.',
      failed: 'Серверное сохранение не удалось; ваш ввод сохранён.',
      invited: 'Приглашение отправлено',
      inviteFailed: 'Приглашение не отправлено; проверьте права и поля.',
      inviting: "Приглашаем…",
      invitedListFailed: "Приглашение отправлено. Не удалось обновить список; обновите его перед повторной отправкой.",
      inviteConflict: "Приглашение уже существует. Проверьте список перед повторной отправкой.",
      inviteUncertain: "Не удалось получить ответ сервера. Проверьте список перед повторной отправкой.",
      listRefreshing: "Обновляем список приглашений…",
      listUpdated: "Список приглашений обновлён.",
      listFailed: "Не удалось обновить список приглашений. Попробуйте ещё раз.",
      showing: 'Показано',
      from: 'из',
      prev: '← Предыдущая',
      next: 'Следующая →',
      noBranchesFound: 'Филиалов по вашему запросу не найдено'
    },
    en: {
      browser: 'Draft saved in this browser',
      saving: 'Saving…',
      saved: 'Saved on server',
      conflict: 'Conflict: your input is preserved. Reload and compare versions.',
      failed: 'Server save failed; your input is preserved.',
      invited: 'Invitation sent',
      inviteFailed: 'Invitation failed; check permissions and fields.',
      inviting: "Inviting…",
      invitedListFailed: "Invitation sent. Could not refresh the list; refresh it before sending again.",
      inviteConflict: "An invitation already exists. Check the list before sending again.",
      inviteUncertain: "Could not receive a response from the server. Check the list before sending again.",
      listRefreshing: "Refreshing invitations…",
      listUpdated: "Invitation list refreshed.",
      listFailed: "Could not refresh the invitation list. Try again.",
      showing: 'Showing',
      from: 'of',
      prev: '← Previous',
      next: 'Next →',
      noBranchesFound: 'No branches match your search'
    }
  }[lang] || {
    browser: 'Draft saved', saving: 'Saving…', saved: 'Saved', conflict: 'Conflict', failed: 'Save failed', invited: 'Invited', inviteFailed: 'Invite failed',
    showing: 'Showing', from: 'of', prev: '← Prev', next: 'Next →', noBranchesFound: 'No branches found'
  };

  const fields = ['name_az', 'name_ru', 'name_en', 'description_az', 'phone', 'whatsapp', 'website'];
  const cookie = document.cookie.split('; ').find(x => x.startsWith('csrftoken='));
  const csrf = cookie ? decodeURIComponent(cookie.slice(10)) : document.querySelector('[name=csrfmiddlewaretoken]')?.value;

  // Auto-open disclosures if any input inside has content or error
  document.querySelectorAll('details.org-disclosure').forEach(details => {
    const inputs = details.querySelectorAll('input, textarea');
    let hasValue = false;
    inputs.forEach(input => {
      if (input.value && input.value.trim() !== '') hasValue = true;
    });
    if (details.querySelector('.org-field-error') || hasValue) {
      details.open = true;
    }
  });

  // Create organization form & sessionStorage persistence
  const create = document.querySelector('[data-org-create-form]');
  const workspaceEl = document.querySelector('[data-workspace]');
  if (create && workspaceEl) {
    const createFields = fields.filter(name => create.elements[name]);
    const userId = workspaceEl.dataset.userId || 'anon';
    const key = `kidsmap:org:create:${userId}`;
    try {
      const data = JSON.parse(sessionStorage.getItem(key) || '{}');
      for (const name of createFields) {
        if (typeof data[name] === 'string' && !create.elements[name].value) {
          create.elements[name].value = data[name];
        }
      }
      // Re-check disclosures after restoring values
      document.querySelectorAll('details.org-disclosure').forEach(details => {
        const inputs = details.querySelectorAll('input, textarea');
        inputs.forEach(input => { if (input.value && input.value.trim() !== '') details.open = true; });
      });
    } catch (_) { /* private storage unavailable */ }

    create.addEventListener('input', () => {
      try {
        sessionStorage.setItem(key, JSON.stringify(Object.fromEntries(createFields.map(name => [name, create.elements[name].value]))));
        const statusEl = create.querySelector('[data-create-status]');
        if (statusEl) statusEl.textContent = copy.browser;
      } catch (_) {
        const statusEl = create.querySelector('[data-create-status]');
        if (statusEl) statusEl.textContent = copy.failed;
      }
    });

    create.addEventListener('submit', () => {
      // Native POST can fail; retain the exact submitted input until confirmed.
      try {
        sessionStorage.setItem(key, JSON.stringify(Object.fromEntries(createFields.map(name => [name, create.elements[name].value]))));
      } catch (_) {}
    });
  }

  const creationConfirmation = document.getElementById('org-create-confirmation');
  if (creationConfirmation && workspaceEl) {
    try {
      const confirmed = JSON.parse(creationConfirmation.textContent);
      const key = `kidsmap:org:create:${workspaceEl.dataset.userId || 'anon'}`;
      const local = JSON.parse(sessionStorage.getItem(key) || 'null');
      if (local && fields.every(name => local[name] === confirmed[name])) sessionStorage.removeItem(key);
    } catch (_) { /* Preserve recovery if storage or confirmation is unavailable. */ }
  }

  // Edit organization form with debounced server draft
  const edit = document.querySelector('[data-org-edit-form]');
  const errorSummary = edit?.querySelector('[data-org-error-summary]');
  if (errorSummary) {
    errorSummary.focus();
    errorSummary.addEventListener('click', event => {
      const link = event.target.closest('a[data-org-error-target]');
      if (!link) return;
      const target = document.getElementById(link.dataset.orgErrorTarget);
      if (!target || target.type === 'hidden') return;
      event.preventDefault();
      target.focus();
      target.scrollIntoView({ block: 'center' });
    });
  }

  if (edit && workspaceEl) {
    const status = edit.querySelector('[data-draft-status]');
    const orgIdEl = document.querySelector('[data-org-id]');
    const orgId = orgIdEl ? orgIdEl.dataset.orgId : '0';
    const userId = workspaceEl.dataset.userId || 'anon';
    const key = `kidsmap:org:${userId}:${orgId}:draft`;
    let timer;
    let inFlight = false;
    let revision = 0;
    let conflicted = false;
    try {
      if (edit.hasAttribute('data-org-server-errors')) {
        // A rejected native POST is newer than any saved recovery copy.
        sessionStorage.setItem(key, JSON.stringify({ source: edit.dataset.sourceVersion,
          fields: Object.fromEntries(fields.map(name => [name, edit.elements[name].value])) }));
        if (status) status.textContent = copy.browser;
      } else if (!edit.hasAttribute('data-org-current-data')) {
        const local = JSON.parse(sessionStorage.getItem(key) || '{}');
        if (local.fields && local.source === edit.dataset.sourceVersion) {
          for (const name of fields) if (typeof local.fields[name] === 'string') edit.elements[name].value = local.fields[name];
          if (status) status.textContent = copy.browser;
        }
      }
    } catch (_) { /* private storage unavailable */ }

    const values = () => Object.fromEntries(fields.map(name => [name, edit.elements[name].value]));
    const saveDraft = async () => {
      if (inFlight || conflicted) return;
      inFlight = true;
      const input = values();
      const sentRevision = revision;
      const sentFields = JSON.stringify(input);
      let acknowledged = false;
      if (status) status.textContent = copy.saving;
      try {
        const response = await fetch(edit.dataset.draftUrl, {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
          body: JSON.stringify({
            draft_id: edit.dataset.draftId || null,
            target_type: 'organization',
            target_id: Number(orgId),
            schema_version: Number(edit.dataset.schemaVersion),
            source_version: Number(edit.dataset.sourceVersion),
            expected_version: Number(edit.dataset.draftVersion),
            fields: input
          })
        });
        const data = await response.json();
        if (response.status === 409) {
          conflicted = true;
          if (status) status.textContent = copy.conflict;
          return;
        }
        if (!response.ok) throw new Error(data.status || 'save');
        edit.dataset.draftId = data.draft_id;
        edit.dataset.draftVersion = String(data.version);
        acknowledged = true;
        // An acknowledgement of A advances CAS, but cannot confirm or erase B.
        if (sentRevision === revision && sentFields === JSON.stringify(values())) {
          if (status) status.textContent = copy.saved;
          try {
            const local = JSON.parse(sessionStorage.getItem(key) || 'null');
            if (local?.source === edit.dataset.sourceVersion && JSON.stringify(local.fields) === sentFields) {
              sessionStorage.removeItem(key);
            }
          } catch (_) { /* private storage unavailable */ }
        }
      } catch (_) {
        if (status) status.textContent = copy.failed;
      } finally {
        inFlight = false;
        if (acknowledged && (sentRevision !== revision || sentFields !== JSON.stringify(values()))) {
          clearTimeout(timer);
          timer = setTimeout(saveDraft, 650);
        }
      }
    };
    edit.addEventListener('input', () => {
      revision += 1;
      const input = values();
      try {
        sessionStorage.setItem(key, JSON.stringify({ source: edit.dataset.sourceVersion, fields: input }));
        if (status) status.textContent = conflicted ? copy.conflict : copy.browser;
      } catch (_) {
        if (status) status.textContent = copy.failed;
      }
      clearTimeout(timer);
      if (!conflicted) timer = setTimeout(saveDraft, 650);
    });
  }

  // Join form
  const join = document.querySelector('[data-join-form]');
  if (join) {
    join.addEventListener('submit', () => {
      join.action = join.querySelector('[data-join-org]').selectedOptions[0].dataset.url;
    });
  }

  // Team invitation form
  const team = document.querySelector('[data-team-form]');
  if (team) {
    const role = team.querySelector('[data-team-role]');
    const roleSummary = team.querySelector('[data-team-role-summary]');
    const updateRole = () => { if (roleSummary) roleSummary.textContent = role.selectedOptions[0].dataset.summary; };
    if (role) { role.addEventListener('change', updateRole); updateRole(); }
    const scope = team.querySelector('[data-team-scope]');
    const branches = team.querySelector('[data-team-branches]');
    if (scope && branches) {
      scope.addEventListener('change', () => {
        branches.hidden = scope.value !== 'selected_places';
      });
    }
    const controls = [...team.querySelectorAll('[data-team-control]')];
    const submit = team.querySelector('[type="submit"]');
    const submitLabel = submit?.textContent;
    const status = team.querySelector('[data-team-status]');
    const refresh = team.querySelector('[data-team-refresh]');
    const invitations = document.querySelector('[data-team-invitations]');
    let sending = false;
    const setBusy = (busy, inviting = true) => {
      sending = busy;
      team.setAttribute('aria-busy', String(busy));
      controls.forEach(control => { control.disabled = busy; });
      if (submit) submit.textContent = busy && inviting ? copy.inviting : submitLabel;
    };
    const refreshInvitations = async () => {
      if (!invitations || !team.dataset.teamListUrl) return true;
      try {
        const response = await fetch(team.dataset.teamListUrl, {
          method: 'GET', credentials: 'same-origin', cache: 'no-store'
        });
        if (!response.ok) throw new Error('list');
        const html = new DOMParser().parseFromString(await response.text(), 'text/html');
        const current = html.querySelector('[data-team-invitations]');
        if (!current) throw new Error('list');
        // Replace only owner-visible, server-rendered invitations; preserve editor input.
        invitations.replaceChildren(...current.childNodes);
        if (refresh) refresh.hidden = true;
        return true;
      } catch (_) {
        if (refresh) refresh.hidden = false;
        return false;
      }
    };
    team.addEventListener('submit', async event => {
      event.preventDefault();
      if (sending) return;
      const payload = {
        email: team.elements.email.value,
        role: team.elements.role.value,
        scope: scope ? scope.value : 'all_network',
        place_ids: [...team.querySelectorAll('[name=place_ids]:checked')].map(x => Number(x.value))
      };
      setBusy(true);
      if (status) status.textContent = copy.inviting;
      if (refresh) refresh.hidden = true;
      try {
        const response = await fetch(team.dataset.teamUrl, {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
          body: JSON.stringify(payload)
        });
        if (!response.ok) {
          if (response.status === 409) {
            await refreshInvitations();
            if (status) status.textContent = copy.inviteConflict;
          } else if (status) status.textContent = copy.inviteFailed;
          return;
        }
        team.reset();
        updateRole();
        if (branches) branches.hidden = scope?.value !== 'selected_places';
        const refreshed = await refreshInvitations();
        if (status) status.textContent = refreshed ? copy.invited : copy.invitedListFailed;
      } catch (_) {
        // A lost response cannot prove that the canonical POST was not committed.
        if (status) status.textContent = copy.inviteUncertain;
        if (refresh) refresh.hidden = false;
      } finally {
        setBusy(false);
      }
    });
    refresh?.addEventListener('click', async () => {
      if (sending) return;
      setBusy(true, false);
      if (status) status.textContent = copy.listRefreshing;
      try {
        const refreshed = await refreshInvitations();
        if (status) status.textContent = refreshed ? copy.listUpdated : copy.listFailed;
      } finally {
        setBusy(false);
      }
    });
    // Release native controls only after safe JSON POST interception is installed.
    team.querySelectorAll('[data-team-control]').forEach(control => { control.disabled = false; });
    const unavailable = team.querySelector('[data-team-unavailable]');
    if (unavailable) unavailable.hidden = true;
    team.querySelector('[type="submit"]')?.removeAttribute('aria-describedby');
  }

  // Standalone places client-side live filter
  const filterInput = document.querySelector('[data-filter-input]');
  if (filterInput) {
    const targetSelector = filterInput.dataset.filterInput;
    const container = document.querySelector(targetSelector);
    if (container) {
      const items = Array.from(container.querySelectorAll('[data-filter-item]'));
      filterInput.addEventListener('input', () => {
        const query = filterInput.value.trim().toLowerCase();
        items.forEach(item => {
          const text = (item.dataset.filterText || item.textContent || '').toLowerCase();
          item.style.display = text.includes(query) ? '' : 'none';
        });
      });
    }
  }

  // Branches search and pagination
  const branchList = document.querySelector('[data-branch-list]');
  const branchSearch = document.querySelector('[data-branch-search]');
  const paginationBox = document.querySelector('[data-branch-pagination]');
  const countLabel = document.querySelector('[data-branch-count-label]');

  if (branchList) {
    const allItems = Array.from(branchList.querySelectorAll('[data-branch-item]'));
    const PAGE_SIZE = 6;
    let currentPage = 1;
    let filteredItems = allItems.slice();

    function renderPage() {
      const focusedControl = paginationBox?.contains(document.activeElement)
        ? document.activeElement.dataset.pageControl : null;
      const total = filteredItems.length;
      const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
      if (currentPage > totalPages) currentPage = totalPages;
      if (currentPage < 1) currentPage = 1;

      // Show/hide items
      const startIndex = (currentPage - 1) * PAGE_SIZE;
      const endIndex = startIndex + PAGE_SIZE;

      allItems.forEach(item => {
        item.style.display = 'none';
      });

      filteredItems.forEach((item, idx) => {
        if (idx >= startIndex && idx < endIndex) {
          item.style.display = '';
        }
      });

      // Update count label
      if (countLabel) {
        if (total === 0) {
          countLabel.textContent = copy.noBranchesFound;
        } else {
          const from = startIndex + 1;
          const to = Math.min(endIndex, total);
          countLabel.textContent = `${copy.showing} ${from}–${to} ${copy.from} ${total}`;
        }
      }

      // Render pagination buttons
      if (!paginationBox) return;
      if (totalPages <= 1) {
        paginationBox.innerHTML = '';
        paginationBox.style.display = 'none';
        return;
      }

      paginationBox.style.display = 'flex';
      paginationBox.innerHTML = '';

      // Prev button
      const prevBtn = document.createElement('button');
      prevBtn.type = 'button';
      prevBtn.dataset.pageControl = 'prev';
      prevBtn.className = 'org-pagination__btn';
      prevBtn.textContent = copy.prev;
      prevBtn.disabled = currentPage === 1;
      prevBtn.addEventListener('click', () => {
        currentPage--;
        renderPage();
        branchList.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      paginationBox.appendChild(prevBtn);

      // Page numbers
      for (let p = 1; p <= totalPages; p++) {
        const pageBtn = document.createElement('button');
        pageBtn.type = 'button';
        pageBtn.dataset.pageControl = String(p);
        if (p === currentPage) pageBtn.setAttribute('aria-current', 'page');
        pageBtn.className = 'org-pagination__btn' + (p === currentPage ? ' is-active' : '');
        pageBtn.textContent = String(p);
        pageBtn.addEventListener('click', () => {
          currentPage = p;
          renderPage();
          branchList.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
        paginationBox.appendChild(pageBtn);
      }

      // Next button
      const nextBtn = document.createElement('button');
      nextBtn.type = 'button';
      nextBtn.dataset.pageControl = 'next';
      nextBtn.className = 'org-pagination__btn';
      nextBtn.textContent = copy.next;
      nextBtn.disabled = currentPage === totalPages;
      nextBtn.addEventListener('click', () => {
        currentPage++;
        renderPage();
        branchList.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      paginationBox.appendChild(nextBtn);
      if (focusedControl) {
        const controls = Array.from(paginationBox.querySelectorAll('button'));
        const replacement = controls.find(btn => btn.dataset.pageControl === focusedControl && !btn.disabled)
          || controls.find(btn => btn.dataset.pageControl === String(currentPage));
        replacement?.focus({preventScroll: true});
      }
    }

    if (branchSearch) {
      branchSearch.addEventListener('input', () => {
        const query = branchSearch.value.trim().toLowerCase();
        filteredItems = allItems.filter(item => {
          const name = (item.dataset.name || item.textContent || '').toLowerCase();
          return name.includes(query);
        });
        currentPage = 1;
        renderPage();
      });
    }

    // Initial render
    renderPage();
  }
})();
