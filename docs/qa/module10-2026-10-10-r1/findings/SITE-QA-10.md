# SITE-QA-10 — OFF мероприятий возвращает пустую 410 страницу

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL application error-state failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** guest. **URL/endpoint:** `/ru/events/ и canonical Event detail; AZ/EN counterparts`.

**Шаги:** Выключить events section через native settings. Открыть list и event detail во всех 18 cells.

**Ожидание:** Читаемое локализованное сообщение с выходом к доступным разделам при корректном HTTP статусе.

**Факт:** 36 checks list/detail: HTTP410, bodyLength=0; rendered browser полностью пустой.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2: человек получает пустую страницу вместо понятного результата действия/перехода.

**Первопричина / гипотеза:** Подтверждено: early guards возвращают HttpResponseGone() без body/template.

**Source:** `src/catalog/views.py:362`; `src/catalog/views.py:1298`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [flags.result.txt](../flags.result.txt)
- [screenshots/flag-event-false-list-ru-390.png](../screenshots/flag-event-false-list-ru-390.png)
- [screenshots/flag-event-false-detail-ru-390.png](../screenshots/flag-event-false-detail-ru-390.png)
- [current-boundary.result.txt](../current-boundary.result.txt)

**Область исправления:** Локализованный rendered 410 response с навигацией, сохранить семантику disabled feature и отсутствие скрытых данных.

**Владелец / зависимости:** Shared error template/header/footer, three languages/mobile/PC; SITE-QA-09 separately.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-10-repair.txt). Аудит ничего не исправляет.
