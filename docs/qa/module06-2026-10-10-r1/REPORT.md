# Модуль 06 — публичный каталог, поиск, фильтры и карта

**DONE — FAIL; свежая локальная приёмка завершена с явными NOT RUN.** Дата: 2026-10-10, Asia/Baku. Четыре OPEN PUBLIC-QA: три ошибки интерфейса P2 и одна локальная проблема compiled locale P3. Приложение, правила, миграции и существующие assertions не исправлялись. Commit/push/deploy и обращения к production не выполнялись.

Execution identity: `/root`, один исполнитель. Каноническое определение: [.agents/agents/kidsmap-orchestrator/agent.md](C:/kidsmap/.agents/agents/kidsmap-orchestrator/agent.md). Обязанности orchestrator, frontend-reviewer, browser-qa и backend verification выполнялись последовательно; независимых исполнителей нет. Применены writing-plans, kidsmap-ui-design, frontend-design, fixing-accessibility, playwright, systematic-debugging и verification-before-completion в пределах AUDIT ONLY.

## 1. Состояние области

| Snapshot | Фактическое значение |
|---|---|
| Checkout | `C:\kidsmap` |
| LOCAL HEAD | `8d188b316f800fbedf0b1e376905dfd4924cb1b6` |
| Branch | `task33-progress` |
| WORKTREE при входе | Dirty: журнал, чужие QA каталоги 01–05 и place-qa планы; полный список в snapshot.json. Собственный каталог06 уже создан к моменту snapshot. Application files без dirty diff. |
| active_run | `NONE`, файл docs/task33/implementation-status.md не изменён |
| Источники стенда | WORKTREE, включая существующие ignored `.mo`; 2784 SHA-256, digest `933b55c01caf9ab69bce9d81d23b69e87c262ffcf5d192917e8d9272b0f7ee83` |
| Runtime | Python3.12.15, Django6.0.2; native headless Chromium153.0.8010.12 |
| Production | UNKNOWN / NOT RUN; подключения не было |
| Требуемые документы | Девять входных документов доступны; missing `[]` в documents.json |

[Snapshot](snapshot.json), [документы](documents.json), [изоляция](isolation.json), [финальная сверка](verification.json), [команда сверки](verification-command.json). Исторические отчёты использованы только как checklist. Канонический [промпт06](C:/kidsmap/docs/qa/module-acceptance-prompts.md:210) определяет scope; модули01–05 уже DONE, поэтому этот запуск выполняет только06.

Codebase-memory-mcp использован первым для архитектурных подсказок проекта C-kidsmap: index ready, 105710 nodes, 201512 edges; 74 partial parses и 56 unindexed directories. Generation timestamp не получен: точная freshness UNKNOWN, coverage best effort. Релевантные динамические Django/ORM связи сверены с исходниками; graph cache не сохранён. Карта ответственности: catalog views → [filtering](C:/kidsmap/src/catalog/services/filtering.py) → [catalog_search](C:/kidsmap/src/catalog/services/catalog_search.py:35) → public presentation/map payload; [map_identity](C:/kidsmap/src/catalog/services/map_payload.py:21) отделяет confirmed venue от независимого place; publication и revisions отделяют candidate от live. UI карта/панель находятся в catalog templates, catalog_map.js и CSS. Граф не используется как доказательство удаления.

Создан собственный новый PostgreSQL17-alpine `kidsmap-module06-20261010-r1`, localhost55437, DB `module06` и disposable `test_module06`. Применены175 существующих migrations только в этой DB. HTTP8817 — основной стенд; HTTP8818 — companion для configured Google failure branch. Оба слушают127.0.0.1, без autoreloader. Собственные `.tmp/module06-20261010-r1` media/private-media/test-media, LocMem cache/email, cookies и browser sessions. `DJANGO_TESTING=1`; launcher удаляет унаследованные credential variables, testing не загружает checkout .env, server socket guard блокирует внешние соединения. OAuth/analytics/IndexNow выключены. Companion использует заведомо недействительную QA строку map key; SDK запрос прерывается браузером. Реальные ключи не читались/не использовались.

Соответствие источников проверено сочетанием startup SHA guards обоих launcher, финального сравнения2784 файлов, PID/command line собственных listeners, import path и native UI. `/qa/version/` возвращает manifest, но одно это echo не доказывает версию загруженного приложения. Финальные listeners:8817 PID33848,8818 PID36896; контейнерные volumes, HTTP версии и exit codes находятся в verification.json. Стенды оставлены для просмотра, credentials лежат только в ignored scratch.

