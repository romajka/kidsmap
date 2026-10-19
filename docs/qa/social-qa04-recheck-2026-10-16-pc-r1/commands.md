# SOCIAL-QA-04 — команды свежего PLAN run

`C:\kidsmap`, PowerShell + Ubuntu-24.04 WSL, собственный `social04-pc-plan-r1`. Старые QA scripts не запускались автоматически; новые launchers/runtime созданы в ignored scratch после проверки источников/зависимостей. Приложение не исправлялось.

| Команда/проверка | Exit/result |
|---|---|
| `git status --short`, `git branch --show-current`, `git rev-parse HEAD` |0; transfer852938d + retained dirty SOCIAL03/QA docs/.cbmignore |
| Codebase Memory list/index/search/trace/coverage, проект C-kidsmap | ready, generation2026-10-16T18:56:53Z; cited coverage metadata_changed/unavailable/partial; source fallback verified |
| `python -X utf8 .tmp/social04-pc-plan-r1/bootstrap.py` |0;1020source match current approved SOCIAL03, entry captured |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/scripts/build_isolated_locales.py build --output /mnt/c/kidsmap/.tmp/social04-pc-plan-r1/locales --locales ru az en --compiler native` |0;3freshMO, sharedMO untouched |
| `wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social04-pc-plan-r1/start.sh` |0; new internal network/volume/app/PG, prior container states recorded |
| `wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social04-pc-plan-r1/prepare.sh` |0; own PG ready/migrate/seed6states/source-gated HTTP |
| PowerShell `Start-Process wsl.exe … proxy.py -WindowStyle Hidden` |own independent loopback33304 helper, PID in ignored scratch |
| `wsl -d Ubuntu-24.04 -- which npx` |0; `/usr/bin/npx`; actual CLI uses Node24 package |
| `… browser_driver.py open about:blank --config=/mnt/c/kidsmap/.tmp/social04-pc-plan-r1/playwright.json` |0; distinct Chromium155 session social04-pc-plan-r1 |
| `… browser_driver.py browser-initial.js` |0; localhost allowlist set before navigation, actual template1020source/fresh sole locales/runtime versions verified |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social04-pc-plan-r1/matrix.py` |0;108cells/1188controlPASS/684styleFAIL/18NAslots, unchanged current source; exit0 means completed capture, not product PASS |
| `wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social04-pc-plan-r1/baseline.sh` |0;4unique existing affected methods,0F/0E,1.502s; own isolated testDB preserved |
| `python -X utf8 .tmp/social04-pc-plan-r1/make_candidate.py` |0; only QA candidate files/diff/hashes created |
| `git apply --check --ignore-space-change docs/qa/social-qa04-recheck-2026-10-16-pc-r1/proposed.diff` |0; unapplied2file proposal |
| `… browser_driver.py neighbors.js` |0;6Favorites control cells/42PASS;6externalfont requests intentionally blocked |
| `python -X utf8 .tmp/social04-pc-plan-r1/publish.py` |0;114native PNG copied with SHA/dimensions; source/container preservation and live metadata verified; one guide note appended |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/scripts/build_isolated_locales.py verify --manifest /mnt/c/kidsmap/.tmp/social04-pc-plan-r1/locales/manifest.json` |0;3current catalogues |
| `python -X utf8 docs/qa/social-qa04-recheck-2026-10-16-pc-r1/verify_artifacts.py` |0; source1020/index/refs/active_run/sharedMO/.cbmignore/previous manifests/proposal/114PNG/links verified; style FAIL preserved |

Targeted baseline command, with `qa=/mnt/c/kidsmap/.tmp/social04-pc-plan-r1` in own shell:

```text
docker exec m09s04-plan-r1-app python "$qa/runtime.py" test
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_invitation_inbox_post_only_recipient_scoped_and_revocation_suppresses_mail
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_csrf_required_for_inbox_actions
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_join_confirmation_form_is_current_owner_post_only
catalog.testcases.test_access_qa02_invitation_decline.InvitationDeclineTests.test_inbox_exposes_decline_for_both_current_invitation_kinds_in_all_locales
```

Actual shell uses continuation backslashes; all4labels are passed to one `runtime.py test` invocation. Backend expected negative403/404/405 stay in raw log. No application assertions changed. Baseline GREEN does not close the CSS bug.

Entry source and locale manifest checked before each django.setup. QA-only role login writes fictional sessions; state comparison concerns notification/invitation/membership/grant/outbox, using explicit READ ONLY transactions/timeouts. GET/browser facts do not prove production or external service success. Expired fixtures are initial synthetic dates, not changed on an active workflow to bypass rules. Auth password/OAuth, actual invite acceptance/rejection/mark-read in browser, simulated transport/error flows and candidate rendering await approved implementation.

Discovery-only command mistakes: PowerShell literal wildcard paths passed to rg were rejected; repeated with `-g`/real directories. A stale skill root and speculative variables.css path were absent; real `.agents/skills` and site.css tokens were read. Early file/socket probes ran while prepare was still migrating and correctly reported not-ready; browser started only after prepare exit0. These were discovery/environment timing observations, not product-test failures. Matrix/targeted tests were not rerun to erase a product FAIL.

Exact browser invocations/exits are in browser-commands.jsonl; runtime settings/profile/credentials are not copied into deliverables. Final verification command/results and preservation are in verification.json and verify_artifacts.py.
