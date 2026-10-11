# Приёмка 01 «Постоянные места» — 2026-10-09, r1

## 1. Решение

**Аудит модуля завершён; приёмка FAIL.** Подтверждены пять baseline defects: один P1 и четыре P2. Приложение не исправлялось. Выполнен только модуль 01; модули 02–13 не принимались. Непроверенные части указаны ниже как NOT RUN и не входят в положительное заключение.

Работу выполнил `/root` последовательно в рамках Django/integration/browser направлений; независимое исполнение специалистами не заявляется. Исторические отчёты использовались только как чек-лист. Все браузерные результаты, данные и скриншоты этого пакета получены заново.

## 2. Checkout, HEAD, WORKTREE, active_run

| Поле | Фактическое значение |
|---|---|
| Checkout | `C:\kidsmap` |
| Branch / HEAD | `task33-progress` / `8d188b316f800fbedf0b1e376905dfd4924cb1b6` |
| WORKTREE при входе | clean |
| WORKTREE после аудита | новый QA-пакет и только строка 01 журнала |
| Существующий active_run | `NONE` в docs/task33/implementation-status.md; файл не изменён |
| Собственный QA run | `module01-20261009-r1`, AUDIT COMPLETE / FAIL |
| Runtime | localhost:8811, DJANGO_TESTING=1, Windows Python3.12.15 / Django6.0.2, свежий PostgreSQL17 |
| Source digest | `589c2d398f3d24d62af28b72e47bbfaeb1c68f8767a080fd83be3a5a5a96b684` |

[Исходный снимок](snapshot.json) содержит SHA-256 2776 файлов src/static/config/locale. Launcher проверяет их перед запуском; `/qa/version/` сообщает тот же HEAD/digest. Финальная проверка всех 2776 хешей: **0 изменений**. [verification.json](verification.json) содержит runtime, native exit codes, Git status/diff и список контейнеров. Git HEAD не менялся; commit/push/deploy не выполнялись. Существующий `kidsmap-manual-portable` оставлен нетронутым.

Прочитаны AGENTS.md, canonical .agents README/registry/orchestrator, architecture/source-of-truth/audit contract, docs/qa/module-acceptance-prompts.md, content-entry-audit-2026-10-06.md и admin-place-map-fix-2026-10-09.md. Недостающих обязательных документов не обнаружено. Codebase memory C-kidsmap: index ready, 74 partial parses, skipped0; API не предоставил timestamp freshness. Graph использован как подсказка; относящиеся к findings связи проверены по текущему source. Source inspection не считается rendered evidence.

## 3. Изоляция и вымышленные данные

Собственный контейнер `kidsmap-module01-20261009-r1`, label `kidsmap.qa.owner=module01-20261009-r1`, loopback port55431, новая DB module01; тесты создавали/удаляли только test_module01. Production credentials не использовались, существующие DB/volumes не копировались. Для localhost контейнера выбран trust auth; он не опубликован наружу.

[qa_settings.py](qa_settings.py) и [run.py](run.py): очищение унаследованных credential environment prefixes, без загрузки checkout .env; LocMem cache/email, отдельные media/private-media, отдельные session/CSRF cookies, пустые integration credentials. Python socket guard запрещает non-loopback соединения; браузер abort всех внешних запросов. Тестовые media/private-media отделены от browser stand при финальном прогоне. Полный server log и локальный пароль находятся только в ignored `.tmp/module01-20261009-r1`; в пакет не копируются. Поиск текущего/прежнего fixture password в текстовых артефактах: 0 совпадений, это ограниченная проверка, не универсальный secret audit.

Фикстуры: owner, outsider, moderator@example.invalid; solid-color PNG; invalid text/corrupt/empty/16MB files; вымышленная организация1 как родитель филиала. Создание организации ORM — только setup: её lifecycle относится к модулю02 и NOT RUN. Места и их проверяемые переходы создавались/сохранялись/отправлялись/одобрялись через UI. ORM/Django Client использовались для read-only диагностики, не для проверяемых transitions.

| ID | Назначение |
|---|---|
| 1 | owner standalone, lifecycle draft/reject/resubmit/approve/public; published edit выявил price projection conflict |
| 2 | owner branch ART, category switches, nested lesson/pricing, media/geo negative paths |
| 3 | admin standalone EDU, draft/photos/no-pin publish, manual coordinates save/reload/clear |
| 4 | новый clean branch FUN, submit/approve/public; gallery→main, реальные RU/EN names, logout/login, повторное approve |

