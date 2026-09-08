# Database audit — 2026-09-08

Role: `database-reviewer`, definition `.agents/agents/database-reviewer/agent.md`. Execution identity: `/root/audit_backend`, **sequential role execution by the same worker that produced backend.md**, after native thread-limit prevented another worker; not an independent second backend review. Mode AUDIT ONLY. Scope: schema/migrations/constraints/index query shapes and legacy migration commands. No production/DB commands, application edits, commits or subagents. Authentication/exploit analysis excluded.

LOCAL HEAD `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`; `git diff --name-only -- src/catalog/models src/catalog/migrations src/catalog/management/commands` empty. Dirty agent-system WORKTREE preserved. Current PRODUCTION revision/schema/data/row counts UNKNOWN. No September 6 aggregates reused as current facts.

## 1. Состояние области

Reused current snapshot, architecture, source map and shared audit/engineering contracts from preceding role; read actual database role and database knowledge before beginning. Codebase Memory project/root/architecture established in preceding role. Fresh database search found command planners and scalar-sync symbols. Coverage generation `2026-09-08T05:59:31Z`, full, complete metadata: command paths and exact 0084/0085/0101/0103/filtering/model files metadata_match/no_recorded_issue. Directory-level migrations coverage was not_tracked, so individual filenames and actual source were checked. Best-effort graph coverage does not establish deployed schema or exhaustive caller coverage.

Source includes migrations through `0103_place_review_cooldown`; 0084 preserves physical legacy JSON column via state-only rename, 0085 adds tariff checks, 0101 adds database-only normalized email uniqueness, 0103 creates persisted review cooldown and changes review-history uniqueness. Pricing/schedule migrations are separate management commands, not automatic completeness guarantees from applied Django migrations.

## 2. Сильные стороны

- `migrations/0084_pricingplan_relational.py:9` uses SeparateDatabaseAndState to retain physical `pricing_plans` JSON while renaming Python state; this is intentional, not unexplained schema drift.
- PricingPlan declares amount/range/kind/billing/quantity/role/date constraints and lookup/order indexes (`models/pricing_plan.py:101`). Schedule day `(place, weekday)` is unique (`models/place.py:670`). This describes local declarations, not validation of current PostgreSQL constraints.
- `migrate_legacy_prices` and `migrate_legacy_schedules` default to non-writing planning; ambiguous values become ambiguous/manual_review instead of forced interpretation. Price migration skips already-existing tariffs in its planned normal path; schedule parser rejects ambiguous text.
- `0101_unique_user_email.py:11–28` uses the migration connection alias, blocks duplicate normalized nonempty values without merging/removing accounts, then creates reversible uniqueness. No secret/user payload is emitted by its duplicate error. Identity decisions remain outside this role.
- `0103_place_review_cooldown.py:9` seeds latest review timestamps in batches, uses the connection alias and unique `(place,user)` cooldown rows, and adds `(place,user,-created_at)` index matching latest-review lookup.

## 3. Реальные проблемы

### DB-01 — P1: migrate_pricing_plans can delete already-modern tariffs

**Environment/trigger:** unchanged LOCAL source; operator runs `migrate_pricing_plans --apply` on a mixed legacy/modern database. A modern place has a primary exact per-lesson tariff (`quantity=1`, `quantity_unit=lesson`) plus an addon, and empty legacy JSON. Primary tariff already generates `price_per_lesson` through signals.

**Evidence:** `src/catalog/management/commands/migrate_pricing_plans.py:22` iterates every Place, with no already-migrated exclusion. `:24–43` reconstructs payload solely from legacy JSON and three scalar columns; existing relational rows are only counted (`:56`). `:59` passes that partial payload to `replace_place_pricing_plans`; `src/catalog/services/pricing_plans.py:325–332` deletes existing rows not retained in the payload. The addon is not represented by scalar projections and is deleted. Even matching primary rows can lose localized titles/conditions/source metadata when normalized defaults replace them. Row-count report uses `max(0, len(saved)-existing)`, so destructive reduction can report zero created without a deletion count.

