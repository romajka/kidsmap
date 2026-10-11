# ANALYTICS-QA-03 — Легитимный Origin с портом отклонён

LOCAL dirty WORKTREE, HEAD8d188b3; AUDIT ONLY. Status: OPEN; severityP2; confidence HIGH within stated local/SIMULATED scope.

Role: guest. URL/endpoint: `http://localhost:8829/ru/events/track/`.

Steps: На публичной карточке открыть номер и нажать ссылку звонка; браузер отправляет same-origin beacon/fetch с Origin localhost:8829.

Expected: Успешный endpoint; phone_click delta+1.

Actual: 403 forbidden_origin; contact delta0. Соответствующий portless Origin проходит7source probes и own Django.

Evidence: [source-review/origin-checks.json](../source-review/origin-checks.json), [native screenshot](../screenshots/native-phone-open-ru-1440.png). Source: `src/catalog/views.py:234`.

Root cause: allowed_hosts удаляет port, Django url_has_allowed_host_and_scheme сравнивает полный netloc.

Priority justification: Потеря contact events на explicit/nondefaultport; portless production UNKNOWN.

Attribution: relevant implementation unchanged against HEAD; pre-existing baseline source failure, no full clean-checkout or production run, new regression not established.

Repair ownership/dependencies: django-reviewer/security-reviewer; точное origin/trusted-origin правило.

Scope: Исправь сравнение легитимных same-origin host:port без расширения доверия к другим origin. Проверь explicit/nondefault/default ports, localhost, trusted origin, hostile origin, null/missing Origin, Referer fallback, HTTPS и rate limits. QA port proxy не переносить в приложение.

[Copyable standalone repair prompt](ANALYTICS-QA-03-repair.txt). No fix performed.
