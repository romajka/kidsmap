# KidsMap — LOCAL acceptance,2026-10-19

Git publication follow-up2026-10-19: user explicitly authorized committing/pushing all completed work to the current codex/module09-transfer-2026-10-16-r1 branch. The implementation acceptance below is historical at base75c6c18; production remains excluded. Versioned plan: docs/plans/project-fixes-2026-10-19.md; complete sanitized report: docs/reports/project-fixes-2026-10-19.md. Raw QA/runtime evidence stays local ignored. No main merge or deploy is authorized.

## Approved14 remediation —2026-10-19

Current decision: **all14items implemented and accepted LOCAL; production NOT_CONTACTED/NOT_APPLIED**. User explicitly approved the plan and local implementation of all14audit points. Modules01–13 remain closed. No commit/push, reset/clean/force push, deployment, production migration/restart/config/data/cleanup occurred. Source files and new migrations remain dirty for review.

Repository C:\kidsmap; origin https://github.com/romajka/kidsmap.git; branch codex/module09-transfer-2026-10-16-r1; unchanged HEAD75c6c18beb35f019a76e96543723448d8ed1cb7d. Two original stashes and implementation-entry dirty reports preserved.0142retained; additive0143_pending_email_change and0144_workflownotification_event_context_db_default tested on disposable PostgreSQL only.

Fresh evidence: full03 **2759/2759 PASS,1050.847s,exit0**, all2679baseline IDs retained,80new;139NodePASS;32standalone PythonPASS/1Windows-junctionSKIP;330responsive browser states and44interaction assertions. Browser visual review then found an empty email-error marker: one conditional markup fix plus one regression. Final UI04 **154/154 PASS,exit0** and **90repeat/additional browser states** cover that last change. The full2759result belongs to full03; it is not represented as another complete run after the markup-only delta. All other application source is identical. Check/drift passed on both snapshots. Exact source manifests/commands, retries and full per-point acceptance are local ignored evidence in docs/qa/project-fixes-2026-10-19/REPORT.md and acceptance.json. Original71audit evidence files were hash-verified unchanged.

| № | Проблема | Итог | Что изменилось | Доказательство |
|---|---|---|---|---|
| 1 | Подтверждение нового email | LOCAL PASS | Рабочий адрес меняется только после кода на новый. До этого новые приглашения и письма не дают прав. Хеш кода,10минут,5попыток,60секунд; проверены гонки, отмена, сбои отправки и удаление аккаунта. | test_project_fixes_email.py;154final focused;25browser actions |
| 2 | Права SEO-админки | LOCAL PASS | Изменения требуют POST,CSRF и нужных разрешений. Просмотр не даёт права запускать исправления или удалять историю. | 26SEO regressions;native dialog keyboard AZ/RU/EN |
| 3 | Приватные файлы при обновлении | LOCAL PASS | Добавлены два постоянных private volumes и явные корни. Оба хранилища запрещают прямой URL. Preflight останавливает выпуск при незащищённых файлах, включая остановленный контейнер. Перенос реальных файлов ещё требует отдельного выпуска. | Two real Docker containers;storage-review.md;3guard tests |
| 4 | Открытие SEO-отчёта | LOCAL PASS | Исправлено форматирование для Django6; динамический текст экранируется. | SEO report200;15responsive report states;escaped script assertion |
| 5 | Цены при публикации занятий | LOCAL PASS | Публикация и снятие занятия обновляют цены и доступность каталога с учётом вложенных тарифов. Сохранены старые скалярные цены, бесплатные и договорные варианты, валюты. | backend full331+6targeted;fresh full regression |
| 6 | Повреждённое расписание | LOCAL PASS | Некорректные JSON/дни/интервалы дают ошибку поля, сохраняя прежние часы; валидное «всё закрыто» остаётся доступным. | Owner HTTP,admin form,shared writer regression |
| 7 | Историческая площадка мероприятия | LOCAL PASS | Карточка мероприятия организации показывает утверждённое место, даже если площадку переименовали или скрыли. | Approved snapshot regression;real organization screenshot |
| 8 | Будущая работа специалиста | LOCAL PASS | Будущая работа помечена датой начала на AZ/RU/EN и не выдаётся за текущую. Согласия и версии связи перепроверяются. | Future/stale ownership regression;real organization screenshot |
| 9 | Запросы страницы организации | LOCAL PASS | Вместо30/74запросов для1/5филиалов —23/23; с занятием и тарифом в каждом филиале —26/26. Данные читаются пакетно без постоянных доверенных кэшей. | Final full BACKEND_QUERY_BUDGET and BACKEND_ACTIVITY_QUERY_BUDGET |
| 10 | Сохранение SEO-истории | LOCAL PASS | Частичная или неудачная проверка сохраняет прежние замечания. Закрываются только фактически проверенные и исчезнувшие проблемы. | Scoped/failed audit regressions;SEO report |
| 11 | Честный результат автоисправления | LOCAL PASS | Статус fixed требует повторной проверки исходной проблемы.200сам по себе недостаточен;404/неизвестное правило/непроверяемая схема не получают ложный успех. Несвязанные рейтинги больше не меняются. | Invariant/schema negative regressions |
| 12 | Настоящий откат рейтинга | LOCAL PASS | Поддерживаемые старые изменения восстанавливают сохранённые числа атомарно. При последующих изменениях данных откат отказывается перезаписывать их. Необратимые действия так и помечаются. | Exact restoration/repeated rollback/interference tests |
| 13 | Совместимость миграции уведомлений | LOCAL PASS | 0142не переписана.0144оставляет SQL default {}, поэтому старый INSERT после миграций работает. Проверен заполненный переход0141→0142→0144и обратимость0144; выпуск блокируется без подтверждённой остановки писателей. | SQL old worker INSERT;MigrationExecutor rehearsal;3release boundary tests |
| 14 | Запросы sitemap | LOCAL PASS | Для5/25занятий и15/75локализованных URL:12/52→2/2запроса. Проверены языки, снимки, скрытые программы, устаревшая связь и повторное использование генератора. | Final full SITEMAP_QUERY_BUDGET;canonical batch contract |