**Impact/severity:** P1 silent loss of current tariff records/metadata through a migration command presented as legacy conversion. This differs from BE-01 ordinary admin scalar loss; do not merge away either trigger. Current production use, affected count and actual incident UNKNOWN. High source confidence; exact fixture reproduction NOT RUN in this role.

**Owner/next:** database-reviewer + django-reviewer; lead notified immediately. Before any application, isolate a lesson+addon+localized-metadata fixture and assert full preservation, including reruns after an operator adds a tariff. A guarded migration/reconciliation plan must distinguish legacy inputs from live scalar projections and report updates/deletions, not only new row counts.

### DB-02 — P2: migrate_legacy_prices rewrites scalar values despite preservation promise

**Trigger:** a scalar-only place has `price_per_month=400` and/or `price_per_8_lessons=200`; run `migrate_legacy_prices --apply`.

**Evidence:** command docstring `migrate_legacy_prices.py:1–6` promises legacy fields remain untouched. Mapping `:32–46` generates membership+quantity month or membership+quantity 8 lessons; neither supplies recurring billing. Model `models/pricing_plan.py:61` defaults billing_mode to one_time. Apply `migrate_legacy_prices.py:233–235` calls ordinary `PricingPlan.save`, with no `_skip_legacy_sync`; signal `models/pricing_plan.py:247–251` calls `sync_legacy_price_fields`. The sync `services/pricing_plans.py:351–366` clears all derived columns first, restores monthly only for recurring membership/month/count1, and restores eight lessons only for product_type lesson/one_time/quantity8. Neither generated membership matches these conditions, so the original monthly/package scalar becomes None. The other command uses different mappings (`migrate_pricing_plans.py:34–35`).

**Impact:** amount survives in a relational row, but legacy per-product fields are not preserved and the two migration routes encode the same old field differently. This is bounded projection/semantic drift (P2), not total price loss or proof that all monthly products must be recurring. High source confidence, runtime reproduction NOT RUN here.

**Tests/owner/next:** existing `testcases/legacy_migrations.py:34` asserts generated product/quantity tuples without refreshing and checking scalar values/billing semantics. QA's selected legacy suite passed but does not cover preservation. Database-reviewer and backend owner must choose documented product semantics and a preservation/projection contract, then verify old→new→old values and both command paths. Avoid silently changing the existing test's business meaning just to get green.

### DB-03 — P2: migration “re-check” uses stale planned objects and no place lock

**Trigger:** price or schedule editor writes after the command's planning read but before `_apply`; especially meaningful schedule days added while legacy schedule migration is planning.

**Evidence:** `migrate_legacy_prices.py:191` prefetches pricing rows and retains Place objects in outcomes, then `_apply:225–231` calls `.exists()` on the same related manager inside atomic without refresh/locking. `migrate_legacy_schedules.py:56–63` prefetches `schedule_days__intervals` and stores outcomes; `_apply:91–98` serializes the same object and then calls destructive schedule replacement. `services/place_schedule.py:391–412` reads `.all()` from these related managers; `:418` deletes prior schedule days. Neither apply path selects/locks a fresh Place or compares source values to the planned snapshot. An atomic block alone does not make the previously prefetched snapshot fresh.

**Impact:** comments promise protection against a writer between planning/apply, but the checks are not a reliable current-state verification. Schedule replacement may overwrite newly entered hours; price migration may add duplicate plans. Confidence high for missing freshness/coordination, medium for exact concurrent outcome; PostgreSQL interleaving NOT RUN, no observed live corruption claimed. P2 justified as an operational race with concrete trigger, not routine single-process failure.

**Owner/next:** database-reviewer + QA. Verify deterministic plan→synthetic intervening edit→apply on disposable DB, then a PostgreSQL concurrent-writer test. Reviewed application plan needs a fresh source comparison and shared writer coordination, or a proven exclusive maintenance window. Existing rerun tests only demonstrate sequential idempotency.

