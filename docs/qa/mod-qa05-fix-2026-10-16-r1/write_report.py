from pathlib import Path
import json,hashlib
h=Path(__file__).resolve().parent;r=h.parents[2];v=json.loads((h/'verification.json').read_text());p=v['preservation'];guide=r/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';entry=json.loads((h/'entry.json').read_text());before=guide.read_bytes();assert hashlib.sha256(before).hexdigest()==entry['files'][str(guide.relative_to(r))]
note=f"- Module08 MOD-QA-05 **CLOSED LOCAL**, 2026-10-16: [scoped REPORT]({h.name}/REPORT.md), [verification]({h.name}/verification.json). Approved one-line row-trigger focus fix; fresh native RED BODY →159native GREEN observations, RU/AZ/EN×6widths,45PNG. Initial HTML focus/trap retained; warning/danger Escape+Cancel restore visible same trigger; shared view/menu sample PASS. Domain unchanged;2entry QA HTTP/74containers preserved; HEAD/branch/active_run unchanged. MOD06–08 OPEN; full ACCEPT08 once after tasks, global separately. No production/commit/push/deploy/module09.\n\n"
marker='## Сколько задач осталось и как идти';assert marker in before.decode();after=before.decode().replace(marker,note+marker,1);guide.write_text(after);assert guide.read_text().replace(note,'',1).encode()==before
(h/'status-note.json').write_text(json.dumps({'path':str(guide.relative_to(r)),'before':hashlib.sha256(before).hexdigest(),'after':hashlib.sha256(guide.read_bytes()).hexdigest(),'only_inserted_note':True},indent=2));p['changed_entry_files'].append(str(guide.relative_to(r)));p['unchanged_files']-=1;(h/'preservation.json').write_text(json.dumps(p,indent=2))
report=f'''# MOD-QA-05 — CLOSED LOCAL

Одобренный план: `../mod-qa05-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md`. User approval «дальше», 2026-10-16; [APPROVAL](APPROVAL.md). Один app file, одна добавленная строка. Отдельный свежий scoped запуск, не полная приёмка модуля08.

## Snapshot и причина

`{r}`, HEAD `{v['head']}`, branch `{v['branch']}`, dirty WORKTREE, `active_run: NONE`. Полный entry status/hashes — [entry.json](entry.json). Исторические module07/08 результаты не означают production PASS.

После закрытия dropdown активный пункт скрывался. kmModal запоминал BODY/скрытый пункт, поэтому после закрытия confirmation фокус не возвращался на кнопку строки. Свежий native RED: **1 source FAIL /5control PASS**; actual BODY, исходная кнопка visible/hit. Initial HTML focus и wrap Tab/ShiftTab уже работали. [RED JSON](native-red.js.result.json).

## Изменение

`static/admin/js/kidsmap_place_changelist.js`: после `closeRowActions()` добавлено `trigger.focus({{preventScroll: true}})`. Существующий modal engine теперь запоминает видимый opener и сам возвращает фокус. [Точный patch](implementation.patch), entry source сохранён. Общий notifications engine, AJAX/loading/undo/endpoints, PO и данные не изменены.

## Проверки

**159 native PASS /0FAIL:**156 observations RU/AZ/EN×360/390/768/1024/1280/1440 плюс3 shared observations. В18cells — initial HTML button focus, wrap Tab/ShiftTab, Escape, visible focus style/hit, reopen→Cancel, reload. В6representative cells390/1440 — danger confirmation Escape/Cancel; удаления не выполнялись. Отдельно native menu Escape и переход по view link на ожидаемую публичную карточку. Все подтверждения отменены.

[RU](native-ru.js.result.json), [AZ](native-az.js.result.json), [EN](native-en.js.result.json), [shared](native-shared.js.result.json). **0local console/page/network/HTTP errors**; внешние font requests explicitly blocked, их ошибки сохранены отдельно как external. PNG **45** с размерами/SHA256: [manifest](png-manifest.json). Визуально проверен return-ru-390: контур на исходной кнопке строки.

Команды с аргументами/exits/counts: [commands.jsonl](commands.jsonl). `start.py`: fresh native RU/AZ/EN locale build/verify, exit0; `/qa/source/`958files current process matches disk. `drive.py native-red.js red`: exit0 означает исполнение, semantic RED отдельно; каждый GREEN drive exit0,52/52/52/3PASS. `node --check static/admin/js/kidsmap_place_changelist.js`, `git diff --check`, `final_gate.py`: exit0. Backend suites для однострочного DOM focus patch не повторялись.

## Изоляция и сохранность

DJANGO_TESTING=1; reused verified own fictional PostgreSQL ID совпадает с первичным docker-start.txt; без migrate/reseed/prepare. Свои HTTP/cache/media/private-media/email/venv/locales. Не загружен checkout .env; egress только ownPG, browser толькоownorigin. Manifest проверен **до django.setup**, soleLOCALE_PATHS ownroot, фактически открытые RU/AZ/EN MO только ownroot. [runtime-info](runtime-info.json), [source](runtime-source-final.json), [profile](profile-reuse.json).

Place/Event/Specialist counts4/3/3 и fullfield fingerprint до/после совпадают. Это не hash всех таблиц: authsession/language менялись локальным входом. [domain](domain-final.json).

Сохранены **{p['unchanged_files']}** entryfiles, отсутствующих0; изменены только одобренный JS и эта status-note guide. SharedMO unchanged. **2** entry QA HTTP сохраняют pid/argv/cwd; **74**контейнера — те же ID/ports/state. HEAD/branch/active_run unchanged. [preservation](preservation.json). Старые ограничения continuity предыдущих запусков остаются историческими и этим результатом не отменяются.

## NOT RUN

Полный module08 — один раз после его задач. Global/production/commit/push/deploy/module09, physical devices/non-Chromium не выполнялись. Реальные unpublish/delete submissions не проверялись: цель этого scope — focus/cancel. Optional simulated fallback-icon test не запускался; использован actual sprite renderer. MOD06 i18n и MOD07–08 остаются OPEN, новые scope требуют своих планов.
'''
(h/'REPORT.md').write_text(report);(h/'next-prompt.txt').write_text('Продолжить module08 с PLAN MOD-QA-06 из guide. MOD-QA-05 CLOSED LOCAL: '+str(h/'REPORT.md')+'. Новый scope сначала fresh recheck/implementation plan и approval. Только targeted checks после исправления, полный module08 один раз после всех задач. Preserve dirty/active_run/stands; no commit/push/deploy/production/module09.\n')
print('Report and single guide status note saved')