Release boundary: docs/PRIVATE_STORAGE_RELEASE.md is the concrete future preservation/migration/verification/recovery plan. Protect and verify existing private bytes before replacement; prepare both named volumes with0700roots; stop all writers for the entire0142–0144batch. New SQLdefault preserves old INSERTs after0144, but rollback to old app code reintroduces the email/SEO defects, so keep affected mutations blocked. Production topology, mounts, actual schema, backup restore and external SMTP/Google/search indexing remain unverified. Docker Compose CLI is absent locally: actual source-matched named volumes/containers/storage and a narrow Compose-ps adapter were exercised, not compose up. Physical devices/Safari and production performance were not tested.

Measured query budgets: Organization1/5branches30/74→23/23; with one priced Activity perbranch26/26. Activity sitemap5/25activities12/52→2/2. These measurements do not promise production latency. Legacy current-email accounts without any proof rows retain unchanged-address compatibility, with no invented verification; existing mismatched proof rows fail closed.

One pre-existing cosmetic observation outside the14scope: owner_places.html:84Organization-links controls use tight/native styling and plain links. No measured functional/overflow regression; source unchanged. Proposed separately, not silently implemented. Own labelled test containers/volumes/network/localhost relay and own browser session stopped; source/profiles/evidence retained. active_run closed by lead.

## Historical audit before implementation


Mode: **AUDIT ONLY**. User requested a broad project review, tests, bugs and optimization/SEO recommendations. No application fixes, commit, push, deployment or production access. Modules01–13 and prior accepted fixes remain CLOSED LOCAL in their earlier verified boundaries; this audit does not restart them. New findings require a separate agreed implementation scope.

Decision: **address authorization defects and private-file persistence before recommending a release**. No current production compromise, outage or data loss is established. Source-level defects are accompanied by isolated reproductions; production applicability remains UNKNOWN until a separate read-only preflight.

Lead: `/root`, canonical kidsmap-orchestrator; specialist definitions from `.agents/registry.json`. Backend and SEO specialists supplied source audits, then reviewed root-owned runtime evidence. Security specialist supplied source report/probes but did not complete final runtime sign-off; `/root` independently validated six prepared synthetic probes and source boundaries. No claim of independent security runtime execution.

## 1. State and snapshot

