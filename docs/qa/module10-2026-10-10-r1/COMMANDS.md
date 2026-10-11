# Команды и воспроизводимость QA10

Рабочий каталог C:\kidsmap, shell PowerShell. Все команды ниже — собственный QA10; credentials только в ignored scratch, не в command artifacts. Native browser Chromium153.0.8010.12/headless shell1243, session module10-r1.

Bootstrap helpers: `prepare.py` (создана fresh preservation manifest и ignored credential), `run.py snapshot`, `run.py migrate` (175 migrations), `seed.py` (initial fictional data). Helper seed первые попытки упали на собственной гонке миграций и неправильном lon вместо lng; final seed успешен. Первый qa/state probe был исправлен только в own helper (Organization.archived_at вместо несуществующего deleted_at), собственный main process перезапущен после проверки его identity. Application sources не менялись.

Точные команды собственных runner, воспроизводимые из repo root:

```powershell
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/seed.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/run.py serve
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/run.py serve-errors
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/extra-fixtures.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/lawful-fixtures.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/owned-organization.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/organization-readback.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/mo-check.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/acl-identity.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/tests-run.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/tests-run.py pages
wsl.exe -- docker inspect --format '{{.Id}} {{.Config.Image}} {{range .Mounts}}{{.Name}} {{.Destination}}{{end}}' kidsmap-module10-20261010-r1
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/build-report.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/verify.py
```

Внимание: bootstrap scripts не идемпотентны, не повторять seed/prepare/snapshot на существующей DB, чтобы не подменить entry. Для нового run нужны новое имя/порты/DB/scratch. PG own image postgres:17-alpine, loopback55441, user/DB module10, trust только own local container, отдельный volume; runtime inspect в verification. Полный исходный docker/browser-open shell invocation не был сохранён как отдельный command log; не восстанавливаем его по догадке. Browser executable/config фактически сохранён в ignored scratch/playwright.json; native replay wrapper drive.py содержит exact node CLI executable and run-code arguments без password в committed/effective source.

Unit exact selected labels, native process exit/duration и scrub counts: [tests-command.json](tests-command.json), [pages-tests-command.json](pages-tests-command.json). Первый pages attempt сохранён отдельно. Много failures на уровне наблюдений не означает CLI nonzero: CLI exit0 лишь показывает, что script завершился и вернул rows.

Browser native command ledger (включая failed harness attempts):

