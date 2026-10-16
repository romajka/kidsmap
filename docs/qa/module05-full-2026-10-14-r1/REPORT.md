# ACCEPT-05 — FAIL: OFFER-QA-10 OPEN

2026-10-14, `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` plus preserved dirty WORKTREE, active_run NONE. Sequential root performs Django/database/frontend/browser checks; no independent subagent execution claimed. Canonical `.agents/agents/kidsmap-orchestrator/agent.md` and audit/engineering contracts used. Approved OFFER09 two-file repair, completion of module05 and previously approved OFFER07 same-JS recovery scope. Full ACCEPT05 does **not** pass: nine tariff enum captions remain Russian in AZ/EN, separate OFFER-QA-10/P3. [Finding and proposed scope](FINDINGS.md), [implementation plan](../../superpowers/plans/2026-10-14-offer-qa10-tariff-enum-localization.md). No new locale repair performed without approval.

## 1. State and exact evidence

[Entry snapshot](snapshot.json), [acceptance snapshot](snapshot-acceptance.json), [final snapshot](snapshot-final.json), [verification](verification.json), [counts/discovery hashes](counts.json), [237 state cells](matrix.csv), [PNG manifest](png-manifest.json).334 unique backend methods PASS;1006 accepted native assertions across21batches PASS; fresh enum diagnostic1PASS/2FAIL. These are assertions and state cells, not a claim of1006independent user journeys.14READ ONLY final-state checks PASS.234 earlier matrix cells PASS plus RU enum cell PASS and AZ/EN enum cells FAIL.239PNG, including retained phase/capture history. Counts are verified from actual result JSON.

Exact discovery:20whole explicit test modules plus1named volunteer-readiness guard in [test-corpus.py](test-corpus.py);334unique method IDs in [test-discovery.json](test-discovery.json). Covers13historical module suites,5repair suites01/03/07/08/09, drafts and continuous owner form. No default/no-label wrapper counted as the full corpus; global project corpus and CROSS-QA-02 acceptance are NOT RUN. Earlier09targeted12 methods overlap334. Two affected admin-editor reruns16each also overlap334; do not add them to unique total.

| Check | Evidence / native exit |
|---|---|
| Full module backend | [command](module-tests.command.json), [output](module-tests.txt): exit0,334methods,183.018s test time |
| Shared admin after first/final foreign-source phases | [first16](shared-admin-current-source.command.json), [later16](shared-admin-final-source.command.json): both exit0; final15.310s test time |
| Browser commands / exits | [commands.jsonl](commands.jsonl), sanitized `drive.py`; inspect each result for row status/errors, CLI0 alone is not PASS |
| Final saved state | [command](final-state.command.json) exit0, [READ ONLY state](final-state.json):14checks |
| JS07 syntax / locale v2 verification | [node](node-final-syntax.command.json), [locale](locale-final-verify.command.json): exit0 |
| Final source/locale refresh | v3 [compiler](locale-final-build-v3.command.json) exit1; v4 [compiler](locale-report-build-v4.command.json) exit0; [v4 startup](report-runtime-v4.command.json) exit1, source changed again before setup |
| Evidence verifier | [command](evidence-verification-final.command.json): exit0 verifies evidence and deliberately keeps full decision FAIL |

## 2. Behaviors that passed

Program, Activity, Group and Plan have distinct ownership/publication contracts. Real native Program creation/edit/submit/moderator approve, return/reason, final decline with readonly proposed values, new proposal after decline, unpublish and republish were exercised. Native local Activity creation with two groups4–6/20 and12–15/80, second Activity7–9/15, actual saves/reloads/submits/approvals and native group/activity removal were exercised. Public filtered price20 at age5 and80 at age13 belongs to the same matching group, not a crossed group; second activity age8 gives15 until actual archive.

Native13product types and5price kinds, free/from/range/on_request, empty/zero422, recurring membership interval/count, quantity/unit and USD save/reload passed. Structured price error opens the hidden section and focuses the actual price. Multiple plans/history are covered by the explicit backend corpus and native current tree round-trip. Native condition verification, changed-confirmed data, pending confirmation409 and clearing old verification after approval passed. Group removal leaves old public live content while pending and hides only the removed group after approval; history80 remains.