[observations.txt](observations.txt) содержит только состояние собственных synthetic entities. Mismatch у **approved** revision после применения ожидаем; он не является finding. PLACE-QA-03 основан на pending состоянии до отказа, preserved raw review evidence и price_from/to mismatch после отказа.

## 4. Контракт live/candidate

Проверены `publication.py`, `publication_forms.py`, volunteer review guard и pricing services. Новое место материализует draft, submit формирует кандидат, approve публикует. В опубликованной карточке identity/address остаются в кандидате; допустимые расписание и изменения цен при explicit save применяются немедленно согласно `_immediate`. В UI эти границы проверены на месте1: live identity/address сохранены, schedule/amount обновились. После смены15→18 зависимые scalar projections вызвали собственный base conflict — PLACE-QA-03. Защита реального двухвкладочного конфликта отдельно работает.

R1 write mode на собственном стенде `all`, localized place URLs включены. Это явно заданный локальный QA вариант; production flags/config не читались и не менялись. Общий sign-off других конфигураций не заявляется.

## 5. Функциональная матрица

Основные mutation-сценарии выполнены на RU desktop; public/owner/admin display дополнительно RU/AZ/EN и все ширины. Действия сохранения на каждом языке × каждой ширине не повторялись: это NOT RUN, не 234 успешных бизнес-транзакции. Raw result rows дают индивидуальные PASS/FAIL; наличие CLI exit0 не заменяет их оценку.

| Сценарий / роль | Итог | Свежие доказательства |
|---|---|---|
| owner standalone: partial draft, reload, продолжение, age13>12 error, сохранность ввода, error jump, исправление/submit | PASS | [lifecycle](lifecycle.result.txt), [age screenshot](screenshots/owner-age-error-390.png) |
| reviewer reject, owner reload/resubmit, approve, guest public | переходы PASS; причина FAIL | [moderation](moderation.result.txt), [rejection repeat](rejection-recheck.result.txt) |
| настоящий logout через dropdown/button, login, resume | PASS | [final roundtrip](final-roundtrip.result.txt); первоначальный lifecycle использовал clearCookies, не logout UI |
| owner branch: создание из организации; ART/FUN и subcategory reset; fresh branch submit/approve/public | PASS | [create](branch-create.result.txt), [fill](branch-fill.result.txt), [clean branch](branch-clean.result.txt) |
| names AZ/RU/EN и пустой EN; сохранённый перевод отличается от fallback | PASS | [lifecycle](lifecycle.result.txt), [final roundtrip](final-roundtrip.result.txt), [public](public-final.result.txt), [observations](observations.txt) |
| descriptions/age/contacts/address/region/district заполнение и readiness | основной путь PASS; после coordinate clear FAIL | [owner lifecycle](lifecycle.result.txt), [admin](admin-create.result.txt), [fresh field readback](field-readback.result.txt), [district](district-enable.result.txt) |
| no pin draft/publish/photo persistence, admin | PASS | [admin](admin-create.result.txt), [before/after screenshots](screenshots/no-pin-after-publish-390.png) |
| invalid range, half pair, 0/0 owner | ввод/отказ проверены; **специфический 0/0 guard NOT RUN** | [coordinates](coordinates.result.txt): submit 0/0 заблокирован geography requirement, это не доказательство zero-specific validation |
| valid manual coordinate save/reload и clear/save/reload, admin | PASS | [manual roundtrip](manual-roundtrip.result.txt) |
| valid manual coordinate save/reload, owner | PASS | [ожидание HTTP200 и reload](owner-coordinate-roundtrip.result.txt); ранний [coordinates](coordinates.result.txt) FAIL был harness timing, не app finding. Ветка clear остаётся PLACE-QA-04 |
| no SDK owner clear/locate | FAIL | [повтор](map-recheck.result.txt), PLACE-QA-02 |
| admin geolocation denied/unsupported/granted, no data loss | PASS **SIMULATED** | [geolocation](geolocation.result.txt), physical GPS NOT RUN |
| free admission, paid general ticket, events/free-paid repeated switches, admin12/owner8 переключений | PASS, no hang в выполненных повторениях | [branch fill](branch-fill.result.txt), [admin](admin-create.result.txt) |
| place working hours отдельно от nested lesson Saturday14:00 | PASS | [branch fill](branch-fill.result.txt) |
| cover/gallery reload, reorder, remove, replacement; four file errors не удаляют saved cover | PASS | [media repeat](media-recheck.result.txt), [file errors](file-errors.result.txt) |
| gallery→main save/reload; approve; public cover и изображения | PASS | [final roundtrip](final-roundtrip.result.txt), [public pixel/readback](public-final.result.txt), [390](screenshots/verified-public-en-390.png), [1440](screenshots/verified-public-ru-1440.png) |
| owner published edit: candidate/live boundary | PASS | [published](published.result.txt) |
| mixed price/identity edit moderation | FAIL | [fresh submit](resubmit-diagnose.result.txt), [review inspect](review-inspect.result.txt), PLACE-QA-03 |
| чужой ID1/2, foreign draft, admin insufficient rights | PASS (denial redirects; disclosure не обнаружено) | [negative](negative.result.txt) |
| two tabs: loser conflict/input retained, winner protected | PASS | [negative](negative.result.txt), [conflict](screenshots/conflict-390.png) |
| offline save/error/input retained; reconnect/reload; double save no hang | PASS | [negative](negative.result.txt) |

