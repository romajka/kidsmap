# Модуль06 — команды и native exit codes

Все команды выполнялись из `C:\kidsmap`, PowerShell, без commit/push/deploy. Здесь описана собственная QA область; прежние стенды не перезапускаются. Сначала читать snapshot/fixtures/state-final: повторный seed или исходная negative проверка после публикации27 изменяет смысл сценария.

## Входные read-only проверки

```powershell
Get-Location
git rev-parse --show-toplevel
git rev-parse HEAD
git branch --show-current
git status --short
Get-Content -LiteralPath AGENTS.md -Encoding UTF8
Get-Content -LiteralPath .agents/README.md -Encoding UTF8
Get-Content -LiteralPath .agents/registry.json -Encoding UTF8
Get-Content -LiteralPath .agents/agents/kidsmap-orchestrator/agent.md -Encoding UTF8
Get-Content -LiteralPath .agents/knowledge/architecture.md -Encoding UTF8
Get-Content -LiteralPath .agents/knowledge/source-of-truth.md -Encoding UTF8
Get-Content -LiteralPath .agents/rules/audit-contract.md -Encoding UTF8
Get-Content -LiteralPath docs/qa/content-entry-audit-2026-10-06.md -Encoding UTF8
Get-Content -LiteralPath docs/qa/module-acceptance-prompts.md -Encoding UTF8
```

Graph research через codebase-memory-mcp C-kidsmap и узкое source inspection описаны в REPORT. Исторические результаты не переиспользованы как PASS.

## Собственный стенд

Own setup в [prepare.py](prepare.py), [run.py](run.py), [qa_settings.py](qa_settings.py), [run-configured.py](run-configured.py), [seed.py](seed.py), [fixture-correction.py](fixture-correction.py). Docker доступен через `wsl.exe -- docker`, native `docker` не найден. Использован новый контейнер PostgreSQL17-alpine с только localhost55437 и новой DBmodule06. Container ID `820e82dd5624a8fcb7051de574325966db5562e4b03f1d69393a2792ca4ee566`; реальные current mounts/ports — verification.json. Credentials не выводятся. Историческую Docker shell строку bootstrap отдельный ledger не сохранил; параметры подтверждены свежим inspect, точная строка не реконструируется как evidence.

```powershell
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/prepare.py
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/seed.py
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/fixture-correction.py
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/run.py serve
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/run-configured.py
```

Первые seed попытки отклонены из-за ошибок собственного setup (PricingPlan fields/quantity/0/0). Исправлен только QA seed; финальная фикстура создана успешно. Snapshot2784 файлов,175 migrations и final isolation записаны. Initial setup commands не имеют общего native exit ledger: это ограничение записи команд. Servers долгоживущие, process exit code неприменим; текущие listeners/versions проверяет verify.py. ORM использован только для initial synthetic setup. Audited publication/edit/cancellation/section changes — browser scripts ниже.

Native Playwright CLI запускается абсолютным Node path. Browser binary: `C:/Users/Ramin/AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe`, headless Chromium153.0.8010.12, default1440×950. Собственные sessions module06-r1 и module06-proof.

```powershell
& 'C:/Program Files/nodejs/node.exe' 'C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js' -s=module06-proof open http://localhost:8817/ru/catalog/ --config=.tmp/module06-20261010-r1/playwright.json
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/drive.py filter-settled.js module06-proof
```

Driver использует настоящий `run-code`, new browser contexts, только localhost navigation/requests. `.effective.js` хранит placeholder пароля; значение подставляется в памяти из ignored scratch. Не копировать credentials в команды/отчёты. Exact per-script invocations, UTC/duration/native CLI exits — [BROWSER-COMMANDS.md](BROWSER-COMMANDS.md) и [command-ledger.jsonl](command-ledger.jsonl). CLI1 при собственном screenshot timeout/observer/session error сохранены; Python wrapper/pipeline0 не заменяет native CLI code. Исправления собственного harness и выбор authoritative observations — CORRECTIONS.md и aggregate.py.

## Свежие unchanged tests

Точная native Django команда:

```powershell
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/run.py test catalog.testcases.test_task33_search catalog.testcases.test_task33_map catalog.testcases.test_task33_home_map catalog.testcases.test_public_filter_consistency catalog.testcases.test_place_sorting_and_filtering catalog.testcases.test_search_engine_verification catalog.testcases.test_home_public_metrics catalog.testcases.test_public_section_switches catalog.testcases.test_task33_public_details catalog.testcases.test_task33_event_public catalog.testcases.test_living_map
```

Запись получена через `.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/tests-run.py`. Native exit1:93 methods, один failing method с двумя AZ/EN subtests,0 errors. Launcher test mode использует отдельный `test_module06`, test-media/private-media и CSRF cookie name ожидаемый неизменёнными tests. Изменений assertions нет. tests-command.json содержит timestamp и argv. tests.log после локального CSRF redaction; это сохранённый свежий output, не production logs.

```powershell
& 'C:/Program Files/nodejs/node.exe' --test static/js/tests/google_maps_motion.test.js
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/capture-checks.py
```

6/6 Node tests PASS, native exit0. capture-checks.py также записал MO/PO hashes и redaction count10. Compiled locales не пересобирались. Повтор capture-checks только ради redaction не нужен: второй проход даст0 replacements и заменит исходную metadata.

```powershell
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/http-negative.py
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/state.py
```

60/60 initial negative HTTP checks PASS; source чтение собственной DB внутри explicit READ ONLY transaction, statement timeout10s/lock timeout2s. Финальный state содержит только вымышленные allowlisted records/fields. После UI публикации27 первоначальный negative script не запускался повторно.

## Финальная сборка evidence

```powershell
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/contact-all.py
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/aggregate.py
.venv/Scripts/python.exe docs/qa/module06-2026-10-10-r1/verify.py
git diff --check
```

Contact previews созданы, native screenshots не изменялись; исходный exit code этой команды не сохранён отдельным ledger. Aggregate exit0:1483 rows,1378 PASS/51 FAIL/54 NOT RUN, no unclassified FAIL;629 PNG =616 native +13 DERIVED. Verify выполняет current source/runtime/listener/volume/syntax/links/credential/journal checks, сохраняет все результаты; strict exit1 из-за двух чужих ledger drifts, own_scope_integrity_pass=true. Это не новый application test failure. Exact JS/Python syntax checks находятся в syntax-final.json. После PASS checks расширение тестов не выполняется без новых оснований.
