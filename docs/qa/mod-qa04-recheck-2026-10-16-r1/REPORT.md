# MOD-QA-04 — PLAN COMPLETE / CONFIRMED OPEN

2026-10-16, `/root`, canonical kidsmap-orchestrator +frontend-admin/browser-qa последовательно; независимые агенты не запускались. Это read-only recheck и план, приложение для MOD04 не менялось.

Фактический `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +dirty WORKTREE, active_run NONE. [Snapshot](snapshot.json), [runtime source](runtime-source-final.json), [verification](verification.json). Production NOT RUN.

Повторно использован только собственный текущий columns QA profile после проверки ownership/runtime/source/isolation: HTTP60617/PG47955, ownDB/cache/media/private-media/file-email, DJANGO_TESTING=1, source957MATCH. Собственные свежие RU/AZ/EN build/manifest заново verified, единственный LOCALE_PATHS. Checkout.env/production credentials не читались, внешние ресурсы blocked; fictional fixtures. Новый setup/DB reseed/full suites не запускались. Ограничения непрерывности старых стендов после сбоя окружения описаны в предыдущем [columns REPORT](../mod-qa03-columns-fix-2026-10-16-r1/REPORT.md); в этом recheck никаких lifecycle операций нет.

**18cells:** RU/AZ/EN×360/390/768×dashboard/Place. Native closed menu→opener focus→Enter→Escape. **18sourceFAIL,38controlPASS**,0local errors, domain fingerprint before/after unchanged. [Actual browser JSON](native-recheck.js.result.json), [commands/exits](commands.jsonl),18PNG с [hash manifest](png-manifest.json). RU390 Place PNG просмотрен визуально. Raw opened768 может содержать transition geometry; sourceFAIL основан на escaped350ms/settled screenshot, не на промежуточном width.

После Escape sidebar остаётся открыт. На360/390 header opener находится под sidebar; pointer hit идёт в панель. На768 current layout persistent, opener доступен после transition, Escape всё равно не сворачивает навигацию. Overlay/повторный Enter продолжают закрывать её. Внутренней close-кнопки нет. Текущий kidsmap_admin_sidebar.js обрабатывает accordion и clear-search, outer Escape/focus integration отсутствует; vendor PushMenu получает только штатный toggle.

Положительный контроль: действующий opener/overlay переключают sidebar; accordion и permissions имеют существующее отдельное покрытие. Приватные данные и бизнес-модели для плана не затрагиваются. Dead/legacy cleanup не предлагался, удалений нет.

[Конкретный implementation plan](IMPLEMENTATION_PLAN.md) — **4файла**, approval pending:

1. `static/admin/js/kidsmap_admin_sidebar.js` — Escape/close/overlay restore-focus/aria state adapter через существующий opener.click().
2. `src/catalog/templates/admin/catalog/includes/sidebar_navigation.html` — явный локализованный close-button внутри sidebar.
3. `static/admin/css/pages/kidsmap_admin_sidebar.css` — только mobile close placement и видимый keyboard focus.
4. NEW `src/catalog/testcases/test_admin_sidebar_escape.py` — meaningful rendered-control regression; поведение проверяется native browser.

План содержит code contract, RED→targetedGREEN и выборочные shared guards; existing full column/search/sort suites не повторять. Используются existing PO key «Закрыть» (RU Закрыть/AZ Bağla/EN Close) и существующий kmi-close. Sidebar не объявляется dialog; отдельный focus-trap/inert контракт не добавляется. На desktop Escape вне sidebar/editor не должен менять его состояние, вложенный prevented Escape имеет приоритет.

**P2 CONFIRMED OPEN.** NOT RUN: MOD04 patch/postpatchGREEN, full module08/global/production/commit/push/deploy. Следующий шаг — approval именно этого четырёхфайлового плана. Одобрение MOD03 не переносится; повторно согласовывать после approval не нужно. MOD05–08/module09 автоматически не исправлялись.
