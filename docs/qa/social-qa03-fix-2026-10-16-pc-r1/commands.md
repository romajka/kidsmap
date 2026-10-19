# SOCIAL03 implementation commands

2026-10-16, Asia/Baku. Execution `/root`, C:\kidsmap, PowerShell +Ubuntu-24.04 WSL. QA launchers below are this run's own scratch helpers; recreate/verify ownership and isolation before reusing them. No production/commit/push/deploy invocation.

| Command | Exit/result |
|---|---|
| `python docs/qa/module09-pc-resume-2026-10-16-r1/verify_artifacts.py` before app edits | 0, prior source1019/index/HEAD/branch/sharedMO/active_run MATCH |
| `python .tmp/social03-pc-fix-r1/bootstrap.py` | 0; entry snapshot/approval created; approved plan SHA recorded |
| Copy exact approved candidate regression into new app test path, guarded by `Test-Path` absence | 0; no existing assertions overwritten |
| `python .tmp/social03-pc-fix-r1/capture.py red` | 0;1020sources, existing controller/template baseline |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/scripts/build_isolated_locales.py build --output /mnt/c/kidsmap/.tmp/social03-pc-fix-r1/locales --locales ru az en --compiler native` | 0;3currentcatalogues. `verify` additionally runs before every django.setup |
| `wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social03-pc-fix-r1/start.sh` | own network/volume/PG/app created; proxy initially tied to exec session |
| `wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social03-pc-fix-r1/red.sh` | 1 expected RED;6methods,3failing methods/14assertion failures,0errors; test DB preserved for isolated GREEN |
| `git apply --check --ignore-space-change --include=src/catalog/controllers/typed_reviews.py --include=src/catalog/templates/catalog/typed_reviews.html docs/qa/module09-pc-resume-2026-10-16-r1/proposed.diff` | 0 |
| Same `git apply` without `--check` | 0; exactly controller/template applied; test file already added first |
| `python .tmp/social03-pc-fix-r1/capture.py green` | 0;1020sources; only approved existing2files differ; new test exact approved candidate |
| `docker start m09s03-fix-r1-pg m09s03-fix-r1-app` after WSL discontinuity | 0; only this run's containers. Own persistent volume retained RED test DB |
| PowerShell `Start-Process wsl.exe -ArgumentList …proxy.py -WindowStyle Hidden` | own independent WSL proxy at127.0.0.1:33271; PID recorded in ignored scratch; no visible helper window |
| `wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social03-pc-fix-r1/green.sh` | 0;10unique methods,0F/0E;9.808s; no unchanged full-suite rerun |
| `wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social03-pc-fix-r1/native-start.sh` | 0; fresh own main DB migrated/fictional72cases seeded, runtime info captured, own HTTP started |
| `npx --yes --package node@24 --package @playwright/cli playwright-cli -s=social03-pc-fix-r1 open about:blank --config=/mnt/c/kidsmap/.tmp/social03-pc-fix-r1/playwright.json` | 0; distinct Chromium155 session |
| `… browser_driver.py browser-initial.js`; `… browser_driver.py snapshot` | 0; external allowlist before app navigation, actual source/template/MO inspected |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social03-pc-fix-r1/matrix.py` | valid final runner0;72real409cells/1224checks. Earlier bounded QA failures retained; prep18Place cases reused, only affected2cells replayed |
| `… lifecycle.py` phased raceprep/race/guards/retry | case-level commands/exits in browser-commands.jsonl; successful phases retained on restart, no successful full matrix repeated |
| `… browser_driver.py normalization-supplement.js` | 0; supplementary HTTP409 validates source's `.strip()` policy, no author-review write |
| `… browser_driver.py restore-after-loading-harness.js` | CLI0 but own restore assertions FALSE: unrouteAll released the queued original B POST. Preserved as failed QA gate, not no-write PASS |
| `… stop_own_driver.py` | stopped only exact owned lifecycle driver while waiting, to avoid a second B POST |
| `… browser_driver.py finish-queued-retry.js` | 0; original single native B POST read back, native reviewer approval/author readback completed; no second B submit for that case |
| Remaining `… lifecycle.py` phases | 0;24race/24guards/24retry accepted; earlier successful cells retained, phased real cooldown waits |
| `… browser_driver.py extra.js` | 0;4 SIMULATED pre-delivery transport aborts, one additional native heading-scroll check; shared existing button contrast observed |
| `python -X utf8 .tmp/social03-pc-fix-r1/publish.py` | 0; successful evidence copied,127 native PNG hashes/dimensions, scoped source/index/HEAD and container-state comparison |
| Own localhost `GET http://127.0.0.1:33271/qa/info/` | 200; final controller/template SHA, testing,120s cooldown and sole fresh locales match |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/scripts/build_isolated_locales.py verify --manifest /mnt/c/kidsmap/.tmp/social03-pc-fix-r1/locales/manifest.json` | 0;3 current catalogues, shared MO unchanged |
| `python -X utf8 docs/qa/social-qa03-fix-2026-10-16-pc-r1/verify_artifacts.py` first attempt | 1; QA metadata shape TypeError, retained failed-row JSON is a list; only verifier iteration corrected |
| Same metadata verifier after correction | 0; source1020/candidates3/prior43artifacts/index/refs/active_run/sharedMO/127PNG/links/guide original bytes verified; no test-suite rerun |

`red.sh` executed:

```text
docker exec m09s03-fix-r1-app python /mnt/c/kidsmap/.tmp/social03-pc-fix-r1/runtime.py test
catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests
```

`green.sh` executed one run with these labels:

```text
catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests
catalog.testcases.test_social_qa01_rating_readback.TypedReviewRatingReadbackTests.test_new_editor_and_foreign_candidate_have_empty_rating
catalog.testcases.test_social_qa02_rejection_feedback.TypedReviewRejectionFeedbackTests.test_rejected_edit_feedback_is_author_only_and_keeps_current_projection
catalog.testcases.test_task33_reviews.ReviewVersionPostgresConcurrencyTests.test_two_edits_compare_and_swap_then_two_approvals
catalog.testcases.test_place_review_cooldown.PlaceReviewCooldownTests.test_early_repeat_is_429_and_never_overwrites_review
```

CAS unit tests document cooldown0; a separate120s guard covers persisted429. Native runtime uses120s throughout. Only initial fictional current4 fixtures were aged10minutes before any native A/C submit; no later timestamps/gates were rewritten. READ ONLY state endpoints use5s statement/2s lock timeouts. Auth setup uses QA-only fixture login; review/approval/GET reload actions use actual application UI. HTTP privacy/CSRF probes and deliberately blocked/delayed transport are identified separately in JSON evidence.

All app patch lines match the approved candidates after newline normalization. Native/helper fixes changed only owned scratch scripts. Failed attempts are listed in [failed-attempts.json](failed-attempts.json), with source/product/environment attribution. Final counts, PNG/source integrity and NOT RUN boundaries are in [verification.json](verification.json).
