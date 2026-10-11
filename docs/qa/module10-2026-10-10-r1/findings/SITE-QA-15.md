# SITE-QA-15 — Две вкладки настроек молча теряют сохранённое изменение

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: confirmed CURRENT LOCAL lost-update failure, native two tabs, no simulated transport. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin, две настоящие вкладки одной сессии. **URL/endpoint:** `/admin/catalog/sitefootersettings/1/change/`.

**Шаги:** Открыть footer form одновременно в A/B. В A изменить только телефон на +994000000013 и сохранить. Не перезагружая B, изменить только email на tabB10@example.invalid и сохранить. Reload обеих вкладок и read-only DB check.

**Ожидание:** Изменение email не стирает уже сохранённый другой телефон; stale form получает понятный conflict/reload или сохраняет только собственный intent.

**Факт:** A сохраняет новый телефон. После B email обновлён, телефон возвращается к +994000000011 из старой формы. Errors отсутствуют, reload обеих вкладок подтверждает потерю A. После evidence прежние вымышленные контакты восстановлены native POST; отдельно native dblclick сохраняет ожидаемое значение.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2: обычные две вкладки могут незаметно отменить ранее сохранённые контакты/другие поля общей секции. Подтверждено RU1440; остальные language/width concurrency combinations NOT RUN.

**Первопричина / гипотеза:** Подтверждён механизм: обычный полный ModelForm POST stale fields; updated_at readonly и не используется для version/conflict check. Сервер видит старое значение телефона как новое намерение B и сохраняет его. Product choice merge vs conflict требует плана, сам silent lost update воспроизведён.

**Source:** `src/catalog/domain_admin/site.py:28`; `src/catalog/models/site.py:369`; `src/catalog/templates/admin/catalog/shared_settings_change_form.html:16`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [current-concurrency.result.txt](../current-concurrency.result.txt)
- [screenshots/current-concurrency-tab-A-save.png](../screenshots/current-concurrency-tab-A-save.png)
- [screenshots/current-concurrency-tab-B-save.png](../screenshots/current-concurrency-tab-B-save.png)
- [screenshots/current-concurrency-reload.png](../screenshots/current-concurrency-reload.png)
- [screenshots/current-concurrency-restored.png](../screenshots/current-concurrency-restored.png)
- [current-concurrency.result.txt](../current-concurrency.result.txt)

**Область исправления:** Установить intent/version policy для SiteSettings section forms: явный conflict с сохранением ввода либо корректное слияние непересекающихся изменений. Не реализовывать blind last-write merge по всей singleton модели.

**Владелец / зависимости:** Django model/admin/forms + shared error UX; separate fields and same-field conflict, double submit, reload/cache; no assertion rewrites.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-15-repair.txt). Аудит ничего не исправляет.
