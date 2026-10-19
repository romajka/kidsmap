# Module13 final cross-module acceptance implementation plan

**Goal:** Complete the user's authorized local Module13 audit, repair confirmed cross-module defects, and report the actual final coverage without promoting historical scoped evidence to product acceptance.

**Architecture:** Preserve current WORKTREE and 44 previous QA packages. Execute sequentially as root using the canonical integration, Django and browser role definitions; no independent specialist claim. Reproduce failures in a unique DJANGO_TESTING=1 PostgreSQL/cache/media/email instance, then minimal source changes and regression checks.

**Spec:** continuation-and-repair-prompts-2026-10-11.md, ACCEPT-13 and CROSS-QA-01/02. Current explicit request authorizes implementation beyond the historical plan-only prompts.

**Constraints:** No production, credentials, commit/push/deploy, old assertions changes, foreign runtime restarts or cleanup. Current PO compiled into own locale directory before Django setup. External services blocked or explicitly simulated.

- [ ] Attest HEAD, branch, dirty source hashes, index, refs, active_run, current containers and previous packages. Check graph freshness/coverage and verify relevant source.
- [ ] Reconcile latest reports for modules01–12, exact version/coverage/remaining gaps; keep scoped versus full acceptance distinct.
- [ ] CROSS-QA-01: PostgreSQL regression for published future scheduled/rescheduled physical and online events in organization + listing + detail, past/cancelled/draft/deleted exclusion and section toggle. Confirm RED then change src/catalog/controllers/public_details.py filter minimally; public detail may truthfully retain cancelled/past while organization upcoming excludes them. Verify actual native reschedule/cancel and reload across locales/widths.
- [ ] CROSS-QA-02: discovery-only compare no-label, wrapper catalog and exhaustive domain test inventory including non-test-prefixed modules; distinguish tracked versus untracked. Write discovery contract regression; retain cache/language/parallel resets. Use one canonical full-discovery route in src/config/test_runner.py, adapt wrapper full and root bridge only if needed. Preserve explicit scoped labels and custom patterns. Prove unique ID agreement and no silently omitted modules. Run the actual full suite, retaining every failure.
- [ ] Investigate confirmed related full-suite failures individually; reproduce baseline/environment versus application causes. Add failing regression and minimal fix when authorized and justified; do not falsify guarded historical environments or weaken assertions.
- [ ] Exercise canonical cross-domain native organization/place/program/activity/specialist/event/moderation/ownership/ACL/toggle/media/review/favorite/analytics flows. Record actual tested cells and absent mandatory cells, console/network/keyboard/overflow.
- [ ] Run applicable Django/Node/Python checks, migration drift/system checks; verify preserved original tests, prior packages, refs and foreign runtime identities. Append current result to guide/MASTER and seal read-only artifact manifest.

Expected implementation paths: src/catalog/controllers/public_details.py; src/config/test_runner.py; test_catalog.py; scripts/run_kidsmap_tests.sh; new catalog.testcases.test_module13_* tests; documentation only for proven invocation changes. Additional paths require a concrete finding plan saved before edits. No schema changes planned.

Acceptance: two historical cross findings freshly resolved, complete discovery with raw unique IDs/counts and exact commands; no false global PASS if any mandatory local acceptance remains missing. Actual GitHub/real integrations/production/native device platforms remain explicitly NOT RUN.

Confirmed RED r2: 7 methods, 10 failed observations, no errors. Canonical complete discovery uses every current catalog.testcases Python module through the existing custom runner; explicit labels and explicit pattern keep their scope. Wrapper full invokes no-label canonical runner. No root wildcard imports or application test assertions changed.
