# Exact execution commands and outcome locations

Run from C:/kidsmap in PowerShell. Commands below refer only to this run; do not reuse another PC's PID/session/volume. Credentials are created in ignored own scratch and never included in artifact commands.

```powershell
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/prepare.py
wsl.exe -- docker run -d --name kidsmap-module13-20261011-r1 -p 127.0.0.1:55444:5432 -e POSTGRES_USER=module13 -e POSTGRES_DB=module13 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/seed.py
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/run.py serve-public-safe
& 'C:/Program Files/nodejs/node.exe' 'C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js' -s=module13-r1 open http://localhost:8831/qa/version/ --config .tmp/module13-20261011-r1/playwright.json
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/read-state.py final-state.json
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/build-report.py
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/verify-final.py
```

[Root native UI per-command UTC/command/CLI exit/duration/results](command-ledger.jsonl). Every listed native script was invoked as `.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/drive.py SCRIPT.js`; fixture/credential substitution occurs only in memory. CLI exit0 does not imply all scenario assertions PASS. Retried raw attempts are preserved. The root ledger contains actual executed exact commands; initialization snippet above documents the stand construction, not a command to replay against an occupied port.

[Browser exact commands](browser-review/REPORT.md), [browser ledger](browser-review/command-ledger.jsonl), [full backend/JS/standalone exact commands and raw exits](test-review/REPORT.md), [JS20 command arrays](test-review/js-results.json), [Django runner at launch](test-review/full-runner-at-launch.py). Native and test isolation profiles differ intentionally and are documented; no production transport occurs.
