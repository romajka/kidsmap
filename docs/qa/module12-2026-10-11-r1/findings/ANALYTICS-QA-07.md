# ANALYTICS-QA-07 — Отказ analytics write ломает публичную карточку

LOCAL dirty WORKTREE, HEAD8d188b3; AUDIT ONLY. Status: OPEN; severityP2; confidence HIGH within stated local/SIMULATED scope.

Role: guest. URL/endpoint: `/ru/place/1-vymyshlennoe-qa12-live/`.

Steps: При здоровых catalog reads через собственный QA adapter вызвать DatabaseError actual DjangoFunnelEventRepository.create_event; открыть карточку.

Expected: Карточка200, аналитика честно недоступна; без фиктивного записанного события.

Actual: Native500 на390/1440, event delta0. Own corrected injection confirmed=true; исходный неверно подключённый mock исключён. SIMULATED fault.

Evidence: [test-review/analytics-fault-observation.json](../test-review/analytics-fault-observation.json), [native screenshot](../screenshots/public-analytics-backend-failure-ru-390.png). Source: `src/catalog/controllers/place_controller.py:735`.

Root cause: Tracking write выполняется синхронно в build_detail_context без обработки отказа независимого analytics storage.

Priority justification: Условный отказ публичного контента из-за analytics write; production incident не утверждается.

Attribution: relevant implementation unchanged against HEAD; pre-existing baseline source failure, no full clean-checkout or production run, new regression not established.

Repair ownership/dependencies: analytics-reviewer/django-reviewer; transaction handling, telemetry errors без payload leakage.

Scope: Изолируй отказ analytics persistence от публичного SSR при исправной основной БД; проверь реальный вызванный repository mock и transaction recovery, logs только безопасные агрегаты, не скрывай основную catalog/ACL ошибку. Native200/reload, event delta0, disabled flag и штатный delta+1 обязательны.

[Copyable standalone repair prompt](ANALYTICS-QA-07-repair.txt). No fix performed.
