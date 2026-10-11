# ANALYTICS-QA-05 — GA unavailable/error показаны как нулевая аудитория

LOCAL dirty WORKTREE, HEAD8d188b3; AUDIT ONLY. Status: OPEN; severityP2; confidence HIGH within stated local/SIMULATED scope.

Role: admin. URL/endpoint: `/admin/catalog/siteanalytics/`.

Steps: Открыть реальный локальный dashboard с обоими GA identifiers пустыми; затем SIMULATED report backend error.

Expected: Явное unavailable/error состояние; не подменять его аудиторией0 и успешным updated timestamp.

Actual: Три KPI0 и «Обновлено сегодня»; ga4.error не показан. Повторено18cells, error adapter явно SIMULATED.

Evidence: [matrix.result.txt](../matrix.result.txt), [native screenshot](../screenshots/admin-error-ru-390.png). Source: `templates/admin/catalog/site_analytics.html:24`.

Root cause: Snapshot хранит enabled/connected/error, template их не использует; kpi default0.

Priority justification: Пользователь получает ложное впечатление успешной загрузки нулевых метрик.

Attribution: relevant implementation unchanged against HEAD; pre-existing baseline source failure, no full clean-checkout or production run, new regression not established.

Repair ownership/dependencies: analytics-reviewer/frontend-admin; dependency04 period semantics.

Scope: Покажи disabled/error/partial/empty/loaded состояния по GA snapshot contract. Нули только при подтверждённом успешном пустом отчёте, updated timestamp отражает успешную загрузку. Дай доступную ошибку и повтор; RU/AZ/EN и шесть widths, без credentials details.

[Copyable standalone repair prompt](ANALYTICS-QA-05-repair.txt). No fix performed.
