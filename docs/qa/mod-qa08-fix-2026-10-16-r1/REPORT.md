# MOD-QA-08 — CLOSED LOCAL

2026-10-16. Одобренный [план](../mod-qa08-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md) выполнен в трёх файлах. Event/Specialist получают четыре применимых фильтра из actual filter_specs; порядок primary config сохраняется, остальные идут следом. Статус можно снять отдельной меткой. Place сохраняет прежние controls/quality/status-chip semantics. Server choices остаются opaque URLs; JS/CSS/PO/ACL/ORM/schema не менялись. [Фактический diff относительно entry](applied.diff), [SHA approved candidate](applied.json). Новый test: src/catalog/testcases/test_mod08_filter_drawer.py.

## Snapshot / изоляция

/home/ramin/kidsmap; e4e05cc213b34e2d771ecb854901bfd016d1db51; task33-progress; dirty WORKTREE; active_run NONE. [Entry](entry.json). Один /root последовательно выполнял frontend-admin/Django/browser/integration роли; независимые специалисты не заявляются. Применены TDD/verification/KidsMap UI/accessibility/Playwright.

Проверено повторное использование только собственного PG b4e125832fb38463089194b973c7bd25f61d3f4534d19bf6e079b6d1acb94766, loopback47955, fictional mod08_plan_r1. Fixture reseed/migrate не запускались. Новый собственный runtime/cache/media/private-media/email/cookies и test_mod08_filter_fix_r1, DJANGO_TESTING=1, чистое окружение без checkout.env/production credentials. Python sockets разрешают только own PG; browser non-local blocked, включая external fonts. Это ограничение transport конкретного QA, не всей машины. [Ownership](profile-reuse.json), [runtime](runtime-info.json), [current server](server-current.json).

Текущие RU/AZ/EN PO собраны в уникальную .tmp/mod-qa08-fix-2026-10-16-r1/locales; build/verify exit0, sole LOCALE_PATHS и manifest gate до django.setup. [Manifest](locale-manifest.json). [Работающий source](runtime-source-final.json):961path, actual module/template origins, startup=disk; project MO открывались только из own каталога. Общие MO сохранены.

## RED → GREEN

[Все точные команды/exits/durations](commands.jsonl). Новый backend RED:6методов,10assertionFAIL,0ERROR — missing drawer filters и status chips. Новый тест сначала ошибочно ожидал только3primary fields; ожидание уточнено до4available fields. Повтор задел QA source guard; он отдельно сохранён как harness failure. [Окончательный controls RED](backend-red-final.txt):1method/6locale assertionFAIL, exit1. [Браузерный RED](native-red.js.result.json):2sourceFAIL/8controlsPASS.

[Первый GREEN](backend-green.txt):8methods, из них7PASS; один новый Reset method имел2subFAIL из-за неверного ожидания name_asc после Reset, который намеренно возвращает newest-first. Исправлено точное ожидаемое множество/порядок fictional IDs; существующие assertions не трогались. [Повтор только Reset](backend-green-reset.txt):1/1PASS,exit0. Приняты8уникальных методов:6новых +2representative search/ACL. Повторные full suites MOD01–07 не запускались.

[Accepted browser](accepted-observations.json):**470PASS/0FAIL**,36cells Event/Specialist×RU/AZ/EN×360/390/768/1024/1280/1440. Настоящие login/language menu, keyboard Enter/open, select auto-navigation, последовательные category/status/date(two params)/owner либо format/status/is_active/direction, exact rendered IDs/counts, выбранные options, Apply, reload, удаление status-chip, несовместимые условия→zero results, Reset→full queue. Все сохраняют предусмотренные q/sort/прочие filters. Geometry/labels/control associations checked. Дополнительно Place RU/EN×390/1440 сохраняет legacy fields, quality section, category/search/sort/status и Reset. [ACL9PASS](shared-acl.json):specialist-only staff получает200 Specialist,403 Event/Place во всех языках; synthetic staff setup отдельно от GET domain проверок.

Первоначальный unprefixed QA API выдавал AZ titles/options независимо от UI. Поэтому24RU/EN comparisons были ложными FAIL. Исправлен только testing helper посредством explicit X-QA-Language translation override; повторены только24comparisons, остальные432browser observations сохранены. AZ12comparisons не повторялись. Shared/correction run38PASS. [Harness details](harness-correction.md). Console/pageerror/local network unexplained0; внешние fonts blocked, настоящие внешние сервисы не проверялись. Фикстуры/domain/M2M/locations/documents до/после совпали; сессии/новая fictional staff identity не входят в этот fingerprint.

## PNG / сохранность / пределы

[PNG manifest](png-manifest.json):76current native frames —36viewport,36полных drawer,4Place. Выборочно визуально открыты RU360 event, EN360 specialist drawer, AZ1440 event drawer; ручной просмотр каждого кадра не заявляется. Два prepatch RED PNG имели те же generated filenames и были перекрыты GREEN: отдельные current-run RED PNG не сохранились. RED observations JSON и неизменные13PNG PLAN bundle сохранены; это ограничение артефактов, не отдельное доказательство prepatch pixels текущего запуска.

[Preservation](preservation.json):33672entryfiles, changed только2approved existing apppaths; новый test — третий разрешённый файл. Остальные33670entryfiles без изменений/пропусков;74container IDs/names/ports/states и entry HTTP43482 argv/cwd сохранены. SharedMO/HEAD/branch/active_run unchanged. Старый процесс не перезапускался и не используется как current-source proof. Более ранние interruption/continuity NOT VERIFIED из предыдущих run сохраняются. После этого отчёта в guide добавляется только текущий статус.

При просмотре выявлен отдельный baseline: footer count остаётся русским в AZ/EN; existing fuzzy PO содержит другой placeholder total вместо count и не попадает в fresh MO. Это вне approved3files; PO не исправлялись. Передано в полный ACCEPT-08 для отдельного finding/плана, поэтому весь модуль этим отчётом не закрывается.

**NOT RUN:** полный ACCEPT-08 (следующий этап, один раз), global corpus/production/commit/push/deploy/module09, cross-browser/physical touch/screen reader/system select popup pixels. Никаких новых application fixes вне scope. Исторические MOD01–07 CLOSED LOCAL; закрыт только MOD08 в пределах описанных текущих проверок.