Контролируемые вымышленные fixtures:30 мест со всеми требуемыми статусами; approved organization и branch, published specialist и скрытые состояния; scheduled/cancelled/past и неопубликованные события; три опубликованных направления/группы Aurora с возрастами4–6/9–13/7–10 и ценами25/120/40, приватное занятие/цена999; разные районы, подтверждённая общая площадка, одинаковые координаты независимых мест, missing/0/0/partial точки, длинные тексты, пустые переводы и три локальных PNG. Исходный setup допустимо использует ORM. Испорченные точки внесены только как SIMULATED legacy fixtures до аудита; проверяемые publish/edit/cancel/section transitions выполнены настоящим UI. [Fixtures](fixtures.json), [исходное private state](http-negative.json), [финальный read-only state](state-final.json).

Сохранность: из5473 входных byte hashes финальная проверка сравнивает5472 вне журнала. Отмечен внешний drift двух чужих ledger файлов `docs/qa/place-qa06-plan-2026-10-10/{browser-command-ledger.jsonl,command-ledger.jsonl}`; происхождение UNKNOWN, отката/перезаписи не было. Чужой PostgreSQL `kidsmap-placeqa06-plan-20261010` был на входе, но отсутствует среди running containers в конце; действий с ним не выполнялось. Чужие HTTP8811/8812/8815/8816 соответствуют входным PID. Нельзя заявить побайтовую неизменность всего чужого состояния. Strict preservation verification имеет exit1 из-за drift; `own_scope_integrity_pass=true`:2784 исходника без изменений, runtime соответствует snapshot, secrets/links/syntax checks PASS. Из журнала изменена только строка06 (line26); чужой active_run сохранён.

### Выполненные сценарии

Итог: **1483 observation rows:1378 PASS,51 FAIL,54 NOT RUN**. Это строки сценарий×роль×язык×ширина, а не1483 независимых unit tests. [Matrix CSV](matrix.csv), [полные данные](matrix.json), [counts](results-summary.json). HTTP строки не имеют browser width. UNRECORDED в raw metadata не означает выполнение на всех размерах.

| Сценарий / роль | Язык / ширина | Итог и доказательство |
|---|---|---|
| Home; catalogue; organization/specialist/event lists и details; place fallback; activity; empty catalogue / anonymous | RU/AZ/EN ×360/390/768/1024/1280/1440 | 216 rendered states; render, root overflow и local images PASS. matrix.result.txt |
| Menu, native entity links, card navigation / anonymous | RU/AZ/EN ×390/1440; mobile Escape390 | PASS; navigation-proof, extras, tail |
| Partial names AZ/RU/EN, address, group name, empty results, unpublished suggestions / anonymous | RU/AZ/EN ×390/1440; suggestions и HTTP отдельно | PASS; functional, extras, http-negative |
| District, category/subcategory, age, no-review rating, permanent/temporary type; reset/sort/page/direct URL/Back/Forward/reload / anonymous | RU/AZ/EN ×390/1440 | PASS в окончательных observations; functional/tail/extras/type-proof. Legacy price params проверены по действующему contract normalization |
| Native category+age Apply, matched group price, reload / anonymous | Все18 сочетаний | 54/54 PASS; filter-settled. ART+age9 показывает120, а не25; ART+age5 не заимствует возраст другой группы |
| Sort open; Space/Tab/Shift+Tab/Escape; visible focus / anonymous | Все18 сочетаний | 36/36 PASS; public-native settled observations |
| Native category pointer в исходной панели / anonymous | Все18 сочетаний | RU/AZ360/390 и EN360 FAIL; остальные13 PASS. PUBLIC-QA-04, pointer-final |
| Shared venue, independent identical coordinates, invalid/no point; private map exclusion / anonymous | RU/AZ/EN ×390/1440, payload; rendered grouping все18 | PASS; functional/map-browser/extras. List count не обязан равняться числу физических pins: места без точки остаются в списке, confirmed venue объединяется |
| Popup geometry и native close / anonymous; SDK interface SIMULATED | Все18 сочетаний | Mobile360/390 PASS; desktop768/1024/1280/1440 FAIL24 observations. PUBLIC-QA-01; map-geometry |
| Marker Enter, Escape, focus return, coincident chooser, correct member URL / anonymous; adapter | RU/AZ/EN ×360/390 | PASS; map-browser. Последующие12 desktop combinations NOT RUN из-за inaccessible close |
| No configured map key / anonymous | Все18 сочетаний, HTTP8817 | Graceful unavailable state и Escape PASS; matrix |
| Configured Google script failure / anonymous; transport abort SIMULATED | Все18 сочетаний, HTTP8818 | Terminal error FAIL18, Escape/list PASS18; PUBLIC-QA-02. RU390 повторно через15s; sdk-failure/error-evidence |
| Gallery next/thumbnail/reload; native phone Space; held request+duplicate Enter; error/retry / anonymous | RU/AZ/EN ×390/1440 | PASS; tail. Held/aborted localhost POST явно SIMULATED transport, последующий fetch реальный локальный |
| Two tabs query isolation / anonymous | RU/AZ/EN ×390/1440 | PASS; tail. Concurrent write/moderation conflicts этим не покрываются |
| Private direct IDs: draft/pending/rejected/inactive/archived и private pricing / anonymous | RU/AZ/EN; HTTP | 60/60 PASS до публикации27; private payload/price999 исключены. http-negative |
| Section labels / admin | RU/AZ/EN ×390/1440 | RU2 PASS, AZ/EN4 FAIL; PUBLIC-QA-03. admin-functional |
| Disable sections → save → fresh public navigation/API/cache → restore / admin/public | Admin1440; RU/AZ/EN public390 | PASS; admin-functional. Org/spec404, events410 соответствуют contract |
| Pending27 → native publish → public reload; published25 → native unpublish →404/map gone / admin/public | AdminRU1440; publicRU390 | 4/4 PASS; admin-resume |
| Published27 → edit AZ title → save candidate → editor reload → old live → Hub reason+approve → new search/map/reload / admin/public | Admin1440; public RU/AZ/EN390 | 12/12 PASS; update-live. Candidate не появляется в live до approval |
| Scheduled1 → owner login/cancel with reason → cancelled public / owner/public | OwnerRU390; public RU/AZ/EN1440 | 5/5 PASS; event-native. Initial public width metadata corrected from actual context definition |

