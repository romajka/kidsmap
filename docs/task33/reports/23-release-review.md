# Stage 23 — independent release/recovery review

Role: `release-reviewer` (canonical `.agents/agents/release-reviewer/agent.md`), AUDIT, 2026-10-03. Assignment: release and recovery boundary of LOCAL ACCEPTANCE R1; no application edits. Snapshot: `task33-progress`, LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`; stages 21–22 and their migrations are dirty/untracked WORKTREE, so HEAD is not the R1 implementation. Production state, active image, schema, cohort and data are UNKNOWN; production was not contacted. Parent's entry snapshot: `scratch/task33-stage23-entry-20261003-102704Z`, 97 files in `23-entry-manifest.json`.

## 1. State

The architecture requires expand → compatible reader/writer → isolated conversion → cohort enable, and preservation of post-switch writes during recovery (`architecture.md`, “Данные и перенос”, “Проверки и выпуск”; `migration-map.md`, “Откат”). The current conversion command is expressly limited to QA04 (`src/catalog/management/commands/convert_task33_catalog.py:handle`, `src/catalog/services/catalog_conversion.py:_require_isolated_database`). Migration 0128 preserves legacy review rows as baseline revisions; 0129–0130 follow it. These sources describe a local pilot, not an executable production conversion/release.

## 2. Strengths

- The conversion planner uses a read-only PostgreSQL transaction; apply checks a digest, source fingerprints, isolated socket/settings, and persists batches with checkpoint in one transaction (`catalog_conversion.py:build_plan/apply_plan`). Ambiguous affiliation, prices and group assignment remain manual review.
- The migration map forbids reverse schema or restoring an older dump over new records after post-switch writes. `start-server.sh` checks for pending migrations before production web starts.
- QA04 launches disposable network-isolated PostgreSQL, temporary media/cache/email, and guarded credentials (`docs/task33/qa04/README.md`); it is an appropriate local rehearsal surface, subject to the parent's fresh execution.

## 3. Findings

| ID | Priority | Evidence / trigger | Impact, confidence, owner |
|---|---|---|---|
| REL23-01 | P1 release blocker | `git rev-parse HEAD` gives `015d031d…`; `git status --short --branch` lists stage 21–22 source and 0128–0130 migrations as dirty/untracked. `Dockerfile` builds the checkout and CI deploys only a push to `main` (`.github/workflows/deploy.yml`). | There is no immutable exact reviewed R1 source revision or image digest to deploy or roll back to. HIGH, release lead. A source SHA manifest can verify this worktree but must not be called a release revision. No commit/push is authorized here. |
| REL23-02 | P1 release blocker | `architecture.md` calls for cohort enable/disable; scoped source search of `src/catalog/services`, controllers, models and settings found no R1 cohort/write gate. `services/features.py` gates only specialists/events; `settings.py` has a localized Place URL toggle, not a catalog cohort gate. | No demonstrated safe way to turn off R1 writes/UI after new data exists. HIGH for inspected paths, integration/backend owner; dynamic or external gate remains UNKNOWN. A local cohort-disable rehearsal must prove post-switch records remain accessible through a compatible reader. |
| REL23-03 | P1 release blocker | `scripts/release-server.sh` unconditionally runs `migrate`; `scripts/deploy-server.sh` rebuilds/swaps web, and its failure trap only runs `docker compose up -d web`. `migration-map.md` forbids old binary rollback after new writes. | No named, tested rollback-compatible binary/image for schema 0130 plus post-switch data. HIGH, release/backend owner. Do not represent the deploy failure trap as rollback. |
| REL23-04 | P2 gate | Conversion tool's `_require_isolated_database` rejects non-QA04 settings and external DB URLs, by design. `migration-map.md` v1 preserves identity and queues ambiguous values; it does not transform legacy pricing, Org/group links, reviews or media. | Production conversion procedure, real cohort counts and manual decision queue cannot be inferred from local synthetic results. HIGH, database/release owner. A later separately authorized release needs a reviewed production-safe procedure and per-record decisions. |

## 4. Tech debt

Release script combines migrations, defaults sync, translation/static rebuild and Django checks before image swap. There is no pinned prior image in `deploy-server.sh`. Current source does not give a structured R1 monitoring/stop-criteria command or release manifest; parent should specify criteria in `release-R1.md` and keep them distinct from executed acceptance evidence.

## 5. Risks

Migration 0128 executes a data backfill (`preserve_review_sources`), and new versioned writes have no proven reverse migration; older code may ignore new revisions even if it starts. A database restore to a pre-switch point would erase post-switch records unless replay is proved. A local restore drill must compare post-switch identifiers/content counts and URL/media references after recovery; a successful `pg_restore` exit alone is insufficient. The historical full application suite is NOT_GREEN (`reports/22.md`); targeted PASS cannot turn this into a clean release gate.

## 6. Dead/legacy candidates

None proposed for removal. Legacy Place price data, review rows and URLs remain compatibility inputs; zero synthetic rows or absence in graph cannot justify cleanup.

## 7. Test gaps

This reviewer did not run the shared QA launcher, browser, dump/restore, schema migration or production checks. Stage 23 needs fresh isolated restore with a post-switch write, a proven cohort disable/compatible-reader path, full and targeted suites, reconciliation, browser matrix and query comparison. Existing stage 11/22 PASS is historical evidence, not a substitute.

## 8. Recommendations

Keep release acceptance `REVIEW_PENDING` until REL23-01–03 are resolved and rerun locally. State exact artifact identity (future immutable commit/image digest plus source manifest), schema leaf 0130 or later, cohort and kill-switch owner, tested compatible image, backup/restore/replay sequence, monitoring thresholds and stop criteria in `release-R1.md`. Mark any unimplemented gate or untested binary as `NOT READY`; do not deploy, run production backup scripts, or reverse schema. The parent owns final acceptance and release packet; database-reviewer owns migration/recovery evidence, security-reviewer owns publication/ACL review.

## 9. Priority and checks

P0: none confirmed. P1: REL23-01/02/03. P2: REL23-04. P3: none. Executed read-only: `git status --short --branch`, `git rev-parse HEAD`, scoped `rg` for flags/cohort/rollback/migrations, direct inspection of conversion source, 0128/0130 migrations, Docker/CI/deploy/start/release scripts, QA04 README, architecture and migration map. Codebase Memory project `C-kidsmap` was callable, but `check_index_coverage` reported `coverage_unavailable` / `metadata_changed` for these paths at generation `2026-10-03T10:27:11Z`; all critical claims above use direct source. NOT RUN: QA launcher (reserved to parent), browser, local DB restore, production, external integrations, deploy/backup commands.

Handoff to integration-reviewer: incorporate REL23-01–04 into `reports/23.md`/`release-R1.md`; resolve or mark explicit blockers with fresh local tests and independent schema/security/publication evidence. No application or production files were modified by this reviewer.
