# Изолированный стенд02

Данные вымышленные; пароль создан только в `.tmp/module02-20261009-r1/credential` и не является переносимым artifact. Существующие DB/стенды не использовались. Код читается из текущего `C:\kidsmap`; hashes повторно сверены в verification.json.

Новый контейнер без прежних volumes, loopback only, native exit0:

```powershell
wsl -d Ubuntu-24.04 -- docker run -d --pull=never --name kidsmap-module02-20261009-r1 --label kidsmap.qa.owner=module02-20261009-r1 -p 127.0.0.1:55432:5432 -e POSTGRES_USER=module02 -e POSTGRES_DB=module02 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
wsl -d Ubuntu-24.04 -- docker exec kidsmap-module02-20261009-r1 pg_isready -U module02 -d module02
.venv/Scripts/python.exe docs/qa/module02-2026-10-09-r1/capture.py migrate
.venv/Scripts/python.exe docs/qa/module02-2026-10-09-r1/capture.py seed
.venv/Scripts/python.exe docs/qa/module02-2026-10-09-r1/compile_locales.py
```

Первый migrate до готовности PG завершился environment failure; повтор после readiness — exit0. Полные argv/exit codes migrate/seed/test: setup-ledger.jsonl. Translations: locale-build.json. QA helper ошибки (неверные поля region/approved_program_snapshot/import path/Unicode terminal encoding) исправлялись только в собственной обвязке; seed fixture actors создавались get_or_create, destructive cleanup не выполнялся.

Server adapter очищает inherited credential env, не читает application .env, требует DJANGO_TESTING=1, проверяет all source hashes перед стартом, блокирует неloopback socket connects. Запуск hidden; stdout/stderr только в ignored scratch:

```powershell
Start-Process -FilePath 'C:\kidsmap\.venv\Scripts\python.exe' -ArgumentList @('C:\kidsmap\docs\qa\module02-2026-10-09-r1\run.py','serve') -WorkingDirectory 'C:\kidsmap' -WindowStyle Hidden -RedirectStandardOutput 'C:\kidsmap\.tmp\module02-20261009-r1\server.out.log' -RedirectStandardError 'C:\kidsmap\.tmp\module02-20261009-r1\server.err.log' -PassThru
```

Own server8812, PG55432. Server PID при финальном исполнении25764, `.tmp/.../server.pid` — фактическая локальная запись. Only own initial PID42360 остановлен для загрузки собственных свежих translations; запуск25764 использует тот же WORKTREE. Старый server8811/PG55431 и `kidsmap-manual-portable` оставлены.

Browser: bundle Chromium1243, named sessions `module02-r1`, `module02-matrix`; raw exact run-code ledger: command-ledger.jsonl, scripts/effective scripts contain password placeholder only. Главная visual matrix повторена в dedicated session; каждый scenario context ограничивает запросы localhost8812. Native CLI commands используют сохранённый browser.config.json; последующие screenshot/normalization/contact/hash scripts записывают только пакет02.

```powershell
.venv/Scripts/python.exe docs/qa/module02-2026-10-09-r1/drive.py SCRIPT.js
.venv/Scripts/python.exe docs/qa/module02-2026-10-09-r1/finalize_matrix.py
.venv/Scripts/python.exe docs/qa/module02-2026-10-09-r1/make_contacts.py
.venv/Scripts/python.exe docs/qa/module02-2026-10-09-r1/finish_audit.py
```

Не повторять mutation scripts на существующем наборе как будто это новый аудит. Следующий модуль создаёт новую изоляцию. Полноценного self-contained database export не сохранялось; fictional seed/dependency adapters воспроизводят setup, operation receipts относятся к этому конкретному стенду. Никаких production credentials/env values/dumps/graph caches в пакет не переносилось.