Five supported Place-hours modes save/reload without overwriting lesson schedule. Two valid intervals and closed weekends persist; overlap/reversed/incomplete intervals fail422; legacy scalar31/35 and free-text hours survive unrelated edit. Native branch detach preserves frozen approved Program content and local group30, clears organization/program pointers and removes organization employee edit access. Re-publishing/changing the original Program does not update the detached frozen snapshot. Outsider/foreign editor access is denied.

Actual JSON import/export modal, invalid JSON/Escape, full tree round-trip and partial-name approval passed. Explicit empty tree blocks price approval, public group20 remains and a valid tree is restored/approved. Review ready/price-blocked UI covers36cells across RU/AZ/EN×six widths. Program two-tab409 covers18cells, typed input persists. Place two-tab conflicts use existing422 plus `candidate_version_conflict`; that existing API classification is preserved.

## 3. Repairs and remaining defect

OFFER01–08 historical scoped results are preserved with the fresh module rechecks above; they are not blindly inferred from old PASS. OFFER09 partial-name review pricing is [CLOSED LOCAL](../offer-qa09-fix-2026-10-14-r1/REPORT.md): trusted fallback only when candidate lacks `nested_pricing`, explicit empty candidate precedence retained. New8regression methods plus4existing guards RED→GREEN; native10plus this module's round-trip/36gate cells passed. No readiness/ACL/CAS/schema relaxation.

Full acceptance reopened an additional OFFER07 offline case: unavailable private-draft POST leaves only browser cache, another native candidate-only save keeps live source version, and old candidate base was incorrectly0. In the already approved `static/js/owner_place_continuous.js` scope, recovery now reads candidate metadata from existing signed publication_token as a UI hint; invalid metadata requires explicit recovery. Backend signature/CAS authority remains unchanged; no token stored/exported. Candidate-conflict summary uses existing localized copy. [Supplement plan](repair07-offline-plan.md), [minimal diff](repair07-offline.diff), original [RED3PASS/1FAIL](offline-recheck.result.json) and [GREEN4PASS](offline-recheck.result.attempt1791968740.json), [recovery68PASS](recovery.result.json), [metadata4PASS](metadata-fallback.result.json), [conflict8PASS](conflict.result.attempt1791969128.json). Current private input can resume; old copy stays available for explicit choice and cannot replace newly approved live content.

Previous scoped repairs retained: [01](../offer-qa01-fix-2026-10-13-r1/REPORT.md), [02](../offer-qa02-fix-2026-10-13-r1/REPORT.md), [03](../offer-qa03-fix-2026-10-13-r1/REPORT.md), [04](../offer-qa04-fix-2026-10-13-r1/REPORT.md), [05](../offer-qa05-fix-2026-10-14-r1/REPORT.md), [06](../offer-qa06-fix-2026-10-14-r1/REPORT.md), [07](../offer-qa07-fix-2026-10-14-r1/REPORT.md), [08](../offer-qa08-fix-2026-10-14-r1/REPORT.md). Their source/evidence limits are preserved in the original reports.

OFFER10/P3 remains OPEN: nine system enum names in both AZ/EN. Native [diagnostic](enum-localization.result.json)1PASS/2FAIL with three language screenshots; exact list/cause/plan in FINDINGS. This is the missing caption set explicitly excluded from the earlier OFFER06 plan, not a reopening of its successfully scoped27entries. No application logic defect remains confirmed in the executed functional scenarios; this does not erase OFFER10 or current runtime limitations.

## 4. Debt

Historical Windows launchers/ports/PIDs and prior MO/session files are not portable inputs. The copied owner/admin/shared choice catalogs have unrelated fuzzy entries; this report proposes only the nine confirmed captions. Default Django discovery and unchanged scalar compatibility are not proof of all-project acceptance. No broad cleanup performed.

## 5. Runtime, preservation and risks

Own profile `.tmp/module05-full-2026-10-14-r1`, PostgreSQL17.10 at loopback36021, database `module05full_20261014_r1`, unique container/cache/cookies/media/private-media/email. Actual Python3.12.3, Node20.20.2, Docker29.8.0, msgfmt0.21, playwright-cli0.1.17: [tool receipt](tools-final.json). Fictional owner/employee/outsider/admin, owned network/Places; Program/Activity/Group were created through native UI, not seeded via ORM. No checkout .env, production credentials or remote old data. Runtime strips inherited environment; only its own loopback PostgreSQL connect/connect_ex permitted. Browser external requests blocked. Secret values remain in ignored0600 credentials and are removed from command outputs. Fresh current PO compiled by the helper into sole isolated LOCALE_PATHS before setup; shared old MO bytes preserved.

