# SOCIAL-QA-05 — CLOSED LOCAL, scoped CSS acceptance

2026-10-17, Asia/Baku. Пользователь одобрил [конкретный однофайловый план](../social-qa05-recheck-2026-10-17-pc-r1/IMPLEMENTATION_PLAN.md) сообщением «одобряю». Применён ровно proposed.diff: **только static/css/site.css**, page-specific grid из двух minmax(0,1fr) колонок и одной при≤760px. Переполнение author768 устранено во всех RU/AZ/EN: documentWidth822→768. SOCIAL01–05 CLOSED LOCAL в записанных scopes; **module09 остаётся OPEN**.

Отдельное существующее расхождение заголовка Activity сохранено OPEN/P3, без исправления:9shared checks FAIL до и после CSS. Оно не переклассифицировано в PASS и не отменяет проверенный результат ограниченного SOCIAL05. [Подробности и границы](ADJACENT_OBSERVATION.md).

## Что изменено и почему

Generic grid с минимумами220/260/200px раздувала форму с двумя полями до708px. Новый override внутри .site-reviews-page убирает лишний track и жёсткие минимумы. Остальные consumers generic grid, overflow rules, templates/JS/controller/models/schema/PO и existing test assertions не изменены. Body overflow-x:hidden уже существовал; новый код не маскирует расширение страницы clipping/zoom/transform.

[Applied diff](applied.diff), [approval](approval.json), [approved checklist](implementation-checklist.md), [entry](entry.json), [final source](source-final.json). Normalized after SHA совпадает с candidate manifest.1021source/PO проверены: ровно один изменённый файл, остальные1020 побайтно прежние, включая dirty SOCIAL03–04.

## RED → GREEN

Неизменившийся свежий RED из PLAN сохранён и использован без полного повторения:36cells,324controlPASS,210layoutPASS/24layoutFAIL в3author768cells; три existing backend baseline methods PASS. [RED reference/hash](red-reference.json), [исторический PLAN report](../social-qa05-recheck-2026-10-17-pc-r1/REPORT.md). Перед patch исходники и live origin сверены; bootstrap mount guard и точный порядок его retry описаны ниже.

После patch новый Chromium155.0.8059.12 context/session social05-pc-fix-r1, actual CSS200/source hash, template origin и sole fresh locales подтверждены. Outcome assertions прежние; добавлено ожидание finite animations, без ослабления геометрии.

| Fresh post-patch проверка | Результат |
|---|---|
| Author/guest ×RU/AZ/EN ×360/390/768/1024/1280/1440 |36cells,324controlPASS/234layoutPASS/0FAIL|
| Author ×RU/AZ/EN ×760/761 |6cells,54controlPASS/54layout+trackPASS|
| Native form/sort/focus, submit/reload, vote/reload и guards |17rows/147PASS|
| SIMULATED submit delay/abort |1row/8PASS|
| Shared Place/Activity/Specialist/Event ×RU/AZ/EN ×390/768/1440 |36cells,243PASS/9existing Activity-headingFAIL|
| SIMULATED original-CSS baseline, только9 Activity cells |36parityPASS; те же9heading failures reproduced|
| Existing affected backend methods |3unique PASS,0F/0E,0.355s,exit0|
| Native PNG |111|
| Captured unhandled pageerrors во всех группах |0|

Факты: [matrix](matrix.json), [boundary](boundary.json), [actions](actions.json), [submit transport](submit_transport.json), [shared raw FAIL](shared.json), [original CSS parity](shared_baseline.json), [backend](baseline.log), [PNG manifest](png-manifest.json). Две request failures — намеренные SIMULATED abort до доставки серверу; baseline matrix/boundary/shared не имеют unexpected HTTP failures. Actual API400/401/403 — ожидаемые guard outcomes, не успешные200.

На390/768/1440 во всех языках native GET sort=likes менял выбранное значение и порядок карточек. Нажатие звезды4 меняло hidden rating и четыре active stars.80символьное имя и длинный multilingual textarea text не расширяют форму. Tab name→textarea и focus indicator проверены, выполнены реальные scroll и viewport screenshots карточек/формы после finite animations.

Native POST свежего fictional автора создал ровно один pending SiteReview rating4/name80; success live status и скрытие composer подтверждены. После reload public projection содержит только прежние2approved reviews, pending отсутствует публично и сохраняется в БД. Native like на чужом отзыве меняет UI/counter/reaction record; reload сохраняет состояние. Own buttons disabled и server403, guest native auth toast/API401 для vote/submit, invalid value400 и invalid CSRF403 без записей.

SIMULATED vote и submit transport удерживался до наблюдения busy/disabled состояния, затем прерывался до server delivery. Проверены error feedback, возврат управления, сохранение ввода для submit, неизменность DB и ровно один запрос без auto retry. SIMULATED outcomes явно отделены от actual business POST.

