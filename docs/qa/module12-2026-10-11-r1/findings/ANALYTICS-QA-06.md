# ANALYTICS-QA-06 — AZ дельта содержит русский текст

LOCAL dirty WORKTREE, HEAD8d188b3; AUDIT ONLY. Status: OPEN; severityP3; confidence HIGH within stated local/SIMULATED scope.

Role: owner. URL/endpoint: `/account/places/1/analytics/`.

Steps: С вымышленными previous/current rows открыть AZ owner analytics; previous_views>0.

Expected: Дельта и пояснение на AZ.

Actual: «…% к прошлому периоду» в AZ; native screenshot6 widths.

Evidence: [matrix.result.txt](../matrix.result.txt), [native screenshot](../screenshots/owner-filled-az-390.png). Source: `src/catalog/templates/pages/owner_analytics.html:32/44`.

Root cause: Для percentage small template разделяет только EN и else(RU); AZ попадает в RU.

Priority justification: Локализация пояснения нарушена, числовая метрика корректна.

Attribution: relevant implementation unchanged against HEAD; pre-existing baseline source failure, no full clean-checkout or production run, new regression not established.

Repair ownership/dependencies: frontend-reviewer/analytics-reviewer; перевод обоих delta labels.

Scope: Локализуй пояснения дельты просмотров и контактных действий дляAZ/RU/EN существующей системой. Проверь previous0 (без процента), положительную/отрицательную/нулевую дельту и длинные значения на360/390/768/1024/1280/1440.

[Copyable standalone repair prompt](ANALYTICS-QA-06-repair.txt). No fix performed.
