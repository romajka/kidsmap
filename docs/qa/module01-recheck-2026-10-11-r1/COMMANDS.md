# Exact local commands and final execution status

Working directory `C:\kidsmap`, PowerShell. No application edits, commit/push/deploy or production commands. Existing QA code was adapted into this run's own directory; all browser scenarios executed freshly. Password placeholders are replaced only in process memory, never persisted in commands/results.

```powershell
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/bootstrap.py
.venv/Scripts/python.exe scripts/build_isolated_locales.py build --output .tmp/module01-recheck-20261011-r1/locales --locales ru az en --compiler wsl
wsl.exe -- docker run -d --name kidsmap-module01-recheck-20261011-r1 -p 127.0.0.1:55446:5432 -e POSTGRES_USER=place_recheck -e POSTGRES_DB=place_recheck -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/seed.py
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/finish_initial_fixtures.py
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/run.py serve-public-safe
```

Bootstrap/build/container/snapshot/initial-fixture completion exit 0. Initial seed did not finish; a second seed attempt exit 1 correctly refused already-created actors. Only initial taxonomy/metadata preparation was completed, with `Place.count()==1` guard before native create. Initial migration output [migrate.txt](migrate.txt); confirmed migration rerun exit 0 and “No migrations to apply” in [migrate-confirmed.txt](migrate-confirmed.txt). Serve remains running, tool session81017, HTTP PID16156; a running server has no completed-process exit code.

```powershell
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/run.py test catalog.testcases.test_place_rejection_feedback catalog.testcases.test_place_qa03_pricing_rebase catalog.testcases.test_place_qa04_manual_location catalog.testcases.test_task33_place_nature_localization catalog.testcases.test_task33_place_continuous
.venv/Scripts/python.exe -m unittest scripts.tests.test_build_isolated_locales
$env:KIDSMAP_JSDOM='C:/kidsmap/.tmp/module01-recheck-20261011-r1/jsdom.cjs'
& 'C:/Program Files/nodejs/node.exe' scripts/test_owner_place_map_picker.cjs
$env:KIDSMAP_JSDOM='C:/kidsmap/.tmp/phone-dom/node_modules/jsdom'
& 'C:/Program Files/nodejs/node.exe' scripts/test_location_resolution.cjs
```

Django 38/38 exit 0 ([log](django.txt)); locale helper9/9 exit0 ([log](locale-helper.txt)); map Node12/12 exit0 ([log](map-js-configured.txt)); location Node22/22 exit0 ([log](district-js-configured.txt)). The own jsdom shim requires the existing read-only `.tmp/phone-dom/node_modules/jsdom`, no install or dependency edits. Two initial Node attempts without this environment exit1: [map](map-js.txt), [location](district-js.txt). These are environment failures, not app test failures. The “synthetic storage failure” traceback inside the passing Django suite belongs to an existing negative test.

```powershell
& 'C:/Program Files/nodejs/node.exe' 'C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js' -s=place-recheck-r1 open http://localhost:8841 --config=C:/kidsmap/.tmp/module01-recheck-20261011-r1/playwright.json
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py place-flow.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py review.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/readback.py
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/prepare_price_script.py
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py mixed-price.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py admin-matrix.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py admin-inspect.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py map.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py nature.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py labels.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py public.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py residual.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py visual-diagnostics.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py console-check.js
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/source-proof.py
.venv/Scripts/python.exe scripts/build_isolated_locales.py verify --manifest .tmp/module01-recheck-20261011-r1/locales/manifest.json
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/aggregate.py
```

Browser open exit0. Exact invocation timestamps/durations/repeats and CLI exits: [command-ledger.jsonl](command-ledger.jsonl). Final browser results: place-flow8P, review39P, mixed-price6P, map7P, nature12P, admin-matrix72P, labels54P, public36P, residual6F, visual-diagnostics18P. Final CLI exits all0; CLI0 is not an app PASS oracle. Aggregate rejects any final scenario `error`, then counts row statuses. admin-inspect/console-check are diagnostic data, not counted PASS tests. Earlier results retained as `*.attempt1.txt`; oracle/setup corrections are explained in REPORT.md. Readback final exit0, source-proof exit0, compiler verify exit0, aggregate exit0. Final readback is explicit SQL READ ONLY with timeouts.

Read-only runtime/provenance and preservation commands:

```powershell
Invoke-RestMethod http://localhost:8841/qa/version/
wsl.exe -- docker ps --format '{{.ID}} {{.Names}} {{.Ports}}'
wsl.exe -- docker inspect kidsmap-module01-recheck-20261011-r1 --format '{{.Id}} {{.Config.Image}} {{range .Mounts}}{{.Name}}{{end}}'
git rev-parse --show-toplevel
git rev-parse HEAD
git branch --show-current
git status --short
.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/finalize.py
```

Last command updates only journal row01 and verifies original foreign hashes, other journal bytes, source hashes, active_run, own source attestation and pre-existing loopback listener PIDs/container identities. Final exit0, 11/11 checks PASS in [verification](verification.json). An initial finalizer attempt exit1 used Windows default encoding for UTF-8 browser JSON; corrected only the QA parser and repeated all checks. Source-map discovery used Codebase Memory, but metadata_changed/coverage_unavailable/partial required direct reads. No graph caches copied into artifacts.