Часть первого branch2 продолжения остановилась на географическом состоянии; публикация самого филиала независимо пройдена на fresh branch4. Старые failed/timed-out QA attempts сохранены для прозрачности, не суммируются с успешными повторами и не объявлены новыми дефектами. Главные причины harness failures: неправильный selector, попытка прочитать response body после navigation, преждевременный reload без завершения photo save, hidden controls без раскрытия. [photo-promote](photo-promote.result.txt) FAIL исправлен **в QA-сценарии**, [final roundtrip](final-roundtrip.result.txt) подтвердил difference0 и HTTP200; app code не менялся.

## 6. Реальный браузер и визуал

Bundled Chromium1243 через Playwright CLI0.1.22. Системный Chrome отказал из-за административной remote-debugging policy; политика системы не менялась. [browser.config.json](browser.config.json) указывает фактический binary. Проверки — реальный DOM/render/screenshots, не jsdom.

RU/AZ/EN ×360/390/768/1024/1280/1440:

| Роль/состояния | Cells | PASS | FAIL |
|---|---:|---:|---:|
| owner empty/filled, admin empty/filled, guest public | 90 | 90 | 0 |
| owner map/gallery/open-control/errors-long | 72 | 72 | 0 |
| admin map/gallery/open-control/errors-long | 72 | 69 | 3 |
| Итого deduplicated | **234** | **231** | **3** |

[matrix.csv](matrix.csv) / [matrix.json](matrix.json) содержат scenario/role/language/width/status/screenshot. Источники: [basic](matrix.result.txt), только owner72 из [deep](deep-matrix.result.txt), [admin final](deep-admin-final.result.txt). Первые4 admin rows из deep исключены как незавершённый дубликат. PASS здесь означает выполненный HTTP/render/no-document-overflow и applicable retained/error criterion, **не полную accessibility сертификацию**.

Визуально просмотрены 13 основных contact sheets (все18 ячеек в каждом состоянии) и выбранные полные screenshots: owner/admin mobile/PC, отказ, popup overflow, public explicit EN. [contact-sheets](contact-sheets/) показывают композицию; мелкий текст desktop thumbnail не заменяет full-size evidence. [screenshots-manifest.json](screenshots-manifest.json) содержит **272 PNG** с реальными размерами и SHA-256. Скриншоты `final-public-*-390.png` первоначально сняты на1280 после logout; они **не используются как mobile evidence**. Корректные 390/1440 повторные файлы имеют prefix `verified-public` и реальные размеры в manifest.

Проверены открытые selectors/picker, map unavailable, saved gallery, длинное name/error, Tab/ShiftTab/Enter/Space/Escape в применимых сценариях и focus samples. Confirmed overflow13px в admin picker360 RU/AZ/EN — PLACE-QA-05. Owner error jump фокусирует поле; admin summary/input retained записаны. Полный keyboard traversal каждого control во всех234 состояниях, screenreader, loading/conflict на каждой language/width комбинации — NOT RUN. Offline/loading/conflict exercised RU390 в функциональных сценариях; blanket matrix PASS для них не заявлен.

[console probe](console-probe.result.txt): 9 role/language checks, **0 pageErrors**, local requestfailed0; **15 console error messages**,14 intentionally aborted external requests (Google fonts/Leaflet CDN) и один suppressed beforeunload при harness navigation без gesture. Это ожидаемая изоляция/браузерный harness, а не «console0». В mutation-путях ожидаемые422 validation/conflict записаны отдельно; один thumbnail404 раннего draft не воспроизведён как устойчивый finding. External CDN/font rendering и real SDK — NOT RUN.

## 7. Backend и команды

