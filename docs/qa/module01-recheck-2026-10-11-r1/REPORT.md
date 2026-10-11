# Модуль 01: повторная проверка существующих исправлений

2026-10-11. AUDIT ONLY. Исполнитель `/root`, последовательная проверка в роли kidsmap-orchestrator по `.agents/agents/kidsmap-orchestrator/agent.md`; независимые специалисты не запускались. Scope: установить, исправлены ли прежние PLACE-QA-01–07. Исторические отчёты использованы только как чек-лист. Все результаты ниже получены заново.

**Прежние семь исправлений присутствуют в dirty WORKTREE и проходят целевую повторную проверку на новом стенде со свежими переводами. Полностью закрывать модуль пока нельзя:** остаётся RU placeholder района, ранее CROSS-QA-03, здесь PLACE-QA-08 как alias той же причины. Полная приёмка всего модуля по исходному промпту сейчас NOT RUN.

## 1. Состояние области и snapshot

Checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`. На входе 18 изменённых tracked-файлов, многочисленные чужие untracked отчёты/планы/тесты. `active_run: NONE`. Исправления приложения уже находились в WORKTREE до этого запуска; наличие в HEAD или production не утверждается.

[Snapshot](snapshot.json), [запущенная версия](runtime-version.json), [изоляция](isolation.json). 2788 исходных файлов, digest `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`: entry = startup = current disk. Python 3.12.15, Django 6.0.2, `DJANGO_TESTING=1`, DEBUG=False. Новый HTTP `http://localhost:8841`, PID 16156; PostgreSQL17 `place_recheck`, loopback 55446, отдельный контейнер `kidsmap-module01-recheck-20261011-r1` ID `a41ee5c301ba2bebea8b4472fb098880d6d16aa8981736cb4473b169d382cca9`, volume `70efcee82c7230c684ba0346e64a7f3374cc1cdc15ccde51148f12f0eaf590a5`. LocMem cache/email, отдельные media/private-media, вымышленные аккаунты и фото. Пароль только в ignored scratch, в отчётах отсутствует.

Собственные `.tmp/module01-recheck-20261011-r1/locales` собраны GNU msgfmt через существующий `scripts/build_isolated_locales.py`. Manifest проверен **до django.setup**; sole LOCALE_PATHS указывает в эту сборку. Общие `.mo` не переписывались. [Сравнение PO / новой MO / общей MO](compiled-locales-proof.json). Все три общих каталога отличаются от свежей сборки: обычный запуск, который продолжает использовать их, не получает этот результат автоматически. PLACE-QA-06 закрыт в проверенном изолированном профиле; актуальность любого другого runtime нужно проверять отдельно.

Все запрошенные документы доступны: AGENTS.md, канонический `.agents`, module-acceptance-prompts.md, content-entry-audit-2026-10-06.md и admin-place-map-fix-2026-10-09.md. Недостающих документов в этом списке нет. Codebase Memory использован первым; coverage для релевантных файлов unavailable/metadata_changed, continuous template partial. Поэтому source-выводы сверены непосредственно с файлами; граф не принят за доказательство полноты.

## 2. Сильные стороны и свежие результаты

