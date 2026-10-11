# Модуль 01: постоянные места — свежая приёмка r2

**FAIL в выполненном scope.** Аудит завершён; 6 подтверждённых проблем приложения и 1 отдельная проблема compiled assets. Недоступные части остаются NOT RUN. Дата запуска: 2026-10-09, завершение оформления: 2026-10-10, Asia/Baku. Роль: lead `/root`, направления Django/integration/browser выполнены последовательно одним исполнителем, без заявления независимой проверки. Definition: `.agents/agents/kidsmap-orchestrator/agent.md`. Режим AUDIT ONLY; production не подключался.

## 1. Состояние области и snapshot

Checkout `C:\kidsmap`; branch `task33-progress`; HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`; active_run `NONE`, файл сохранён. На входе уже были изменённый журнал и untracked module01-r1/module02-r1; это чужая работа. Новый run `module01-20261009-r2`. Свежие материалы: [snapshot](snapshot.json), [изоляция](isolation.json), [финальная проверка](verification.json), [matrix CSV](matrix.csv), [matrix JSON](matrix.json), [commands/exit codes](command-ledger.jsonl), [inventory с hash raw attempts](results-inventory.json).

Стенд `http://localhost:8813`, собственный PID 40932; PostgreSQL17-alpine контейнер `kidsmap-module01-20261009-r2`, порт55433, fresh DB, 175 применённых миграций. Python3.12.15, Django6.0.2, Chromium Playwright1243. Прежние серверы8811/PID6112 и8812/PID40848, PG55431/55432 сохранены. Это Windows checkout с Linux PostgreSQL через WSL, а не перенесённая сессия исходного ПК. Стенд r2 оставлен для просмотра.

`/qa/version/` отдаёт текущие HEAD, testing=true и manifest digest `589c2d398f3d24d62af28b72e47bbfaeb1c68f8767a080fd83be3a5a5a96b684`. 2776 файлов src/static/config/locale сверены до/после; изменений нет. Запущены исходники этого WORKTREE с QA-only settings/URL configuration, без monkeypatch бизнес-функций. В manifest включены существующие ignored locale .mo: стенд соответствует AS-IS WORKTREE, включая stale assets, а не чистой пересборке HEAD. Именно поэтому finding06 отнесён к environment.

Прочитаны AGENTS.md, canonical README/registry/orchestrator, architecture/source-of-truth/current-snapshot, audit/engineering/orchestration/testing contracts, `content-entry-audit-2026-10-06.md`, `admin-place-map-fix-2026-10-09.md` и промпт01. Обязательные документы доступны; отсутствующие обязательные документы не обнаружены. План: [PLAN](PLAN.md). Codebase-memory C-kidsmap: ready, 77124 nodes/163927 edges, 74 partial parses; индекс generation 2026-10-09T19:09:23Z. Частичная/недоступная coverage критических файлов не принималась за полноту: переходы и dynamic ORM связи сверены с source. Graph cache в evidence не скопирован.

Изоляция: DJANGO_TESTING=1, отдельные DB/LocMem cache/mail/media/private-media/cookies. `.env` не загружался; внешние ключи пусты; socket guard и browser route блокируют внешний transport. Credentials вымышленных пользователей остаются в ignored scratch и не записаны в deliverables. ORM использован для начальных fixture identities/organization и read-only диагностики; проверяемые переходы создания/черновика/модерации/публикации/изменения выполнены UI, не ORM save.

### Выполненные сценарии

| Scope | Результат | Свежий evidence |
|---|---|---|
| Самостоятельное место: partial → draft → reload → login → error → correction → submit → rejection → resubmit → approve → public | Переходы PASS; причина отказа FAIL | lifecycle, moderation, rejection-recheck `.result.txt` |
| Филиал вымышленной организации, смена category/subcategory, повторный вход через UI | PASS; причина отказа FAIL | branch-fill-stable, branch-lifecycle-stable, final-branch-roundtrip |
| Названия/описания AZ/RU/EN, blank EN и public fallback | PASS content/fallback; UI labels FAIL отдельно | lifecycle, public-smoke, localization, edge-cases |
| Возраст/контакты/адрес, region/district, manual coords | Валидация и roundtrip PASS; district/owner no-SDK FAIL | coordinates, owner-coordinate-roundtrip.effective, manual-roundtrip.effective, map-recheck, district-enable.effective |
| Admin map recheck: no point, invalid range/half pair/0/0, clear; denied/unavailable geolocation | PASS выполненные; физический SDK/GPS NOT RUN | admin-create, edge-cases, geolocation |
| Free/paid/event pricing, 8 owner и 12 admin переключений | PASS без зависания; mixed published candidate FAIL | branch-fill-stable, admin-create, published, review-inspect |
| Place hours 09:00 отдельно от lesson14:00 | PASS public в трёх языках | branch-lifecycle-stable |
| Main/gallery/upload/reorder/remove/replace/promote → reload → public | PASS финальный roundtrip; invalid/corrupt/empty/oversize file ошибки PASS | media-awaited первые4, file-errors, final-branch-roundtrip, public-smoke |
| Foreign ID/rights/double save/two tabs/offline/input retention | PASS выполненные, реальный409 и сохранённый ввод | negative, state-matrix |
| Опубликованное: candidate identity отдельно от live; price/schedule immediate | PASS разделение; FAIL способность approve mixed price candidate | published, candidate-diagnostic, review-inspect |

