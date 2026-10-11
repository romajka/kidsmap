# Команды и native exits

Все команды из `C:\kidsmap`, PowerShell. Random synthetic password читается launcher-ом только из ignored `.tmp/module03-20261010-r1/credential`; значений здесь нет. **Не запускать seed/prepare снова поверх сохранённого evidence**: эти операции подготовительные и изменяют только собственные QA fixtures/snapshot. Browser scripts — stateful последовательность, не независимые универсальные тесты.

Зафиксированные browser invocations/utc/duration/native CLI exits: [command-ledger.jsonl](command-ledger.jsonl). Каждый исполнялся как:

```powershell
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/drive.py SCRIPT.js
```

Drive запускает существующий `node C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js -s=module03-r1 run-code SOURCE` с подстановкой собственной credential в памяти; source в ledger представлен файлом, `.effective.js` сохранён с placeholder. CLI exit0 не означает PASS: в JSON есть FAIL/error. Следует читать все rows и error. Нативные CLI ошибки1 отдельны от assertions.

Функциональная последовательность: inspect → lifecycle (partial harness stop) → complete-proposal → moderation-claim (public selector stop) → cooperation → documents → negative (dblclick/reload race) → error-preview → conflict-recheck → republish → matrix → state-matrix → file-recheck → keyboard → duplicate → progress-recheck → loading-recheck (harness timeout) → loading-observer → boundaries → photo-final (последний полный7PASS) → revocation → revocation-denial → console-final. Raw previous attempts сохранены с `.attemptN.txt`.

Свежая подготовка, выполнявшаяся в этом запуске:

```powershell
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/prepare.py
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/seed.py
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/foreign_fixture.py
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/run.py serve
```

Initial QA seed errors: wrong OrganizationGrant field names, Place region field, creating linked place without structural service; исправлены только own QA script. Initial fictional text включал junk token `test`, из-за которого fixture была невидима public selector; заменены только вымышленные fixture fields и подтверждён public query. Это не findings приложения и не выполнение audited specialist transitions ORM. Standalone place fixture linked via `set_place_organization`. Specialist3 created through native proposal send; profile2 verified foreign identity initial fixture only; profile1 and all audited claim/moderation/cooperation/document/profile transitions nativeUI.

PostgreSQL17-alpine WSL Docker создан заново: container `kidsmap-module03-20261010-r1`, loopback55434→5432, DB/user module03, trust-auth loopback, без production credential/volume. Точный первоначальный shell invocation Docker не сохранён в command ledger; не выдаётся за captured command. Reproduction equivalent только для нового имени/порта:

```powershell
wsl.exe -- docker run -d --name NEW_UNIQUE_CONTAINER -p 127.0.0.1:NEW_PORT:5432 -e POSTGRES_DB=NEW_DB -e POSTGRES_USER=NEW_USER -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
```

Сверка реально запущенных контейнеров/старых PID:

```powershell
wsl.exe -- docker ps --filter name=kidsmap-module --format '{{.Names}} {{.Ports}}'
Get-NetTCPConnection -LocalPort 8811,8812,8813,8814 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalPort,OwningProcess
```

Own8814 PID43560; prior8811/6112,8812/40848,8813/40932; PG55431/55432/55433 сохранены. Own container ID указан в REPORT, environment settings [qa_settings.py](qa_settings.py). Запуск server use_reloader=False проверяет весь source digest до старта и импортирует `C:/kidsmap/src`, не другой checkout. Browser transport blocked outsidelocalhost8814; Python socket guard loopback only; .env не загружен приDJANGO_TESTING=1.

Тесты:

```powershell
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/test_driver.py
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/run.py test catalog.testcases.test_specialist_proposal_drafts.SpecialistProposalDraftTests.test_private_photo_survives_reload_is_author_only_and_copies_on_send
```

Driver subprocess exact eight labels/nativeexit1/launcher57.812s в [backend-result.json](backend-result.json);107 tests runner24.856s,106 PASS/1 ERROR. Single repeat runner0.386s,1 ERROR/nativeexit1; [repeat json](backend-platform-recheck.json). Existing assertions не изменялись.

Read-only/QA packaging:

```powershell
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/locale_probe.py
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/observe_final.py
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/contact_sheets.py
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/package_evidence.py
.venv/Scripts/python.exe docs/qa/module03-2026-10-10-r1/verify_preservation.py
git diff --check
git status --short
```

Locale exit0:12 comparisons,8 mismatches; observe exit0: only isolated fictional aggregate reads;13 contact sheets; packaging/verifier actual latestcounts/exit authoritative in [evidence-summary.json](evidence-summary.json) и [verification.json](verification.json). No commit/push/deploy/production calls.