- Repository `C:\kidsmap`, origin `https://github.com/romajka/kidsmap.git`, branch `codex/module09-transfer-2026-10-16-r1`.
- LOCAL HEAD `75c6c18beb35f019a76e96543723448d8ed1cb7d`. Entry tracked/untracked tree clean; two existing stashes left untouched. Entry manifest3106tracked files preserved locally before report/journal edits.
- Disposable runtime: exact `git archive HEAD`, read-only source mount; Python3.12.15, Django6.0.9, PostgreSQL17.11, Node24.14.0, jsdom29.1.1, isolated Playwright Chromium. Deps image `sha256:0f663c65afc2230d52db10c87ec91996666838377e5d9c8bd90fc41e7610b8b1`.
- DB instances have networking disabled, dedicated qa_stage04/test_qa_stage04 and owned Unix sockets. Existing `scripts/run_isolated_quality.py` clears inherited environment, verifies actual database/role/socket and uses disposable media, LocMem cache/mail and disabled external integrations.
- Codebase Memory `C-kidsmap`: ready but generation2026-10-16T18:56:53Z predates this source. Architecture/symbol/impact tools used first; cited paths reported changed/unavailable coverage. Relevant source/routes/ORM were read directly; historical graph copies were not treated as active code or completeness evidence.
- PRODUCTION: NOT_CONTACTED. Actual image/SHA/schema/data/private mounts, mail, Google and search-console state UNKNOWN. Previous dated release authorization in the old decision pointer is history; current task supplies no production-write authorization.

## 2. Strengths

- Versioned publication candidates, rechecked authorization, ordered parent locks, PostgreSQL constraints and compare-and-swap operations have substantial existing regression coverage.
- Catalog/map readers already include batching and paged data. Organizations, events, specialists, teams and immutable occurrence facts have implemented domain contracts.
- Current JSON-LD serializer escapes script delimiters; Event schema/sitemap exist. Owner readiness delegates to the canonical evaluator. Old findings claiming otherwise were retired for this snapshot.
- Private specialist downloads are access-controlled and outside public media. The confirmed storage issue below concerns persistence across container replacement.
- Fresh public/login, account/editor and selected admin responsive matrices contain no unexpected local HTTP errors, page errors or horizontal document overflow in the tested fixtures. This is bounded browser evidence, not full accessibility/device/provider acceptance.

## 3. Confirmed problems

IDs are deduplicated. All environments below are LOCAL exact HEAD; affected production records/exposure are UNKNOWN. Detailed evidence is local and ignored under `docs/qa/project-audit-2026-10-19/`.

