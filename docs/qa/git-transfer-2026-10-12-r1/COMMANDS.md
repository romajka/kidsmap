# Git transfer verification commands, 2026-10-12

PowerShell, actual checkout `C:\kidsmap`. Commands contain no private credential values. Local `.tmp` settings/credential are ignored and not portable. No server/deploy scripts are called.

```powershell
git ls-remote origin refs/heads/task33-progress refs/heads/main
git diff --cached --name-only
git -c core.safecrlf=false diff --check -- locale scripts src static
.venv\Scripts\python.exe docs/qa/continuation-2026-10-11/verify.py
$env:DJANGO_TESTING='1'
.venv\Scripts\python.exe -m unittest scripts.tests.test_build_isolated_locales
$env:KIDSMAP_JSDOM='C:/kidsmap/.tmp/phone-dom/node_modules/jsdom'
& 'C:/Program Files/nodejs/node.exe' scripts/test_owner_place_map_picker.cjs
& 'C:/Program Files/nodejs/node.exe' scripts/test_location_resolution.cjs
```

Results: remote branch equals initial HEAD; staged inventory empty; app whitespace check0; documentation18 checks PASS; helper9 tests PASS; Node12+22 PASS, all exit0. Documentation verification predates the guide's added transfer-report navigation link; that new link is separately resolved.

The first Django attempt used the former PLACE-QA-08 launcher and could not connect to old loopback55447. The first new-cluster attempt also timed out after WSL/container stopped between separate command invocations. Both discovered40 methods but did not execute test bodies, exit1/environment setup. No test assertions were changed.

```powershell
wsl.exe -- docker run -d --name kidsmap-git-transfer-20261012-r1 --label kidsmap.qa.owner=git-transfer-20261012-r1 -p 127.0.0.1:55448:5432 -e POSTGRES_USER=git_transfer -e POSTGRES_DB=git_transfer -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
.venv\Scripts\python.exe scripts/build_isolated_locales.py build --output .tmp/git-transfer-20261012/locales --locales ru az en --compiler wsl
wsl.exe -- sh -c 'docker start kidsmap-git-transfer-20261012-r1 >/dev/null && docker wait kidsmap-git-transfer-20261012-r1'
.venv\Scripts\python.exe .tmp/git-transfer-20261012/run_tests.py catalog.testcases.test_place_rejection_feedback catalog.testcases.test_place_qa03_pricing_rebase catalog.testcases.test_place_qa04_manual_location catalog.testcases.test_task33_place_nature_localization catalog.testcases.test_task33_place_continuous catalog.testcases.test_place_qa08_district_localization
```

New owned cluster and build exit0, three locale catalogues. The own docker-wait session keeps WSL alive during Windows tests. Final Django40/40 PASS in26.754s, exit0; test DB destroyed. Loopback55448, separate test roots, verified manifest before setup, inherited credential prefixes removed and external connections blocked. Synthetic storage failure is the intended negative case.

Staging/pushing uses reviewed explicit NUL-separated path lists, regular fast-forward commits and `git push origin HEAD:refs/heads/task33-progress`. The package is split into text/source and image batches below the per-push upload bound. No force push, main update, PR or merge. Final commit list and confirmed remote ref are recorded in REPORT/verification.

NOT RUN: new full module01 acceptance, full configured Django/JS corpus, new browser matrix, GitHub quality job, production/real integrations. Historical reports retain their own scopes and failures.
