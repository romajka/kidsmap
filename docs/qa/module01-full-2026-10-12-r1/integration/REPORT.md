# ACCEPT-01 integration evidence — 2026-10-12

Role `integration-reviewer`; execution identity `/root/accept01_tests`; definition `.agents/agents/integration-reviewer/agent.md`; AUDIT ONLY, assigned test corpus and report scope. Application/assertions unchanged. Runtime/test fixture setup is local disposable evidence, never production acceptance.

## 1. State

Checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`. Initial tracked WORKTREE equals HEAD; pre-existing untracked START report preserved. `active_run: NONE` unchanged. [Snapshot](snapshot.json) attests current source parity. Full explicit Django corpus completed: **2092 attempted tests, 2049 PASS / 18 FAIL / 25 ERROR / 0 skip, exit43, stopped=False**. [Results](full-result.json), [summary](full-summary.txt). 42 failures/errors stopped at historical QA04 isolation guards or unavailable guard import: their business behavior is NOT RUN in this loopback profile. The remaining one is a pre-existing legacy specialist assertion. All43 failures/errors reproduced on fresh DB sequentially:18FAIL/25ERROR, exit43 ([rerun](repro-result.json)). No full module/product PASS issued.

Unique integration test DB `test_accept01_integration_20261012_r1` plus four numbered clones, repair DB `test_accept01_integration_repair_20261012_r1`; own LocMem cache/email and media/private-media. START PostgreSQL loopback reused with separate DB names; browser base DB untouched. Allowlisted environment strips inherited credentials before config import; no manage.py/.env loading. Socket egress allows only explicit local PostgreSQL. Own RU/AZ/EN native profile verified before django.setup; shared MO unchanged. [Manifest](locale-manifest.json), [commands](COMMANDS.md).

## 2. Strengths

Fresh delivery regression: 40 Django tests PASS / 0 failure / 0 error / 0 skip, exit0. Exact six labels cover rejection feedback, mixed pricing rebase, manual coordinates, nature localization, continuous form and PLACE-QA08/CROSS-QA03 district localization. This is scoped evidence, never module01 full PASS.

JS unit/DOM corpus: 116 PASS / 0 FAIL / 1 SKIP, exit0 across all 20 declared non-browser files under scripts/test_*.cjs, static/js/tests and scripts/tests/*.test.cjs. Real browser launcher scripts classified separately. [Node](node-corpus.txt).

## 3. Confirmed problems

Existing CROSS-QA-02 discovery gap reproduced: no-label discovery 618 unique tests; wrapper full (`catalog`) 1952; explicit catalog modules plus no-label union 2092. Wrapper misses 140 tests and no-label misses 1474. [Inventory](discovery.json) contains every ID/label. Missing wrapper modules include readiness33, legacy_migrations21, permanent_wizard16, specialists16, adult_classes14, image_uploads14, photo_workflow9, phone_reveal8, postgresql_cutover5, filepond_admin2, taxonomy_admin2. Source: scripts/run_kidsmap_tests.sh full branch, src/catalog/tests.py import list. Current .github/workflows/deploy.yml uses no-label `python manage.py test --parallel 1`; this audit does not claim that CI command covers the explicit2092 IDs. Alias/history retained; no new duplicate defect ID.

Original locale helper suite 9 tests: 2 successful assertions / 6 FAIL / 1 SKIP, exit1; the original format-error negative assertion also passes when WSL is missing and does not by itself prove compiler format validation; missing `wsl.exe` in unchanged six compiler-success scenarios is ENVIRONMENT FAILURE, not app regression. [Original output](locale-helper-original.txt). Supplementary native probe verifies native build, manifest and gettext, stale-source rejection (4 checks exit0) without replacing original assertions or claiming its suite GREEN. Unchanged helper creates own generated `.tmp/locale-tool-test-*` fixture directories; these ignored test artifacts were left intact. [Probe](native-probe.json).

A separate **PRE-EXISTING BASELINE TEST FAILURE** exists in specialists.TestSpecialistsFeatureFlag.test_feature_enabled_by_default, specialists.py:407: expects GET200 from owner_specialist_create, actual302. Current urls.py:217 routes this alias to specialist_workspace_profile; specialist_workspace.py:302 redirects GET with no pk to specialist_workspace_proposal. Verified source plus sequential rerun explains stale assertion; current clean app HEAD matches WORKTREE. No application defect/new PLACE ID inferred.

The42 environment blocks are17 assertion failures requiring historical TASK33_QA_ROOT / fixed test_qa_stage04 / Unix socket;15 conversion errors require QA04 isolation markers;10 notification-crash errors import old guard.socket_path. Own real loopback isolation is not that legacy runtime. Tests/assertions/guardrails were not altered or spoofed to get GREEN.

## 4. Technical debt

JS tests depend on historical ignored node_modules and fixture HTML paths; own pinned jsdom installed in scratch and transparent resolution hook used. No source/assertion changes. Fresh actual HTML reveals legacy-wizard harness mismatch (tests boot old wizard on the current continuous editor); future test PLAN should choose current consumer rather than weakening assertions. No repository root package lock; latest versions not inferred.

## 5. Risks

Discovery completeness is bounded to canonical configured Django source and current script/static corpus. Graph generation2026-10-12 full mode; requested runtime/discovery sources no recorded issue, static/js/tests coverage UNKNOWN; exact filesystem inventory used. Index coverage remains best effort. Final failure attribution is bounded to current clean HEAD and actual sequential reproduction; it does not establish historical release or production state. Full configured corpus execution is not full corpus GREEN.

## 6. Dead/legacy candidates

None proposed. Non-test-prefixed suites are live validation and must not be deleted from discovery assumptions.

## 7. Gaps / NOT RUN

Initial actual-HTML photo-editor Node scenario SKIP because `.tmp/photo-form.html` absent. Root later supplied freshly authenticated actual owner HTML in ignored integration/photo-form.html; exact file-read adapter rerun gives 7 PASS / 1 FAIL / 0 skip (photo-actual-html.txt, exit1). Existing test line122 injects permanent_place_wizard.js manually; actual template loads owner_place_continuous.js and lacks legacy [data-pw-prev], causing old wizard.js:578 null.addEventListener. This is stale legacy test/consumer mismatch, not actual UI runtime failure; no app/new PLACE defect claimed. Sensitive fixture HTML remains ignored and is not copied to reports. Three real Playwright launchers (`test_localized_place_urls`, `test_review_cooldown`, `test_review_submission`) and scripts/tests/*.browser.js NOT RUN by integration role; rendered-browser audit owned by root. Real Google/GPS/provider/screenreader/devices/production NOT RUN. Django/Node mocks are SIMULATED platform/integration boundaries, not rendered acceptance.

## 8. Recommendations / handoff

`kidsmap-orchestrator`: incorporate final Django outcomes, browser role evidence and limits in top report. `integration-reviewer` future CROSS-QA-02 PLAN: make configured discovery authoritative with explicit missing modules and a discovery count/ID oracle; do not implement during ACCEPT-01. WSL-only helper portability deserves a separate approved PLAN, preserving negative guards.

## 9. Priorities

Existing CROSS-QA-02 remains OPEN (P2 verification coverage risk), with portability/legacy consumer debt; environment helper failures recorded as limitations rather than six application defects. No P0/P1 confirmed in executed integration scope.
