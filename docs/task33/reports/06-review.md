# Этап 06 — независимая проверка серверной границы

**PASS.** Security-reviewer `/root/stage06_security`, 2026-09-29; canonical definition `.agents/agents/security-reviewer/agent.md`, режим AUDIT. Исполнитель не менял application, tests, QA или чужие отчёты. Авторизация пользователя: только этап06. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, branch `seo-indexability-20260916`; проверена dirty WORKTREE, а не только HEAD. Production UNKNOWN, не подключались. Полный SHA256 snapshot проверенного source находится в [06-review-evidence.json](06-review-evidence.json).

Codebase Memory проверен до исследования source: project/root совпадают. Финальный coverage generation `2026-09-29T10:30:26Z`, full; десять основных путей имеют `metadata_match/no_recorded_issue`. Ignored inventory truncated2000/2025; coverage best-effort. Критические выводы проверены в файлах.

Проверены `organization_ownership:_actor/_reviewer/submit_claim/moderate_claim/request_join/_confirm/detach/transfer_owner`, JSON controller и его URL, `place_access:has_place_permission/organization_place_permissions`, `Place.save` и `catalog_structure:preserve_place_structure/save_program/save_activity`, model moderation и admin callbacks. Создание ограничено allowlist: существующий ID/owner/status/verified не принимаются. Claim остаётся pending, передачу решает уполномоченный active staff; владение и публикация разделены CLAIM/PUBLICATION. Volunteer Org proposal не создаёт business owner; существующий volunteer Place workspace сохраняется. Новые Place/Org получают управление без verified/publication. Прямые права и team memberships остаются per-Place; новая динамическая Org-owner связь даёт view/edit/stats только при подтверждённом business link и актуальных версиях обеих сторон. Informational link и pending requests не выдают эти права.

Оба current owners подтверждают join; один owner подтверждает обе стороны одним запросом. Locks и ownership versions исключают согласие до смены владельца, включая away-and-back; повтор approved join не увеличивает counter. Transfer приостанавливает прежнюю Place team и отменяет её pending invitations; stale Org/Place full save не возвращает владельца или старое Org proof. Для legacy owner-controller write используется повторный ACL под Org→Place lock. Detach доступен любой стороне, включая archived Org; approved Program материализуется с provenance, local IDs/prices/groups/reviews/visibility сохраняются, inherited contacts прекращаются.

В ходе независимого source review lead получил и исправил конкретные проблемы:

| Граница | Проверенная коррекция |
| --- | --- |
| Management claim | Старый model callback больше не активирует карточку и не разрешает moderation обычному account. |
| Stale Org full save | Сохраняются текущие owner/version/proof; старое подтверждение не восстанавливается после transfer. |
| Approved Program snapshot | Предыдущая approved часть фиксируется до pending edit; partial Activity.save сохраняет snapshot/provenance. |
| Archived affiliation | Архив Org не блокирует detach; legacy create использует общий duplicate warning и явный independent create. |
| Admin stale claim | Narrow catch ValidationError/ValueError даёт warning/redirect либо bulk skip; PermissionDenied сохраняет403. |
| Network edit / Org transfer | Org lock получен до Place lock и fresh ACL; deterministic PostgreSQL case доказывает ожидание transfer и отказ revoked owner. |

Последние два RED воспроизвёл lead (`/tmp/task33-06-red-admin`, `/tmp/task33-06-red-network-lock`); reviewer не присваивает себе эти запуски. Финальная независимая проверка reviewer лично выполнена:

```text
python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_ownership --label catalog.testcases.test_task33_catalog_schema --output /tmp/task33-06-security-independent-final
```

**70 tests =39 ownership +31 schema; 0 failures,0 errors,0 skips;22.636s,exit0.** Сюда входят foreign IDs/mass assignment, CSRF/POST/auth, active account и volunteer boundaries, два/один owner, informational link, stale claim/deleted applicant, idempotency, stale full saves/proof, сохранение approved snapshot при pending edit, partial snapshot,11-е место, duplicate choice и real PostgreSQL races: final confirmations, competing claims, transfer/confirmation, detach/pending edit, network edit/Org transfer. Django check и makemigrations --check --dry-run PASS. PostgreSQL17.10, catalog leaf0118,152 applied/0 unapplied. Fixture forward migration сохраняет прежние поля/IDs/URLs. DJANGO_TESTING=true; disposable single DB/cache/media/email, network/libpq guard, external_credentials_present=false. Cleanup PASS; собственные container/run/socket scratch удалены. Промежуточный независимый68-test run тоже PASS, но финальным evidence служит70-test run.

Подтверждённых оставшихся security blockers этапа06 нет. NOT RUN reviewer: полный application suite (его baseline comparison выполняет lead), rendered browser (новых forms/UI в этом server scope нет), production, внешние integrations. SQL/records/raw logs в repository не копировались. Это не аудит всех legacy photo/team/background writers и не доказательство будущего stage07 grants или stage08 revision workflow; внутренние integrity hooks не являются самостоятельными ACL APIs. Публичный Program renderer и полный редакционный цикл остаются следующими отдельными scopes.

Handoff → **django-reviewer `/root`**: сверить финальные source SHA, закончить полный baseline comparison, отчёт06/журнал и снять active_run. Следующие этапы и production reviewer не запускал.
