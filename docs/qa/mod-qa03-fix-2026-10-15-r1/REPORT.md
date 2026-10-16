# MOD-QA-03 — approved CSS applied, ID OPEN / JS supplement pending

2026-10-15. Одобренный CSS scope выполнен точно; задача целиком **не закрыта**. [Approval](approval.json), [applied diff](applied.diff), [application hashes](applied.json). Новая причина меню требует отдельного согласования [MENU_SUPPLEMENT_PLAN.md](MENU_SUPPLEMENT_PLAN.md). Closed IDs: []. Полный модуль08 не принят.

## Snapshot и изоляция

`/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, active_run NONE. [entry.json](entry.json):30995существующих файлов/69контейнеров/8известных HTTP. CSS до patch совпал с approved proposal SHA. Одобрение «да» относится к предшествующему однофайловому27строчному плану; заново его не запрашивали. Единственный изменённый app file `static/admin/css/pages/kidsmap_changelist.css`, все старые байты сохранены как префикс. JS приложения остался исходным.

Роли frontend-admin/browser-qa/integration-reviewer выполнены последовательно одним lead, независимые subagent-аудиты не заявляются. Использованы KidsMap UI, accessibility, systematic debugging, TDD через meaningful native RED→GREEN и verification-before-completion. Codebase graph/source map из PLAN retained; exact CSS/static source перепроверен.

Старый собственный PLAN-профиль проверен перед коротким RED:PID655705,953source matches disk, DJANGO_TESTING=1, no env, source CSS SHA unchanged — [red-profile-source.json](red-profile-source.json). Все новые afterpatch проверки на новом собственном профиле: DB/user `mod03_fix_r1`, PostgreSQL54341, HTTP47071, own container/volume `mod-qa03-fix-2026-10-15-r1-pg`. Own fresh venv Python3.12.3/Django6.0.2, hash-verified own pypdf6.20.1 copy; установленный общий site-packages используется только для чтения. [dependency manifest](dependency-manifest.json), [runtime-info.json](runtime-info.json).

175миграций на своей БД; только fictional1admin/3Place/3Event/3Specialist. Свои cache/media/private-media/email. Очищенное env, DJANGO_TESTING=1, checkout `.env` не загружен. Socket guard разрешает только свой PG; native browser разрешает только свой origin, внешние fonts намеренно blocked. Это не host-wide firewall. Текущие3PO собраны заново `scripts/build_isolated_locales.py`:build0/verify0, один own LOCALE_PATHS до django.setup, manifest проверяется на старте. Shared MO не перезаписаны. [locale manifest](locale-manifest.json), [runtime final source](runtime-source-final.json).

## RED → проверка CSS

Свежий targeted unpatched RED: [native-red.js.result.json](native-red.js.result.json),140observations=127PASS/13expectedFAIL/0NOTRUN. Native login/language/sidebar/open menu,36PNG; поддерживает причины из прежнего PLAN baseline1037PASS/84FAIL, который целиком не повторяли перед patch.

Применён exact27line append: scoped horizontal table viewport Place/Event/Specialist, Place min1000px/updated140px, mobile sort left alignment. Toolbar/sidebar/search/backend/PO не менялись.

Fresh accepted afterpatch [native-green-matrix-r2.js.result.json](native-green-matrix-r2.js.result.json): **1121PASS/0FAIL/0NOTRUN**,108основных комбинаций трёх очередей×RU/AZ/EN×6ширин×2sidebar;288native состояний/PNG. Те же baseline assertions; только ожидается конечная ширина sidebar. Root≤1px overflow, readable date/row height, локальная scroll surface, toolbar controls и sort/columns panel bounds.18mobile expanded overlay состояний не используются для взаимодействия с закрытым фоном; menus проверены после native закрытия overlay. Это целевая responsive-матрица, не полный модуль08 или вся админка. Domain fingerprint unchanged. Console/network diagnostics в raw result:176blocked external requests+176associated console messages,0local errors/pageerrors.

## Дополнительные FAIL и границы

Actual source CSS menu safety: [native-menu-safety.js.result.json](native-menu-safety.js.result.json),12observations=7PASS/5FAIL. Place390last actions ниже viewport; Event390/1024first/last panel обрезан внутри table/row. Exact prepatch CSS replay в собственном браузере дал те же5FAIL и SHA исходного CSS: [native-prepatch-menu-replay.js.result.json](native-prepatch-menu-replay.js.result.json). Это отдельная существовавшая причина, не объявленная регрессией CSS. При replay подменялся только stylesheet response, исходный JS и данные неизменны; replay явно SIMULATED, не runtime старого checkout.

Неприменённый JS proposal: [supplement plan](MENU_SUPPLEMENT_PLAN.md), [exact diff](MENU_SUPPLEMENT_V2.diff). Browser-only v2-r3 prototype20PASS/0FAIL, node syntax0; это SIMULATED feasibility, не фактически внесённое исправление. Ранние prototype FAIL сохранены; locator после portal и screenshot/resize разделены от source acceptance. Дополнительные функциональные сценарии: [native-flows-r2.js.result.json](native-flows-r2.js.result.json); точные статусы приведены в verification. Shared Place column controls в Event/Specialist ссылаются на отсутствующие header targets: функциональное скрытие этих targets NOT RUN, menu bounds проверены; это не выдано за GREEN.

## Прерывание и preservation

Во время первого afterpatch matrix и первого функционального прохода пришло `turn_aborted`. Их semantic result/exit не получены; partial PNG сохранены под original prefixes, первая матрица не объявляется PASS. Повторён только прерванный targeted проход с новым prefix r2, source assertions прежние. [interruption.json](interruption.json).

После прерывания отсутствовали все8entry HTTP PIDs и собственный697108. Нельзя утверждать, что HTTP процессы сохранены. Причина исчезновения отдельно не доказана; по времени это обнаружено после interruption. Ни один foreign HTTP не перезапущен. Поднят только новый собственный профиль с той же собственной БД:PID711181, [server-current.json](server-current.json), прежняя server.json сохранена.69entry контейнеров сохранили ID/state/ports; own70th PG работает. Исторический continuity четырёх HTTP до module07 также остаётся NOT VERIFIED. [preservation-before-status-update.json](preservation-before-status-update.json), [verification.json](verification.json).

До изменения статусного guide30994из30995старых файлов были побайтно неизменны; отличался только approved CSS. После guide update дополнительно разрешены только собственная статусная заметка и ссылка. Нет reset/clean/stash, commit/push/deploy/production; active_run не присваивался. Старые отчёты/fixtures/контейнеры не удалялись. Все app изменения сверх approved CSS отсутствуют.

## Команды / evidence / NOT RUN

[commands.jsonl](commands.jsonl) содержит exact argv/exits/durations браузера и setup. Отдельный ошибочный `python3 runtime.py runtime-info` завершился1, потому что системный Python без Django; повтор с own venv exit0, app assertions не менялись. Неполученные exits interrupted scripts помечены UNKNOWN, не0. Metadata/proposal scripts и terminal syntax checks описаны в verification.

[PNG manifest](png-manifest.json): hashes/dimensions/group каждого файла, включая RED, interrupted partial, actual source GREEN и явно SIMULATED replay/prototypes. Ручной просмотр выбранных PNG не объявляется просмотром всех изображений. Native paths/keyboard применены; source/HTTP200/jsdom не подменяют rendered evidence.

**NOT RUN / OPEN:** фактический JS supplement и его полный postpatch acceptance, закрытие MOD-QA-03, недовыполненные/проваленные функциональные ветки, другие MOD IDs04–08, ACCEPT-08, полный07/все модули, production. Уже принятые MOD01/02 не перепроверялись целиком и не отменяются этим scope. После этого отчёта ждать approval нового JS scope; не начинать следующий модуль автоматически.

Конечная функциональная выборка: [accepted-functional.json](accepted-functional.json) — **163PASS/24FAIL/12NOTRUN**, плюс12отдельных boundary NOT RUN для несуществующих column targets Event/Specialist. Keyboard horizontal scroll и wheel прошли во всех18cells; keyboard sort focus, filter expand/collapse, Place column hide/restore, native empty/reset проверены в доступных ветках. Реальные24FAIL — сохранение поиска при sort/reload Event/Specialist,12NOTRUN — зависимое продолжение после `?e=1`, где кнопки reset уже нет. Данные unchanged. Exact prepatch CSS replay отдельно подтвердил2sourceFAIL Event/Specialist наRU1024: [native-sort-prepatch-replay.js.result.json](native-sort-prepatch-replay.js.result.json). Никаких исправлений сортировки этим run не делалось; нужен отдельный свежий план её причины.

Исходный полный функциональный result145PASS/42FAIL/12NOTRUN retained. В Place исходный fixture запрос `QA Queue 2` не был уникальным: поиск включает общие fictional телефон/адрес, поэтому ожидание одной строки было неверным oracle. Только6Place cells/78assertions повторены с точной фразой `"QA Queue 2"`, та же проверка одной строки/search/sort/reload:79PASS включая отдельную неизменность данных; глобальный check не удваивается при merge. Assertions не ослаблены, backend не менялся. [QA harness corrections](qa-harness-corrections.json). Остальные24sourceFAIL не заменялись и не скрывались.

Уточнение baseline replay:5PASS/5FAIL/**2NOTRUN**, все5идентичностей FAIL совпадают с actual-source menu run7PASS/5FAIL. Два prepatch readiness control завершились timeout; они не объявлены PASS. Первый metadata gate ошибочно требовал7controlPASS и для replay; retained в verification-gate-r1.json, проверка исправлена на точные raw counts без изменения browser assertions.

Final metadata gate: **24PASS/0FAIL/1NOT VERIFIED**, последняя граница относится к8foreign HTTP после interruption. PNG manifest: **691** файлов с hashes/dimensions (36RED,288accepted CSS matrix,259interrupted partial,12actual menu,12SIMULATED prepatch replay,48SIMULATED JS proposal,36functional PNG). Closed IDs остаются[]. Фактический JS SHA исходный; приложение содержит только exact approved CSS append.