Точные IDs/role/language/width/status находятся в matrix. У функциональных сценариев с несколькими viewport указан mixed и соответствующий script; мутационный lifecycle преимущественно RU. Нельзя трактовать display matrix как повторение полного lifecycle на каждом языке и ширине.

Контракт по source `src/catalog/services/publication.py:305` / `propose`: при explicit_save расписание (`schedule`, `schedule_mode`, structured schedule и notes) может применяться сразу; суммы legacy price fields и amount-only pricing_plans — сразу, если условия не менялись и в pending нет pricing/condition blockers. Остальные name/description, адрес/география, категория, фото/галерея и изменённые условия остаются candidate до review. Это условный контракт, а не обещание immediate для любой цены. Browser подтвердил live name/address неизменными до одобрения, schedule/amount immediate и photos после approval. Candidate payload/base/live сверены read-only диагностикой.

Реальный browser display/state matrix: RU/AZ/EN × 360/390/768/1024/1280/1440. 342 проверки состояний/geometry: 339 PASS, 3 FAIL (category popup360 в каждом языке). Включены empty/filled, map/gallery/open controls, long errors, loading/offline/conflict и modal keyboard. Дополнительно functional/localization rows дают итог454: **431 PASS / 17 FAIL / 6 NOT RUN**. Это строки наблюдений, а не454 независимых транзакции или17 разных дефектов.

381 свежий PNG, [manifest с SHA256](screenshots-manifest.json), 16 contact sheets; [визуальный просмотр и границы](visual-review.md). Ключевые: [PC review blocker](screenshots/review-published-error-1440.png), [mobile rejection](screenshots/owner-rejection-390.png), [mobile public](screenshots/public-final-2-en-360.png), [mobile modal](screenshots/modal-admin-ru-360.png), [offline/focus](screenshots/state-owner-offline-az-1024.png). Screenshot capture сделан настоящим Chromium после UI действий; source inspection/jsdom/HTTP200 не использовались как его замена.

## 2. Сильные стороны

Сохранение частичного черновика, reload и повторный вход удерживают данные. Age/coordinate/file validation не уничтожает ввод и saved photo. Unauthorized ID не раскрывает чужой draft, two-tab конфликт защищает более новые данные, offline состояние сообщает о несохранении. Филиал проходит отказ/повторную отправку/одобрение. Public RU/EN явные переводы соответствуют сохранённым полям, blank EN остаётся blank в storage и показывается fallback с соответствующей подсказкой. Финальные фото сверены с editor по decoded pixels и reload. Место и занятия имеют отдельные часы.

## 3. Реальные проблемы

Все findings OPEN, исправлений нет; у каждого собственные repro, факт/ожидание, evidence, причина/уверенность, severity rationale, scope/dependencies и копируемый repair prompt: [полный список](findings/README.md).

| ID | Severity | Классификация | Проблема |
|---|---|---|---|
| [PLACE-QA-01](findings/PLACE-QA-01.md) | P2 | pre-existing baseline | Owner не видит сохранённую причину отказа |
| [PLACE-QA-02](findings/PLACE-QA-02.md) | P2 | pre-existing baseline | Clear/locate молчат без SDK |
| [PLACE-QA-03](findings/PLACE-QA-03.md) | P1 | pre-existing baseline | Mixed identity+pricing edit создаёт stale candidate base и блокирует approve |
| [PLACE-QA-04](findings/PLACE-QA-04.md) | P2 | pre-existing baseline | Район disabled после перехода point→manual region |
| [PLACE-QA-05](findings/PLACE-QA-05.md) | P2 | pre-existing baseline | Admin category popup overflow360 |
| [PLACE-QA-06](findings/PLACE-QA-06.md) | P2 | environment/generated assets | Stale ignored .mo искажают description/map labels |
| [PLACE-QA-07](findings/PLACE-QA-07.md) | P3 | baseline source translation gap | Nature choices русские в AZ/EN |

Предыдущие reports не использовались как evidence. App исходники в этом запуске не менялись, поэтому новые regression от его app изменений отсутствуют; слово baseline означает воспроизведено на текущем snapshot, а не историю появления или production статус.

## 4. Tech debt

Candidate base зависит от производных legacy price projections; coupling подтвержден03. Map provider initialization связывает доступность базовых form actions с SDK02. Generated gettext assets могут отставать от source06. Это конкретные области для отдельного плана, не разрешение на рефакторинг всего редактора.

## 5. Risks и simulated integrations