Финальный native результат: **84 tests, 71.912s, 0 failures, 0 errors, OK, exit0**. [backend-repeat.txt](backend-repeat.txt) и [backend-result.json](backend-result.json). Existing assertions не менялись. Test DB freshly created/destroyed; Django test settings и отдельные unit media/private-media. Первый shell-redirection прогон показал unittest OK, но PowerShell exit1; из-за этого выполнен один повтор с native subprocess exit capture. Synthetic storage-error trace в suite ожидаем сценарием, не потеря production media. Full suite NOT RUN.

Точные команды launcher/browser/test; только собственные ресурсы:

```powershell
wsl -d Ubuntu-24.04 -- docker run -d --pull=never --name kidsmap-module01-20261009-r1 --label kidsmap.qa.owner=module01-20261009-r1 -p 127.0.0.1:55431:5432 -e POSTGRES_USER=module01 -e POSTGRES_DB=module01 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r1/run.py seed
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r1/run.py fixture-org
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r1/run.py fixture-images
# Фактический server subprocess: run.py serve; запускался скрыто с redirected logs в ignored scratch.
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r1/run.py serve
npx.cmd --yes --package @playwright/cli playwright-cli -s=module01-r1 open http://localhost:8811/ru/ --config=docs/qa/module01-2026-10-09-r1/browser.config.json
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r1/drive.py lifecycle.js
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r1/test_driver.py
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r1/package.py
git diff --check
```

Не запускать setup повторно поверх текущих fixture DB/ports. [test_driver.py](test_driver.py) содержит полный argv пяти test labels; [command-ledger.jsonl](command-ledger.jsonl) содержит native CLI exit codes/durations последних браузерных запусков. Более ранние вызовы воспроизводимы как `drive.py <script.js>` по сохранённым scripts/results; ledger для них не был включён и точные timestamps не реконструируются. [drive.py](drive.py) передаёт JS через node subprocess argv, подставляет ignored credential только в памяти и сохраняет result без echoed executed code. `.effective.js` содержит actual QA scenario с placeholder пароля. Ранний npx multiline quoting и console encoding failures — environment/harness; не приложение.

QA-only wrapper `source_version` при server startup логирует лишь ID/match booleans/mismatch field names, затем вызывает оригинал. [source-diagnostics.jsonl](source-diagnostics.jsonl) не содержит токенов. Business behavior source не менялось; влияние observer ограничено диагностической записью.

## 8. Подтверждённые дефекты и самостоятельные repair prompts

| Finding | Приоритет | Результат |
|---|---|---|
| [PLACE-QA-01](findings/PLACE-QA-01.md) | P2 | причина отказа не видна владельцу |
| [PLACE-QA-02](findings/PLACE-QA-02.md) | P2 | owner clear/locate без SDK бездействуют |
| [PLACE-QA-03](findings/PLACE-QA-03.md) | P1 | dependent price projections блокируют approve собственного mixed edit |
| [PLACE-QA-04](findings/PLACE-QA-04.md) | P2 | district disabled после clear и ручного выбора Баку |
| [PLACE-QA-05](findings/PLACE-QA-05.md) | P2 | admin category popup overflow360 на трёх языках |

Каждый файл содержит steps/expected/actual/source hypothesis/evidence/scope/dependencies и готовый копируемый промпт. Все пять воспроизведены на исходном чистом HEAD: **baseline failures этого snapshot**, не вновь внесённые регрессии. Исторические отчёты не используются для утверждения, когда именно дефект появился. Подтверждённых новых регрессий от этого audit-only запуска нет, application hashes неизменны.

## 9. Ограничения и продолжение

NOT RUN: production, external Google/Leaflet services, OAuth/IndexNow/analytics/SMTP, physical GPS/devices, real screenreader, full backend suites, все mutations на каждой language/width, полный admin/owner keyboard control-by-control audit, специфическая zero0/0 валидация отдельно от geographic requirements. SIMULATED только browser geolocation APIs/permissions/coordinates. SDK absence реально наблюдалась, но намеренно обеспечена локальной изоляцией. Модуль02 организация/affiliations и модули03–13 вне scope.

Открытый P1 запрещает считать модуль production-ready. Следующий незавершённый модуль журнала — **02**. Модуль13 после01–12. Для исправлений пользователь должен выбрать соответствующий repair scope; этот запуск их не выполняет.

Локальный QA stand8811 и собственный PG контейнер оставлены для просмотра synthetic результатов; credentials/media только ignored scratch. Следующий модуль должен создать собственную isolated DB/cache/media и свободный port, не сбрасывать этот стенд и существующий portable. Существующий active_run NONE не переименован в QA marker. [Текст следующего чата](next-chat.txt).
