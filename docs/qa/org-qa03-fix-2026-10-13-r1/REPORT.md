# ORG-QA-03 — перенос панели: LOCAL repair evidence

2026-10-13 Asia/Baku; root, kidsmap-orchestrator `.agents/agents/kidsmap-orchestrator/agent.md`, sequential execution. Scope approved by «одобряю»: [PLAN](../module02-remaining-recheck-2026-10-13-r1/PLAN-ORG-QA-03.md). Production NOT RUN.

## 1. Состояние области

Причина ORG-QA-03 исправлена: форма и её правая группа controls допускают перенос; меню не маскируется global overflow:hidden. Точный application diff только `static/admin/css/pages/kidsmap_changelist.css`: flex-wrap базового search form, flex-wrap/max-width toolbar-right и комментарий. Полная приёмка module02 ещё NOT RUN/IN PROGRESS; новый отдельный ORG-QA-05 OPEN ниже.

LOCAL `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +dirty WORKTREE, active_run NONE. [entry.json](entry.json) сохранён до edits, [entry-final.json](entry-final.json) — текущий source snapshot (включает одновременно одобренные AZ/EN edits второго плана). Services/ACL/CAS/ownership/connect transports и чужие source/test changes не изменены этим запуском.

Собственный runtime `http://127.0.0.1:58417`, PID50295, DB orgqa03_20261013_r1, shared только свой PG container module02-remaining-recheck-2026-10-13-r1-pg на127.0.0.1:35715. [Source/runtime](runtime-version-final.json), fresh isolated [RU/AZ/EN manifest](locale-manifest.json), own cookies/cache/media/private-media/email/browser session, DJANGO_TESTING=1, no checkout .env, egress blocked кроме своего PG. Copy of fictional baseline DB only. Чужие процессы/active_run сохранены.

## 2. Сильные стороны / executed

До patch: [recheck](../module02-remaining-recheck-2026-10-13-r1/recheck.result.json) RU/AZ/EN1024 document overflow +194/+122/+109. После patch [browser.result.json](browser.result.json): **84 PASS, 0 FAIL, pageerrors0, local network errors0**. 36 RU/AZ/EN×6widths×sidebar geometries, 24 native search/keyboard selection/target/preview/cancel/sort/filter assertions и24 affected shared-consumer renders (Event, Specialist, PlaceOwnershipRequest, PlaceReview ×3langs×768/1024). Native preview/cancel readback [no-mutation-readback.json](no-mutation-readback.json): 3 fictional Places не подключились, owner IDs неизменны, READ ONLY с timeouts.

Первый controls probe отдельно: `controls.result.json` — 24PASS/6NOT RUN из-за wrong selector для columns, не acceptance columns. Mobile table parent overflowX auto, scrollWidth900>client324; существующий локальный table scroll сохранён. Search input focus визуально задаётся parent border, buttons/summary outline; сведения о фокусе в этом JSON.

## 3. Реальные проблемы

Нативное нажатие checkbox выпадающего меню columns на390 обнаружило clipped popup. Второй controls attempt завершился CLI no-result/timeout; не PASS. [columns-baseline.result.json](columns-baseline.result.json): исходный CSS, соответствующий entry hash, и patch дают одинаковый x=-31.296875. Новая причина **ORG-QA-05 / P2 / baseline**: меню шириной170 right-aligned к кнопке, которая на переносе стоит слева; checkbox вне viewport. [План](PLAN-ORG-QA-05.md) ждёт отдельного approval. Не переименовывать baseline в regression ORG-QA-03 и не засчитывать full module PASS.

## 4. Tech debt

Shared admin CSS имеет viewport и content-width зависимости; текущий diff не переустраивает design system.

## 5. Risks

Старые recheck runtime source snapshots становятся историческими после edits; чужие/старые процессы не перезапускались. Новые own profiles проверены отдельно. Font requests blocked — не внешняя визуальная интеграция. Принятие84 assertions не означает доступность всех dropdown states; columns FAIL сохранён отдельно.

## 6. Dead/legacy

Не исследовано, ничего не удалялось.

## 7. Tests gaps / NOT RUN

CSS mirror tests не добавлялись. Full248 module tests подготовлены по discovery, запуск отложен до завершения согласованных locale corrections, чтобы не повторять full runs. ORG-QA-05 mouse/keyboard/full viewport GREEN NOT RUN. Production/commit/push/deploy NOT RUN.

## 8. Handoff

Основной nowrap defect устранён и доказан. Полное закрытие условий панели/модуля ожидает ORG-QA-05 отдельный scope. Не менять service/API/ownership. Продолжение в `../module02-full-2026-10-13-r1/`.

## 9. Priorities

ORG-QA-03 P2 root repair выполнен; полный module acceptance не выставлен. ORG-QA-05 P2 OPEN. Отдельных P0/P1 не установлено.
