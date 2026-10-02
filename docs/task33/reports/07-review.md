# Этап07 — независимый backend review

Canonical role `.agents/agents/django-reviewer/agent.md`, execution identity `/root/stage07_review`, 2026-09-29. Назначение primary: только bounded source/ACL/schema review и личный isolated QA; application не редактировалась. APPROVED IMPLEMENT07 принадлежит primary security-reviewer. Production UNKNOWN, не подключались.

LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, dirty WORKTREE. Лично проверены 30 SHA до и после запуска: совпали между собой и с `07-source-manifest.json`; HEAD не представляет новую реализацию. Changed by reviewer: только этот отчёт и `07-review-evidence.json`, scratch scripts в /tmp.

## Решение и evidence

**PASS для независимого bounded backend review07.** Незакрытых подтверждённых blocker findings нет. Это не зелёный full application suite и не production readiness.

Проверены `business_team.py:has_action/_locked_item/invite/accept/change_grant/confirm_member/create_branch`, `place_access.py:permission_configuration/platform_has_action`, `owner_place_use_cases.py:resolve_owner_permission_scopes`, `DjangoOwnerPlaceRepository.managed_queryset`, `views.py:_build_managed_places_summary`, legacy team repository/controller, `OwnerReviewsController.set_review_approval`, `business_team_api.py:business_team_action`, model transfer hooks и `domain_admin/owner.py:_BusinessTeamDiagnosticMixin`.

В начальном review найдены реальные интеграционные обходы: legacy scope и private readers доверяли active membership без live owner; repository writes принимали stale invitation; business review POST сохранял moderation; Org transfer не приостанавливал team; hidden admin допускал arbitrary grant writes; route nested precheck не гарантировал parent под lock. Primary исправил эти границы; reviewer перепроверил actual final source и лично выполнил tests, включая реальные POST/negative/races. OfferingGroup также проверяет archive родительской Activity. Platform staff permission остаётся отдельным fresh resolver и не выводится из business grant.

Place membership остаётся конкретным; NULL-place не становится сетью. selected scope не захватывает новый филиал, all_network не выдаёт Org/Program actions автоматически. Branch.create отдельный: owner Org владеет Place, сотрудник остаётся автором. Detach прекращает network grant и сохраняет current direct grant. Parent locks Organization→Place→grant/invitation сериализуют принятие/передачу/revocation и защищённый legacy Place write. Backend предоставляет action configuration; никаких frontend enum/UI changes reviewer не делал.

Codebase Memory обнаружен и использован: repository root совпал; generation10:47:26, initial paths metadata_match с best-effort caveat. New implementation graph coverage UNKNOWN; выводы проверены в actual source.

## Личные fresh проверки

Команда:

```text
python3 /tmp/task33-07-review-tools/run.py --mode all --label catalog.testcases.test_task33_permissions --label catalog.testcases.test_task33_ownership --label catalog.testcases.test_task33_catalog_schema --label catalog.testcases.owner.TestCreatedByIsAuditOnly.test_creator_manages_the_new_place_through_ownership --output /tmp/task33-07-independent-final-v3
```

Это /tmp-only extension unchanged QA04 launcher/clean environment/settings/network+libpq guards. Личный запуск: **106tests,0failures,0errors,0skip,31.641s,exit0**. Содержит35permission+39ownership+31schema+1unchanged legacy provenance case; negative endpoint/CSRF/ID checks и3новые real PostgreSQL races: transfer против accept, revoke против legacy Place write, dual accept creates one membership. Прежние ownership/schema races также вошли в запуск.

Check и makemigrations --check --dry-run PASS. Fresh DB153 migrations applied/0unapplied, catalog leaf0119. PostgreSQL17.10, Django6.0.2/Python3.12.3/psycopg3.2.10; DJANGO_TESTING=1, disposable Unix-socket PostgreSQL/network none/no ports/tmpfs, LocMem cache/email, isolated media, foreign transports guarded, production credentials absent. Cleanup PASS.

Собственные7дополнительных negatives PASS: NULL-place legacy; actual Program требует separate action; accepted invitation replay отказан; чужой nested route403 без записи; malformed stored actions fail closed; Program-only не даёт Place.edit; stale account object после deactivation немедленно теряет resolver/managed-reader access.

Личный populated0118→0119 probe PASS: concrete membership, NULL-place membership, pending invitation — **3records**, каждое прежнее concrete field byte/value-identical; новые action/base/expiry NULL не становятся согласием. Concrete grant сохранил Place.edit; NULL-place доступа не получил; pending legacy invitation с неизвестными snapshots/expiry не принят и остаётся PENDING. Raw fixtures/rows/SQL/logs не копировались в repository, только booleans/counts/test IDs/hashes.

Первый собственный extension запуск `/tmp/task33-07-independent-final` остановился до suite: ENVIRONMENT_FAILURE/ImportError, потому что /tmp override не экспортировал `commands.dump`, который импортирует QA04 fixtures. Исправлен только scratch harness; повторный fresh directory PASS. Initial cleanup PASS. Это не application regression, assertions не ослаблялись.

После первоначального независимого105PASS primary обнаружил regression только metadata provenance (`source=resolver` вместо прежнего `direct`). Legacy assertion не изменялся; primary воспроизвёл RED и восстановил direct/team/organization provenance при прежнем canonical action resolver. Этот отчёт обновлён после личного fresh106PASS на updated30SHA,7negatives и retention повторно PASS; предыдущий105run сохранён исторически в evidence.

## Границы и handoff

Independent full canonical suite NOT RUN; его свежую baseline классификацию проверяет primary, этот review не выдаёт чужой запуск за личный. Rendered browser/production/external integrations/реальные пользовательские данные/08–28 NOT RUN. Новые UI экраны не создавались. Source/runtime evidence проверяет локальные synthetic contracts, эксплуатация и нагрузка production UNKNOWN.

Named handoff: **primary security-reviewer `/root`** — сверить финальный full suite с06 и exact changed outcomes, сохранить matching30source SHA, закрыть отчёт07/журнал и только собственный active_run. Следующий08 запускается отдельно. Evidence: [07-review-evidence.json](07-review-evidence.json).