Полные URLs, данные, наблюдения, FAIL и ссылки PNG находятся в matrix/raw results; свежие подтверждения заменяют только собственные ошибочные ранние ожидания. Все raw attempts сохранены. [CORRECTIONS](CORRECTIONS.md) объясняет13 исправлений QA harness: transition timing, hidden responsive locator на768, navigation waits, canonical `/event/` URL, invalid fixture district, observer API, custom confirmation. Никакие application assertions не менялись. Ранние harness FAIL не выданы за продуктовые дефекты, а CLI0 с structured error не считается PASS.

### Визуал и диагностика

Сохранены **616 native PNG** и13 явно DERIVED contact sheets: [SHA/размеры/время](screenshots-manifest.json). Все216 базовых страниц действительно отрисованы в Chromium; PC/mobile failures сняты отдельно. Просмотрены12 контактных листов всех18 сочетаний каждого базового состояния, а также отдельные PC/mobile evidence проблем. Contact sheets — уменьшенные previews верхнего viewport, не новая браузерная проверка и не доказательство всех пикселей длинной страницы. Исходные full-page PNG не изменялись; [источники previews](visual-review-sources.json). Размещение длинных заголовков/fallback и empty states проверено; root horizontal overflow не найден в этих216 состояниях. Это не исключает внутренние перекрытия controls: PUBLIC-QA-01/04 подтверждены реальной геометрией и native click.

В базовых18 contexts:54 console errors и72 failed external requests (54 unpkg,18 maps.google.com), **0 failed local requests**; внешние запросы намеренно заблокированы. Это SIMULATED integration/environment diagnostics, не утверждение о production outage. Actual pageerror и SDK execution отдельно от console сообщения. Configured SDK abort и phone network error имеют собственные raw diagnostics/PNG. Клавиши выполнены для конкретных sort/drawer/phone/marker controls; полный accessibility/focus trap аудит всех страниц NOT RUN.

### Команды и тесты

[COMMANDS](COMMANDS.md) содержит точные executable/commands и35 browser command attempts с native CLI exits/durations; [ledger](command-ledger.jsonl) — первичное доказательство. Python drive wrapper иногда возвращает0 при CLI1: используется `cli_exit_code`, не wrapper exit.

- Unchanged11 Django suites:93 methods,92 successful methods;1 failing method с2 EN/AZ subtest failures,0 errors, native exit1. `PublicSectionSwitchTests.test_admin_section_controls_follow_selected_language` — PUBLIC-QA-03, existing ignored `.mo` environment. [Команда](tests-command.json), [log](tests.log), [locale proof](locale-proof.json).10 локальных CSRF значений в test HTML отредактированы, counts/exit/assertions сохранены: redaction.json.
- Existing Node map motion suite:6/6 PASS, native exit0. [Команда](js-tests-command.json), [log](js-tests.log).
- Local private HTTP:60/60 PASS. После UI публикации27 начальные negative expectations к27 больше неприменимы; поздние private exclusions проверены отдельно.
- Aggregation exit0: нет unclassified FAIL. Final source/runtime/journal/links/syntax/credential checks — verification.json и verification-command.json; strict exit1 из-за чужого drift отделён от результатов приложения.