## 4. Tech debt

Two similarly named price migration commands have incompatible scope, conversion and preservation semantics. Reports count proposed/created rows without complete before/after fingerprints. Operational checkpoints are per-place atomic in legacy commands, but there is no persisted source-version contract connecting audit plan to later apply. These are maintainability consequences of DB-01–03, not extra inflated incident IDs.

## 5. Risks

0101 uses normal `CREATE UNIQUE INDEX` in a migration and has no explicit command-level lock/statement timeouts. Duplicate preflight is good, but deployment needs a bounded PostgreSQL rehearsal and table-size/write-traffic estimate; lock duration and production readiness UNKNOWN, so no outage finding assigned. `makemigrations --check` cannot independently verify the database-only index's deployed presence. Reverse migration drops the named index; forward/reverse and duplicate preflight on PostgreSQL NOT RUN.

Query shapes: scalar sync filters plans by `(place,is_active,charge_role,currency)`, matching `pricing_lookup_idx`; public queryset (`content_quality.py:236`) combines status/deletion, text expressions, schedule relation and DISTINCT; price filtering uses a primary active AZN minimum. These deserve representative EXPLAIN, but no plan/cardinality/timing evidence was collected, so no missing-index or slow-query finding. Foreign-key integrity/current orphan counts, constraint validation, backup restore and production app-role privileges UNKNOWN.

## 6. Dead/legacy candidates

No confirmed removals. Physical legacy JSON and scalar columns are both historical inputs and current projections; current commands and public consumers still read them. Migration0084 state mapping is deliberate. Do not delete or fake-apply 0101 because it is absent from auth.User model state. Dated row counts cannot prove a command/table unused today.

## 7. Tests gaps

Executed here: graph search/coverage; targeted source reads; app-scope `git diff --name-only` (empty); report whitespace/section verification. **No Django/DB commands or migration applications were run by this role.** Reused [qa.md](qa.md) with attribution: selected 375 tests, exit1, 12 failure records solely in public.py; selected pricing/readiness/legacy modules had no failure records. That run used disposable SQLite memory DB, LocMem cache/email, scratch media and denied external sockets. System check/migration drift check passed there. Exact commands are retained in QA section1.

NOT RUN: PostgreSQL migration forward/reverse, live constraints/catalog introspection, EXPLAIN, concurrent writers, fresh DB-01–03 fixture probes or restore. QA has no usable local PostgreSQL and did not substitute an unknown server. Needed regressions: modern mixed-plan preservation across migrate_pricing_plans; legacy scalar/projection equivalence for monthly and packages; stale plan rejection and concurrency; explicit 0101 duplicate/preflight/index/reverse tests on PostgreSQL. BE-01/BE-03 fresh SQLite observations remain backend-owned and are not independent database-role proof.

## 8. Recommendations

1. Treat DB-01 as a required precondition before authorizing the broad legacy pricing command; review a non-destructive mixed-state reconciliation plan with counts/fingerprints.
2. Resolve the two price migration mappings and the promise about preserving scalars; test serialized full records, not only row IDs/counts.
3. Establish fresh source checks and writer coordination before applying planned schedule/price conversions.
4. Schedule isolated PostgreSQL integrity/migration/locking checks and read-only representative query plans. No production application is authorized by this report.

## 9. P0/P1/P2/P3

| Priority | Finding | Boundary |
|---|---|---|
| P0 | None | No incident evidence |
| P1 | DB-01 | Source-confirmed destructive command path, runtime reproduction pending |
| P2 | DB-02, DB-03 | Projection discrepancy and concrete concurrency risk; production UNKNOWN |
| P3 | Command/report contract debt | Included without extra incident IDs |

Handoff: lead deduplicates against backend BE-01 (different entry point); QA owns new isolated tests; release reviewer owns rehearsal/maintenance/deployment boundaries. Changed only this database report during the sequential role.
