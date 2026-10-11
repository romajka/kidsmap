# Exact commands — module05 fresh isolated QA

PowerShell, cwd C:/kidsmap. Python native Windows, WSL только Docker. Не выполнять повторно bootstrap на существующей DB; на другом ПК использовать новый run/ports/container/settings. Scratch password генерируется seed.py и не переносится в report.

```powershell
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/prepare.py
wsl.exe -- docker run -d --name kidsmap-module05-20261010-r1 -p 127.0.0.1:55436:5432 -e POSTGRES_DB=module05 -e POSTGRES_USER=module05 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/seed.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/fixture-correction.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/run.py serve
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/fixture-add.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/fixture-admin-access.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/fixture-restore.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/tests-run.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/tests-extra.py
```

Bootstrap/175 migrations/fixtures exits0; fixture-correction исправлял исключительно начальные invented surroundings, до первого audited offering. Проверяемые transitions выполнялись browser; отдельные suites используют собственный test_module05, independent from stand DB.

Browser CLI start использует cached @playwright/cli, config .tmp/module05-20261010-r1/playwright.json; native Chromium binary1243. Exact session:

```powershell
node C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js -s=module05-r1 open --config=.tmp/module05-20261010-r1/playwright.json
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py functional3.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py functional4.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py matrix.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py admin-matrix.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py schedule-fresh.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py pricing.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/server-state.py final
node docs/qa/module05-2026-10-10-r1/check-js.cjs
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/finalize.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/author.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/report.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/update-journal.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/verify.py
```

Все additional browser команды, даты, native exit codes, elapsed seconds и repetitions: [command-ledger.jsonl](command-ledger.jsonl). Выполнялись также probe, functional1/2, save-probe, lifecycle, diagnostics, restore/restore-read, adversarial, multiple, admin-lifecycle, detach, roundtrip, common, catalog-corrected, conflict-matrix, events-recheck, rejection/rejection-repro, clipping/badge-diagnostic и browser-meta. Каждый .js — native run-code через drive.py; executed credential не сохраняется, .effective.js содержит placeholder. Последовательность существенна: это fixture run, а не idempotent suite. По месту ledger raw outputs использованы как evidence; audit conclusion не приравнивает CLI0 к PASS.

119 final test native command и exit0: [tests-command.json](tests-command.json).131 extra и exit0: [tests-extra-command.json](tests-extra-command.json). Первый cookie-environment119 exit1 (13 failures), собственный adapter corrected без app/assertion edits, repeat0. Verify/generation commands exits записаны в [verification.json](verification.json) и [verification-command.json](verification-command.json). Source and prior hashes сохранены [snapshot](snapshot.json), [preservation](preservation-entry.json). No commit/push/deploy/cleanup.
