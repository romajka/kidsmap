# Module07 ACCESS-QA-01 — focus lifecycle implemented; OPEN pending CSS scope

2026-10-14, Asia/Baku. Один `/root`, последовательно канонические kidsmap-orchestrator/frontend-reviewer/browser-qa; независимых специалистов не запускал. Режим APPROVED IMPLEMENT последнего [конкретного плана](../access-qa01-recheck-2026-10-14-r1/IMPLEMENTATION_PLAN.md), разрешение пользователя «начни испарвлять модуль 7» в этой переписке. [Approval record](approval.json). Новые планы ACCESS02/04/05 этим не одобрены.

## Что изменено и что остаётся

Только application file `src/catalog/templates/auth/login.html`: actual opener, восстановление прежних inert атрибутов background, dynamic Tab/Shift+Tab по видимым enabled controls, focusin guard, Space на opener при сохранении href/noJS, cancelable initial-focus readiness, loading focus, visible success action и доступное имя success dialog. Закрытие Escape/крестиком/backdrop/успехом возвращает focus. [Reviewable diff](repair.diff), [loaded source](runtime-source-final.json).

**ACCESS-QA-01 остаётся OPEN.** Управление фокусом прошло GREEN, однако submit не показывает видимый keyboard indicator на всех18 cells. [Visible-focus54](visible-focus.js.result.json):36PASS/18FAIL. Higher specificity `.page-account_login .auth-form > .btn` в `static/css/site.css:22797` перекрывает общий focus shadow; actual outline/shadow/background/color до/после одинаковы, хотя `:focus-visible=true`. Expanded native probe border/transform/filter/::before тоже не изменяются. CSS в исходном одобренном плане исключён; он не исправлялся автоматически.

Для завершения ID нужен [CSS_SUPPLEMENT_PLAN.md](CSS_SUPPLEMENT_PLAN.md): один scoped rule с outline3px и offset3px для submit, один дополнительный файл `static/css/site.css`. Это конкретное дополнение scope с причиной, кодом и targeted acceptance; approval ещё не получен. Existing assertions не ослаблены ради GREEN.

## Snapshot / сохранность

