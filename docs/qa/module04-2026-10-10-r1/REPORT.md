# Модуль 04 «Мероприятия» — свежая приёмка 2026-10-10 r1

**FAIL, audit завершён; 3 OPEN P2, ограничения остаются NOT RUN.** Исполнитель `/root`, один последовательный запуск по определениям `.agents/agents/kidsmap-orchestrator/agent.md`, `django-reviewer/agent.md`, `browser-qa/agent.md`; независимых специалистов не запускали. Scope: только модуль 04, AUDIT ONLY. Приложение, правила, миграции и существующие assertions не изменены. Production/credentials/commit/push/deploy NOT RUN.

## 1. Состояние области

Фактический checkout **C:\kidsmap**, branch **task33-progress**, HEAD **8d188b316f800fbedf0b1e376905dfd4924cb1b6**. `active_run: NONE` из `docs/task33/implementation-status.md:7` сохранён побайтно. Его старый `source_head` не подменял текущий SHA. На первичной проверке dirty были журнал и папки module01-r1/r2, module02-r1, module03-r1. [Snapshot перед запуском сервера](snapshot.json) уже включает собственную созданную папку module04; [итоговый WORKTREE](verification.json) также содержит новые чужие QA-планы, оставленные без изменений. Все требуемые документы доступны; [missing_required_docs: []](source-facts.json).

Новый стенд **http://localhost:8815**, Django 6.0.2 / Python 3.12.15, собственный PostgreSQL 17-alpine **127.0.0.1:55435**, DB `module04`, unit DB `test_module04`. 175 записей миграций. LocMem cache/email, отдельные media/private-media/unit-media, cookies и Playwright session `module04-r1`; [изоляция](isolation.json). PostgreSQL container `kidsmap-module04-20261010-r1`, отдельный anonymous volume, [Docker status/mount/ports](docker-runtime.txt). Все акторы, организаторы, площадки и фото вымышленные. Начальная фикстура **0 Events**; все 3 Event созданы UI. Сетевой guard сервера допускает только loopback; браузер блокировал весь non-local transport. Карта/SDK, внешние fonts, email delivery, сторонние integrations **SIMULATED unavailable**, не live integration PASS.

Сервер запущен без reloader из этого checkout, Python PID **43232**, launcher **23080**. `/qa/version/` вернул этот HEAD и digest `589c2d398f3d24d62af28b72e47bbfaeb1c68f8767a080fd83be3a5a5a96b684`. [Process proof](runtime-process.json), [runtime/hash/preservation](verification.json): **2776** source/assets/locale файлов + отдельно **8** root templates неизменны. Initial launcher digest не включал корневой `templates/`; их hashes отдельно сняты перед финальной матрицей состояний и перепроверены. Использованные compiled `.mo` — фактический WORKTREE, не перекомпилированная версия. Source proof — версия стенда, исходники и roundtrip вместе, не только HTTP 200.

Graph-first: C-kidsmap ready, 88227 nodes/178873 edges, generation 2026-10-09T21:09:07Z. Relevant paths metadata_changed; owner template partial, Python coverage unavailable. Не полагались на шумные backup/dynamic edges; соответствующие формы, routes, сервис и model проверены по source. [Ограничения graph](source-facts.json). Исторический content-entry audit использован только как checklist.

Чужие 3896 входных файлов, кроме целевой строки журнала, сохранили hashes. Во время работы появились чужие `place-qa*-plan` и `docs/superpowers/plans` — сохранены. На входе HTTP 8811/8812/8813/8814 работали; на финальном snapshot слушали 8811/8812, 8813/8814 уже не слушали. Причина не установлена, команд остановки этих процессов здесь не было; не перезапускали чужие стенды. Все прежние PG ports 55431–55434 остаются доступными в Docker inventory. [Фактическое состояние](runtime-process.json), [PG inventory](preserved-docker-ports.txt).

## 2. Сильные стороны и выполненные сценарии

Все PASS ниже ограничены свежим локальным stand и указанными наблюдениями. [Подробные результаты](scenario-results.json), [CSV по роли/сценарию/языку/ширине](scenario-matrix.csv), [матрица представлений](matrix.csv).

