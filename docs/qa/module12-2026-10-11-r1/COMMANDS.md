# Exact executed commands

Checkout C:/kidsmap, PowerShell. All setup commands completed exit0;175 isolated migrations. serve commands are persistent owned processes, no completed exit is claimed. Container loopback trust has no password.

```powershell
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/prepare.py
wsl.exe -- docker run -d --name kidsmap-module12-20261011-r1 -p 127.0.0.1:55443:5432 -e POSTGRES_DB=module12 -e POSTGRES_USER=module12 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/seed-metrics.py
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/run.py serve-public-safe
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/run.py serve-errors
node C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js -s=module12-r1 open http://localhost:8829/qa/version/ --config .tmp/module12-20261011-r1/playwright.json
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/seed-empty.py
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/visual-index.py
```

Browser ledger (all attempts retained):

|Command|CLI exit|Seconds|Result|
|---|---|---|---|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py functional.js`|1|22.88|[functional.result.txt](functional.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py functional.js`|0|39.61|[functional.result.txt](functional.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py contacts.js`|0|19.7|[contacts.result.txt](contacts.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py matrix.js`|0|149.22|[matrix.result.txt](matrix.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py contacts.js`|0|17.41|[contacts.result.txt](contacts.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py rename-probe.js`|0|7.01|[rename-probe.result.txt](rename-probe.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py keyboard.js`|0|35.62|[keyboard.result.txt](keyboard.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py fault.js`|0|2.73|[fault.result.txt](fault.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py lifecycle.js`|1|51.11|[lifecycle.result.txt](lifecycle.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py lifecycle.js`|0|64.64|[lifecycle.result.txt](lifecycle.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py devices-periods.js`|0|13.66|[devices-periods.result.txt](devices-periods.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py states.js`|0|75.45|[states.result.txt](states.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py telemetry.js`|0|111.74|[telemetry.result.txt](telemetry.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py empty.js`|0|49.03|[empty.result.txt](empty.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/drive.py private-proof.js`|0|2.94|[private-proof.result.txt](private-proof.result.txt)|

[Exact13 Django labels, runtimes and raw methods](test-review/primary.json), [test commands/counts](test-review/REPORT.md). Source probes: `source-review/source_checks.py` exit0/18files and `source-review/origin_checks.py` exit0/7checks. Root `build-report.py`, `verify.py` and `update-journal.py` are own artifact operations; final exact exits in verification.json.
