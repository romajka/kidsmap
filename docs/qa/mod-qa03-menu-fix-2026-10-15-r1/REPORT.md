# MOD-QA-03 menu supplement — scoped LOCAL PASS; whole ID OPEN

2026-10-15. Одобренное JS-дополнение реализовано и проверено. Только `static/admin/js/kidsmap_place_changelist.js`; прежний CSS27line fix сохранён. **Closed historical IDs: []**: сортировка Event/Specialist и неподтверждённая поддержка их column controls не выдаются за исправленные. [Следующий конкретный PLAN сортировки](SORT_IMPLEMENTATION_PLAN.md) требует отдельного approval; backend здесь не менялся. Full ACCEPT-08 NOT RUN.

## Snapshot и approval

Checkout `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, active_run NONE. [entry.json](entry.json):31777existing files,70existing containers,1known live HTTP at entry. [Approval](approval.json): человеческое «одобряю» относится к MENU_SUPPLEMENT_PLAN.md предыдущего run, только одному JS-файлу. Изменения других задач/отчётов сохранены; новый app file не создавался. One lead, роли frontend-admin/browser-qa/integration-reviewer выполнялись последовательно, независимые агенты не заявляются.

Сначала применён exact approved f51eac… candidate, [applied-approved.diff](applied-approved.diff). Реальные проверки Tab/resize выявили недочёты его implementation. В том же согласованном keyboard/scroll/resize scope исправлены non-Node event.target guard, initial focus первого доступного Place action и игнорирование запоздавшего scroll notification при неизменном положении trigger. Новых файлов/доменов/действий/permissions/labels не добавлялось. [Within-scope refinement](within-scope-refinement.json), [pending scroll refinement](pending-scroll-refinement.json), [final app diff](applied-final.diff). Не утверждается, что финальные байты идентичны первоначальному prototype; исходный и промежуточные варианты сохранены. Эти доработки выполняют уже одобренный контракт, не требуют повторного approval того же scope.

## Изолированный runtime и source

Новый профиль `.tmp/mod-qa03-menu-fix-2026-10-15-r1`, DB/user `mod03_menu_fix_r1`, PostgreSQL46731, HTTP57187, own container/volume `mod-qa03-menu-fix-2026-10-15-r1-pg`.175migrations, Python3.12.3/Django6.0.2; copied hash-verified own pypdf6.20.1, shared installed packages read-only.1fictional admin+3Place+3Event+3Specialist, собственные cache/media/private-media/email. DJANGO_TESTING=1, env очищен, checkout `.env`/production credentials не загружены. Socket guard разрешает только свой PG, browser routing разрешает только свой origin; внешние fonts intentionally blocked. Это не host-wide firewall.

Текущие RU/AZ/EN PO собраны отдельно build0/verify0, [manifest](locale-manifest.json), sole own LOCALE_PATHS до django.setup. Shared MO не перезаписаны.953actual source hashes, реальные Python/template origins и3own MO подтверждаются runtime/source; installed Django/allauth/jazzmin22catalogues учитываются отдельно, не считаются checkout locales. [Runtime-info](runtime-info.json), [final runtime source](runtime-source-final.json), [server-current.json](server-current.json). Own loopback/testing-only checkpoint endpoint пишет только QA evidence в новый run; не добавлен в application urls/source, не меняет domain records.

## Meaningful RED → GREEN

Fresh before JS patch на проверенном собственном предыдущем profile: [native-red.js.result.json](native-red.js.result.json),12observations=7PASS/5sourceFAIL,0NOTRUN. Подтверждены выход Place last-row menu за нижний край и clipping Event panels.

После exact initial JS: [native-edge.js.result.json](native-edge.js.result.json),20corePASS/1TabFAIL; [native-resize-red.js.result.json](native-resize-red.js.result.json),1PASS/1FAIL с реальным TypeError `contains` для non-Node resize target. После первой доработки resize2PASS retained; Tab ещёFAIL [native-edge-green.js.result.json](native-edge-green.js.result.json). После устранения stale scroll: [native-edge-final.js.result.json](native-edge-final.js.result.json) **21PASS**. Все исходные FAIL сохранены; assertions не ослаблялись.

Actual final JS, без injected CSS/JS/response substitution:

- [RU](native-menu-ru.js.result.json), [AZ](native-menu-az.js.result.json), [EN](native-menu-en.js.result.json): **397PASS каждый, всего1191PASS/0FAIL/0NOTRUN** в rows.72base cells (2queues×3locale×6width×2sidebar),60interactive cells,180first/last popup states,12native mobile overlay states.12mobile-expanded backdrop boundaries и9fitting-table scroll boundaries явно NOT RUN в отдельном boundary array: скрытый фон не нажимали, scroll dismissal не объявлен там, где таблица не двигается.
- Проверены geometry/hit-test/root, readiness и actions, keyboard Enter/visible focus/Escape/точный возврат trigger focus, outside click, native scroll/resize, повторное открытие, Event focus leaving, same-node portal и восстановление исходного parent/style/href/labels, отсутствие body portal после закрытия. Ни одна domain action не активирована.
- [Shared Place controls](native-shared-place.js.result.json):79PASS; [shared Specialist smoke](native-shared-specialist.js.result.json):61PASS. Native search/empty/reset, keyboard focus и horizontal scroll, filter drawer, поддерживаемые Place columns, reload. Известный broken Specialist sort не подменялся и не объявляется GREEN; unmatched Event/Specialist column targets отдельно NOT RUN.

Итого accepted current-source1352PASS observations =1191matrix+21finaledge+79+61shared. Прежний CSS1121PASS retained, весь его корпус не повторяли. Все own domain before/after fingerprints unchanged; console/network raw сохранены, намеренно blocked fonts отделены от local/page errors. [verification.json](verification.json) содержит точные counts/gates/границы. Сохранены checkpoints по каждому языку для защиты evidence при interruption.

## Оставшиеся причины

[Fresh sort recheck](native-sort-current-recheck.js.result.json):2ожидаемых sourceFAIL,1matching row до sort, `?e=1` после native sort у Event/Specialist. Это не регрессия меню; причина была подтверждена до patch и сохраняется. [SORT_IMPLEMENTATION_PLAN.md](SORT_IMPLEMENTATION_PLAN.md): четыре точных proposed files, backend0changes, ждём нового scope approval. Исторические MOD04–08 просмотрены только по заголовкам для исключения неправильного alias; их задачи не начинались. Прочие NOT RUN не закрываются этим отчётом.

## Interruption и preservation

Во время начальных probes пришёл turn_aborted. На повторной проверке own PID764876 уже отсутствовал; перезапущен только собственный новый profile, current PID774118. Его старые server/source manifests сохранены. Единственный entry foreign HTTP711181 после interruption также отсутствует: сохранность **NOT VERIFIED**, чужой HTTP не перезапускался. Предыдущая граница8HTTP и ещё более ранняя4HTTP не переобъявляются PASS.70entry containers сохраняют ID/state/ports, own71st PG added, исходные31777files кроме approved JS (и собственного status-guide дополнения в конце) проверены по bytes. [Preservation](preservation-before-status-update.json), [verification](verification.json). active_run NONE не присваивался. Никаких reset/clean/stash/commit/push/deploy/production.

[commands.jsonl](commands.jsonl) — exact test/setup argv/exits/durations. node --check current JS0; собственные evidence scripts AST check, final metadata gates и PNG hashes/dimensions указаны в verification. [PNG manifest](png-manifest.json) разделяет RED/intermediate/final actual evidence; SIMULATED source в acceptance не используется. Ручной просмотр3representative PNG описан отдельно, не утверждается просмотр всех кадров.

**NOT RUN:** полный module08/глобальный корпус/production, исправление sorting и его backend tests, full role/permission matrix (само permission behavior не менялось), negative unpublished/no-coordinate action branches (fixture три published), прочие MOD04–08. Closed IDs остаются[]. После menu fix возможен только отдельный PLAN/approval новой причины, не автоматическое implementation sorting.

## Финализация 2026-10-16 после последнего interruption

Browser evidence относится к2026-10-15; полный corpus заново не запускался. Fresh финальная сверка31777entry files: **31775unchanged**, изменились только approved JS и собственный guide note/link, missing0.953source hashes по-прежнему совпадают с реально проверенным runtime-source-final-start.json; JS final SHA `671f7b6a772e7f459eb90a322875cb285892586e8321ceaf9be2a4c9d491da85`. [preservation-final.json](preservation-final.json), [finalization-context.json](finalization-context.json). runtime-source-final.json — сохранённый actual runtime snapshot15октября, не утверждение живого процесса16октября.

Own PID774118 после последнего interruption отсутствует и не перезапускался при финализации. Entry foreign HTTP711181 также отсутствует. Все70entry container IDs существуют; у57совпадают также state/ports, у13есть отличия — [container-drift-final.json](container-drift-final.json). Причина внешних изменений не установлена, чужие процессы/контейнеры не перезапускались и не чистились. Сохранность runtime/state этих стендов **NOT VERIFIED**; более ранняя успешная проверка70контейнеров не подменяет текущую границу. Перед новым тестовым запуском нужна новая проверка/собственный профиль.

Final metadata gate: **23PASS/0FAIL/3NOT VERIFIED** (container state, foreign HTTP, own HTTP after interruption).266PNG с SHA/dimensions:192final matrix,12final edge,24shared controls,12RED,24intermediate retained,2OPEN sorting recheck. Native scoped1352PASS retained;2sort sourceFAIL остаются OPEN. Final app изменения только согласованный JS; CSS и backend сохранены. Новая4file backend-реализация сортировки/test file НЕ начата. Нет production/commit/push/deploy, active_run NONE.
