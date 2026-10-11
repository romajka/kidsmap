# SITE-QA-11 — Loading и удаление медиа захардкожены на русском

**OPEN / P3 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL application localization failure; SIMULATED transport. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin. **URL/endpoint:** `/admin/catalog/sitegalleryimage/`.

**Шаги:** EN/AZ: задержать/оборвать own upload через browser route, открыть delete confirmation. Проверить visible loading/title/buttons.

**Ожидание:** Состояния и действия на выбранном языке.

**Факт:** По 12 FAIL на loading и deletion title (AZ/EN ×6 widths): «Загрузка…», «Удалить изображение?» и русские actions. Нативный транспорт при этих проверках SIMULATED; текст реально rendered.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P3: оператор получает смешанный язык при загрузке/подтверждении действия.

**Первопричина / гипотеза:** Подтверждено: literals в kidsmap_site_media.js передаются kmModal; это отдельная причина от SITE-QA-07 compiled gettext.

**Source:** `static/admin/js/kidsmap_site_media.js:180`; `static/admin/js/kidsmap_site_media.js:313`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [media-errors.result.txt](../media-errors.result.txt)
- [screenshots/modal-final-viewport.png](../screenshots/modal-final-viewport.png)
- [screenshots/upload-loading-en-390.png](../screenshots/upload-loading-en-390.png)
- [screenshots/upload-error-en-390.png](../screenshots/upload-error-en-390.png)
- [current-focus.result.txt](../current-focus.result.txt)

**Область исправления:** Использовать существующий JS translation mechanism для этих состояний и ошибок, сохранить loading/disabled behaviour.

**Владелец / зависимости:** Admin frontend/localization; runtime .mo build отдельно по SITE-QA-07; loading/error/delete native checks.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-11-repair.txt). Аудит ничего не исправляет.
