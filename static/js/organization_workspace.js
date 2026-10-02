(() => {
  const lang = (document.documentElement.lang || 'az').slice(0, 2);
  const copy = {
    az: { browser: 'Qaralama bu brauzerdə saxlanıb', saving: 'Saxlanır…', saved: 'Serverdə saxlanıb', conflict: 'Konflikt: daxil etdiyiniz məlumat saxlanılıb. Səhifəni yeniləyib müqayisə edin.', failed: 'Serverdə saxlamaq mümkün olmadı; daxil etdiyiniz məlumat qalıb.', invited: 'Dəvət göndərildi', inviteFailed: 'Dəvət göndərilmədi; icazə və sahəni yoxlayın.' },
    ru: { browser: 'Черновик сохранён в этом браузере', saving: 'Сохраняем…', saved: 'Сохранено на сервере', conflict: 'Конфликт: ваш ввод сохранён. Обновите страницу и сравните версии.', failed: 'Серверное сохранение не удалось; ваш ввод сохранён.', invited: 'Приглашение отправлено', inviteFailed: 'Приглашение не отправлено; проверьте права и поля.' },
    en: { browser: 'Draft saved in this browser', saving: 'Saving…', saved: 'Saved on server', conflict: 'Conflict: your input is preserved. Reload and compare versions.', failed: 'Server save failed; your input is preserved.', invited: 'Invitation sent', inviteFailed: 'Invitation failed; check permissions and fields.' }
  }[lang] || null;
  if (!copy) return;
  const fields = ['name_az', 'name_ru', 'name_en', 'description_az', 'phone', 'whatsapp', 'website'];
  const cookie = document.cookie.split('; ').find(x => x.startsWith('csrftoken='));
  const csrf = cookie ? decodeURIComponent(cookie.slice(10)) : document.querySelector('[name=csrfmiddlewaretoken]')?.value;
  const create = document.querySelector('[data-org-create-form]');
  if (create) {
    const createFields = fields.filter(name => create.elements[name]);
    const key = `kidsmap:org:create:${document.querySelector('[data-workspace]').dataset.userId}`;
    try { const data = JSON.parse(sessionStorage.getItem(key) || '{}'); for (const name of createFields) if (typeof data[name] === 'string' && !create.elements[name].value) create.elements[name].value = data[name]; } catch (_) { /* private storage unavailable */ }
    create.addEventListener('input', () => {
      try { sessionStorage.setItem(key, JSON.stringify(Object.fromEntries(createFields.map(name => [name, create.elements[name].value])))); create.querySelector('[data-create-status]').textContent = copy.browser; } catch (_) { create.querySelector('[data-create-status]').textContent = copy.failed; }
    });
  }
  const edit = document.querySelector('[data-org-edit-form]');
  if (edit) {
    const status = edit.querySelector('[data-draft-status]');
    const key = `kidsmap:org:${document.querySelector('[data-workspace]').dataset.userId}:${document.querySelector('[data-org-id]').dataset.orgId}:draft`;
    let timer;
    try { const local = JSON.parse(sessionStorage.getItem(key) || '{}'); if (local.fields && local.source === edit.dataset.sourceVersion) { for (const name of fields) if (typeof local.fields[name] === 'string') edit.elements[name].value = local.fields[name]; status.textContent = copy.browser; } } catch (_) { /* private storage unavailable */ }
    const values = () => Object.fromEntries(fields.map(name => [name, edit.elements[name].value]));
    edit.addEventListener('input', () => {
      const input = values();
      try { sessionStorage.setItem(key, JSON.stringify({ source: edit.dataset.sourceVersion, fields: input })); status.textContent = copy.browser; } catch (_) { status.textContent = copy.failed; }
      clearTimeout(timer); timer = setTimeout(async () => {
        status.textContent = copy.saving;
        try {
          const response = await fetch(edit.dataset.draftUrl, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf }, body: JSON.stringify({ draft_id: edit.dataset.draftId || null, target_type: 'organization', target_id: Number(document.querySelector('[data-org-id]').dataset.orgId), schema_version: Number(edit.dataset.schemaVersion), source_version: Number(edit.dataset.sourceVersion), expected_version: Number(edit.dataset.draftVersion), fields: input }) });
          const data = await response.json();
          if (response.status === 409) { status.textContent = copy.conflict; return; }
          if (!response.ok) throw new Error(data.status || 'save');
          edit.dataset.draftId = data.draft_id; edit.dataset.draftVersion = String(data.version); status.textContent = copy.saved;
          try { sessionStorage.removeItem(key); } catch (_) { /* private storage unavailable */ }
        } catch (_) { status.textContent = copy.failed; }
      }, 650);
    });
  }
  const join = document.querySelector('[data-join-form]');
  if (join) join.addEventListener('submit', () => { join.action = join.querySelector('[data-join-org]').selectedOptions[0].dataset.url; });
  const team = document.querySelector('[data-team-form]');
  if (team) {
    const scope = team.querySelector('[data-team-scope]');
    const branches = team.querySelector('[data-team-branches]');
    scope.addEventListener('change', () => { branches.hidden = scope.value !== 'selected_places'; });
    team.addEventListener('submit', async event => {
      event.preventDefault(); const status = team.querySelector('[data-team-status]');
      const payload = { email: team.elements.email.value, role: team.elements.role.value, scope: scope.value,
        place_ids: [...team.querySelectorAll('[name=place_ids]:checked')].map(x => Number(x.value)) };
      try {
        const response = await fetch(team.dataset.teamUrl, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf }, body: JSON.stringify(payload) });
        if (!response.ok) throw new Error('invite'); status.textContent = copy.invited; team.reset(); branches.hidden = true;
      } catch (_) { status.textContent = copy.inviteFailed; }
    });
  }
})();
