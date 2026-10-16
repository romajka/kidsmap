# Module06 — LOCAL PASS, ACCEPT-06

Все PUBLIC-QA-01–06 CLOSED LOCAL в выполненном scope. Подтверждённых OPEN в модуле06:0. Production/global13/real map SDK не принимались.

## Snapshot, scope and authorization

Checkout `/home/ramin/kidsmap`; branch `task33-progress`; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` + сохранённый dirty WORKTREE. `active_run: NONE` без присвоения. Приёмка зафиксирована `2026-10-14T12:31:11.652598+00:00`. [Исходный срез](snapshot.json), [текущий runtime](runtime-version-final.json), [финальная проверка](verification.json).

Пользователь поручил весь модуль06 и явно одобрил [конкретный план](../../superpowers/plans/2026-10-14-module06-public-map-filters.md), затем дополнения PUBLIC05 и PUBLIC06. Работа выполнена последовательно одним lead; независимые агенты не заявляются. Без commit/push/deploy/production.

## Изменения и приёмка ID

| ID | Причина и результат | Свежая приёмка |
|---|---|---|
| PUBLIC-QA-01 | Popup560px в карте400px давал отрицательный top; размер ограничен картой, внутренние карточки прокручиваются, закрытие остаётся доступным. Clamp и ResizeObserver учитывают окончательную ширину сетки. | RED [геометрия](map-geometry.result.json) →36 GREEN;72 scroll/keyboard с12 targeted resize recheck, исправившими3 resize FAIL. |
| PUBLIC-QA-02 | SDK script error и отсутствие callback оставляли Loading; добавлены терминальная ошибка RU/AZ/EN,12s ожидание и native retry. Новый script действительно загружается; старые ошибки/повторный callback не создают второй набор markers. Empty filter очищает timer; возврат к непустому результату запускает новое ожидание. | [SDK164](sdk-final-acceptance.result.json), свежий2-check empty roundtrip RED→GREEN, native retry RED→GREEN. Transport/interface SIMULATED. |
| PUBLIC-QA-03 | Исторические ignored MO устарели; source PO уже содержал нужные строки. | Собственные fresh RU/AZ/EN, helper verify и sole LOCALE_PATHS до django.setup;6 native labels и15 targeted final locale consumers GREEN. Общие MO не изменялись; application/PO patch для03 не нужен. |
| PUBLIC-QA-04 | `z-index:1!important` и `isolation:isolate` удерживали drawer под hero. | Сняты только при открытом responsive drawer. Fresh RED6 affected cells →18 native pointer GREEN;18-cell комбинированные фильтры/54 assertions и keyboard/focus. |
| PUBLIC-QA-05 | Marker перехватывал Escape: popup закрывался, карта оставалась открытой. | [HEAD RED](escape-head-recheck.result.json) → scoped map capture, popup→marker→map→opener native checks во всех18 cells. Enter/Space и coincident chooser сохранены. |
| PUBLIC-QA-06 | Auto column телефона оставляла Details/Route50–63px; надписи выходили за кнопки на desktop. | Fresh12 FAIL/6 mobile PASS →18 GREEN. Две кнопки рядом, phone/revealed number отдельной строкой. Native phone/Details/close18 и9 final targeted checks; номер после раскрытия также полностью читается. |

Только3 application files: `static/js/catalog_map.js`, `static/css/pages/catalog_places.css`, `src/catalog/templates/catalog/place_list.html`. [Reviewable diff](repair.diff), [SHA](accepted-source.json). Backend/ACL/CAS/candidate-live/публикация/schema/существующие assertions не менялись. Error/retry labels следуют существующим RU/AZ/EN data attributes template, новых PO-правок нет.

## Native acceptance и данные

**1539 accepted unique browser assertions**,18 cells RU/AZ/EN×360/390/768/1024/1280/1440: [нормализованные строки](accepted-browser-rows.json), [matrix.csv](matrix.csv). Это объединение конкретных проверок, не утверждение о каждом возможном варианте продукта.

705 assertions: главная, каталоги/карточки места, организации, специалиста, события, activity, cancelled/empty/long fallback; render/root overflow/local images/basic controls. Дополнительно real search/name/address/group/filter/sort/pagination/Back/Forward/reload/reset, same-group age/category/price, shared venue links, independent equal coordinates/chooser, missing/zero/partial point exclusion, private HTML/map/suggestions exclusion, native gallery/phone, keyboard/focus, map close/scroll/resize и SDK failure/retry/late callback.

[Сохранение и одобрение](admin-approved-lifecycle.result.json): native staff save создаёт pending candidate и сохраняет live. Настоящее reviewer approval обновляет search/map; unpublish после разрешения candidate скрывает карточку и очищает результаты. [Pending guard](pending-guard-acceptance.json) подтвердил отказ снятия при незавершённом candidate — это правильный контракт. [Разделы](section-negative-finish.result.json): native disable/save, ожидаемые404/410, restore/save/reload и fresh public menu/cache. [Событие](event-cache-lifecycle.result.json): owner native reschedule/reload/cancel, старые публичные ссылки и списки RU/AZ/EN показывают актуальный статус. [READ ONLY readback](final-state.json):8 PASS с statement_timeout10s/lock_timeout2s, только вымышленные fixtures.

## Tests и exact exits

[Explicit discovery](test-discovery-final.json): **288 разных methods**. No-label/full wrapper/global corpus не объявлялись полными.

| Receipt | Methods / результат | Exit |
|---|---|---|
| [module-tests](module-tests.command.json) |93 PASS,56.783s test execution |0|
| [discovery supplement](discovery-supplement-tests.command.json) |195 methods:185 PASS;10 methods дали16 failed/2 error subtests из-за own QA settings |1|
| [environment recheck](supplement-environment-recheck.command.json) |Только эти10 unchanged methods PASS,10.889s |0|
| [affected template](affected-template-tests.command.json) |29 affected methods PASS,12.516s; входят в288 |0|
| [final locale consumers](final-locale-consumers.command.json) |15 affected methods PASS,16.222s; входят в288 |0|
| [final semantic/source gate](acceptance-verification.command.json) |1539 browser/8 readback/source/locales/PNG gate |0|

Причина supplemental failures: serve profile включал localized URLs и собственный PUBLIC_BASE_URL; существующие unit suites рассчитывают на canonical TESTING defaults и свои override_settings. Исправлен только own test launcher, assertions сохранены.93+185+10=288 accepted unique methods; targeted repeats не добавляются как новые tests. Команды полностью в [commands.jsonl](commands.jsonl), stdout рядом с command receipts. Browser CLI может вернуть0 при semantic FAIL; решающими являются JSON statuses и последняя verify.py, не один CLI exit.

## Изоляция и инструменты

Python `3.12.3`, Django `6.0.2`, Node `v20.20.2`, Chromium `153.0.8010.36`, PostgreSQL `17.10`. Own PostgreSQL container/volume `module06-full-2026-10-14-r1-pg`; loopback DB port `57959`, HTTP profile по [server.json](server.json). Собственные DB/cache/media/private-media/email/session cookies; DJANGO_TESTING=1; fictional users/organizations/places/events. Checkout .env не загружался; credentials только ignored `.tmp`, не в отчёте/Git. Backend connect/connect_ex разрешён только на собственный PostgreSQL; browser внешние requests блокирует.

[Fresh locale manifest](locale-manifest-final.json), sole root `/home/ramin/kidsmap/.tmp/module06-full-2026-10-14-r1/locales-final/locale`. Foreign PO additions вызвали strict stale-catalog refusal; создан новый own каталог и процесс перезапущен, shared MO сохранены. Current process/checkout/source MATCH подтверждён финальным gate. Helper/test/source hashes — provenance вместе с реально выполненными тестами, не отдельный общий PASS.

## Evidence и сохранность

[721 PNG с SHA/размерами](png-manifest.json), включая application RED, промежуточные QA попытки и accepted frames. Все PNG не объявляются GREEN; результаты привязаны к receipts. Выборочно просмотрены actual rendered screenshots, в том числе clipping и финальные controls.

Сохранены чужой dirty WORKTREE, active_run и стенды. [Foreign drift](concurrent-foreign-drift.json): admin sidebar/ownership preview/import registration и PO additions из параллельной работы; они не откатывались и не присваивались этому repair. Собственные source changes ограничены указанными3 файлами. Исторические [Windows audit](../module06-2026-10-10-r1/REPORT.md) и предыдущие module01–05 reports сохранены.

Сырые неудачные попытки не скрыты: initial SDK clone не запрашивал script; одного z-index снятия было мало из-за isolation; window resize измерял промежуточную сетку; timer после empty истекал без сброса; Node URL отсутствовал в CLI sandbox;301 response принимался преждевременно за завершение AJAX; event route оказался singular; native empty404 даёт browser navigation error; publish/unpublish требуют настоящего confirmation modal; pending candidate нельзя считать live edit. QA исправления следуют source/реальным переходам; существующие tests/assertions ради green не менялись.

## NOT RUN и handoff

Real Google/Leaflet SDK/tiles/provider compatibility/GPS; реальные credentials/integrations/email/звонок/external route/clipboard; physical devices/другие engines/screen reader/exhaustive Tab traversal; global13/full corpus и CROSS-QA-02 discovery; production/release/cache rollout — **NOT RUN**. Map adapter/transport **SIMULATED**. Own newer adapter создаёт z-index0 SDK pane: старый simulation pane не имел stacking context и рисовал fake marker поверх app popup; app CSS/позиционирование при этом не подменялись.

Переход дальше разрешён после этого LOCAL результата: следующий конкретный scope — PLAN ACCESS-QA-01 модуля07, [готовый prompt](next-prompt.txt). NETWORK ACCESS-QA-03 alias ORG-QA-02 уже имеет свою свежую scoped приёмку; не переисправлять по старой очереди. Модуль07 автоматически не начат.