Главный риск выполненного пути — невозможность одобрить mixed published edit без отклонения/повторного исправления. Реальные Google Maps, external network/API, физический GPS не запускались. Denied/unsupported geolocation и coordinates заданы browser simulation; loading создан задержкой native autosave response, offline через Chromium offline. Реальный server409 проверен. Эти сценарии явно SIMULATED integrations, не доказательство работы провайдера.

Console/network собраны в raw results. Uncaught pageerrors в display/state matrices не обнаружены; network не объявляется полностью чистым: ожидаемые422/409, invalid upload responses, blocked external requests и temporary thumbnail404 при раннем draft отдельно видны в raw evidence. Общий native CLI exit0 не означает PASS каждой row.

## 6. Dead/legacy candidates

Удаление не предлагается. Legacy price fields участвуют в действующем publication contract, статус ACTIVE/CANNOT DELETE по этому scope. Наличие старых reports и duplicated QA helper scripts не доказывает dead application code. Database/data deletion audit NOT RUN.

## 7. Tests gaps, точные команды и exit codes

Выполнено заново: 84 существующих Django tests, OK, native exit0, 53.978s: [log](backend-repeat.txt), [result](backend-result.json).

```powershell
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/test_driver.py
# Native command inside driver:
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/run.py test catalog.testcases.place_readiness catalog.testcases.test_admin_candidate_cover catalog.testcases.test_task33_place_continuous catalog.testcases.photo_workflow catalog.testcases.test_place_json_and_pricing_modes
$env:KIDSMAP_JSDOM='C:\kidsmap\.tmp\phone-dom\node_modules\jsdom'
node --test scripts/test_location_resolution.cjs
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/drive.py lifecycle.js
# Each actual browser scenario command, duration and CLI exit: command-ledger.jsonl
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/package.py
git diff --check
```

Native node result7/7 PASS exit0: [log](location-js-tests.txt), [result](location-js-result.json). First JS attempt lacked historical jsdom directory: environment failure, rerun used existing supported KIDSMAP_JSDOM override. A Windows CP1251 wrapper print error occurred after native output/result were saved; native test result remains exit0. Expected mocked storage failure traces in tests are not app failure. Existing assertions не изменялись.

Fresh stand commands:

```powershell
wsl -- docker run -d --name kidsmap-module01-20261009-r2 --label kidsmap.qa.owner=module01-20261009-r2 -e POSTGRES_DB=module01 -e POSTGRES_USER=module01 -e POSTGRES_HOST_AUTH_METHOD=trust -p 127.0.0.1:55433:5432 postgres:17-alpine
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/run.py snapshot
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/run.py migrate
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/run.py seed
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/run.py serve
```

Serve — длительно работающий процесс; отсутствие terminal exit не выдаётся за успешно завершённый command. Runtime endpoint и source hash verification подтверждают старт. Fixture password не включён в команды отчёта. Для browser bootstrap и технических операций см. PLAN/scripts и ledger; copied helper source не означает выполненный сценарий.

Harness setbacks не выданы за app findings: старый selector published-save, race saved-state waits, lazy image decode до scrollIntoView, неверное ожидание orange fixture вместо blue, сравнение '0' vs '0.000000', ошибочное ожидаемое AZ название. Первичные attempts сохранены, итоговая выборка в package.py исключает superseded rows. 0/0 draft retention/admin refusal проверены, но isolated owner0/0 publication после harness stop остаётся NOT RUN.

NOT RUN: full backend/JS suites; полный mutation lifecycle во всех18 language/width cells; настоящий SDK/GPS/external integration; exhaustive keyboard всех контролов, screenreader, Firefox/Safari и физические устройства; owner0/0 isolated submit; production. Enter/Tab/Shift+Tab/Escape modal и часть form controls проверены; Space для всех widgets и полная accessible focus traversal не подтверждены. Продолжение независимых проверок выполнено несмотря на harness/environment stops.

## 8. Recommendations и handoff

Сначала отдельно согласовать scope03 (publication), затем01/02/04/05. Для06 — воспроизводимый isolated compiled catalog build; source gap07 проверить отдельно после rebuild. Промпты исправления самостоятельны, но не авторизуют реализацию. Аудит не делает commit/push/deploy и не меняет приложение/правила/миграции/assertions.

Из journal следует, что02 уже DONE; повтор module01 выполнен по последнему явному заданию пользователя. Следующий незавершённый модуль03;13 после остальных. [Текст следующего чата](next-chat.txt). Обновлена только строка01; чужая строка02 и остальной текст сохранены побайтно. Финальная проверка2776 source files и888 ранее существовавших files, active_run и secret scan — в verification.json.

## 9. P0/P1/P2/P3

P0:0. P1:1 (03). P2:5 (01/02/04/05 application +06 environment). P3:1 (07). Итого6 app findings +1 environment finding. Вывод FAIL ограничен выполненными local сценариями; «всё работает» и production readiness не заявляются.