Вручную просмотрены native form RU768, cards RU390 и SIMULATED submit error RU390. Это проверка этих кадров; full WCAG/всех состояний/всех offscreen элементов не заявляется.111PNG — native captures, без композитов или подрисовки.

## Изоляция и сохранность

C:\kidsmap, LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36, branch codex/module09-transfer-2026-10-16-r1; task33-progress e4e05cc213b34e2d771ecb854901bfd016d1db51. Index tree881e0c48c7d557c46221beb3b2410a157982f861 и staged diff empty, active_run:NONE, .cbmignore/sharedMO/старые dirty application файлы сохранены.

Один lead последовательно выполнил frontend/browser/Django checks, без независимых subagents. TDD использует сохранённый native RED→реальный post-patch GREEN; новый app test не добавлялся для CSS-only scope. Existing backend assertions не менялись.

Новый собственный m09s05-fix-r1-app, internal network m09s05-plan-r1-net, repository bind RO и только новый scratch RW. Повторно использован проверенный собственный fictional PG m09s05-plan-r1-pg/DB; post-patch testDB отдельная test_m09s05_fix_r1. Python3.12.15/Django6.0.2/PG17.11. Очищенный env/DJANGO_TESTING=1 до setup, без .env/production credentials; отдельные cache/media/private-media/locmem email. Fresh RU/AZ/EN MO собраны из текущих PO и проверены до каждого setup, sole LOCALE_PATHS, sharedMO не пересобирались. Localhost-only browser/external blocked; реальный password/OAuth NOT RUN.

Loopback33326 и отдельный hidden WSL proxy принадлежат этому run. Для QA-only reviewer role/aggregate state после baseline перезагружен только собственный serve PID, проверенный по exact runtime.py path; контейнеры и чужие процессы не перезапускались. При final snapshot сохранены IDs/states всех34entry containers, добавлен только один свой app. Foreign restart commands0; whole-machine process continuity **NOT VERIFIED**.

Сохранены все81файл предыдущего PLAN05, включая его OPEN report/diff/verification, и43/181/149/212manifest entries предыдущих PC runs. Новая guide note добавлена отдельно; прежние байты восстанавливаются удалением только этой note. [Preservation](preservation.json).

## Зафиксированные попытки и соседнее наблюдение

Первый bootstrap guard ошибочно ожидал RW mount всей .tmp, тогда как прежний app монтирует RW только свой PLAN scratch; entry ещё не создавался. После первоначального source/live proof и exact apply-check одобренный CSS hunk был применён; locale build завершился0. Retry проверил actual narrow mount и exact candidate after SHA; entry baseline взят из сохранённого PLAN, все1020прочих source hashes совпали. Для нового scratch создан отдельный собственный app с узким RW mount. Отказ guard не обойдён расширением прав прежнего контейнера.

Первый запрос до ready Django дал RemoteDisconnected/CLI ERR_EMPTY_RESPONSE; после readiness source/soleMO подтверждены. После преднамеренного own serve helper reload Windows metadata probe также опередил готовность и получил WinError10053; actual actions затем завершились147PASS. Restart чужих сервисов не применялся.

Shared smoke сохранил243PASS/9FAIL: controller target_name получает str(Activity), отображая Activity object (1). Original JSON/raw CLI сохранены. Formatter additionally raised KeyError id после записи shared.json; исправлен только diagnostic formatter, shared suite не повторялся.9affected Activity cases отдельно открыты с SIMULATED original site.css в transport: original normalized SHA совпадает с PLAN baseline, те же9заголовков воспроизводятся. Source/controller/model hashes прежние. Product assertions не ослаблялись; Activity app code не менялся. Graph coverage для новых cited paths unavailable/metadata_changed; вывод проверен source и native parity, reindex не выполнялся.

Некоторые первоначальные read-only literal searches включали отсутствующие предполагаемые пути; actual source найден в base.html/catalog_structure.py. Все существенные failed attempts и исправления QA orchestration: [attempts.json](attempts.json), [commands](commands.md).

## Граница результата

**SOCIAL05 CLOSED LOCAL в одобренном CSS scope.** Existing ADJ-ACTIVITY-TITLE/P3 OPEN; [отдельное наблюдение](ADJACENT_OBSERVATION.md) для будущего решения. Shared smoke не объявляется полностью зелёным. Никаких исправлений Activity или SOCIAL06 в этом запуске.

Full ACCEPT09/global corpus/SOCIAL06–09/module10/physical/other browsers/real screenreader/full WCAG/real external integrations/production/commit/push/deploy **NOT RUN**.3backend methods выполнены один раз post-patch; это те же3метода pre-patch, не6unique и не полный corpus. Без reset/clean/stash/смены dirty checkout.

Следующий шаг — отдельный PLAN SOCIAL-QA-06 по поручению пользователя. Full ACCEPT09 один раз после очереди исправлений, global отдельно. [Verification](verification.json), [artifact manifest](artifact-manifest.json), [next prompt](next-prompt.txt).
