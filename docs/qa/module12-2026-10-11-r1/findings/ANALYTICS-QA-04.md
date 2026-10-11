# ANALYTICS-QA-04 — Период90 использует годовые GA KPI

LOCAL dirty WORKTREE, HEAD8d188b3; AUDIT ONLY. Status: OPEN; severityP2; confidence HIGH within stated local/SIMULATED scope.

Role: admin. URL/endpoint: `/admin/catalog/siteanalytics/?period=90`.

Steps: Выбрать90дней. В SIMULATED GA snapshot задать отличающиеся month/year/quarter числа; читать native KPI.

Expected: KPI относятся к выбранным90дням.

Actual: На кнопке90; KPI3650/3651/3652 из year. Own assertion quarter92 vs year367 FAIL. Chart/table отдельно честно подписаны30дней.

Evidence: [test-review/ga90-observation.json](../test-review/ga90-observation.json), [native screenshot](../screenshots/admin-filled-ru-390.png). Source: `src/catalog/services/admin_analytics.py:37`.

Root cause: _ga_period_key(90)→year; Reporting PERIODS.year=364daysAgo.

Priority justification: Неверное сравнение периода и бизнес-оценка; реальные GA значения NOT RUN.

Attribution: relevant implementation unchanged against HEAD; pre-existing baseline source failure, no full clean-checkout or production run, new regression not established.

Repair ownership/dependencies: analytics-reviewer + django-reviewer; GA report range contract, timezone property UNKNOWN.

Scope: Согласуй диапазон KPI с90дней selector; сохрани явный фиксированный30дней contract chart/tables либо отдельно согласуй его изменение. Проверь7/30/90/365, invalid fallback, inclusive calendar endpoints/timezone, partial GA failure; только mocked reports без реальных запросов.

[Copyable standalone repair prompt](ANALYTICS-QA-04-repair.txt). No fix performed.
