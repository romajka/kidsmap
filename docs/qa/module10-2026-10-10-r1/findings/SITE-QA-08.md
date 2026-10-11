# SITE-QA-08 — Мобильные формы общих настроек переполняют viewport

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL application layout failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin. **URL/endpoint:** `/admin/catalog/sitebrandingsettings/1/change/ и другие общие settings sections`.

**Шаги:** Открыть заполненные формы в RU/AZ/EN на 360/390. Проверить document.scrollWidth, bounding rects inputs/file-upload, screenshot.

**Ожидание:** Форма и поля помещаются в viewport без горизонтального скролла.

**Факт:** 26 FAIL cells. Пример RU 360: document/body width=611, input vTextField width=362, file-upload width≈543.7, right≈610.7.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2: часть формы и введённых значений на телефоне выходит за экран.

**Первопричина / гипотеза:** Подтверждён DOM trigger: generic text/file controls шире доступного поля. Полный CSS cascade root ещё требует bounded inspection при repair; не доказана одна универсальная CSS строка.

**Source:** `src/catalog/templates/admin/catalog/shared_settings_change_form.html`; `src/catalog/domain_admin/site.py`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [matrix-filled.result.txt](../matrix-filled.result.txt)
- [screenshots/admin-sitebrandingsettings-ru-360.png](../screenshots/admin-sitebrandingsettings-ru-360.png)
- [current-matrix.result.txt](../current-matrix.result.txt)
- [current-settings.result.txt](../current-settings.result.txt)

**Область исправления:** Responsive bounds для generic settings fieldsets/inputs/file controls и перенос длинных путей; не скрывать проблему overflow-x:hidden.

**Владелец / зависимости:** Frontend-admin/KidsMap UI rules; native filled/errors RU/AZ/EN 360/390 и desktop regression.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-08-repair.txt). Аудит ничего не исправляет.
