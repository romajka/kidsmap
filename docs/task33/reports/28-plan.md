# R2 Local Acceptance Plan

**Goal:** выполнить только Task33 stage28 и подготовить reports/28.md/release-R2.md с точным статусом каждого требования.
**Architecture:** текущий dirty WORKTREE сохраняется и проверяется; PostgreSQL/HTTP/browser используют disposable QA04 и независимые freezes. Native recovery переносит post-switch данные, private/public media и durable notification queue в отдельный restore DB; совместимый frozen reader читает восстановленное при отключённых новых writes.
**Tech Stack:** существующие Django6/Python3.12/PostgreSQL17/QA04, WSL Ubuntu24.04, cached Chromium; frameworks/production connections не добавляются.
**Spec:** ../prompts/28.md, ../decisions.md D01–D15, ../architecture.md «Проверки и выпуск», ../migration-map.md.

## Scope and ownership

Entry392/392 preserved, dependency27 source185/185 MATCH, HEAD015d031d8eb17114bd860159dde805b38df3c13c, branch task33-progress; active_run20261003-194618Z /root integration-reviewer. Root owns QA/full baseline classification, acceptance matrix, final report/journal/manifests. Three independent canonical reviewers are explicitly required by prompt: security owns qa28/security_* and28-security*; database owns qa28/recovery_* and28-database*/28-recovery*; release owns qa28/artifact*/release_* and28-release*/28-artifact*/release-R2.md. After review slots free, canonical browser-qa owns qa28/browser* and28-browser*. No overlapping writes; no application edits by reviewers without coordinated root plan.

- [x] Inspect graph freshness/coverage, verify actual relevant source and deployment boundaries. Inventory all prompts' acceptance requirements without importing old PASS as current execution.
- [x] Run fresh root full explicit PostgreSQL suite using `qa26/backend_run.sh all stage28-full-current1-20261003` without selected labels; run Task33 regression if full failures obscure target status. QA04 source `all_labels()` includes every canonical testcase module; mode choices are all/discovery/probe. First command incorrectly used full and failed argparse before DB/tests; preserve as launcher-usage error, not application failure. Record unique IDs, migration/checks/cleanup, every failed ID and classification against24 baseline/current decisions. Never weaken assertions for green.
- [x] Independent security source+isolated negative review: Owner/Admin/Volunteer ACL/publication, private docs/download/storage, typed reviews, Specialist claims/employment, Event organizer/venue/history, outbox stale/CSRF and public URL/SEO privacy. Exact own commands/freezes, no production.
- [x] Independent database conversion/reconciliation/recovery: dry-run unchanged, interruption/resume/rerun, post-switch R1+R2 records (Specialist/doc/history/Event/notification queue), native dump restore separate DB and media-byte comparison, compatible current artifact reader writes-off GET/read and denied writes. Performance comparison captures actual queries/timing on synthetic matching source with bounded sizes; no production/load claim.
- [x] Independent release builds immutable local artifact and records archive/manifest/interpreter/dependencies/schema/static identity; verifies CI/nginx/private media/cohort/preflight and compatible recovery compatibility with DB reviewer. `release-R2.md` records exact local artifact, validation, stop criteria, external gates; production image UNKNOWN unless actually local-built, never inferred from HEAD.
- [x] Fresh browser AZ/RU/EN×320/360/390/768/1024/1280/1440 on final current application: representative R1 Owner/Admin/Volunteer/Public plus Specialist/Event surfaces, keyboard/errors/empty/history/URLs/SEO and public privacy, console/static/overflow. Retained earlier suites require source equality and explicit attribution; no old screenshot PASS claimed fresh.
- [x] Reproduce substantive findings before fixes; TDD/systematic-debugging apply when triggered. Coordinate exact scope, re-run related checks and independent review; refresh artifact/recovery/browser if application changed.
- [x] Fill requirement matrix with final evidence/status including NOT_RUN external OAuth/Maps/SMTP and physical-device boundaries. Blocking release defects remain blocking; no production-ready claim.
- [x] Final hash/preservation/inventory/review consistency verification; update reports/28.md, release-R2.md, README and status. DONE only if local criteria met, otherwise exact REVIEW_PENDING/BLOCKED remainder. Clear active_run only after all executors finish. No production/commit/push/merge/deploy.

Existing authorization executes this plan directly; skill handoff/commit suggestions do not override prompt production/Git prohibitions.

Final closure: current evidence/limitations are in28.md; full NOT_GREEN and security failure preserved.