Source receipts are **phased**: [09 executed phase](../offer-qa09-fix-2026-10-14-r1/runtime-version-final.json), [module v2 receipt](runtime-phase-v2.json) had entry/startup/disk MATCH. Foreign admin/theme/ownership-preview source and PO changed repeatedly: [initial8files](concurrent-foreign-drift.json), [later9files](concurrent-drift-at-final.json), [later4files](concurrent-drift-after-last-refresh.json). Foreign files preserved; no revert, foreign PID stop or active_run assignment. Only own exact script/PID was restarted. Old source MATCH is not current checkout or production evidence.

Final v3 build failed duplicate RU `Редактировать карточку` introduced in foreign input. The author changed RU; v4 build passed, but it changed again before Django startup and the strict helper refused stale catalogs. [Source change receipt](ru-source-after-compile-failure.json), [runtime diagnostic](runtime-v4-failure.txt). Latest own HTTP process exited; own PostgreSQL and foreign stands retained. Current full runtime match is BLOCKED, not asserted. A new run must compile a fresh unique directory after the current input stabilizes; never bypass verification/reuse stale MO. No endless restart/test loop performed.

## 6. Legacy/archive boundaries

Native Activity and Group archive/removal and tariff history preservation passed. Native Program archive is NOT RUN/not exposed in supported UI (owner has submit/edit; admin exposes publication actions and readonly archive field). Its model-level archive/data constraints are tested in the corpus; no nonexistent user transition invented. Legacy records were not bulk migrated or deleted; unrelated old pricing/text remained.

## 7. Failure classification and NOT RUN

[Retained failures](retained-failures.json) distinguish actual07RED now fixed, QA wrong confirm URL, missing candidate-version input, incorrect409 expectation for Place's422classified conflict, and the additional owner-name harness attempting a hidden EN field. That extra owner-only name UI path is NOT RUN; the corrected harness then had no runtime because stale locale verification correctly stopped startup. Admin partial-name native path and shared owner/admin review-equivalence guard passed. Initial PostgreSQL bootstrap transient connection failed, then owned prepare-resume exited0; no test assertion changed for it. v3/v4 compile/start failures are concurrent input/environment problems. They do not become regression findings or PASS.

Offline unavailable draftPOST, malformed publication-token metadata in an intercepted own GET, and controlled native POST loading delay are explicitly SIMULATED faults/timing; other tested transitions use real UI and real owned server responses. No simulated response masquerades as actual publication/save. Remote email delivery/maps/OAuth/analytics/external integrations, production, deployment, commit/push, other full modules/global corpus, bulk migration, other engines/devices/real screen reader/exhaustive keyboard paths are NOT RUN. Browser pageerrors0 in accepted batches; local network lists contain intentionally triggered422/409/404, not unreported successful requests. No separate complete DevTools console-message corpus was captured for every cell; pageerror/network evidence is the recorded limit.

Some full-page admin screenshots resize viewport-dependent sidebar layout during capture; they remain phase/capture history, not sole evidence of actual desktop no-occlusion. Actual [final1440viewport](screenshots/admin-final-1440-viewport.png) and [geometry before/after](admin-viewport.result.json) show sidebar300/content-left324. Representative owner price390, public group390, review error390 and desktop viewport images were inspected directly. Full-page source geometry alone is not a visual PASS.

## 8. Next action

Approve only the saved OFFER10 plan for nine captions in the three named PO files. Correct captions, verify actual RU/AZ/EN shared enum choices and affected owner/admin native save/reload/screens; preserve other current PO edits. Reuse334 unchanged backend method results with hashes, run targeted locale/browser checks only. Refresh own runtime after new manifest. Keep this FAIL report and add an acceptance supplement; module06 begins only after the outstanding scope is resolved/accepted. [Next prompt](next-prompt.txt). No module06 work started.

## 9. Priority decision

P0/P1/P2: no new confirmed unresolved finding in the executed module05 functional scope. P3: OFFER-QA-10 OPEN, high confidence native language inconsistency. Full verdict FAIL and current-wide runtime BLOCKED. Scoped OFFER01–09 CLOSED LOCAL does not imply a full module, production or all-project PASS.