| ID / priority | Trigger and observed effect | Source / owner |
|---|---|---|
| SECURITY-01 / P1 | An active user changes profile to an unused, unverified invited email, discovers the invitation in inbox and accepts it. Both place and organization grant paths reproduced without control of the fictional mailbox. Existing-user account takeover is not claimed. | `src/catalog/forms.py:791`, `controllers/auth_controller.py:111`, `controllers/workflow_notifications.py:23`, `services/business_team.py:219`; Django/security |
| SECURITY-02 / P1 | Ordinary nonvolunteer staff with zero model permissions uses GET custom SEO admin URLs. Synthetic history was deleted; auditor/fixer write-mode dispatch reproduced with service mocks. GET also lacks POST/CSRF protection. | `src/catalog/domain_admin/seo.py:39`, handlers61/77/95; admin/security/SEO |
| SECURITY-03 / P1 conditional release risk | Compose persists media/static only. `/kidsmap-private-media` and `/app/private_media_drafts` are writable-container paths. Two clean containers using this mount pattern retained the public synthetic file but lost both private markers. Current production file existence and full app recovery remain unverified. | `src/config/settings.py:497`, `src/catalog/private_storage.py:17`, `services/server_drafts.py:124`, `docker-compose.yml`; release/security/DB |
| SECURITY-04 / P2 | Opening a persisted SEOAuditRun report produces real authenticated Chromium HTTP500. `format_html` receives no interpolation arguments and Django6 raises TypeError. | `src/catalog/domain_admin/seo.py:159`; admin/SEO |
| BE-01 / P2 | Activity approval leaves Place scalar price NULL while public nested tariff137AZN exists; the public catalog excludes the place. After unpublish there are0public plans but legacy fallback still displays137AZN. | `src/catalog/services/publication.py`, `services/pricing_plans.py`, `services/content_quality.py`; Django/DB |
| BE-02 / P2 | `[null]` or `[{}]` schedule JSON raises TypeError/KeyError in all three owner/admin form constructors. Invalid JSON in the shared helper can validate as seven closed days and overwrite a real schedule; the latter proof isolates the helper, not a complete owner/admin HTTP save. | `src/catalog/forms.py:135`; Django/owner/admin |
| BE-03 / P2 | Organization Event card displays today's Place name instead of approved `venue_snapshot.label`, while Event detail retains the historical venue. | `src/catalog/controllers/public_details.py:141`; Django/public UI |
| BE-04 / P2 | Confirmed employment starting30days later appears as an ordinary specialist on Organization page without future state/date; the same specialist profile correctly classifies it as future. | `src/catalog/controllers/public_details.py:98`, `services/specialist_presentation.py:35`; Django/public UI |
| BE-05 / P2 optimization | Warm Organization detail measured30SQL queries for1branch and74for5: +11queries per extra branch. Reader materializes all branches and performs per-branch enrichment. No production latency or index prescription is inferred. | `src/catalog/controllers/public_details.py:26`, `services/public_presentation.py`; Django/DB |
| SEO-PROJECT-01 / P2 | Partial sitemap/schema/links audits and scanner failure erase unrelated open SEOIssue rows. Synthetic ORM proofs show all four retention scenarios lose the old issue. | `src/catalog/services/seo_audit_engine.py:69`; SEO/Django |
| SEO-PROJECT-02 / P2 | `missing_canonical` remains absent, but safe-fix records `fixed` after HTTP200 and after HTTP404. The original metadata invariant is not rechecked. | `src/catalog/services/seo_fix_engine.py:112`; SEO/Django |
| SEO-PROJECT-03 / P2 | Rating fixture9/4.5 becomes0/0 after recalculation; rollback remains0/0 while recording `is_rolled_back=True`. Old values are not restored. | `src/catalog/services/seo_fix_engine.py:155`; SEO/Django/DB |
| RELEASE-01 / P2 rollout risk | After0142, `event_context` is NOT NULL without a persistent SQL default. An INSERT matching old code and omitting the field fails. Existing deploy script migrates while the old web stays online; code-only rollback is not established safe. | `src/catalog/migrations/0142_workflownotification_event_context.py`, `scripts/deploy-server.sh:64`; release/DB |

Confidence HIGH for these isolated observations. SECURITY-03 impact is conditional on corresponding files existing at container replacement; no assertion of production data loss. RELEASE-01 is a tested mixed-version compatibility constraint, not a failed migration. Every proposed remediation must preserve existing permissions, historical facts and legacy compatibility.

## 4. Tech debt

- Verified current email has multiple representations/consumers; mutable User.email is used as authorization identity in invitation paths.
- Custom admin endpoints need a consistent explicit action-permission, method and CSRF contract. Default admin wrapper access does not establish model-action authorization.
- Projection updates through signals coexist with QuerySet.update publication transitions. Tariff/public-visibility readers and writers must share a declared refresh contract.
- SEO engine tests assert statuses more strongly than restored values or original metadata invariants; diagnostic false-green remains possible.
- Private storage paths need one complete persistent/backup inventory; source defaults alone are insufficient for release and recovery.
- Historical knowledge pages predate major schema/runtime changes; use them for navigation, then verify current source.

## 5. Risks and limits

No production crawl, SQL, credentials, logs, image inspection, data changes, migration, restart, backup or cleanup. No user records/private bytes copied from production. No live SMTP/OAuth/Google Maps/Search Console, physical devices, Safari/Firefox, full screen-reader acceptance, dependency advisory audit or full production restore drill.

Browser fixtures:26fictional Places,1Organization,5affiliated branches and synthetic accounts. External unpkg.com/maps.google.com/fonts.googleapis.com blocked; real provider geometry and remote-font fidelity are not certified. Public metadata passed the sampled locale/route matrix; that does not establish search-engine indexing/rank or production canonical host correctness.

Authentication throttling, OTP concurrency, direct tariff-write races and broader team resolver query costs are source-review risks requiring scoped measurements, not confirmed exploits. All source-only optional currency scenarios are explicitly NOT RUN. Historical10000-place performance and carousel observations were not remeasured or silently closed.

## 6. Dead / legacy candidates

