# PLACE-QA-02 — current-source audit and implementation scope

Date: 2026-10-10 (Asia/Baku). Mode: AUDIT / PLAN. Executor `/root`, sequential canonical kidsmap-orchestrator / frontend-reviewer responsibility; integration-reviewer contract consulted. No independent specialist execution claimed. No implementation authorization inferred from the finding.

## Snapshot

Checkout `C:\kidsmap`; branch `task33-progress`; HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`; journal `active_run: NONE`. Production was not accessed and its current state is UNKNOWN.

Incoming changes: modified `docs/qa/module-acceptance-prompts.md`; untracked module01-r1/r2, module02-r1, module03-r1 and module04-r1 QA directories. PLACE-QA-01 plan/evidence remains pending approval and unchanged. No existing stand/process was stopped or reconfigured. New work is confined to this audit directory and the linked plan.

## Fresh reproduction

Executed [run_baseline.py](run_baseline.py), which runs the unchanged application JS in synthetic jsdom fixtures. `DJANGO_TESTING=1` is set for the Node child; Django/DB/cache/email/media are not loaded or used. No external requests. Geolocation denial and late Leaflet are local doubles, not actual browser permission or SDK integration.

| Case | Result |
|---|---|
| Clear manual point with unavailable provider | FAIL: latitude remains `40.4093` |
| Clear with configured Google and absent SDK | FAIL: latitude remains `40.4093` |
| No navigator.geolocation | FAIL: selected-point text unchanged |
| Geolocation permission-denied fixture | FAIL: getCurrentPosition called zero times |
| Leaflet becomes available after unavailable placeholder | FAIL: renderer initialized zero times |

Node runner: **5 tests, 0 passed, 5 failed, 0 skipped, exit 1**. Audit recorder exits 0 because it successfully recorded the expected failing baseline; this is not a passing application test suite. [Raw output](baseline-map-controls.txt), [exact child commands/exit codes](command-ledger.jsonl), [source hashes and isolation](snapshot.json), [reproduction fixture](baseline-map-controls.cjs).

Exact recorder invocation:

```powershell
.venv/Scripts/python.exe docs/qa/place-qa02-plan-2026-10-10/run_baseline.py
```

Recorder exit 0; source hashes before/after match, and application diff from HEAD is empty. The recorded note about legacy/placeQA01 preservation is limited to the hashed files and the operations performed, not a claim that other active chats cannot update their own files.

## Root cause and impact

`static/js/owner_place_map_picker.js:228` defines locate handling but only provider initialization binds it. Clear and manual-coordinate synchronization are also inside `initLeafletMapPicker` / `initGoogleMapPicker`. In `initMapPicker:455`, unavailable fallback disables search and sets `mapInitialized=1` without binding clear/locate. That same flag prevents later renderer initialization. High confidence; source and fresh DOM behavior agree.

`permanent_place_map.html` contains the manual fields/actions and `data-permanent-map` discriminator. `permanent_place_form.html` loads the JS and external SDK tags. The script is also used by event/legacy forms; the proposed new behavior is confined to permanent-map roots and retains legacy paths with smoke coverage.

The existing `km:map-change` is consumed by `location_resolution.js` and owner continuous draft/save tracking. Preserve this event. Server `clean_place_location` owns geography: derived city/district may change when the point changes; unrelated user fields must remain intact. No backend rule or database schema change is proposed.

## Graph and source verification

Codebase Memory `C-kidsmap` reported the matching repository/branch/HEAD. Focused map-symbol discovery returned 10 results with `has_more=false`. Depth-2 trace identified provider initializers, shared state, search, locate and point helpers. Coverage checks returned `metadata_changed` / `coverage_unavailable`; generations auto-refreshed during investigation. Critical JS, template wiring, consumer events and server boundary were read directly. Graph results were navigation hints, not proof of completeness; no graph cache was exported.

A preliminary Windows `rg` call with an unexpanded `test_location*` filename returned OS error 123. Exact-file discovery/read supplied the relevant server tests. This was a discovery-command error, not a Django test failure.

## Proposed change and next gate

[Implementation plan](../../superpowers/plans/2026-10-10-place-qa02-map-fallback.md): independent clear/geolocation controls; idempotent late SDK attachment; stale geolocation callback protection; RU/AZ/EN feedback and live status; focused regression tests and real browser persistence on a new isolated stand.

Fresh rendered browser reproduction, DB save/readback, server regression tests and screenshots are **NOT RUN** in this planning phase. Also NOT RUN: full unrelated suite, production, real map/geolocation provider integrations, commit/push/deploy. Existing 2026-10-09 screenshots/results remain historical evidence.

Finding status remains **OPEN / P2**. Await approval of PLACE-QA-02 scope; do not treat the PLACE-QA-01 plan or this audit as application-change authorization.
