# MOD-QA-12/13 — LOCAL PASS

2026-10-16, KidsMap module08. Пользователь одобрил [CSS plan](../mod-qa09-11-fix-2026-10-16-r1/findings/MOD-QA-12-PLAN.md) и [queue plan](../mod-qa09-11-fix-2026-10-16-r1/findings/MOD-QA-13-PLAN.md). Реализованы только3уникальных app/testfiles. [Approval](approval.json), [точный diff](approved-implementation.diff), [verification](verification.json), [final gate](final-gate.json).

## Снимок и изменения

Фактический /home/ramin/kidsmap, branch task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +dirtyWORKTREE, active_run:NONE. [Entry](entry.json). Не делались reset/clean/stash.

- MOD12: в static/admin/css/pages/kidsmap_changelist.css два legacy-селектора ограничены через #km-toast; unified title получил overflow-wrap:anywhere. Исчезли тёмный фон/тёмный текст, fixed44px и выход длинного названия за рамку. Legacy fallback сохранён.
- MOD13: только capacity branch show() в static/admin/js/kidsmap_notifications.js: таймер вытесняемого oldest отменяется, узел удаляется синхронно. MAX3 и нормальный dismiss220ms/duration/hover/API/modal сохранены.
- NEW scripts/tests/notifications_toast_capacity.test.cjs: исполнение настоящего движка с контролируемыми DOM/timers проверяет первые3, четвёртое/newest3, already-leaving с последующим таймером, rapid20+clearAll. Existing assertions не менялись.

## RED → GREEN и браузер

Точные команды/exits/durations: [commands.jsonl](commands.jsonl), первичный RED command/exit: [receipt](RED-receipt.json).

- Свежий Node RED:4tests,1PASS/3FAIL по timeout250ms, exit1 ([output](targeted-red.txt)); GREEN4/4PASS, exit0 ([output](targeted-green.txt)).
- Свежий actual browser RED: settled toast текст выходит за рамку ([result](RED-settled-toast-v2.js.result.json)); четвёртое уведомление не возвращает управление за1501ms, первые3рендерятся ([result](RED-toast-capacity-native.js.result.json)). Вход4notices явно SIMULATED; настоящий engine; закрыт только свой context.
- **341accepted native PASS,0FAIL**: [JSON](accepted-browser.json), [CSV](accepted-browser.csv). RU/AZ/EN×360/390/768/1024/1280/1440,18cells. В каждой4настоящих действия draft→published→draft→published **без ручного удаления уведомлений между действиями**.72успешныхPOST, длинное HTML-like/quotes/$& название, settled loading/success geometry/contrast≥4.5, escaping, max3, actual persisted state/reload.
- Loading response delay явно SIMULATED, затем пропущен настоящийPOST. Burst20 — SIMULATED inputs в настоящий неизменённый engine: newest3, без зависания. Keyboard Enter close и clearAll проверены во всех18cells.
- В390px каждогоязыка: native confirmation Tab/ShiftTab/focus; SIMULATED network abort с читаемымerror и возвратомbusy; hover дольше600ms удерживаетtimer, mouseleave запускаетнормальныйdismiss.6localdiagnostics ожидаемы:3abortrequestfailed+3ERR_FAILEDconsole. Другихlocalconsole/networkerrors0; внешниеfonts/resources явноblocked.
- Legacy fallback RU1440: SIMULATED отсутствие window.kmToast, но **2настоящихPOST** и настоящий #km-toastrenderer. Белый текст, originalfixed44px/layout, обеоперацииPASS ([result](legacy-fallback.js.result.json)). Итого74успешныхPOST и3SIMULATEDabort.
- PNG с SHA/dimensions: [manifest](PNG-manifest.json). Representative RU360/AZ1440 визуально просмотрены; всеPNG вручнуюнепросматривались. Первый RED helper ошибочно ожидалpublish при исходномpublished; исправлена толькоQAветкаconfirm/unpublish, сохранены обаoutputs.
- Syntax node --check и freshlocale verify exit0. Полный261Django и неизменённые13targeted не повторялись.

## Стенд, source, сохранность

Новый profile .tmp/mod-qa12-13-fix-2026-10-16-r1; собственные mod1213_fix_r1/test_mod1213_fix_r1, cache/media/private-media/fileemail/cookies, вымышленные данные. ExactownedPGID/loopback47955/dependencySHA проверены передreuse; существующиеDBнеизменялись. Свежие RU/AZ/EN PO собраны native в свойкаталог, manifest проверен, единственный LOCALE_PATHS доdjango.setup. .env/productioncredentials не загружались; socketguard толькоownPG, внешниебраузерныеобращенияblocked.

OwnHTTP45935/currentPID в server-current.json; [финальныйsource](runtime-source-final.json) подтверждает965hashes, actualtemplate/moduleorigins,testing иsolefreshMO. Сравнение с полным ACCEPT:956общихsourceнеизменны,5проверенныхизменений,4новыхtests;3POотдельнымmanifest покрыты MOD09/10 ([ledger](acceptance-source-ledger.json)).

[Preservation](preservation.json), [finalgate](final-gate.json): изменены2approvedexistingappfiles+statusguide; обратныйpatch восстанавливаетentrySHA, NEWtest несуществовалприentry. Остальныеfiles/sharedMO/HEAD/branch/active_runNONEсохранены.4entryQAHTTPпровереныпоPID/argv/cwd,74containersпоID/ports/state. Чужиестендынеостанавливались; перезапускалсятолькосвойновыйHTTP.

## Итог и границы

MOD12/13 CLOSED LOCAL; новыйподтверждённыйfinding не найден. Общий [ACCEPT-08 LOCAL PASS](../module08-accept-2026-10-16-r2/REPORT.md) сохраняет полный261run ипоследующиецелевыепроверки; историческиеFAILотчётынеизменены. Historical AZ UNKNOWN невыдаётсязаднимчисломзадоказаннуюпричину; свежийcapacityRED→GREENсамостоятелен.

NOT RUN: повторныйfull261, общийкорпусвсехмодулей, модуль09, cross-browser/physicaldevices/screenreader, отдельнаяstress/loadsuite, productionвэтойQAфазе. ПродакшенприёмканеподменяетсяLOCALPASS. Следующийразрешённыйшагпользователя: безопасныйGitpackage/push иserverrelease послеготовностимодуля; это отдельнаяфаза, секретывGit/отчётынекопировать.