Фактический root `/home/ramin/kidsmap`; `task33-progress`; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` + dirty WORKTREE; `active_run: NONE`. [Entry](entry.json):27487file hashes, включая3ignored shared MO,5 актуальных прежних QA processes и55container identities. Прежние изменения и артефакты сохраняются; own new files только этот каталог и ignored scratch. Guide изменяет только текущую module07 note. [Verification](verification.json) — integrity/source/locale gate, не PASS18failed focus indicators.

Без reset/clean/stash/commit/push/deploy/production/active_run assignment. Старые стенды не перезапускались. После patch они могут иметь старый cached template/source mismatch; это не утверждение, что они обновлены. Перезапускались только собственные fix PID после точной argv/cwd проверки, [receipts](commands.jsonl). Старый recheck/RED каталог сохранён побайтно.

## Проверки / native exits

**606 accepted-scope observations:588PASS/18FAIL**, [rows](accepted-current-observations.json); это UI observations, не606независимых end-to-end тестов.

- [Current focus162](focus-matrix-r3.js.result.json):162PASS, RU/AZ/EN×360/390/768/1024/1280/1440. Original [RED162](../access-qa01-recheck-2026-10-14-r1/focus-matrix.js.result.json):54PASS/108FAIL, byte-identical original template SHA на entry проверен. Tab/Shift+Tab/inert/Escape/opener/Space/close/geometry GREEN.
- [Effective states324](states-effective.json):324PASS во всех18cells.198 сохранены из11complete stage2 cells по [source provenance](states-forward-provenance.json);126fresh stage3 rows закрыли7remaining cells. Raw stage2 содержит211PASS и timeout повторного focus,13partial AZ1440 rows superseded свежим whole-cell recheck. Остальные unchanged cells и full backend/module corpus не повторялись. Error/loading/success/close handlers byte-identical; changed initial-focus readiness отдельно проверен заново во всех18.
- [Additional RED3](edge-red-fixed.js.result.json) → [GREEN3](edge-green.js.result.json): rapid close, new dynamic background control, late actual success after close. DOM fixture/600ms transport delay явно SIMULATED, actual focus/endpoint настоящие.
- [Boundaries9](boundaries.js.result.json):9PASS; prior inert exact preservation, no-enabled-controls fallback и close; настоящая JavaScript-disabled standalone link→native POST/done RU/AZ/EN390. Synthetic DOM fixture только QA.
- [Native reset54](reset-flow.js.result.json):54PASS, RU/AZ/EN390/1440,6different fictional users. Modal actual AJAX POST→собственное локальное письмо→реальная ссылка→native new-password form→old-password login refusal/new-password login→consumed-link denial. Эти переходы не симулировались. Local email backend не real SMTP delivery.
- [Visible focus54](visible-focus.js.result.json):36PASS (success/close),18FAIL submit; computed styles проверены после220ms CSS settling и pointer вне кнопок, PNG. `matches(':focus-visible')` само по себе не считалось visible PASS.
- [Backend](reset-tests.txt):unchanged `catalog.testcases.test_password_reset`,9methods PASS, native exit0,6.157s. Запуск после первого patch, до уточнений initial-focus timing; backend/test/markup contract сохранён, последний template исполняется в current native matrix. Повторный unchanged9-run не выдаётся за новый.
- [READ ONLY own DB](readback.json), statement_timeout10s/lock_timeout2s:6users,175migrations, все old passwords denied/new passwords accepted, transport guard rejects external connect. Только агрегаты/booleans, никаких hashes/passwords/user records в report.

Точные argv/exits/seconds в [commands.jsonl](commands.jsonl). CLI exit0 может сопровождаться semantic FAIL; решают JSON statuses. Первый integrity gate exit1 ошибочно назвал .env.example новым: entry исключала env-named paths, а inventory comparison не повторяла тот же фильтр. Содержимое env не читалось; исправлен только own metadata filter, raw verification-attempt1.json/verification-output.txt сохранены.

First additional RED launcher exit1 попал в profile из-за own previous authenticated session; corrected own initial clearCookies, raw сохранён. No application/assertion change ради него.

## Причина уточнений initial focus

Синхронный focus при CSS `visibility:hidden→visible` не всегда выполнялся. [Diagnostic](focus-open-diagnostic.js.result.json) показывает попытку focus DIV modal с hidden visibility и BODY после inert. Two-frame вариант прошёл162, но на repeated-open одна cell осталась BODY; [reopen diagnostic](reopen-focus-diagnostic.js.result.json) подтвердил hidden visibility на обоих frames. Финальная версия ждёт **actual computed visible**, сохраняет один отменяемый animation-frame handle, guards open/current in-dialog focus. Close отменяет ожидание; CSS transitions сохранены. [Implementation detail](guidance-adjustment.md). Все stage errors/outputs сохранены; source/current focus GREEN не выводится из первой попытки.

## Изоляция и source процесса

Own PostgreSQL17.10 container/volume `access-qa01-fix-2026-10-14-r1-pg`, bind127.0.0.1:37319, DB `access_qa01_fix_r1`, test DB `test_access_qa01_fix_r1`. HTTP127.0.0.1:57061, current PID по [server.json](server.json). Python3.12.3/Django6.0.2, Node20.20.2, Chromium153.0.8010.36, новая session `accessqa01fixr1`. Собственные cookies/LocMem cache/media/private-media/filebased email в ignored `.tmp/access-qa01-fix-2026-10-14-r1`.

DJANGO_TESTING=1 до settings/django.setup; inherited env очищен, manage.py/.env не импортировались. Все credentials/письма/подписанные links только ignored scratch/in-memory. Backend connect/connect_ex разрешён только к own PostgreSQL; browser external requests abort; OAuth/Maps/analytics/IndexNow disabled. AJAX400/network failure/held request — SIMULATED; actual success/reset/auth transitions настоящие. No production access.

Current RU/AZ/EN PO собраны только в новый own каталог helper `scripts/build_isolated_locales.py`, [manifest](locale-manifest.json)/[verify](locales-verify.txt). Sole LOCALE_PATHS verified до django.setup; shared MO не переписаны. Source identity — argv/cwd/PID + startup selected-file hashes, actual imported views/forms paths и **loaded cached login template source SHA**, browser UI и final disk comparison. Это не один echo endpoint.

## PNG / diagnostics / пределы

[PNG manifest](png-manifest.json): current native192scene files (18×10modal/focus/state +6×2confirmation/replay), SHA/dimensions. Same own scene names represent latest captures; stage2 captures повторных scenes не все сохранены отдельными PNG. Raw stage outputs/source checkpoints сохранены; immutable historical recheck PNG вне own folder сохранены. Не объявляются все192GREEN: submit-visible-focus18 показывают FAIL.

Просмотрены originals RU mobile/network, RU1440close/success, final current visible-focus/confirmation/replay; source/jsdom/HTTP200 не заменяли browser transitions. Focus matrix pageerrors/localBadResponses0. Intentional abort/400 отдельно в diagnostics. No screen-reader/Firefox/Safari/physical-device claims.

ACCESS03=ORG02 имеет [module02 accepted evidence](../module02-full-2026-10-13-r2/REPORT.md), повторный patch по historical FAIL не делался. Свежий network lifecycle, ACCESS02/04/05 recheck/fix, ACCEPT-07/full module corpus, global13, real external integrations/SMTP/production и natural token TTL — **NOT RUN**. Module07 PASS не заявляется; module08 не начат.

[Next prompt](next-prompt.txt): сначала одобрить конкретное CSS дополнение либо оставить ACCESS-QA-01 OPEN. После его scoped GREEN — отдельный PLAN ACCESS-QA-02, затем04/05; ACCEPT-07 один раз после задач.
