# MOD-QA-05 — CLOSED LOCAL

Одобренный план: `../mod-qa05-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md`. User approval «дальше», 2026-10-16; [APPROVAL](APPROVAL.md). Один app file, одна добавленная строка. Отдельный свежий scoped запуск, не полная приёмка модуля08.

## Snapshot и причина

`/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, `active_run: NONE`. Полный entry status/hashes — [entry.json](entry.json). Исторические module07/08 результаты не означают production PASS.

После закрытия dropdown активный пункт скрывался. kmModal запоминал BODY/скрытый пункт, поэтому после закрытия confirmation фокус не возвращался на кнопку строки. Свежий native RED: **1 source FAIL /5control PASS**; actual BODY, исходная кнопка visible/hit. Initial HTML focus и wrap Tab/ShiftTab уже работали. [RED JSON](native-red.js.result.json).

## Изменение

`static/admin/js/kidsmap_place_changelist.js`: после `closeRowActions()` добавлено `trigger.focus({preventScroll: true})`. Существующий modal engine теперь запоминает видимый opener и сам возвращает фокус. [Точный patch](implementation.patch), entry source сохранён. Общий notifications engine, AJAX/loading/undo/endpoints, PO и данные не изменены.

## Проверки

**159 native PASS /0FAIL:**156 observations RU/AZ/EN×360/390/768/1024/1280/1440 плюс3 shared observations. В18cells — initial HTML button focus, wrap Tab/ShiftTab, Escape, visible focus style/hit, reopen→Cancel, reload. В6representative cells390/1440 — danger confirmation Escape/Cancel; удаления не выполнялись. Отдельно native menu Escape и переход по view link на ожидаемую публичную карточку. Все подтверждения отменены.

[RU](native-ru.js.result.json), [AZ](native-az.js.result.json), [EN](native-en.js.result.json), [shared](native-shared.js.result.json). **0local console/page/network/HTTP errors**; внешние font requests explicitly blocked, их ошибки сохранены отдельно как external. PNG **45** с размерами/SHA256: [manifest](png-manifest.json). Визуально проверен return-ru-390: контур на исходной кнопке строки.

Команды с аргументами/exits/counts: [commands.jsonl](commands.jsonl). `start.py`: fresh native RU/AZ/EN locale build/verify, exit0; `/qa/source/`958files current process matches disk. `drive.py native-red.js red`: exit0 означает исполнение, semantic RED отдельно; каждый GREEN drive exit0,52/52/52/3PASS. `node --check static/admin/js/kidsmap_place_changelist.js`, `git diff --check`, `final_gate.py`: exit0. Backend suites для однострочного DOM focus patch не повторялись.

## Изоляция и сохранность

DJANGO_TESTING=1; reused verified own fictional PostgreSQL ID совпадает с первичным docker-start.txt; без migrate/reseed/prepare. Свои HTTP/cache/media/private-media/email/venv/locales. Не загружен checkout .env; egress только ownPG, browser толькоownorigin. Manifest проверен **до django.setup**, soleLOCALE_PATHS ownroot, фактически открытые RU/AZ/EN MO только ownroot. [runtime-info](runtime-info.json), [source](runtime-source-final.json), [profile](profile-reuse.json).

Place/Event/Specialist counts4/3/3 и fullfield fingerprint до/после совпадают. Это не hash всех таблиц: authsession/language менялись локальным входом. [domain](domain-final.json).

Сохранены **33037** entryfiles, отсутствующих0; изменены только одобренный JS и эта status-note guide. SharedMO unchanged. **2** entry QA HTTP сохраняют pid/argv/cwd; **74**контейнера — те же ID/ports/state. HEAD/branch/active_run unchanged. [preservation](preservation.json). Старые ограничения continuity предыдущих запусков остаются историческими и этим результатом не отменяются.

## NOT RUN

Полный module08 — один раз после его задач. Global/production/commit/push/deploy/module09, physical devices/non-Chromium не выполнялись. Реальные unpublish/delete submissions не проверялись: цель этого scope — focus/cancel. Optional simulated fallback-icon test не запускался; использован actual sprite renderer. MOD06 i18n и MOD07–08 остаются OPEN, новые scope требуют своих планов.
