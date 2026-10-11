# Команды и native результаты

Рабочая директория `C:\kidsmap`, PowerShell. Password только в ignored `.tmp/module04-20261010-r1/credential`, не в командах/артефактах. Результаты driver очищены от echoed executed code/credential, `.effective.js` содержит placeholder. Нельзя повторно выполнять seed/prepare поверх сохранённого стенда: для новой проверки создать новый run/ports/DB.

| Действие | Native exit / факт |
|---|---|
| git rev-parse HEAD; branch --show-current; status --short (отдельные read-only вызовы) | 0; snapshot.json |
| prepare.py | 0; 3897 входных hashes включая журнал |
| docker run | 0; новый container/volume |
| run.py migrate | 0; 175 migration records |
| seed.py | 0; 6 actors, 2 orgs, 1 verified specialist, 4 venues, 0 Events |
| run.py snapshot | 0; 2776 hashes |
| run.py serve | продолжающийся own process 43232, no reloader; exit пока не существует |
| Playwright open | 0; отдельный session module04-r1 |
| run.py test, 14 labels ниже | 1; 129 tests:118 PASS/2 application baseline failures/9 environment preflight failures |
| drive.py scripts | CLI/native 0; этот exit не означает PASS: JSON errors/rows отдельно в command-ledger и report |
| server_state.py | 0 для moderation-entry/boundaries/media/final; первая submission попытка 1 (ошибка собственного поля action вместо kind), исправлен только собственный script |
| fixture-stimuli.py revoke/restore/hide-venue/restore | 0; fixture-only, Event ORM writes 0 |
| source-facts.py / translation-proof.py / package.py | 0 |
| verify.py до обновления журнала | 1 ожидаемо: journal row04 ещё не изменён; прочие сохранности PASS |
| verify.py после отчёта/строки журнала | см. verification.json; требуется 0/PASS |

```powershell
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/prepare.py
wsl.exe -- docker run -d --name kidsmap-module04-20261010-r1 -p 127.0.0.1:55435:5432 -e POSTGRES_DB=module04 -e POSTGRES_USER=module04 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/seed.py
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/run.py serve
node C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js -s=module04-r1 open http://localhost:8815/qa/version/ --config=.tmp/module04-20261010-r1/playwright.json
```

Native tests (лог перенаправлен в django-tests.log; `$LASTEXITCODE` сохранён в django-tests.exit.txt):

```powershell
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/run.py test catalog.testcases.test_owner_event_entry catalog.testcases.test_event_admin_readiness catalog.testcases.test_task33_event_security catalog.testcases.test_task33_event_schema catalog.testcases.test_task33_event_queries catalog.testcases.test_task33_event_public catalog.testcases.test_task33_event_owner_contract catalog.testcases.test_task33_event_domain catalog.testcases.test_task33_event_dashboard catalog.testcases.test_task33_event_concurrency catalog.testcases.test_task33_event_calendar_ui catalog.testcases.test_task33_event_calendar_review catalog.testcases.test_task33_event_calendar catalog.testcases.test_task33_event_admin_precision
```

Точный browser driver формат и каждый запуск/повтор с UTC/duration/native exit: [command-ledger.jsonl](command-ledger.jsonl).

```powershell
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py lifecycle.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py resume.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py moderation.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py boundaries.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py media.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py matrix.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py photo-clear-probe.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py state-matrix.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py occurrence.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py rights-open.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/fixture-stimuli.py revoke
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py rights-submit.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/fixture-stimuli.py restore
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py venue-open.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/fixture-stimuli.py hide-venue
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py venue-submit.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/fixture-stimuli.py restore
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py final-paths.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py last-public.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py visual-review.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/drive.py tampering.js
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/server_state.py final
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/package.py
.venv/Scripts/python.exe docs/qa/module04-2026-10-10-r1/verify.py
```

Это воспроизводимые собственные QA scripts, не новая application test suite. Tests scopes и важные UI изменения не выполнялись ORM-сохранением. Fixture metadata/storage не переносится обычным Git.
