# MOD-QA-07 — CLOSED LOCAL

Исправлены все подтверждённые причины MOD-QA-07 в согласованной области: сводка больше не дробит HTML на символы, ссылки переводят фокус к полям, заголовок и список читаются на телефоне. Это локальный результат. Полная приёмка модуля08 и production ещё не проверялись.

## Одобрение и snapshot

Пользовательское «да», 2026-10-16, одобряет [CSS_SUPPLEMENT_PLAN](../mod-qa07-fix-2026-10-16-r1/CSS_SUPPLEMENT_PLAN.md); [зафиксированное одобрение](APPROVAL.md). Предыдущая трёхфайловая правка уже выполнена и повторно не согласовывалась.

Actual checkout `/home/ramin/kidsmap`; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, `active_run: NONE`. [Полный входной снимок](entry.json). Старые отчёты и незакоммиченные изменения сохранены; LOCAL PASS не означает production PASS.

## Изменение

Только `static/admin/css/pages/specialist_form.css`: две scoped rules для `[data-specialist-errors]` внутри страницы специалиста. Сводка получила блочное расположение, заголовок — размер1rem и нормальные отступы. Заголовок располагается над сообщениями, а не сжимается рядом с ними. [Точный diff](implementation.patch).

JS, шаблон, серверная валидация, права, PO и схемы не менялись в этом дополнении. Все исходники предыдущей правки и тестов совпали: из960source files изменился только этот CSS,959неизменны.

## RED → GREEN и проверки

Свежий RU390 до CSS: **1ожидаемый source FAIL и5контрольных PASS**. Заголовок дробился на много строк; сообщения, фокус, отклонение сохранения и данные уже работали. [RED JSON](native-red.js.result.json), отдельный RED PNG.

После применения точного candidate: **128новых actual native PASS,0FAIL**. Из них108проверок на18сочетаниях RU/AZ/EN×360/390/768/1024/1280/1440: настоящий Save с неверной формой и принятием native confirm, заголовок не более2строк, список ниже, отсутствие горизонтального обрезания, одно целое сообщение, сохранённый ввод, Enter→видимый чекбокс и неизменность данных. [RU36](native-ru.js.result.json), [AZ36](native-az.js.result.json), [EN36](native-en.js.result.json).

Ещё20проверок — только representative RU390/EN1440: несколько ошибок и ошибка вложенной формы, фокус обычного поля и inline price, длинный экранированный текст, отсутствие HTML injection/частичного сохранения, обычная перезагрузка и навигация разделов. [Shared sample](native-shared.js.result.json). Новых simulated cases или injected styles нет: проверялся реальный CSS приложения.

**Предыдущие5backend methods и184browser checks не перезапускались.** Их PASS сохранены по неизменным исходникам и hashes evidence; в прежних184есть2явно SIMULATED checks, они не объявляются actual. [Retained evidence](retained-core-evidence.json), [предыдущий core REPORT](../mod-qa07-fix-2026-10-16-r1/REPORT.md). Его исторический OPEN из-за CSS сохраняется как история; текущий отчёт закрывает дополнение.

23PNG с размерами/SHA256: [manifest](png-manifest.json). Визуально просмотрен AZ360 после правки. **0local console/page/network/HTTP errors**; внешние fonts requests явно заблокированы, соответствующие external diagnostics сохранены отдельно.

## Изоляция и исходники работающего процесса

Собственная вымышленная DB `mod07_plan_r1` повторно использована только после проверки принадлежности, PostgreSQL ID/порта и исходников. Без migrate/reseed этой DB. Отдельные HTTP/cache/media/private-media/email/venv/locales созданы для текущего запуска. DJANGO_TESTING=1; checkout.env не загружался, production credentials не использовались; backend egress ограничен own PostgreSQL, browser — own origin. [Profile](profile-reuse.json), [runtime info](runtime-info.json).

RU/AZ/EN PO текущего checkout собраны через scripts/build_isolated_locales.py в новый каталог. Manifest проверен **до django.setup**, единственный LOCALE_PATHS указывает на own root; actual opened project MO, template origins, PID и960source hashes сверены. Shared MO не изменены. [Manifest](locale-manifest.json), [live source](runtime-source-final.json).

## Команды и сохранность

[Точные команды, exits и durations](commands.jsonl): locale build/verify/runtime-info exit0; native-red CLI exit0 с отдельно подтверждённым semantic FAIL1; native-ru/az/en/shared exit0 с36/36/36/20PASS. `git diff --check` и `final_gate.py` exit0. Backend command в этом CSS-запуске отсутствует намеренно. [Финальный gate](final-gate.txt), [verification](verification.json).

Входные **33502файлов неизменны**, missing0. Из existing files изменён только одобренный CSS и собственная status note в guide. **3entry QA HTTP сохранили PID/argv/cwd,74контейнера — ID/порты/состояние.** HEAD/branch/active_run unchanged. [Preservation](preservation.json). Ранние ограничения continuity из MOD06 не отменяются этим текущим снимком.

Full-field fingerprint Specialist, M2M specializations, locations, documents, Place/Event совпадает до/после и с предыдущим core run. Это ограниченная проверка доменных данных, не всех таблиц: fictional login меняет sessions/language. [Before](domain-before.json), [after](domain-final.json).

## NOT RUN и следующий шаг

Успешные изменения записей, удаления, запись приватных документов, physical devices/non-Chromium не выполнялись. Полный module08 будет один раз после его последней задачи MOD-QA-08; общая приёмка всех модулей отдельно. MOD08 требует своего свежего PLAN, приложение по нему не исправлялось. Module09, production, commit/push/deploy не запускались.