| UTC | Точная команда | CLI exit | Seconds | Result |
|---|---|---:|---:|---|
| 2026-10-10T15:16:48.559399+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py probe.js` | 1 | 2.08 | [probe.result.txt](probe.result.txt) |
| 2026-10-10T15:17:32.946748+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py probe.js` | 0 | 2.89 | [probe.result.txt](probe.result.txt) |
| 2026-10-10T15:18:40.886024+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py probe.js` | 1 | 32.45 | [probe.result.txt](probe.result.txt) |
| 2026-10-10T15:19:24.898896+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py probe.js` | 0 | 9.17 | [probe.result.txt](probe.result.txt) |
| 2026-10-10T15:23:59.803640+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py matrix-empty.js` | 0 | 162.56 | [matrix-empty.result.txt](matrix-empty.result.txt) |
| 2026-10-10T15:25:12.938068+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py settings.js` | 0 | 17.2 | [settings.result.txt](settings.result.txt) |
| 2026-10-10T15:26:37.780766+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py matrix-filled.js` | 1 | 11.25 | [matrix-filled.result.txt](matrix-filled.result.txt) |
| 2026-10-10T15:30:07.360071+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py matrix-filled.js` | 0 | 141.28 | [matrix-filled.result.txt](matrix-filled.result.txt) |
| 2026-10-10T15:40:06.749502+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py flags.js` | 0 | 462.36 | [flags.result.txt](flags.result.txt) |
| 2026-10-10T15:42:27.513010+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py acl.js` | 0 | 12.47 | [acl.result.txt](acl.result.txt) |
| 2026-10-10T15:43:51.598952+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py keyboard.js` | 1 | 9.8 | [keyboard.result.txt](keyboard.result.txt) |
| 2026-10-10T15:45:17.796213+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py keyboard.js` | 1 | 2.38 | [keyboard.result.txt](keyboard.result.txt) |
| 2026-10-10T15:48:35.438150+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py keyboard.js` | 0 | 140.94 | [keyboard.result.txt](keyboard.result.txt) |
| 2026-10-10T15:50:56.195115+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py media-errors.js` | 0 | 58.53 | [media-errors.result.txt](media-errors.result.txt) |
| 2026-10-10T15:54:48.088469+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py finish.js` | 0 | 33.45 | [finish.result.txt](finish.result.txt) |
| 2026-10-10T16:02:54.049712+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py faq-proof.js` | 0 | 33.94 | [faq-proof.result.txt](faq-proof.result.txt) |
| 2026-10-10T16:04:04.449750+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py modal-proof.js` | 1 | 57.11 | [modal-proof.result.txt](modal-proof.result.txt) |
| 2026-10-10T16:05:46.793702+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py modal-proof.js` | 0 | 48.3 | [modal-proof.result.txt](modal-proof.result.txt) |
| 2026-10-10T16:06:13.663575+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py organization-proof.js` | 1 | 10.94 | [organization-proof.result.txt](organization-proof.result.txt) |
| 2026-10-10T16:07:10.233343+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py organization-proof.js` | 0 | 6.17 | [organization-proof.result.txt](organization-proof.result.txt) |
| 2026-10-10T16:07:23.856021+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py network-proof.js` | 0 | 4.05 | [network-proof.result.txt](network-proof.result.txt) |
| 2026-10-10T16:07:55.306410+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py organization-proof.js` | 0 | 7.8 | [organization-proof.result.txt](organization-proof.result.txt) |
| 2026-10-10T16:09:05.997454+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py visual-final.js` | 0 | 25.5 | [visual-final.result.txt](visual-final.result.txt) |
| 2026-10-10T16:10:26.272420+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py organization-proof.js` | 0 | 6.91 | [organization-proof.result.txt](organization-proof.result.txt) |
| 2026-10-10T16:13:34.155393+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py focus-proof.js` | 0 | 49.17 | [focus-proof.result.txt](focus-proof.result.txt) |
| 2026-10-10T16:28:56.961866+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py current-matrix.js` | 0 | 155.03 | [current-matrix.result.txt](current-matrix.result.txt) |
| 2026-10-10T16:30:13.351905+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py current-settings.js` | 0 | 21.02 | [current-settings.result.txt](current-settings.result.txt) |
| 2026-10-10T16:31:14.902355+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py current-focus.js` | 0 | 61.48 | [current-focus.result.txt](current-focus.result.txt) |
| 2026-10-10T16:31:55.461899+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py current-boundary.js` | 0 | 40.39 | [current-boundary.result.txt](current-boundary.result.txt) |
| 2026-10-10T16:34:48.524267+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py current-pages.js` | 0 | 172.97 | [current-pages.result.txt](current-pages.result.txt) |
| 2026-10-10T16:34:52.653936+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py current-network.js` | 0 | 4.06 | [current-network.result.txt](current-network.result.txt) |
| 2026-10-10T16:36:44.459771+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py current-console.js` | 1 | 0.33 | [current-console.result.txt](current-console.result.txt) |
| 2026-10-10T16:37:14.685335+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py current-console.js` | 0 | 15.16 | [current-console.result.txt](current-console.result.txt) |
| 2026-10-10T16:43:57.487837+00:00 | `.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive.py current-concurrency.js` | 0 | 6.91 | [current-concurrency.result.txt](current-concurrency.result.txt) |

После foreign source drift: exact commands

```powershell
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/prepare-current.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/run-current.py serve
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/run-current.py serve-errors
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/drive-current.py current-matrix.js
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/current-checks.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/current-readback.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/tests-run.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/tests-run.py pages
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/annotate-current.py
```

Original full tests/commands сохранены в attempts; 2 повторных selected suites в финальном test-summary. Повтор запуска текущих helpers не означает право менять приложение.
