# PLACE-QA-04 — fresh DOM diagnosis and proposed scope

Date: 2026-10-10, Asia/Baku. Mode: AUDIT / PLAN. One sequential executor `/root`, canonical orchestrator/frontend-reviewer responsibilities; no independent specialist execution claimed. Application implementation awaits scope approval.

## Snapshot and preservation

Actual checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, journal `active_run: NONE`. Current application files match HEAD. PRODUCTION not accessed; current production state UNKNOWN.

Incoming modified `docs/qa/module-acceptance-prompts.md`, untracked module01-r1/r2, module02-r1, module03-r1, module04-r1 QA directories, earlier plans/evidence and all foreign stands were left untouched by this task. No service/container was created, stopped or changed for this finding. [Snapshot and source hashes](snapshot.json).

During final verification, the shared QA register `docs/qa/module-acceptance-prompts.md` changed concurrently (observed last-write UTC 06:54:05). The initial strict hash verifier exited 1 on this document only; all checked application and prior-plan hashes still matched. Its current diff contains the module status rows, including the completed module04 audit. The foreign change was preserved, and [before/current hashes](preservation-drift.json) explicitly record the mismatch. It is not reported as full input-hash equality or rolled back.

Codebase Memory project `C-kidsmap` was checked before source investigation. Path coverage reported `metadata_changed` / `coverage_unavailable`; graph hits were used as research hints, not proof of completeness. Resolver symbols/callers and template consumers were verified in source and literal search. No graph caches were copied into artifacts.

## Verified cause and impact

- `static/js/location_resolution.js:values` disables the district when it clears geography after coordinate changes. `update` handles coordinate events and has an unchanged-point early return; no manual-region listener repairs district availability.
- `permanent_place_form.html` loads the continuous editor, not the legacy wizard's region binding. The active `owner_place_continuous.js` updates markers/preview but does not re-enable the district.
- The continuous editor's `fields()` skips disabled controls, so this state also prevents district inclusion in normal draft serialization. A valid manual choice must be enabled before submission, not just visually displayed.
- `apply(saved)` restores fields one at a time and emits `change` after each. Replaying this observed contract against the real resolver loses restored geography or leaves district disabled depending on field order. Full editor restore remains a browser verification gate.
- `clean_place_location` and `prepare_place_location` already support validated region/district with both coordinates absent. They distinguish it from a partial/invalid point and validate coordinate geography independently. No backend policy change is proposed.
- Shared resolver consumers include admin and legacy wizard. Scope limits the new manual behavior to continuous owner forms and includes non-continuous regressions.

P2 remains appropriate: an owner cannot complete the supported manual geography transition. Fresh evidence confirms the JavaScript cause on LOCAL HEAD; no production claim is made.

## Fresh checks

[Audit fixture](baseline-district.cjs) evaluates the unchanged production resolver under jsdom with local Promise-based fetch responses. No map SDK, Django, database, service credentials or external calls are used. Node child processes receive an allowlisted OS environment plus `DJANGO_TESTING=1` and the local jsdom module path.

| Check | Result |
|---|---|
| Point → clear → Baku enables district | FAIL: disabled remains true |
| Point → clear → another region → Baku | FAIL: disabled remains true |
| Manual Baku → another region | FAIL: district remains enabled |
| Initial saved manual Baku district without coordinates | PASS |
| Partial point does not unlock manual district | PASS |
| Resolved Baku point enables district | PASS |
| Late old response does not overwrite current manual values | PASS; does not establish enabled state |
| Draft field/change replay, region before coordinates | FAIL: restored region becomes empty |
| Draft field/change replay, coordinates before region | FAIL: district remains disabled |

Final expanded baseline: **9 tests, 4 PASS, 5 FAIL, exit 1**. [Raw output](baseline-district.txt). Existing resolver suite: **7 PASS, exit 0**. [Raw output](existing-resolver-tests.txt). An initial seven-case exploratory run was expanded to cover the restore-order concern; the final recorded run includes all nine cases.

The first failed assertions stop those individual tests: downstream FormData/address assertions in that failing case were not reached and are not reported as passing. The restoration checks replay `apply(saved)`'s source-observed assignment/change sequence; they do not execute the whole editor or its network/localStorage restoration.

Recorder command: `.venv/Scripts/python.exe docs/qa/place-qa04-plan-2026-10-10/record_baseline.py`, exit 0. This means the expected RED baseline and unchanged sources were recorded successfully; it does not mean the defect is fixed. [Exact native child commands, exit codes and outputs](command-ledger.jsonl), [recorder](record_baseline.py).

Historical [district evidence](../module01-2026-10-09-r2/district-enable.effective.result.txt) was used as a checklist. Historical [manual roundtrip](../module01-2026-10-09-r2/manual-roundtrip.effective.result.txt) covers admin coordinate save/reload and is not evidence of an owner roundtrip.

## Proposed implementation and limitations

[Reviewable plan](../../superpowers/plans/2026-10-10-place-qa04-manual-district.md): one continuous district-state helper in the resolver, a bounded restore start/end binding in the existing editor, asset version updates, targeted JS/server regressions and a new isolated browser run. Server-owned geography, ACL and lifecycle are preserved. PLACE-QA-02 map buttons and other findings are separate scopes.

NOT RUN for this finding: fresh Django/PostgreSQL stand, actual editor/browser baseline, database save/reload, logout/login, local/server draft restore, RU/AZ/EN rendered checks, screenshots, full backend suites, external integrations and production. There are no new screenshots. jsdom and source review are not rendered-browser evidence. These runtime checks are explicit pre/post-change gates in the proposed approved implementation.

Final audit verification is recorded in [plan-verification.json](plan-verification.json): HEAD/active_run, application diff, input hashes with the documented QA-register drift, document links, test counts and approval status. Verification command: `.venv/Scripts/python.exe docs/qa/place-qa04-plan-2026-10-10/verify_plan.py`. First attempt exited 1 on the concurrent documentation change; corrected verifier exited 0, checking protected sources and recording that change explicitly.
