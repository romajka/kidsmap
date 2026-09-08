# QA audit — 2026-09-08

Role: integration-reviewer. Execution identity: `/root/audit_qa`, independently delegated runtime specialist; definition `.agents/agents/integration-reviewer/agent.md`. LOCAL HEAD: `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`; application source equals HEAD (`git diff --name-only HEAD -- src static templates requirements.txt .github scripts` empty). Existing agent-system WORKTREE changes preserved. PRODUCTION UNKNOWN; never contacted. Scope: existing benign regression tests, discovery, isolated environment, CI source; no application fixes. Verification-before-completion and systematic-debugging skills applied to evidence classification.

## 1. Состояние области

Python 3.12.3, Django 6.0.2 available in `.venv`. Safe disposable harness: `/tmp/kidsmap-audit-20260908-qa/run.py` + `audit_settings.py`. Clears inherited environment while preserving HOME, sets DJANGO_TESTING=1/DEBUG=1, source settings plus explicit SQLite database, in-memory test database, LocMem cache/email, temporary media/static. Google credential path points to deliberately absent scratch file; GA/IndexNow keys cleared. All Python socket connect methods blocked. No .env loaded by manage.py/settings. Synthetic browser DB reserved for root; test runner does not use it as the test database. Faster MD5 password hashing is a harness override, not production configuration.

PostgreSQL NOT RUN: native postgres/initdb unavailable; installed Snap Docker fails before daemon access because it cannot create `/run/user/1000/snap.docker` under read-only sandbox. No unknown existing server used. SQLite does not establish PostgreSQL migrations, expression constraints, locking, concurrency or production parity. External transport disabled and real Google/GA/IndexNow unverified.

Exact commands, relative to repository root:

```sh
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py check
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py makemigrations --check --dry-run
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py test catalog.testcases.pricing_plans catalog.testcases.pricing_plans_relational catalog.testcases.place_readiness catalog.testcases.legacy_migrations catalog.testcases.public catalog.testcases.test_place_json_and_pricing_modes catalog.testcases.test_json_roundtrip_audit catalog.testcases.test_seo_landing_visibility --noinput --verbosity 1
```

Checks: system check exit 0, no issues; migration drift check exit 0, `No changes detected`. Targeted tests: exit 1, **375 executed, 66.364s, 12 failure records across 11 methods**, zero errors/skips reported. FAQ method produces two failed subtests. All failure records belong to `catalog.testcases.public`; no failures in other selected modules. Imported TestCase classes can expand explicit labels; 375 is runner count, not a unique coverage count. Scratch log `targeted.log` contains only local synthetic test output and is not a repository deliverable.

## 2. Сильные стороны

Business suites exercise relational price synchronization/idempotence, non-tariff readiness, legacy migration ambiguity, JSON round-trip, publication visibility and localized sitemap behavior. These selected non-public suites produced no failures in this environment. The custom runner resets cache and active locale per test (`src/config/test_runner.py:_reset_global_state`), and TESTING selects LocMem (`src/config/settings.py`). CI provisions disposable PostgreSQL17 and Redis, pins Python dependencies, checks migrations and gates deployment on the quality job.

## 3. Реальные проблемы

**QA-01 — P2: default discovery omits 138 existing tests.** LOCAL, high confidence. `src/catalog/tests.py:1–12` imports only selected non-test-prefixed modules; `.github/workflows/deploy.yml` executes default `manage.py test --parallel auto`. Runtime `DiscoverRunner.build_suite([])` yields **605 unique IDs**. Comparing flattened IDs with each non-test-prefixed module yields omitted modules: adult_classes14, image_uploads14, legacy_migrations21, permanent_place_wizard16, phone_reveal8, photo_workflow9, place_filepond_admin2, place_readiness31, place_taxonomy_admin2, postgresql_cutover5, specialists16. Total138; checked without database execution using harness shell. Impact: green CI does not exercise these existing domain cases. Owner integration-reviewer/release-reviewer; next step explicitly include/rename suites and assert discovery inventory, without changing business assertions.

**QA-02 — P2: current public regression baseline is red.** LOCAL HEAD source, high confidence reproduction; older commit introduction UNKNOWN. Public failures at `src/catalog/testcases/public.py`: map serialization2467/2522; accessibility label2035; language selector626; password-reset wording481; FAQ589 (AZ and EN); static version query884; home direct-phone765; detail phone1100; RU count541; AZ/EN catalog wording2927. This is a pre-existing failure relative to this audit's unchanged application source, not an audit-introduced regression and not proof of production failure. Four phone/map expectations reference old direct telephone rendering while current controller emits `has_phone` (`place_controller.py:777`) and templates use reveal controls; classify these as contract/assertion drift pending domain confirmation. Password reset expects “Password reset” while current response says “Reset password”: wording mismatch, not proof of broken recovery. Other wording/ARIA/count failures require UI contract reconciliation. No assertions modified. Owner public frontend + integration reviewer.

**QA-03 — P2: untranslated drawer strings in AZ/EN render.** LOCAL, high confidence. Existing FAQ test detects Russian visible strings in both locales: login helper, free listing helper, language heading. Exact source `src/catalog/templates/includes/header.html:335,355,445`; these msgids absent from AZ/EN `.po` files on bounded literal search. This supports a source localization gap rather than merely stale compiled translations for these three phrases. Rendered-browser visibility/responsive impact belongs to root browser QA; Django HTML alone does not establish screenshots. Owner frontend-reviewer; next step add translations and verify compiled assets and real drawer at each locale.

## 4. Tech debt

