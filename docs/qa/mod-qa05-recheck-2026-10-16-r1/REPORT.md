# MOD-QA-05 — PLAN COMPLETE / CONFIRMED OPEN

2026-10-16, `/root`, canonical kidsmap-orchestrator/frontend-admin/browser-qa последовательно, без независимых агентов. Stage PLAN ONLY, приложение для MOD05 не менялось. `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +dirty WORKTREE, active_run NONE. [Snapshot](snapshot.json), [current source](runtime-source-final.json), [verification](verification.json).

Использован только проверенный свой MOD04 profile: DJANGO_TESTING=1, fictional domainDB/owncache/media/private-media/file-email, отдельный current ownHTTP34827, source958MATCH; текущие свежие own RU/AZ/EN MO/soleLOCALE_PATHS verified. Env/production credentials не загружались, внешние ресурсы blocked. Setup/DB/полные старые suites повторно не запускались; lifecycle операций в этом recheck нет.

Свежий native sample RU/AZ/EN×390/1440: **20controlPASS/6sourceFAIL**,12PNG; RU390 modal PNG просмотрен визуально, не все12. [Browser JSON](native-recheck.js.result.json), [commands/exits](commands.jsonl), [PNG manifest](png-manifest.json). Опубликованный fictional Place→more keyboard Enter→снять с публикации→initial focus→Tab/ShiftTab→Escape. Все confirmations отменены; domain before/after unchanged,0local diagnostics.

**Уже работает:** initial focus на настоящей BUTTON, first/last wrapping Tab/ShiftTab. Историческая причина SVG use/нефокусируемого первого элемента не воспроизводится: getFocusableElements уже использует a[href] и фильтрует tabindex/disabled/visibility; focusWhenVisible ждёт готовность. Общий engine не нужно переписывать по старому FAIL.

**Осталось:** после Escape activeElement BODY во всех6samplecells. Исходная row more-button видна, находится в viewport и получает pointer hit, но focus не возвращается. Handler сохраняет trigger, затем closeRowActions скрывает активный menu item, после чего kmModal запоминает BODY/скрытый элемент. Current close visibility/generation guards работают по своему контракту, возвращать фокус им некуда.

[Предложенный план](IMPLEMENTATION_PLAN.md) — **один app file/одна строка**, [готовый diff](proposed.diff), [source/candidate hashes](proposal-manifest.json). В `static/admin/js/kidsmap_place_changelist.js` после row-handler closeRowActions добавить `trigger.focus({preventScroll: true});` до открывания confirmation. Modal получит правильный текущий opener автоматически. Source hash совпадает; candidate не применён.

Это минимальный scope оставшейся причины. Warning и danger confirmations этого row-handler получают правильный trigger; loading/AJAX/actions/PO/vendor/общий modal engine не меняются. Переводы отдельного MOD06 не входят. Meaningful regression — тот же actual browser trigger BODY→GREEN; backend-тест строки JS не нужен. После approval проверить18targetcells и несколько representative shared cancellation/menu guards; старые полные CSS/search/sort/columns/modal наборы не повторять.

P2 CONFIRMED OPEN. NOT RUN: patch/postpatchGREEN, полный18cellacceptance (планирование проверило6representativecells), настоящий unpublish/delete/confirm (всё отменено), full module08/global/production/commit/push/deploy/module09. Dead-code/cleanup не предлагались. Existing files/stand не изменялись этим PLAN; его source guard сравнивает весь current958-file snapshot.

Следующий шаг — отдельное approval этого one-file/one-line плана. После одобрения тот же scope повторно не согласовывать.
