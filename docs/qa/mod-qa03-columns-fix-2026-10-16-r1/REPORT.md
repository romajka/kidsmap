# MOD-QA-03 — колонки LOCAL PASS; выявленные причины ID закрыты локально

2026-10-16, исполнитель `/root`, canonical kidsmap-orchestrator; frontend-admin/django-reviewer/integration-reviewer/browser-qa выполнены последовательно основным исполнителем, независимых агентов не было. Определения `.agents/agents/<id>/agent.md`. [Approval](APPROVAL.md): пользовательское «…точечное и примерочное тестирование…продолжай» разрешает ранее показанный четырёхфайловый план колонок. Full module08 acceptance не выполнялась.

## 1. Состояние и snapshot

`/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, dirty WORKTREE, `active_run: NONE`. [Entry](entry.json), [current source](runtime-source-final.json), [verification](verification.json). Собственный HTTP PID30142, loopback60617; PostgreSQL loopback47955/database `mod03_columns_fix_r1`. Текущие957 source hashes совпадают с running startup и WORKTREE. Source/HEAD/production — разные состояния; production NOT RUN.

Shared columns menu содержало Place-only targets; Jazzmin Event/Specialist headers не имеют column-* классов. Галочки тихо не управляли реальными колонками. Fresh nativeRED: Place1controlPASS, Event/Specialist2FAIL; [JSON](native-red.js.result.json),3отдельных columns-red PNG.

## 2. Что изменено и что работает

Только4согласованных paths, [точный собственный diff](implementation.patch): `src/catalog/templatetags/admin_dashboard_tags.py`, shared `km_changelist_search_panel.html`, только Column Visibility Toggler блока `static/admin/js/kidsmap_place_changelist.js`, NEW `src/catalog/testcases/test_admin_queue_columns.py`.

Варианты и реальные индексы из permission-filtered cl.list_display, подписи из тех же admin metadata, что в таблице. Скрываются/возвращаются фактические header и все row cells. Название всегда видно. Place сохраняет старый storage key, Event/Specialist имеют свои. Неверный JSON и устаревшие preferences безопасны. Частная колонка документов отсутствует у обычного reader, индексы остаются правильными при отсутствии action-checkbox/documents. Корзина Place использует настоящую дату удаления. Existing queryset/ACL/модели/PO/CSS/vendor не изменены.

## 3. Реальные проблемы и локальный итог

Колонки: **scoped LOCAL PASS**. Все выявленные причины MOD-QA-03 теперь CLOSED LOCAL: предшествующие CSS/menu/SORT/SEARCH принимаются в ранее проверенных границах; новая причина колонок проверена сейчас. [Связь с сохранёнными evidence](retained-evidence.json):953из956предыдущих source hashes не изменились;3изменённых paths ограничены этим patch, старые row-menu JS prefix/suffix и search/sort template boundaries совпадают побайтно. Новый test —957й path.

Полный модуль08 остаётся OPEN. Следующий MOD-QA-04 свежо подтверждён отдельно: Escape не закрывает sidebar, [PLAN/report](../mod-qa04-recheck-2026-10-16-r1/REPORT.md). Одобрение колонок на него не переносится.

## 4. Tech debt

Metadata подписей повторно используется, новых переводов не добавлено. Старые некорректные/непереведённые модельные подписи, например Specialist Updated at/рейтинг, остаются видимым долгом и не выдаются за whole-UI localization PASS. Ни одна отдельная новая историческая ID не введена.

## 5. Риски и сбой окружения

Во время QA обнаружены отсутствующими own HTTP148598/controller154527; затем ownPG оказался exited255 с сохранённым volume. Причина не установлена; перезапуск окружения — только гипотеза. [Infrastructure evidence](infrastructure-interruption.json), [interruption notes](interruption.md), original checkpoints/metadata в interruption-01/02. Семь завершённых batches и20partialPASS не повторялись. AZ/EN768 восстановлены из первых10PASS и продолжены с оставшихся cells. Попытки до readiness остаются failed harness attempts в commands/scratch, не считаются appFAIL/GREEN.

Восстановлены только свои verified container/volume и HTTP; без reseed/migrations. [Domain after recovery](domain-after-recovery.json) равен исходному fingerprint. Старые PID не выдаются за живые.

На финальной сверке **два чужих контейнера** (предыдущие search/sort) сохранили ID/ports, но running→exited; entry HTTP104840 отсутствует. **Continuity этих стендов NOT VERIFIED**, чужие процессы/контейнеры не перезапускались. Все73entry container identities сохранены, остальные state/ports совпадают. [Preservation](preservation.json). Функциональный LOCAL PASS не скрывает эту эксплуатационную оговорку.

## 6. Legacy/dead candidates

Удалений/refactor/cleanup нет. Старые key Place сохранены; устаревшие entries игнорируются, новые настройки записывают только реальные optional columns. Предыдущие отчёты/сырые FAIL/PNG сохранены.

## 7. Целевые проверки и gaps

[Commands/exits](commands.jsonl), [semantic gate](final_gate.py), [PNG manifest](png-manifest.json).

- Новый5-method RED:68assertionFAIL/0ERROR, [вывод](tests-red.txt). После patch **9unique methods PASS**, exit0, [GREEN](tests-green.txt):5новых и4representative existing — по одному search/sort плюс2private-document ACL. Полные старые search/sort/CSS/menu suites не повторялись по прямому правилу пользователя.
- **954 accepted native PASS**: RU/AZ/EN×360/390/768/1024/1280/1440×3queues =54base cells/90reachable sidebar states;18mobile overlays явно ограничивают доступ к фону. Native Tab/Space, видимый focus, настоящий checkbox→header/all rows→reload→restore; реальные labels/field cells; menu geometry в viewport после обычной прокрутки.
- Pilot RU390:32PASS/3rawFAIL из неверного focus oracle, требовавшего outline. Браузер измерил видимый3pxbox-shadow; [probe](native-focus-probe.js.result.json)/PNG и [correction](harness-focus-correction.md). Перепроверены только3focus cases:3PASS, без app change;32PASS не повторялись. Raw pilot не переписан.
- [Edge28PASS](native-edges.js.result.json): cross-model navigation и persistence, Place trash/date toggle, empty states на трёх очередях, обычный reader без documents; битый JSON/non-array/stale/identity и legacy Place prefs явно **SIMULATED setup**, дальнейшие native controls реальные. Доменные данные до/после совпали.
- Всего **982 accepted native PASS**,0local console/page/network/HTTP errors. External fonts/resources blocked, это не проверка интеграций.
- **101 actual PNG**, hashes/dimensions verified, RED раздельно с GREEN. Визуально просмотрены RU390 Specialist menu и RU390 sidebar next-recheck; не заявляется ручной просмотр всех PNG.
- Полный модуль08/global, физические устройства/non-Chromium, внешние интеграции/production/commit/push/deploy NOT RUN.

Source inspection/jsdom/HTTP200 не заменяли browser. Данные source модуля по hash не подменялись. Before/after fingerprint всех полей Place/Event/Specialist (4/3/3fictionalrows) совпал, [final](domain-final.json); это не утверждение о всех таблицах.

## 8. Изоляция, сохранность и следующий шаг

DJANGO_TESTING=1, отдельные PG/testDB/cache/media/private-media/file-email; checkout.env/production credentials не читались, унаследованный env очищен; socket egress только ownPG, browser только loopback. Проверенные собственные dependency copies; никаких сетевых install.

Current RU/AZ/EN PO собраны scripts/build_isolated_locales.py в новый `.tmp/mod-qa03-columns-fix-2026-10-16-r1/locales`, [manifest](locale-manifest.json), build/verify exit0. Проверка до setup, единственный собственный LOCALE_PATHS, все3ownMO реально открыты. Shared MO не менялись.

Entry32643 файлов: 32639неизменённых, 4допустимых changed existing paths,0missing; новыйtest/своиQAдобавлены. Только3approvedapp files плюс appended guide status; HASH list в preservation. HEAD/branch/active_run прежние, no reset/clean/stash. Ограничения foreign service continuity указаны выше отдельно.

Следующий шаг — отдельно одобрить [четырёхфайловый MOD-QA-04 PLAN](../mod-qa04-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md). Старые полные корпуса не гонять снова. Полный08 один раз после MOD04–08; module09 не начинать.

## 9. Приоритеты и решение

MOD-QA-03 P2: **CLOSED LOCAL для выявленных причин**; полная приёмка module08 ещё pending. MOD-QA-04 P2: CONFIRMED OPEN, PLAN готов, patch не одобрен/не применён. Чужая process/container continuity: NOT VERIFIED после обнаруженного сбоя; file/source preservation подтверждены отдельно.