**QA-04 — P3: test invocation is fragmented and not self-isolating.** `scripts/run_kidsmap_tests.sh:16` directly invokes manage.py without setting DJANGO_TESTING; `src/config/test_runner.py:28` clears configured cache per test. In a developer shell with shared Redis configuration this is an avoidable operational risk, not observed production damage. Wrapper auth labels also omit standalone Google/reset suites. Node DOM scripts require ignored `.tmp/phone-dom/node_modules/jsdom` (`scripts/test_phone_reveal.cjs:7`, similar photo editor script); no checked-in package manifest/lock found in bounded tracked-file search. Owner QA/release; next step one explicit safe entry point plus reproducible JS dependencies.

## 5. Risks

SQLite, DEBUG=1, MD5 hashing and blocked transports differ from CI/production. PostgreSQL-specific integrity and deployment status remain UNKNOWN. The reported number is selected runner executions, not statement coverage or complete product certification. Tests can import other TestCase classes through helper modules; discovery inventory needs deduplication. Missing temporary static directory caused a benign WhiteNoise warning; full production static build was not tested. Actual external sign-in and security reproductions were deliberately NOT RUN under root's narrowed scope.

## 6. Dead/legacy candidates

No deletion proposed. Non-test-prefixed suites are active tests omitted by naming/import wiring, not dead code. Old direct-phone assertions are candidates for contract review against committed reveal behavior; retain until intended public behavior is confirmed. Legacy price/migration tests remain relevant; passing SQLite results do not authorize removal of compatibility code.

## 7. Tests gaps

Default discovery misses explicit domain tests (QA-01). Current workflow contains no Node/browser execution. Auth/Google/volunteer negative tests, malicious payload reproductions, real providers, PostgreSQL concurrency/constraints, production data and real CI run status were not independently verified here. Dedicated browser evidence is root-owned. Selected public suites contain benign sign-in/reset page rendering checks, not a newly authored security reproduction.

## 8. Recommendations

First repair discovery wiring and establish a classified clean PostgreSQL baseline. Reconcile phone/copy assertions with current contracts; do not restore exposed telephone fields just to satisfy old tests. Fix verified missing locale strings with rendered verification. Add reproducible JS/browser setup and guard the test entry point against inherited database/cache credentials. Keep product fixes in a separately approved implementation plan.

## 9. P0/P1/P2/P3

No P0/P1 established by this QA work. P2: QA-01 discovery coverage, QA-02 red regression baseline, QA-03 locale gap. P3: QA-04 execution reproducibility/isolation ergonomics. Domain data-loss findings belong to backend report and need their own evidence; no security exploit inference from this test run.

Additional verification (same snapshot/harness):

```sh
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py test catalog.testcases.permanent_place_wizard catalog.testcases.image_uploads catalog.testcases.photo_workflow catalog.testcases.phone_reveal catalog.testcases.catalog --noinput --verbosity 1
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py test audit_benign --noinput --verbosity 1
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py test audit_benign.BenignPreservationProbe.test_owner_malformed_schedule_save_observation --noinput --verbosity 1
```

Additional existing tests: **163 executed, 15.950s, exit1, one failure**, `catalog.testcases.catalog.CatalogMapQueryEfficiencyTests.test_map_serialization_query_count_does_not_grow_with_schedules`, source `catalog.py:159`: expects4 queries, observes5. This reproduces the current unchanged baseline; historical similar result is not needed as proof. It is a budget mismatch, not evidence of unbounded N+1 growth or measured production latency. Other selected suites had no failures. Combined existing runs: **538 test executions** (not deduplicated unique tests), **13 failure records across12 methods**, zero errors/skips reported; do not compute unique test coverage by summing labels.

Root explicitly authorized two benign disposable data-preservation probes after narrowing security scope. No application tests/assertions were changed. First command's scratch module then contained two observations and exited0 (2 tests,0.025s):

- **BE-01 confirmed**, backend-owned P1: synthetic published scalar-only fixture (`create_quality_place(price_to=120)`), bound ordinary `PlaceAdminForm` with existing model data, valid location and `pricing_plans='[]'`. `is_valid()` true; `form.save()` and refresh changes scalar range **80–120 → None/None**, status remains published. No `_save_draft` flag or new publication transition. Mechanism: admin clean assigns empty relation payload; Place.save synchronizes empty plans into scalar fields. This observation demonstrates data loss even though existing pricing/readiness suites pass. Add a real preservation regression before fixing.
- **BE-03 parser behavior confirmed**: `validate_schedule_payload('{broken')` returns errors={} and seven closed days. The subsequent explicitly selected owner-save observation is recorded below. This is malformed benign data validation, not an injection payload or authentication reproduction.

Owner-save observation: **1 test,0.032s,exit0**. Existing fixture with six open days; `OwnerPlaceEditForm(instance=p, data={'name_az':'Synthetic audit edit','schedule_mode':'regular','structured_schedule':'{broken'}, draft_save_only=True)` is valid. `p=form.save(); form.save_schedule(p); refresh_from_db()` leaves **zero open days**. BE-03 therefore has actual isolated persistence evidence, not only parser/source inference. Scratch probes assert setup validity and print observed outcomes; their green status means the observation ran, not that data preservation passed. Three observations total were executed across two commands; scratch module was extended between commands.

Priority addendum: QA itself assigns no new P1; backend-owned BE-01 P1 now has QA runtime support, and BE-03 has runtime support at backend's chosen severity. Those are not duplicated as separate QA findings. Application files still unchanged. Production impact, affected row counts and provider status remain UNKNOWN.
