# Executed commands

Checkout `C:\kidsmap`, PowerShell. Safe argv, timestamps, durations, exit codes and output files are in [command-ledger.jsonl](command-ledger.jsonl). Credential values were generated in ignored scratch and injected into browser code only in process memory.

```powershell
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/bootstrap.py
.venv\Scripts\python.exe scripts/build_isolated_locales.py build --output .tmp/place-qa08-fix-20261011-r1/baseline-locales --locales ru az en --compiler wsl
wsl.exe -- docker run -d --name kidsmap-place-qa08-fix-20261011-r1 -p 127.0.0.1:55447:5432 -e POSTGRES_USER=qa08_district -e POSTGRES_DB=qa08_district -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
```

Bootstrap output was captured by an asynchronous shell call; its completion is established by the completed entry/foreign-file inventory and subsequent successful setup. Builder and docker creation exit0. The first new test run saved in `django-red.txt` had the expected RU failure plus an incorrect new QA assumption about identical language-dependent option ordering. Source `locations.py:521` sorts translated labels; the new test was corrected to compare the stable code set. Windows shell output encoding also damaged displayed non-ASCII in that first log. Existing tests/assertions were untouched. The UTF-8 recorder and corrected RED rerun retain the proper application failure below.

```powershell
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py django-red-confirmed .venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/run.py test catalog.testcases.test_place_qa08_district_localization
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py apply-po-fix .venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/apply_fix.py
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py build-fixed .venv\Scripts\python.exe scripts/build_isolated_locales.py build --output .tmp/place-qa08-fix-20261011-r1/fixed-locales --locales ru az en --compiler wsl
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py verify-fixed .venv\Scripts\python.exe scripts/build_isolated_locales.py verify --manifest .tmp/place-qa08-fix-20261011-r1/fixed-locales/manifest.json
.venv\Scripts\python.exe -c "from pathlib import Path; Path('.tmp/place-qa08-fix-20261011-r1/locale-profile').write_text('fixed-locales', encoding='utf-8')"
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py django-green .venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/run.py test catalog.testcases.test_place_qa08_district_localization catalog.testcases.test_place_qa04_manual_location catalog.testcases.test_task33_place_nature_localization
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py migrate .venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/run.py migrate
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py seed .venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/seed.py
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py runtime-snapshot .venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/run.py snapshot
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/run.py serve
```

RED:2 tests,1 RU failure, exit1. GREEN:6/6 PASS, exit0. Fixed build, manifest verify, migration, initial seed and snapshot exit0. Test DB `test_qa08_district` was created/destroyed within this run's cluster. Native server stdout/stderr are in ignored scratch, not deliverables; server PID19364, HTTP8842, tool session95426 remains running and has no completed-process exit code.

Browser CLI path was the existing local installation. The initial own config used installed Chrome, which exited during launch (`browser-open.txt`, exit1); a snapshot without an open session also exited1. Only own config was switched to the already present Chromium headless shell executable. No browser install, unrelated session or production access.

```powershell
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py browser-open-headless-shell 'C:/Program Files/nodejs/node.exe' C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js -s=place-qa08-fix-r1 open about:blank --config=C:/kidsmap/.tmp/place-qa08-fix-20261011-r1/playwright.json
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/drive.py placeholder-matrix.js
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/drive.py roundtrip.js
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py source-proof .venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/source_proof.py
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py aggregate .venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/aggregate.py
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/record.py finalize .venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/finalize.py
```

Final browser open, both scripts, source proof and aggregate exit0;75+12=87 PASS observations. First aggregate image-read attempted before the asynchronous writer finished; no image was returned then, the completed aggregate exited0 and subsequent visual reads succeeded. Native PNG screenshots were opened with `view_image`; six DERIVED contact/crop sheets were also visually inspected. Finalize result is in [finalize.txt](finalize.txt), [verification](verification.json).

Safe read-only discovery/preservation: git HEAD/branch/status, active_run line, OS loopback listeners, `docker ps --format '{{.ID}} {{.Names}} {{.Ports}}'`, targeted source reads and Codebase Memory coverage. Its relevant coverage was unavailable/metadata_changed, so critical conclusions were checked directly against source. No graph caches persisted. SQL in own `qa/state/` uses explicit READ ONLY transaction, statement_timeout10s and lock_timeout2s; browser saves are native POST.
