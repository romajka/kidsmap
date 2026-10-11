# SITE-QA-12 — DEBUG=False 404 не локализован и не содержит пути восстановления

**OPEN / P3 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL shared error UX failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** guest. **URL/endpoint:** `http://localhost:8824/{ru|en|default}/qa10-no-such-page/`.

**Шаги:** Открыть заведомо неизвестный URL на отдельном own DEBUG=False stand во всех 18 cells.

**Ожидание:** Читаемая общая ошибка на выбранном языке и ссылка домой/в каталог.

**Факт:** Дефолтный английский Not Found/Page not found для всех языков, 0 anchors. HTTP404 и отсутствие overflow корректны. DEBUG=True диагностические страницы исключены из findings.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P3: нет локализованного возврата в приложение после неправильной ссылки.

**Первопричина / гипотеза:** Подтверждено на локальном DEBUG=False: используется default Django 404; проектный общий error rendering не применяется. Production reverse-proxy error page не исследован.

**Source:** `src/config/urls.py`; `docs/qa/module10-2026-10-10-r1/qa_urls.py`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [keyboard.result.txt](../keyboard.result.txt)
- [screenshots/404-debug-false-ru-390.png](../screenshots/404-debug-false-ru-390.png)
- [current-boundary.result.txt](../current-boundary.result.txt)

**Область исправления:** Общий localized 404 для Django route miss с доступной навигацией, корректным статусом и без деталей внутренних URL.

**Владелец / зависимости:** URL/error handler + templates/locales, DEBUG=False tests; не менять proxy/production в этом repair.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-12-repair.txt). Аудит ничего не исправляет.
