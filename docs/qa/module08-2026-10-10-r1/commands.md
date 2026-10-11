# Команды и фактические результаты

Working directory C:\kidsmap, PowerShell, login:false. Browser driver запускает установленный Node/Playwright CLI с session module08-r1; effective JS с placeholders сохранён рядом. Пароль читается только из ignored scratch; executed code с секретом не сохраняется. CLI exit0 означает выполнение скрипта, а не PASS всех observations.

## Targeted existing Django tests

```text
C:\kidsmap\.venv\Scripts\python.exe C:\kidsmap\docs\qa\module08-2026-10-10-r1\run.py test catalog.testcases.test_task33_publication catalog.testcases.test_task33_admin_editors catalog.testcases.test_task33_volunteer_hub catalog.testcases.test_task33_completion_moderation catalog.testcases.test_volunteer_admin catalog.testcases.test_volunteer_dashboard catalog.testcases.test_moderation_sla catalog.testcases.place_readiness catalog.testcases.test_admin_candidate_cover catalog.testcases.test_task33_specialist_privacy
```

215/215 PASS, failures0/errors0/skipped0,147.499s, native exit0. [Точный argv и exit](tests-command.json), [stdout/stderr](tests.log). Изолирован test_module08, unit-media/unit-private-media/LocMem email. CSRF cookie в unit process csrftoken под существующие тесты; browser stand использует собственный cookie. Assertions приложения не менялись.

## Реальный Chromium

| № | Exact driver command | CLI exit | Seconds | Raw result |
|---|---|---|---|---|
| 1 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py discover.js` | 0 | 8.47 | [discover.result.txt](discover.result.txt) |
| 2 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py flows.js` | 0 | 31.09 | [flows.result.txt](flows.result.txt) |
| 3 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py matrix.js` | 0 | 92.23 | [matrix.result.attempt1.txt](matrix.result.attempt1.txt) |
| 4 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py flows2.js` | 0 | 31.67 | [flows2.result.txt](flows2.result.txt) |
| 5 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py matrix.js` | 0 | 303.49 | [matrix.result.txt](matrix.result.txt) |
| 6 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py acl.js` | 1 | 1.42 | [acl.result.attempt1.txt](acl.result.attempt1.txt) |
| 7 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py acl.js` | 0 | 43.09 | [acl.result.txt](acl.result.txt) |
| 8 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py supplement.js` | 0 | 204.25 | [supplement.result.attempt1.txt](supplement.result.attempt1.txt) |
| 9 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py flows3.js` | 1 | 33.05 | [flows3.result.txt](flows3.result.txt) |
| 10 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py gallery.js` | 0 | 20.47 | [gallery.result.txt](gallery.result.txt) |
| 11 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py supplement.js` | 0 | 104.31 | [supplement.result.txt](supplement.result.txt) |
| 12 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py gallery-resume.js` | 0 | 22.66 | [gallery-resume.result.attempt1.txt](gallery-resume.result.attempt1.txt) |
| 13 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py gallery-resume.js` | 1 | 24.3 | [gallery-resume.result.txt](gallery-resume.result.txt) |
| 14 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py flows3-resume.js` | 0 | 17.52 | [flows3-resume.result.txt](flows3-resume.result.txt) |
| 15 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py gallery-finish.js` | 0 | 8.02 | [gallery-finish.result.txt](gallery-finish.result.txt) |
| 16 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py editor-validation.js` | 0 | 13.72 | [editor-validation.result.txt](editor-validation.result.txt) |
| 17 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py final-proof.js` | 1 | 17.67 | [final-proof.result.attempt1.txt](final-proof.result.attempt1.txt) |
| 18 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py final-proof.js` | 0 | 47.53 | [final-proof.result.txt](final-proof.result.txt) |
| 19 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py editor-finish.js` | 0 | 6.5 | [editor-finish.result.txt](editor-finish.result.txt) |
| 20 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py specialist-save-proof.js` | 0 | 3.8 | [specialist-save-proof.result.txt](specialist-save-proof.result.txt) |
| 21 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py specialist-finish.js` | 0 | 48.53 | [specialist-finish.result.attempt1.txt](specialist-finish.result.attempt1.txt) |
| 22 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py specialist-finish.js` | 0 | 21.61 | [specialist-finish.result.txt](specialist-finish.result.txt) |
| 23 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py specialist-valid-finish.js` | 0 | 6.95 | [specialist-valid-finish.result.txt](specialist-valid-finish.result.txt) |
| 24 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py drawers.js` | 0 | 89.61 | [drawers.result.txt](drawers.result.txt) |
| 25 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py searches.js` | 0 | 230.44 | [searches.result.txt](searches.result.txt) |
| 26 | `.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drive.py search-retry.js` | 0 | 4.02 | [search-retry.result.txt](search-retry.result.txt) |

В журнале 26 native browser executions; exits {0: 22, 1: 4}. Counts authoritative: [results-summary](results-summary.json), [matrix.json](matrix.json), [396 исключённых/заменённых observations](excluded-observations.json). Не-JSON uncaught harness failures не получают выдуманного количества assertion rows. Все попытки сохранены; latest результаты выбирает [aggregate.py](aggregate.py).

## Подготовка и финальная проверка

```powershell
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/prepare.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/seed.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/bootstrap-retry.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/run.py serve
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/seed-extra.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/seed-taxonomy.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/filter-contract.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/aggregate.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/contacts.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drawer-contacts.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/write-report.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/verify.py
git diff --check
wsl.exe -- docker inspect kidsmap-module08-20261010-r1 --format '{{.Id}} {{.Config.Image}} {{json .Mounts}}'
wsl.exe -- docker exec kidsmap-module08-20261010-r1 postgres --version
```

Setup: первый migrate exit1 (PG ещё не готов), первый seed exit1 (неполная обязательная category), следующий seed exit1 (гонка с завершением migrations/UndefinedColumn). Собственная незавершённая QA DB переинициализирована до browser transitions; guarded bootstrap-retry exit0 после175 migrations. Итоговый migrate exit0 [migrations.log](migrations.log); serve остаётся running PID42060, это не завершившаяся команда с exit0. prepare/snapshot/extra fixtures/taxonomy/filter-contract/aggregate/contacts exits0. Итог verify/git diff --check подтверждается [verification.json](verification.json), а не ожиданием скрипта.

Docker stand: новый postgres:17-alpine, actual PostgreSQL17.11, localhost55439, unique container/volume в [runtime-final](runtime-final.json). Полный первоначальный shell argv docker creation отдельно не записан; current image/mount/ID проверены read-only inspect. Команды выше не являются сценарием для повторного запуска поверх завершённого stand: bootstrap содержит guards и fixtures не идемпотентны.

Exploratory source reads с неверным путём и собственные PowerShell quoting/cp1251 ошибки не являются failures приложения. Финальные Python AST/JS syntax проверки включены в verify. Production/foreign stand commands не выполнялись.