## 2. Сильные стороны

На вымышленных данных общий reader согласует опубликованность списка, search suggestions, map и прямых detail URLs. Age/category/price относятся к одной подходящей группе; private999 не влияла на public цену. Подтверждённая физическая площадка объединяет участников, одинаковые координаты сами по себе не объединяют бизнесы. Места без валидной точки не пропадают из списка. Native save/reload, moderation approval и cancellation отражаются в локальных public readers; candidate/live разделены. Phone duplicate request и network retry прошли, галерея сохраняет ожидаемый результат после reload.

## 3. Реальные проблемы

| ID | Класс | Эффект | Severity |
|---|---|---|---|
| PUBLIC-QA-01 | Pre-existing current local application baseline; adapter interface SIMULATED | Desktop venue popup выше400px карты, верх и close обрезаны | P2 |
| PUBLIC-QA-02 | Pre-existing current local application baseline; transport SIMULATED | Failed configured SDK оставляет Loading без terminal error/retry | P2 |
| PUBLIC-QA-03 | Environment failure: existing ignored `.mo` | AZ/EN admin section labels русские; `.po` содержит перевод | P3 |
| PUBLIC-QA-04 | Pre-existing current local application baseline; actual native pointer | Mobile hero intercepts category click в5 сочетаниях | P2 |

Каждый defect отдельно оформлен в [FINDINGS.md](FINDINGS.md): роль, URL, шаги, ожидание/факт, raw/PNG, source cause, scope/dependencies и самостоятельный копируемый repair prompt. Воспроизводимость текущего HEAD установлена; момент появления и regression относительно другой версии не установлен. Ни один дефект не исправлялся.

## 4. Tech debt

Карта требует согласованных ограничений размера popup и terminal bootstrap состояния; существующий stacking context влияет на drawer поверх hero. Compiled locale freshness на этом checkout расходится с tracked sources. Собственный reusable QA harness также нуждается в строгом propagation native exit и ожиданиях navigation/visibility; это отмечено отдельно, не как дефект приложения.

## 5. Risks

Увеличение одного z-index без проверки ancestor contexts может создать новые перекрытия. Retry SDK должен учитывать поздний callback и duplicate listeners. Реальный SDK projection/tiles/clustering отличается от локального адаптера; совместимость без отдельного теста не доказана. Изолированный LocMem подтверждает один процесс, не distributed cache invalidation. Чужой drift и отсутствующий running container имеют UNKNOWN origin; их состояние не восстанавливалось.

## 6. Dead/legacy candidates

Кандидатов на удаление не подтверждено. Поддержка legacy query params и missing/legacy coordinates — наблюдаемый reader contract, не доказательство dead code. Graph coverage и synthetic fixtures недостаточны для удаления кода/DB structures; source/data audit production не выполнялся.

## 7. Tests gaps

**NOT RUN:** actual Google/Leaflet SDK, tiles, clustering и live external links/calls; production; full repository suites; shared/multi-worker cache; полная concurrent write/conflict/moderation матрица; полный keyboard/contrast/screen-reader аудит всех overlays; exhaustive manual pixel review всех full-page screenshots. Desktop adapter действия после недоступного close — blocked PUBLIC-QA-01. Обязательная typo/fuzzy search функция по source не установлена (`icontains`), поэтому не назначен вымышленный дефект её отсутствия. No production/private fixtures или реальные внешние ключи не использованы. Tests за другие модули не заменяют эти ограничения.

## 8. Recommendations

Использовать четыре отдельных repair prompts из FINDINGS.md с согласованным конкретным scope. В приёмке исправлений сохранить native clicks, geometry, all18 языковых/width combinations, current baseline/locale classification и реальные vs SIMULATED integrations. Не менять existing assertions для green. Перед следующими проверками заново снять snapshot и создать новый стенд. Следующий аудит — только07; [готовый текст](next-chat.txt), [все13 модульных заданий](PROMPTS-INDEX.md). Модуль13 выполнять после остальных.

## 9. P0/P1/P2/P3

В реально выполненном scope P0/P1 не подтверждены; это не общая security/production гарантия. P2: PUBLIC-QA-01/02/04 — ограниченная недоступность public controls/error handling, с рабочими обходными keyboard/list paths и без обнаруженной потери данных. P3: PUBLIC-QA-03 — неверные локальные administrative labels при рабочей функции. Все четыре OPEN. Завершён аудит06, а не исправление продукта.