| Сценарий | Роль / язык / ширина | Результат и свежие доказательства |
|---|---|---|
| Создание, частичное заполнение, черновик с каждого из 3 шагов, reload фото/адреса/имени | organization owner, RU desktop | PASS, [lifecycle](lifecycle.result.txt); попытка logout-helper завершилась ошибкой собственного селектора, настоящий logout/login выполнен в [resume](resume.result.txt) |
| Выход из account menu, вход, продолжение, неполная отправка, addressable server errors, исправление, submit | owner, RU 1440 | PASS, [resume](resume.result.txt), [ошибка](screenshots/submission-error-ru-1440.png) |
| Отказ с причиной → owner исправление → повторная отправка → одобрение → сервер published → публичная карточка | admin + owner, RU desktop | PASS, [moderation](moderation.result.txt), [read-only сервер](server-media.json), [реальный public roundtrip](media.result.txt). Admin pending/rejected/published совпали с сервером |
| Организация / подтверждённый специалист, категория ART/TECH/SPRT, отсутствие организатора | owner/person/empty, RU | PASS, [boundaries](boundaries.result.txt). Foreign/zero organizer payloads отвергнуты [tampering](tampering.result.txt) |
| Разделение organizer и venue, чужая published площадка, hidden/foreign draft недоступны | owner, RU | PASS; Event 3 org=1 и venue=2 другого владельца. [Server](server-final.json), [UI/HTTP negatives](boundaries.result.txt), [tampering](tampering.result.txt) |
| Отзыв прав организатора и скрытие площадки при открытой форме | owner, RU 1440 | PASS для guard: HTTP403 / field error. [Rights](rights-submit.result.txt), [venue](venue-submit.result.txt). Изменение сторонней сущности **SIMULATED fixture-only**, сами Event действия UI; Event ORM writes=0 |
| Очно→онлайн→очно, сохранность ещё не сохранённого адреса; online очищает физическую локацию | owner/person, RU | PASS, [resume](resume.result.txt), [boundaries](boundaries.result.txt), [online approved server](server-final.json) |
| Asia/Baku, полночь 20→21 и перенос 22→23, equal/end-before/partial pair/expired, age reversed | owner/person, RU | PASS, [boundaries](boundaries.result.txt), [expired](final-paths.result.txt), [occurrence](occurrence.result.txt). UTC 19:30→20:30 соответствует Baku 23:30→00:30 |
| Возраст/цена/телефон/описание, fallback AZ vs реально сохранённые RU/EN | owner/admin/public | PASS по roundtrip. [До переводов](screenshots/public-AZ-fallback-ru-1440.png), [native translation/media save](media.result.txt), [DB языковых полей](server-final.json). Owner пишет AZ, admin отдельно сохранил RU/EN; язык UI не выдавали за перевод |
| Primary upload/replacement, invalid PNG, native multiple file picker, gallery order/delete, reload и public images | owner/admin/public, RU desktop | PASS кроме удаления primary. [Media](media.result.txt), [ошибка файла](screenshots/corrupt-photo-ru-1440.png), [gallery before save](screenshots/admin-gallery-before-save-ru-1440.png), [public after save](screenshots/public-translated-gallery-ru-1440.png) |
| Published edit | owner/admin | PASS текущего контракта: owner edit pending/published блокируется; admin меняет approved содержание сразу. У Event нет Place candidate/live revision workflow. Об этом source `owner_events_controller.edit_event`, `views.owner_event_edit`, `EventAdmin.save_model`, domain; не invent дополнительную модерацию |
| Две вкладки, stale rejection, сохранность второй формы, сервер не перезаписан | person, все 18 комбинаций | PASS, [126 проверок состояний](state-matrix.result.txt), [conflict EN mobile](screenshots/state-conflict-en-390.png) |
| Loading aria-busy, повторный Enter: один POST | person, все 18 комбинаций | PASS, [state matrix](state-matrix.result.txt). Симуляция задержки собственного POST 1400ms |
| Сетевой abort save → reload → явный restore вводa | owner, RU desktop | PASS, [final paths](final-paths.result.txt), [recovery](screenshots/network-recovery-ru-1440.png). Abort транспортный SIMULATED; серверный save не состоялся |
| Чужие ID GET/POST edit/manage/cancel/reschedule | outsider | PASS 403, [boundaries](boundaries.result.txt), [tampering](tampering.result.txt). Forged POST — свежий browser-request, отдельно от native UI lifecycle |
| Перенос, причина, invalid interval, cancel, новый public state, прежний URL, сохранность venue/photo/identity/history | owner/public | PASS, [occurrence](occurrence.result.txt), [сервер 2 history entries](server-final.json), 18 canceled cards. Cancelled card остаётся в афише с state без countdown согласно существующему контракту; [повторная проверка](last-public.result.txt) |
| Online опубликованное мероприятие специалиста | person + staff moderator + public, 18 комбинаций | PASS, [moderator approval](final-paths.result.txt), [online public](last-public.result.txt). Сохранённая физическая география пустая |
| Обещания о профилях/участниках/рассылке | owner/public | PASS проверенного copy: права связаны с verified person; online регистрация согласуется по контакту; manage явно говорит, что participant notifications/refunds через KidsMap не выполняются. Реальную рассылку/регистрацию не симулировали как выполненную интеграцию |

