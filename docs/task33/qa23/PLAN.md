# Stage 23 isolated R1 rehearsal implementation plan

> **For agentic workers:** execute these tasks in this session; use `writing-plans`, TDD and verification-before-completion. Scope is stage 23 only.

**Goal:** Provide fresh, disposable-PostgreSQL evidence for conversion, row preservation and restore after new writes, without using production or the deployment/backup scripts.

**Architecture:** A test module exercises application contracts on the QA04 test database. A small QA23 wrapper prepends a child command module to the unchanged QA04 launcher, then performs a synthetic base-database rehearsal and native `pg_dump`/`pg_restore` solely in the launcher-owned container. Only aggregate/digest results enter Git reports; raw dump remains under ignored external evidence.

**Tech Stack:** Django 6, PostgreSQL 17, Python 3.12, Docker local, WSL Ubuntu 24.04, QA04 launcher.

**Spec:** `docs/task33/prompts/23.md`, `docs/task33/migration-map.md`.

## Global constraints

- Preserve dirty worktree; no production connection, real credentials, deploy/backup scripts, commit, push, merge or later stages.
- Run with `DJANGO_TESTING=1`, QA04 disposable Unix socket, no outbound network or external integrations.
- Do not touch the parent-owned R1 cohort gate implementation or another agent's tests. A failing gate-dependent test stays red until the parent supplies the gate.
- Never treat restoring a pre-switch dump over post-switch writes as rollback. Restore a post-switch dump into a separate disposable database and verify both pre- and post-switch row digests.

### Task 1: Application contract test

**Files:** Create `src/catalog/testcases/test_task33_r1_acceptance.py`.

**Interfaces:** `build_plan`, `apply_plan`, `reconciliation` from `catalog.services.catalog_conversion`; existing `business_team.has_action`, review services and canonical public URL helpers. Test consumes only synthetic rows.

- [ ] Write a test that snapshots explicit Place/PricingPlan/media/review/reaction rows, runs dry-run → one-batch interruption → resume → rerun, then compares each row digest and ledger key count. The test must fail if a source row is removed or modified.
- [ ] Run it via QA04 on a fresh Linux mirror and observe red for an absent rehearsal helper or missing behavior; correct fixture/setup errors before calling it behavioral red.
- [ ] Add the smallest test helper and fixture necessary, then run it to green.
- [ ] Add separate negative permission/publication and URL checks covering parent, standalone owner, network owner, selected manager, all-network manager, volunteer and moderator; derive expected grants from decisions D02/D03, not implementation conditionals.
- [ ] Rerun selected module on a fresh mirror; record command, count and result.

### Task 2: Native restore rehearsal

**Files:** Create `docs/task33/qa23/rehearsal.py`, `docs/task33/qa23/bridge/commands.py`, `docs/task33/qa23/README.md`.

**Interfaces:** `rehearsal.py` imports `docs/task33/qa04/run.py` without edits and prepends QA23 bridge to child `PYTHONPATH`; bridge calls QA04 `commands.main('probe', [])`, then performs controlled rehearsal. It writes `r1-rehearsal.json` to `TASK33_QA_OUTPUT`.

- [ ] Write a failing isolated probe for ownership discovery: exactly one running QA04 container must match both nonce label and the child's Unix socket mount, network none, no published ports and PGDATA tmpfs.
- [ ] Implement container discovery and all native process calls as argument arrays without shell expansion.
- [ ] In base QA DB, create synthetic source rows, snapshot row-level SHA-256 (no row values in output), run conversion dry-run/partial/resume/rerun and compare snapshots.
- [ ] Create post-switch rows, take an actual custom-format `pg_dump`, create a new database inside the same owned container, `pg_restore` there, and query both DBs for equal curated row digests and counts. Keep the source DB intact.
- [ ] Run QA04 wrapper with a new output stamp; verify `run.json` cleanup and native restore evidence. If any check fails, record failure and do not claim acceptance.

### Task 3: Closure and handoff

**Files:** Create `docs/task33/reports/23-recovery-closure.md`; retain main report/status/release packet ownership with parent.

- [ ] Document exact source snapshot, commands, TestCase and restore results, coverage and blockers, with raw dump path outside Git and no private records.
- [ ] Check `git diff --check`, inspect only owned files, and send parent a compact evidence handoff.
