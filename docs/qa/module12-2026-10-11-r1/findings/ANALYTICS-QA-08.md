# ANALYTICS-QA-08 — AZ административная аналитика имеет русские labels

LOCAL dirty WORKTREE, HEAD8d188b3; AUDIT ONLY. Status: OPEN; severityP3; confidence HIGH within stated local/SIMULATED scope.

Role: admin. URL/endpoint: `/admin/catalog/siteanalytics/`.

Steps: ВыбратьAZ в admin, открыть KPI/график/таблицы с отключённымGA либо SIMULATED filled report.

Expected: Названия метрик и подписей наAZ, без неверных переводов.

Actual: KPI/подписи наRU при Statistika/Unikal/Baxışlar наAZ;11 fuzzy PO ключей отсутствуют вMO,15проверенныхentries совпадаютHEAD.

Evidence: [source-review/locale-checks.json](../source-review/locale-checks.json), [native screenshot](../screenshots/admin-filled-az-390.png). Source: `locale/az/LC_MESSAGES/django.po:11260`.

Root cause: gettext вызван корректно; fuzzy drafts неверны и не попали вMO. Компиляция без проверки переводов недостаточна.

Priority justification: Непоследовательная локализация admin, числа не изменены.

Attribution: relevant implementation unchanged against HEAD; pre-existing baseline source failure, no full clean-checkout or production run, new regression not established.

Repair ownership/dependencies: frontend-admin; locale build dependency SITE-QA-07, отдельный content cause; not duplicate owner06.

Scope: Согласуй и исправь только11 неверных fuzzy AZ analytics переводов, затем обнови соответствующийMO существующим locale workflow. Не снимай fuzzy со всего файла и не меняй чужие pendingPO строки. Проверь placeholders, native AZ KPI/chart/tables/empty/error и RU/EN smoke; сохранность иных locale edits обязательна.

[Copyable standalone repair prompt](ANALYTICS-QA-08-repair.txt). No fix performed.