Rendered Chromium headless shell 1243 — реальный браузер через Playwright CLI, отдельные контексты. Native Chrome remote-debugging недоступен по локальной policy; **native Chrome/physical mobile не проверены**. Матрица RU/AZ/EN × **360/390/768/1024/1280/1440**, 3 пустых owner steps + 3 заполненных specialist steps + admin published + public published: **144/144 geometry/document-language PASS**, unexpected pageerror/local HTTP≥400 = **0** в этом capture. Это не PASS всей локализации: [copy_status в CSV](matrix.csv) отдельно FAIL для AZ/EN owner и RU admin.

Дополнительно 126 наблюдений conflict/error/loading/double-Enter/open-select/keyboard-format/translated-public, 18 отменённых и 18 online public карточек. Tab→Shift+Tab вернули category; Enter навигации, Space radio и Escape select проверены. Focus sample имел видимую 3px green shadow; native radio выбран и имеет label. Long texts не дали root overflow в проверенных capture. [Visual review](visual-review.result.txt), [PC поля](screenshots/admin-fields-ru-1440.png), [mobile public viewport](screenshots/viewport-public-ru-390.png). Публичная галерея статическая, открываемой image-modal там нет. Доказательства — **328 PNG** с hashes в [manifest](screenshots-manifest.json).

## 3. Реальные проблемы

| ID | P | Подтверждённый факт | Отдельный finding и готовый repair prompt |
|---|---|---|---|
| EVENT-QA-01 | P2 | RU EventAdmin owner/venue подписаны как дата/главное фото; compiled `.mo` расходится с исправленным `.po` | [Finding + prompt](findings/EVENT-QA-01.md) |
| EVENT-QA-02 | P2 | Кнопка удаления primary не отмечает настоящий checkbox; фото остаётся после save/reload | [Finding + prompt](findings/EVENT-QA-02.md) |
| EVENT-QA-03 | P2 | Recovery/readiness инструкции и кнопки остаются RU в AZ/EN; часть .po уже переведена, часть новых msgid отсутствует, compiled каталоги отстают | [Finding + prompt](findings/EVENT-QA-03.md) |

Это **свежие current baseline failures**, а не объявленные новые regressions: рабочая сравнимая версия не предъявлена. Production impact не проверен. Удаление фото опубликованного события не было отправлено кнопкой; обход публикационного gate **не доказан**.

## 4. Tech debt

Shared media JS угадывает checkbox id и влияет на несколько редакторов; здесь подтверждён Event. Поставка `.po/.mo` не отражает фактический source content. UI presence/readiness и серверный gate проверены отдельно; штатный raw count заполненности не эквивалентен семантической валидности. Graph index не даёт достаточное покрытие динамических ORM/routes; source остаётся необходимым.

## 5. Risks

Смешанный язык важен в conflict/recovery, хотя защита версии работает. Live integrations и authentic внешние fonts заблокированы: типографика с загрузившимися внешними шрифтами остаётся NOT RUN, geometry вывод ограничен fallback rendering. QA root templates добавлены в отдельный hash manifest позднее initial launcher snapshot; факт и граница явно приведены выше. Появление чужих планов и исчезновение двух старых HTTP listeners учтены без вмешательства.

## 6. Dead/legacy candidates

