# Module02 — оставшиеся ORG-QA-03 / ORG-QA-04: свежий recheck и планы

2026-10-13 Asia/Baku. Execution identity root; каноническая роль kidsmap-orchestrator `.agents/agents/kidsmap-orchestrator/agent.md`. Последовательный запуск, независимые специалисты не заявляются. LOCAL ONLY; production UNKNOWN / NOT RUN.

## 1. Состояние области

**ORG-QA-03 CONFIRMED OPEN (P2), ORG-QA-04 CONFIRMED OPEN (P3).** Application implementation и полная ACCEPT-02 NOT RUN. Пользователь поручил завершить весь модуль; подготовлены два конкретных плана оставшихся исправлений, ожидающие approval конкретных файлов/copy согласно AGENTS.md. ORG-QA-01 и ORG-QA-02=ACCESS-QA-03 ранее LOCAL scoped accepted, повторные patches не выполнялись.

Checkout `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, active_run NONE. [Entry snapshot](entry.json) включает исходные source hashes/dirty; [verification](verification.json) подтверждает все application/locale/existing tests неизменными и 215 файлов предыдущего NETWORK-GRANT-UI run сохранёнными. Не commit/push/deploy.

Новый собственный stand `http://127.0.0.1:43073`, PID32502, unique container `module02-remaining-recheck-2026-10-13-r1-pg`, PostgreSQL17.10, explicit loopback `127.0.0.1:35715`, собственная fresh DB `module02remaining_20261013_r1`. Без копирования чужой DB/.env/credentials. Synthetic admin/owner/org/Place fixture seed в собственном run; секреты generated и находятся только в ignored `.tmp` mode600. Уникальные cookies/cache/media/private-media/email/browser session, DJANGO_TESTING=1. Python runtime очищает inherited env и блокирует исходящие подключения кроме своего PG. Browser блокирует внешние URL. Свежий [locale manifest](locale-manifest.json), helper build/verify exit0, sole LOCALE_PATHS до setup; shared PO/MO неизменны. [Runtime source match](runtime-version-final.json).

## 2. Сильные стороны

Обе гипотезы проверены текущими источниками и реальным browser, без переносимых исторических портов/PID. Девять [PNG с hashes](png-manifest.json); source inspection отдельно от rendered evidence. Codebase Memory project `home-ramin-kidsmap`, ready, indexed2026-10-13, path coverage metadata_match для business.py/CSS/search include/editor template; graph только navigation, факт по source/browser. Context7 использован для актуального named-session CLI.

## 3. Реальные проблемы

**ORG-QA-03:** admin Place selection `/admin/catalog/place/?q=QA02+LOCAL+BULK` на1024×950, sidebar open. [recheck.result.json](recheck.result.json): RU document1218 (+194), AZ1146 (+122), EN1133 (+109). Toolbar660, form630, formScroll871/799/786; computed flexWrap nowrap. Причина `static/admin/css/pages/kidsmap_changelist.css` базовое `.km-toolbar #changelist-search.km-search-form`, wrap только media<=900. Confidence high; локальный baseline defect, новая regression не установлена.

Временный QA addStyleTag (не application patch) wrap формы дал35PASS/1FAIL в36 cells: наRU768/open сама группа sort/columns шире формы (397>382). [Первый probe](layout-probe.result.json) сохранён. Уточнение добавляет wrap/max-width для `.km-toolbar-right`; [refined probe](layout-probe-refined.result.json) **36/36 geometry PASS** RU/AZ/EN×6 widths×две sidebar позиции. В screenshot names `*-proposed-wrap.png` сохранён последний refined preview; первый probe геометрия остаётся JSON, его первоначальные preview PNG были заменены refined preview в этом собственном run. Это feasibility proof плана, не acceptance исправления. CSS не записывался в application.

**ORG-QA-04:** admin organization add/edit, AZ/EN русские headers/tab/sections. [Browser recheck](recheck.result.json), [same-process copy proof](copy-proof.json): 15 source strings возвращают RU; 14 exact msgid отсутствуют в AZ/EN PO, `Одобрить заявку` существует fuzzy и не входит в compiled catalogue. Lazy section/model/readonly labels реагируют на override в одном процессе; frozen labels не причина. Source: OrganizationAdmin.editor_sections, BusinessEditor badges, Organization._meta verbose_name_plural, business/change_form template. Scope — эти15 strings, [точные AZ/EN тексты](proposed-copy.json). Другие русские sidebar строки не включены автоматически. Confidence high, P3, без изменения data/moderation contracts.

## 4. Tech debt

Оставшийся общий translation debt вне15 entries не исправлялся. Общий CSS shared между пятью changelists; affected consumers перечислены в плане, потребуют проверки после patch.

## 5. Risks / сохранность

Входные source hashes полностью совпадают; чужой WORKTREE и active_run сохранены. Прежние stand processes были отсутствующими до этого запуска и не перезапускались. Работа касается только собственного нового profile. Возможные новые findings полной ACCEPT-02 нельзя молча включать в два плана. Общие translated msgid затрагивают несколько admin consumers; точечные проверки обязательны.

## 6. Dead/legacy candidates

Не исследовались, удаления не выполнялись.

## 7. Tests gaps и ограничения

Полная ACCEPT-02, native connect/preview/cancel lifecycle, все candidate states/mutation/readback, post-patch GREEN, full project discovery, production и реальные external integrations NOT RUN. Recheck не заменяет acceptance. Browser pageerrors0; local404 `/accounts/profile/` — default admin-login redirect, не одна из проверяемых страниц и не причина findings; authenticated admin edit/list pages доступны. Внешние browser requests blocked. Geometry probe не доказывает keyboard/control lifecycle.

Целевой baseline: **4 tests PASS, exit0, 4.824s**, [targeted-baseline.txt](targeted-baseline.txt): `catalog.testcases.test_organization_admin_labels` (2), `catalog.testcases.test_task33_admin_editors.AdminEditorTests.test_organization_admin_draft_and_submit_use_candidate`, `...test_pending_editor_shows_current_and_candidate_separately`. Existing assertions unchanged. Warning об отсутствующем собственном staticfiles каталоге — environment configuration warning; runserver обслуживает repository static через isolated profile. Полный корпус не запускался.

## 8. Recommendations / handoff

[PLAN-ORG-QA-03](PLAN-ORG-QA-03.md): только CSS в двух правилах и QA evidence. [PLAN-ORG-QA-04](PLAN-ORG-QA-04.md): только15 entries в AZ/EN PO и QA evidence. Исправления требуют одобрения конкретных plans; общее поручение завершить модуль уже принято, его повторно спрашивать не нужно. После этих двух работ — один полный ACCEPT-02 по guide, audit-only; не запускать модуль03 автоматически.

## 9. Приоритеты

P2 ORG-QA-03: инструменты массового выбора обрезаются. P3 ORG-QA-04: смешанный язык затрудняет редактор. Оба OPEN, plans ready. Новых P0/P1 не заявлено, module02 PASS не выставлен.