No deletion recommended or performed. Scalar/JSON/text compatibility paths, identity wrappers and historical events remain in use or usage UNKNOWN. Graph absence, empty synthetic tables and tests alone do not establish safe deletion of code or DB structures.

## 7. Fresh checks

Full Django gate: **2679tests PASS,0failures/0errors/0skips,806.098s, exit0**. Fresh migrate (including catalog0142), system check and `makemigrations --check --dry-run` completed. All2679discovered methods appear in the log; this is a current run on this PC, not the source-PC historical result.

Other completed checks:

- Node25workflow unit/DOM files:139PASS,0FAIL,0SKIP, exit0, with actual authenticated Django photo-form fixture.
- Standalone Linux Python:27tests,26PASS/1Windows-junctionSKIP, exit0. `pip check`: no broken requirements.
- Extra characterization:14tests OK/2.805s, exit0:6security +7backend +1migration. PASS here means the defect/constraint reproduced; it is not a product acceptance result.
- SEO ORM: four retention cases,200/404false-fix cases, rating rollback; synthetic transactions rolled back, network mocked. Exact-source safe-serialization probe also passed.
- Real Chromium:240responsive states =105public/login +60account/editor +75admin, AZ/RU/EN ×390/768/1024/1280/1440. All sampled routes200, no unexpected local HTTP errors/page errors/document overflow; public JSON-LD parse, main landmark, images and basic button names checked.19keyboard/navigation/search checks passed. Additional persisted SEO report intentionally reproduced HTTP500 and remains OPEN.
- Container replacement marker proof and0142SQL-default compatibility proof reproduced the release risks. This is not a full upload/recovery or production migration rehearsal.

Exact scripts/commands, logs, JSON and failed-attempt ledger are local under `docs/qa/project-audit-2026-10-19/commands.md`, `attempts.md`, `entry.json`, `security-runtime-validation.md`, `backend.md`, `seo.md`. Screenshots: `output/playwright/project-audit-2026-10-19/`. Intentionally absent historical docs/qa/verify_transfer.py were not restored. No test assertions or application source were changed for green.

## 8. Recommendations and handoff

1. Agree a first scope for SECURITY-01/02: verified email identity and explicit SEO admin action authorization/method/CSRF; negative tests for ordinary/staff/volunteer/reviewer/superuser and current/pending addresses.
2. Before any release, agree persistent private-root configuration and byte-preserving transition/recovery acceptance for SECURITY-03. Coordinate0142with old/new writers and rollback; do not run the broad deploy script as a diagnostic.
3. Address BE-01/02with one domain contract for tariff projection/visibility and shared fail-closed schedule validation. Preserve legitimate missing-input/draft/legacy paths.
4. Repair SEO report rendering, retention, actual metadata rechecks and truthful rollback semantics. Engine green status must not be used as current SEO acceptance until fixed.
5. Optimize Organization branch reader first: measured+11queries per branch. Separately Activity sitemap measured12queries/5activities/15URLs versus52queries/25activities/75URLs (warm local0.0345s→0.1084s). This is a P3 batch-reader candidate, not a demonstrated production latency incident or promised speedup.
6. Align Event venue and employment timing across public projections; then repeat affected locale/browser checks. Optional Event schema image enrichment and broader SEO audit coverage follow correctness/security work.

Named next owners: Django/security for identity and custom admin boundaries; release/DB/security for persistent storage and0142rollout; Django/DB for pricing/schedules/query batching; SEO/admin for diagnostic engine and report; integration/browser for acceptance. Implementation awaits user's decision on concrete scopes.

## 9. Priorities and decision

- P0: none established.
- P1:2confirmed authorization defects (SECURITY-01/02) and1conditional private-storage release/data-loss risk (SECURITY-03).
- P2:10confirmed isolated bugs/rollout constraints (SECURITY-04, BE-01…05, SEO-PROJECT-01…03, RELEASE-01).
- P3/candidates: measured Activity sitemap query scaling, diagnostic coverage/schema enrichment, contract consolidation. Unmeasured risks are not promoted to confirmed findings.

Recommendation: remediate the P1 boundaries/storage risk first; source and current test success do not authorize production release. Preserve module closure and existing work; stop at recommendations. The previous decision pointer is preserved in local `docs/qa/project-audit-2026-10-19/master-before.md`.