Удалять ничего не предлагается. Legacy organizer resolution/compatibility поля прочитаны как contract; production/data аудит их использования NOT RUN. Шумный graph edge не основание объявлять код или таблицу dead.

## 7. Tests gaps, ошибки окружения и NOT RUN

Native Django: **129**, **118 PASS**, **2 baseline assertion FAIL** (`test_global_russian_labels`, `test_shared_translation_consumers`, EVENT-QA-01), **9 environment preflight FAIL → сценарии NOT RUN**. Последние требуют `TASK33_QA_ROOT.startswith('/tmp/kidsmap-task33-qa04-')` в `require_disposable_postgres`; Windows root этому не соответствует. Path не подменяли фиктивным Linux значением, assertions не меняли. Native exit **1**; [log](django-tests.log), [exit](django-tests.exit.txt), [точная команда](COMMANDS.md). Не считать 9 preflight ошибками приложения или доказанными DB/migration проверками. Часть кириллицы в native PowerShell log испорчена console encoding; browser/JSON подписи сохранены UTF-8 и независимо подтверждены.

Дополнительные NOT RUN: production snapshot/deploy compatibility; настоящие Google map SDK/geolocation/geocoding и permission-denial с рабочим SDK; calendar popup с внешним flatpickr (transport blocked); полный screen-reader/контраст-аудит; physical touch/mobile и другие browser engines; публикационный gate при действительно отправленном удалении primary; административные error/loading/conflict/open-related-object modals на всей матрице (owner states выполнены); persistence каждого translation toggle в каждом locale/width (основной roundtrip RU admin плюс public 18 cells выполнен); venue change после approval и изменение уже начавшегося occurrence native UI (fresh Django guard tests выполнены); отдельная user-deactivation вместо organizer reassignment; регистрация участников, настоящая доставка email/уведомлений, integrations; polled background jobs; всю gallery keyboard reorder/replace/error матрицу (drag/order/delete/reload выполнены); полное завершение conflict merge после выбора всех различий; визуальная проверка каждого пикселя каждого PNG. Root geometry/focus samples не заменяют эти проверки.

Search: native catalog query Enter выполнен в [last-public](last-public.result.txt), фактические результаты сохранены. Полнота Event discoverability и все search/calendar filters относятся к более широкому модулю 06/13 и здесь **NOT RUN**, не объявлены PASS по одному render.

Собственные harness ошибки сохранены в `*.attemptN.txt`: неверный logout selector, SCI вместо TECH, hidden language/menu selectors, gallery chooser, public-link strict selector. Независимые проверки продолжены и соответствующие важные пути завершены новыми scripts. Неверное ожидание удаления cancelled card из афиши исправлено сверкой текущего source/test и повторным browser capture; findings из этого не делали. [Агрегат](evidence-summary.json): 367 PASS наблюдений, 3 FAIL наблюдения (два — одно label finding), 2 отброшенных ожидания NOT RUN; это не число уникальных полностью принятых сценариев. Copy FAIL EVENT-QA-03 отдельно указан в matrix и finding.

## 8. Recommendations и передача

Исправления в этом запуске не выполнялись. Сначала согласовать конкретный scope/план соответствующего repair prompt; скоординировать общий locale процесс EVENT-QA-01/03; исправить media lookup EVENT-QA-02, повторить native roundtrip. Не менять правила/публикационные gates ради green. Новая приёмка после исправлений требует новых доказательств, эти результаты её не заменяют.

[Команды/exit codes](COMMANDS.md), [snapshot](snapshot.json), [серверный итог](server-final.json), [изоляция](isolation.json), [hashes/секреты/сохранность/журнал](verification.json), [evidence summary](evidence-summary.json), [328 screenshots](screenshots-manifest.json). Журнал обновлён **только строкой 04**, модуль 05 остаётся NOT RUN. [Текст следующего чата](next-chat.txt). Модуль 13 после остальных. Другие QA modules в этом запуске не выполнялись.

## 9. P0/P1/P2/P3

P0 **0**, P1 **0**, P2 **3 OPEN**, P3 **0** подтверждённых findings. Решение: **DONE — FAIL (audit complete; limits NOT RUN)**. Функциональные PASS относятся к перечисленным свежим действиям; полную готовность продукта или production этот отчёт не подтверждает.