| Дефект | Целевой результат | Свежая проверка | Source в WORKTREE |
|---|---|---|---|
| PLACE-QA-01 | PASS | Native отказ с причиной, escaping HTML, reload; RU/AZ/EN × все 6 ширин; исправление → повторная отправка → одобрение | permanent_place_wizard.py:78; owner_place_continuous.html:9 |
| PLACE-QA-02 | PASS, provider integrations SIMULATED/NOT RUN | Без SDK работают clear, сообщение отсутствия геолокации и отказа; текущие JS-тесты 12/12, включая guards/stale callbacks | owner_place_map_picker.js:97,517 |
| PLACE-QA-03 | PASS | 15→18 одновременно с названием и адресом; draft/reload; live identity сохраняется до review; native submit/approve и публичная цена 18; Django rebase tests | publication.py:355–370 |
| PLACE-QA-04 | PASS в выполненном сценарии | Без точки Sumgait отключает район, Baku включает; неполная пара отключает; clear → Baku → Yasamal → native save → reload; location JS 22/22 | location_resolution.js:54,140 |
| PLACE-QA-05 | PASS в выполненных сценариях | Длинная категория и поиск помещаются на RU/AZ/EN × 360/390/768/1024/1280/1440; Escape при пустом поиске возвращает focus; outside click сохраняет focus | kidsmap_place_form.css:1146,1232; kidsmap_place_form.js:1283,1338 |
| PLACE-QA-06 | PASS только fresh compiled profile | 18 клеток map notice + 54 проверки подписей description при **открытых** AZ/RU/EN tabs; 9/9 тестов helper | scripts/build_isolated_locales.py; собственные run.py/qa_settings.py |
| PLACE-QA-07 | PASS | Правильные Biznes/İctimai məkan, Business/Public space и RU подписи; оба стабильных enum через native save/reload на трёх языках | текущие locale/*/LC_MESSAGES/django.po |

Полный native путь этого запуска: новое самостоятельное место → частичное заполнение → server draft → reload → выход/вход → продолжение → materialized draft → ошибка возраста и сохранность ввода → исправление → отправка → отказ с причиной → повторная отправка → одобрение → публичная карточка → изменение опубликованного → draft/reload → review → одобрение. Эти переходы не выполнялись ORM-сохранением. ORM применялся только для начальных вымышленных аккаунтов/таксономии/отдельного connection target; дальнейший DB readback — READ ONLY.

После изменения цены live price_from/price_to и relational plan равны 18.00. Публичные название/адрес сверены до и после review. Смена nature сохраняется в candidate: после native reload public_space виден редактору, live nature остаётся business. Пустой name_en остаётся пустым в БД; публичный EN показывает AZ fallback с предупреждением и `lang` исходного текста, а не сохранённый английский перевод. Public presentation использует `public_presentation.translated`, AZ fallback; старый общий getter Place не является oracle этого SSR.

Итоги: **38/38 Django, 34/34 Node, 9/9 locale helper — exit 0**. Браузер: **252 PASS / 6 FAIL / 12 NOT RUN**; 6 FAIL относятся к одной оставшейся причине RU placeholder, не к шести отдельным дефектам. Это наблюдения/границы scope, а не количество независимых end-to-end тестов. [Counts](counts.json), [матрица по роли/языку/ширине](matrix.csv), [точные наблюдения](browser-observations.json), [команды](COMMANDS.md).

Сохранены **164 свежих native PNG**, [manifest с SHA](screenshots-manifest.json), дополнительно три производных contact sheets. Визуально просмотрены все 18 viewport captures: [admin](contact-admin.jpg), [owner map error](contact-owner.jpg), [public](contact-guest.jpg), отдельно mobile error/rejection и остаточная проблема. Автоматическая геометрия/видимые labels проверены на 18 клетках; просмотр всех 164 полноразмерных PNG вручную не заявляется.

## 3. Реальная оставшаяся проблема

**PLACE-QA-08 / ранее CROSS-QA-03, P3:** в RU owner editor пустая option района — «Rayon seçin». Свежая сборка переводов это не устраняет: в RU PO ключ «Выберите район» только obsolete, в новой RU MO отсутствует, а AZ MO содержит этот перевод. [Отдельный finding](PLACE-QA-08.md), [самостоятельный repair prompt](PLACE-QA-08-repair.txt), [fresh evidence](residual.result.txt).

На шести ширинах прочитана настоящая option; для видимого screenshot сделан native выбор пустой option с блокировкой всех non-GET после логина. Это **SIMULATED unsaved state**, server/candidate/live не менялись. Исправление не выполнено. Это повторное подтверждение известной причины, а не доказанная новая regression.

## 4. Tech debt и классификация ошибок запуска

Обычные runtime могут брать старые shared MO; helper сам не переключает чужие launchers. Изолированная свежая сборка доказывает выполненный профиль, а не готовность deployed assets. Старый helper Place.name_i18n и текущий SSR presentation имеют разные fallback; проверять нужно фактического потребителя.

Сохранённые `*.attempt1.txt` не выдаются за дефекты приложения: первый admin oracle искал скрытый RU tab; первый public oracle учитывал скрытый offscreen drawer и ожидал fallback общего getter; затем исправлены **собственные QA oracle**, повторён browser. Map QA первоначально пытался выбрать район после неполной пары без повторного Baku: source намеренно очистил географию. Этот сценарий оставил invalid draft, поэтому первый nature save вернул 422; затем ввод исправлен через UI и native save/reload прошёл. Assertions приложения и существующие тесты не менялись.

Первый Node запуск без KIDSMAP_JSDOM — 2 environment exit 1; повтор с существующей read-only зависимостью прошёл. Подготовка собственной длинной категории прервалась; завершены только initial fixtures до audited creation. Несколько ошибок собственного readback (имя поля, Decimal/console encoding) устранены в QA-скрипте, не в приложении. Final readback exit 0. Ошибки процесса/QA oracle отделены от app finding.

## 5. Risks и SIMULATED integrations

В диагностических 18 browser profiles нет pageerror и local HTTP>=400. Есть 24 console `net::ERR_FAILED` от намеренной блокировки внешних assets; отдельная свежая [проверка URL](console-check.result.txt) подтвердила Google Fonts и unpkg Leaflet. Внешний transport не разрешался, шрифты могут использовать fallback; реальные Google SDK, геокодер и GPS NOT RUN. Geolocation denial/unavailable заданы через synthetic browser API и явно отмечены SIMULATED. Другие стенды, production, credentials и внешние отправки не использованы.

## 6. Dead/legacy candidates

Ничего не удалено и не объявлено мёртвым. Устаревшие shared MO требуют отдельного решения о сборке, а не удаления. Обsolete RU entry рассматривается только как конкретная причина перевода.

## 7. Tests gaps

Этот запуск — целевой recheck семи исправлений, не полная повторная приёмка всех требований модуля. В [матрице](matrix.csv) 12 scope rows NOT RUN: филиал/все категории; все переключения pricing и concurrency; полный coordinate corpus; реальные providers/GPS; полный gallery corpus; opening hours/lesson timetable combinations; все ACL endpoints; two tabs/double submit/network recovery matrix; полный keyboard/screen reader; все состояния × роли × 18 клеток; full configured suite/clean-HEAD comparison; production. Старые проверки этих областей не заменяют свежий прогон.

## 8. Recommendations

Не исправлять PLACE-QA-01–07 заново по старому r2: текущие изменения уже существуют и целевые сценарии прошли. Для закрытия module01 отдельно решить PLACE-QA-08/CROSS-QA-03, подтвердить используемую runtime сборку переводов, затем повторить недостающие сценарии полного module prompt. Существующие исправления не commit/push/deploy в этом запуске. [Текст следующего чата](next-chat.txt).

## 9. P0–P3 и сохранность

P0/P1/P2 в целевом recheck не подтверждены; один P3 alias известной причины. Regression относительно clean HEAD UNKNOWN; прежний baseline/source gap подтверждён свежим browser и compiled catalogue. Приложение, правила, миграции, assertions не изменялись. Только собственные QA артефакты и строка 01 журнала. [Final preservation/runtime checks](verification.json): **11/11 PASS, finalize exit0**; 18365 входных файлов проверены, кроме разрешённой строки01, остальные байты журнала и 2788 исходных файлов сохранены. active_run и прежние localhost listeners/containers сохранены. Canonical MASTER_AUDIT не переписывался. Первый собственный finalizer остановился на Windows default text encoding при чтении UTF-8 browser JSON; QA parser исправлен, повторная проверка инвариантов прошла.
