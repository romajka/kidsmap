# MOD-QA-08 — CONFIRMED OPEN / PLAN COMPLETE

**Последняя задача модуля08 подтверждена. Приложение не изменено.** [План на3файла](IMPLEMENTATION_PLAN.md), [двухфайловый candidate diff](proposed.diff), [source/candidate hashes, applied:false](proposal-manifest.json). Третий файл — новый regression test. Для реализации требуется отдельное одобрение scope.

## Текущий факт

Native RU/AZ/EN×Event/Specialist×390/1440: **12cells,42наблюдения —12source FAIL и30controls PASS**. У Event видна только категория, а status/start_datetime/owner отсутствуют. У Specialist select отсутствуют полностью, хотя сервер предоставляет status/is_active/consultation_format/specializations. С разными fictional категориями Event уже не буквально пустой: историческое описание уточнено по свежему evidence.

[Принятые наблюдения](native-accepted.json), [raw RU](native-ru-first.json), [AZ](native-az.js.result.json), [EN](native-en.js.result.json). Панель открывается клавиатурой; её count совпадает с исходной очередью. Существующий Event category selection→Apply→Reset работает, сохраняет q/sort и возвращает ожидаемые2/3records. [Перепроверенный category count](native-category-correction.js.result.json).

Причина source/baseline: общий `km_changelist_search_panel.html` использует whitelist полей мест. Существующие km_primary_filters Event/Specialist не участвуют в renderer. Фильтрация queryset на сервере работает; нужно вывести уже определённые choices, а не писать новые бизнес-фильтры. [Event contract](contract-event.json), [Specialist contract](contract-specialist.json), [Place control contract](contract-place.json).

## Предлагаемое исправление

Только2existing appfiles +1NEWtest:

- `src/catalog/templatetags/admin_dashboard_tags.py`: normalized drawer groups из actual filter_specs с порядком km_primary_filters для Event/Specialist; Place legacy branch сохраняется. Status chips разрешаются для Event/Specialist, без изменения Place exclusions.
- `src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html`: отобразить группы и связать labels/select, скрыть пустой quality block и неверную подсказку о единственном status-control у Event/Specialist. Search hidden params, counts, кнопки, data attrs и классы сохраняются.
- `src/catalog/testcases/test_mod08_filter_drawer.py`: новый actual-response/choiceURL/count/chip/reset/Place regression contract; сначала RED, затем GREEN.

JS/CSS/PO/ModelAdmin/list_filter/schema/ACL не меняются. Сохраняется существующая навигация при изменении select. Candidate лежит только внутри QA bundle, к runtime не подключался; Python candidate syntax checked, это не postpatch validation.

## Snapshot и изоляция

Actual `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, `active_run: NONE`. [Entry](entry.json), [profile](profile-reuse.json). Старые LOCAL PASS не являются production evidence.

Создана **новая собственная DB `mod08_plan_r1`** на проверенном own PostgreSQL.2fictional users,3Event с разными category/date/status/owner,3Specialist с разными status/active/format/directions,2Place для shared controls. Старые fixtureDB не использовались для браузерных действий этой задачи. Собственные HTTP/cache/media/private-media/email/venv/locales. DJANGO_TESTING=1, env cleared before setup; checkout.env/production credentials не загружались. Backend egress только own PG, browser только own origin.

Свежие RU/AZ/EN PO собраны через isolated helper, manifest проверен до django.setup, soleLOCALE_PATHS и actual opened projectMO подтверждены.960appsource files и template/module origins работающего PID совпадают с диском и entry hashes. Shared MO не изменены. [Runtime](runtime-info.json), [source](runtime-source-final.json), [locale manifest](locale-manifest.json).

Все проверки GET-only; full-field Place/Event/Specialist, M2M directions, locations/documents fingerprint unchanged. Sessions/lang менялись через fictional login, неизменность всех таблиц не заявляется. [Before](domain-before.json), [after](domain-final.json).

Graph-first: root/project verified, начальная generation2026-10-16T07:47:10Z; relevant tag/test paths дополнительно проверены generation2026-10-16T08:20:58Z. Metadata match — подсказка, не completeness proof. Dynamic ModelAdmin/filter_specs/choices проверены непосредственно в source/runtime. Graph data/cache не сохранялись в repo. Роли frontend-admin/Django/browser выполнялись последовательно одним lead, independent review не заявляется.

## QA-helper correction

RawRU имел4sourceFAIL +1ошибочный QA-countFAIL. Public query middleware правильно убирал query у временного /qa/filter-contract/; helper получал unfiltered3 вместо filtered2. **Application middleware/assertions не менялись.** Только own helper перенесён под /api/qa/mod08/filter-contract/, сохраняющий query; endpoint остаётся TESTING/loopback/read-only. Перепроверен только1failedcontrol, получены2records и правильные q/sort. Остальные completed controls не повторялись. [Correction note](harness-correction.md), исходный FAIL сохранён, [replacement PASS](native-category-correction.js.result.json).

## Прерывание среды и сохранность

Подготовка прервалась до HTTP/browser evidence; её незавершённому prepare exit присвоен UNKNOWN, PASS из него не принят.4entry HTTP исчезли, own PG наблюдался exited. Чужие HTTP не перезапускались. После проверки точного container ID/loopback port запущен только свой PG; PostgreSQL выполнил recovery. Новая own DB сохранилась с166migrations и0users/events/specialists; продолжены только её оставшиеся schema/seed steps, итог175migrations. [Interruption](interruption.json), [read-only recovery counts](db-recovery-counts.json), [prepare](prepare.txt). Два ранних readiness отказа означали startup PG, не application finding; подготовка возобновлена после accepting-connections.

Сейчас74container ID/ports/states совпадают с entry, но непрерывность работы через interruption **NOT VERIFIED**.4старых HTTP остаются absent; foreign restart не выполнялся. Свой HTTP поднят заново на проверенном свободном порту; helper correction перезапускала только его.

**33585entryfiles unchanged**, missing0; единственное изменение вне нового QA bundle — собственная status note guide. Application changes0,960source hashes unchanged; HEAD/branch/active_run сохранены. [Preservation](preservation.json). Сохранность чужих данных через прерывание не выводится из совпадения current container states; подтверждён только ограниченный domain snapshot новой own DB во время recheck.

## Команды и ограничения

[Commands/exits/durations](commands.jsonl): create-owned-db/build/verify exit0; первый prepare interrupted/UNKNOWN; start-resume prepare/runtime-info exit0. CLI native-ru/az/en exit0, semanticFAIL отдельно; targeted correction exit0/1PASS. Candidate compile и git diff check PASS, `verify.py` exit0 означает PLAN gate, не исправленный ID. Небольшая опечатка `else13` в собственном verify.py исправлена до gate; source assertions не менялись.

13PNG с SHA256/размерами: [manifest](png-manifest.json), Specialist EN390 визуально просмотрен. **0local console/page/network/HTTP errors**; external font requests явно blocked и отдельно диагностированы.

**NOT RUN:** patch, новые backend RED/GREEN, candidate browser feasibility, postpatch36cells, full module08/global/production/commit/push/deploy/module09. После approval — только targeted проверки новой причины и representative shared guards. После завершения последней задачи — полный ACCEPT-08 один раз по guide; общая приёмка всех модулей отдельно. Новых закрытых ID этим PLAN нет.
