# Административная карта места — завершение локальных исправлений

2026-10-09. Авторизация: пользователь «исправь все что осталось, если опять что-то найдёшь — исправь». Один `/root`, kidsmap-orchestrator последовательно, без независимых подагентов. Scope: CE-C-03/04 и подтверждённые связанные дефекты локации административного места. [План](../superpowers/plans/2026-10-09-admin-place-map-fallback.md). **Все подтверждённые дефекты в выполненном scope исправлены локально. Полный sign-off проекта не заявляется.**

## Срез, изоляция и сохранность

LOCAL HEAD `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, branch `task33-progress`, dirty WORKTREE. Source/runtime SHA `aba704c7f1b63588abcea683f3f713cfff6081a6f92d7949860313ee522771f2`,2769 файлов. Исходный manifest2768 расширен существующим regression script `scripts/test_location_resolution.cjs`; его прежние bytes сохранены отдельно. Проверка каждого исходного hash при startup и упаковке. [Evidence/version](admin-place-map-fix-2026-10-09/evidence.json), [собственный diff](admin-place-map-fix-2026-10-09/local.diff), [WORKTREE](admin-place-map-fix-2026-10-09/worktree-status.txt).

Только isolated http://localhost:8790/qa/ : DJANGO_TESTING=1, PostgreSQL kidsmap-reacceptance-20261009 с network=none и без DB-портов; synthetic fixture данные, LocMem cache/email, отдельные media/private-media, очищенное окружение, network/libpq guards. Unit tests используют другую disposable DB. Перезапуск только собственного8790 с проверкой PID/cmdline;8788 сохранён. Production/commit/push/deploy не выполнялись.

Изменены14 файлов:3 templates,3 JS,1 CSS,6 PO/MO и1 существующий JS regression script. Остальные source files побайтно сохранены; прочие строки переводов, context/plural и metadata сохранены. Python/models/schema/migrations/ACL/canonical publication/ownership не менялись. Исторические QA отчёты не переписаны. Новые решения добавлены в журнал и MASTER_AUDIT.

## Исправления и свежие RED

Роль: demo_moderator. Основные URL: `/admin/catalog/place/154/change/` для responsive/keyboard, `/admin/catalog/place/155/change/` для negative/CAS/moderation. Все карточки вымышленные.

| Дефект | До исправления, свежий RED | Исправление и проверка |
|---|---|---|
| CE-C-03 P3, активная кнопка карты без SDK | Enter ничего не делает, панель hidden | Local JS подключается независимо от external SDK; Enter/Space открывают ручные координаты, unavailable объяснён |
| CE-C-04 P3, mobile clipping | Все3 подписи выходят за границы кнопок на390; Range/DOM и PNG подтверждают | Mobile stack, auto height/min44, wrapping и видимый focus outline; проверяются внутренние текстовые границы, не только document overflow |
| «Ввести вручную» скрывает открытые поля | Handler toggled hidden вместо явного открытия | Всегда показывает поля и фокусирует latitude; повтор и Tab до longitude PASS |
| Ошибка геолокации не видна | JS писал в отсутствующий status element | Native live status + RU/AZ/EN ошибки, manual/no-pin fallback; denied/unsupported/granted сценарии |
| Повтор SDK callback создаёт2 карты | Локальный adapter RED maps=2 | Состояние root переиспользуется; повтор maps=1, старые handlers не остаются на другом state |
| Invalid point объявляется выбранной | Latitude999 давала selected status | Numeric range проверяется для отображения точки; server validation неизменна |
| Серверные ошибки скрыты | POST200 с latitude error, но inputVisible=false | Error lat/lng раскрывают панель и поля; неверный ввод остаётся для исправления, error видим |
| Потеря фокуса после confirm | Фокус остаётся в скрытой панели | Возврат на toggle; Space/Enter/Tab и2px focus outline PASS |
| Устаревшее ARIA описание после загрузки SDK | Enabled search продолжал описываться как map unavailable | Ссылка на unavailable description удаляется при восстановлении SDK |
| Offline panel обещает клик по неработающей карте | Пустой canvas320px и инструкция перетаскивать маркер | Canvas/hint скрыты без SDK, кнопка называется «Указать координаты»; при SDK возвращаются map labels |
| Shared geographic indicator объявляет999 выбранной | Rendered error PNG, browser RED и новая JS regression FAIL | Только qualified valid point считается выбранной; invalid latitude/longitude/Infinity и валидные0/0 покрыты |

Первопричины находятся в `change_form.html` (conditional local JS), `kidsmap_place_location.js` (state/availability/errors/focus), `kidsmap_place_form.js` (manual toggle), `section_location.html` (status/error visibility), `kidsmap_place_form.css` (38px/overflow), `location_resolution.js` (nonempty strings вместо валидного индикатора). Shared resolver изменён только в отображении point label, без изменений fetch/serial/cancel/географических правил. Asset versions обновлены для изменённых ресурсов.

## PASS / FAIL / NOT RUN

| Проверка | Итог | Границы |
|---|---|---|
| Matrix RU/AZ/EN×360/390/768/1024/1280/1440 | PASS162 | Text, no-key Enter/fallback, manual focus/repeat/Tab, open/closed panel geometry, Range clipping, native draft/reload;0 pageerror/local HTTP≥400 |
| Новые fallback/error labels RU/AZ/EN | PASS15 |5 фраз сравниваются с ожидаемыми rendered текстами/атрибутами для каждого языка |
| Keyboard/focus/offline panel | PASS8 | Space/Enter/Tab, возврат фокуса, видимые поля без перекрытия footer на360/390/1440, нерабочая map hint скрыта |
| Manual point, range/pair errors, clear, stale tabs, moderation | PASS12 | Неверный ввод сохраняется, stored candidate не повреждён; stale tab не восстанавливает cleared point |
| Rendered invalid point/error visibility | PASS4 | Два индикатора не объявляют999 выбранной; input/error видим и999 остаётся для исправления |
| Create→draft→reload→publish without point | PASS7 | Native новая карточка; главная фотография сохраняется; координаты пусты |
| Public card without point390/1440 | PASS2 | HTTP200, адрес отображается |
| Shared Event admin render390/1440 | PASS2 | HTTP200/0pageerror; это smoke GET, не повтор полной Event приёмки |
| Late SDK callback/repeat | PASS1, simulation | Локальный Map/Autocomplete adapter; actual Google NOT RUN |
| Geolocation feedback/manual/no data loss | PASS9 | Denied/unsupported — local browser API adapters; granted — native Chromium geolocation с synthetic coordinates. Physical GPS NOT RUN |
| Existing admin/readiness/photo server regressions | PASS107,64.947s | Свежий PostgreSQL прогон после первых исправлений |
| Final error-template/admin photo subset | PASS14,15.998s | Повтор после ошибок координат; после него только JS/CSS/asset/query/labels и display point qualification, Python source прежний |
| Shared location JS tests | PASS7,exit0 |5 существующих +2 новых; RED7:6PASS/1FAIL, затем GREEN7/7 |
| Full project/backend/JS suites | NOT RUN | Здесь targeted scope,107 уникальных серверных тестов,14 повторно |
| Real SDK/key/auth/geocoding/device GPS/Screen reader/Safari/Firefox | NOT RUN | Внешние интеграции и реальные устройства не запускались |

Финальный browser inventory:222 PASS/0FAIL. Предшествующие RED и прерванные собственные harness runs отделены от финального результата в evidence. В исходном negative harness `.errorlist` не находил custom `.km-pf-field__error`; это исправлено в QA script. Попытка одобрения после очистки без выбора города/района была неверной последовательностью, а не новым бизнес-дефектом: очистка точки намеренно инвалидирует полученную по ней географию. Финальный сценарий явно выбирает адресные город/район, затем сохраняет, отправляет и одобряет. Это правило не менялось; тест дополнительно подтверждает invalidation.

Новая карточка без точки опубликована и открыта публично. Существующая точка вводилась/подтверждалась и сохранялась, затем явно очищалась; stale tab не восстановила её, cleared candidate прошёл native submit/review и published lat/lng остались NULL. Публикация без точки не освобождает от действующих требований адресной географии. Никакого прямого изменения organization_id, расширения ролей или обхода canonical transitions нет.

## Скриншоты и воспроизведение

[PC](admin-place-map-fix-2026-10-09/screenshots/green-1440.png), [mobile](admin-place-map-fix-2026-10-09/screenshots/green-390.png), [manual focus](admin-place-map-fix-2026-10-09/screenshots/manual-focus-390.png), [offline open](admin-place-map-fix-2026-10-09/screenshots/offline-open-390.png), [server error](admin-place-map-fix-2026-10-09/screenshots/error-coordinates-390.png), [public](admin-place-map-fix-2026-10-09/screenshots/public-no-pin-390.png). Перед/после и полный список — evidence. Скриншоты просмотрены; живая форма и публичная карточка использовались, design-прототипы не засчитаны.

[Browser scripts](admin-place-map-fix-2026-10-09/scripts), [107 log](admin-place-map-fix-2026-10-09/server-tests.log), [14 log](admin-place-map-fix-2026-10-09/final-server-tests.log), [JS RED](admin-place-map-fix-2026-10-09/js-red.log), [JS GREEN](admin-place-map-fix-2026-10-09/js-tests.log).

```bash
node --check static/admin/js/kidsmap_place_location.js
node --check static/admin/js/kidsmap_place_form.js
node --check static/js/location_resolution.js
node --test scripts/test_location_resolution.cjs
.venv/bin/python .tmp/content-completion-20261009/run_unit.py catalog.testcases.admin.TestAdminOwnershipModerationUX catalog.testcases.place_readiness catalog.testcases.test_admin_candidate_cover
.venv/bin/python .tmp/content-completion-20261009/run_unit.py catalog.testcases.place_readiness.PlaceAdminFormReadinessTests catalog.testcases.test_admin_candidate_cover
.venv/bin/python .tmp/ce-map-final-20261009/launch.py
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py locale-labels
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py matrix
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py negative
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py bad-point
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py keyboard
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py focus-visibility
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py offline-panel
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py sdk-repeat
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py geolocation
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py lifecycle
.venv/bin/python .tmp/ce-map-final-20261009/run.py --script final_contract.py
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py public
.venv/bin/python .tmp/ce-map-final-20261009/run_browser.py shared-event
.venv/bin/python .tmp/ce-map-final-20261009/package.py
```

Launcher и guards проверены. Для воспроизведения нужен этот synthetic stand; scripts содержат собственные fixture IDs, а не production URLs. При новой lifecycle карточке обновить final_contract/public path перед public probe. Не переносить результаты на production. Codebase Memory использован как историческая навигация; static/template/current behavior подтверждены source/DOM/исполнением, не графом.

CE-C-03 и CE-C-04 — FIXED LOCAL. Подтверждённых OPEN в проверенном административном map scope не осталось. Реальные external integrations и общий project sign-off остаются NOT RUN, не объявлены работающими. Own active_run закрыт, stand8790 оставлен; чужие изменения сохранены.
