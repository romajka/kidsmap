# ANALYTICS-QA-01 — Staff без model permission читает общую статистику

LOCAL dirty WORKTREE, HEAD8d188b3; AUDIT ONLY. Status: OPEN; severityP2; confidence HIGH within stated local/SIMULATED scope.

Role: staff. URL/endpoint: `/admin/catalog/siteanalytics/`.

Steps: Войти активным staff без view_siteanalytics/change_siteanalytics; открыть URL напрямую.

Expected: 403/404, метрики недоступны.

Actual: 200; реальная страница общей статистики. С SIMULATED GA staff видит300/301/302. Проверено18 cells.

Evidence: [test-review/staff-permission-observation.json](../test-review/staff-permission-observation.json), [native screenshot](../screenshots/acl-admin-staff-ru-390.png). Source: `src/catalog/domain_admin/site.py:470`.

Root cause: changelist_view не вызывает model permission check; admin wrapper проверяет лишь active staff.

Priority justification: Доступ к агрегатам вне назначенных прав; раскрытие индивидуальных записей не доказано.

Attribution: relevant implementation unchanged against HEAD; pre-existing baseline source failure, no full clean-checkout or production run, new regression not established.

Repair ownership/dependencies: analytics-reviewer → django-reviewer/security-reviewer; правило разрешённых model permissions, proxy admin routes.

Scope: Добавь проверку view/change permission в статистическом changelist, согласованную с действующим admin ACL; проверь staff без permissions/с view, superuser, guest и proxy routes. Не выдавай staff дополнительные права для обхода ошибки.

[Copyable standalone repair prompt](ANALYTICS-QA-01-repair.txt). No fix performed.
