# SITE-QA-08: свежая проверка и конкретный план — 2026-10-18

**SITE08/P2 CONFIRMED OPEN; exact2file PLAN READY / approval pending. Приложение не изменено.** Модуль10 остаётся14OPEN (10P2/4P3), full acceptance pending. [План](IMPLEMENTATION_PLAN.md), [точный diff](proposed.diff), [кандидат/SHA](candidate-manifest.json), [проверки](verification.json).

Lead frontend-admin, сверка kidsmap-orchestrator выполнены /root inline по canonical definitions; независимого исполнения специалистами не было. Scope: заполненные общие settings forms, их responsive bounds и доступность штатных mobile actions у editable. LOCAL HEAD `852938d96764ae315b92859e3651e5ea62054a36`, branch `codex/module09-transfer-2026-10-16-r1`, исходная точка — dirty WORKTREE. Production UNKNOWN/не контактировали.

## Что подтверждено

На новом source-guarded стенде33570, текущих3root locale и синтетической fixture RU360 branding document.scrollWidth=1097 при viewport360; input600px, file widget1029.9px. Существующий shell grid/fieldset сохраняет auto minimum. Файловая clear-checkbox попадает под boolean `:has(input[type=checkbox])` rules (`flex:none !important`, `max-width:none !important`); Select2 имеет intrinsic/inline ширину322px и min-width200px. У boolean help блока аналитики это же правило даёт1095.66px. В root остальных shared consumers отсутствует Bootstrap col-12; активный base оборачивает его в flex.row. На≤760 shell скрывает action card, а общей форме не добавляет alternative mobile buttons. Исторические26 FAIL не выдаются за текущий счёт.

Source: shared_settings_change_form.html:6–8/15/86–119/125–139; kidsmap_admin_form_shell.css:634–646/936–1000/3112–3195; actual registry в evidence/static-runtime.json содержит9потребителей. Graph C-kidsmap ready, generation2026-10-16, metadata_changed/coverage_unavailable и partial CSS; использован как подсказка, критические связи проверены source/runtime, graph CALLS0 не интерпретирован как отсутствие потребителей.

## Предлагаемое изменение

Ровно2application files: общий шаблон получает собственный CSS link, marker и col-12; новый `static/admin/css/pages/kidsmap_settings_forms.css` ограничивает intrinsic/grid/file/Select2/boolean-helper размеры и переносы. Штатные mobile buttons показываются только через marker от Django has_change_permission. Общая shell CSS, Place/Event templates, JS, backend, права, модели, schema, PO и revision/save semantics остаются прежними. SITE21 column для каталога сохраняется. Readonly mobile hidden state сохранён; SITE20 desktop readonly buttons и SITE11 copy остаются отдельными OPEN.

## Выполненные проверки

Native Chromium/Playwright CLI,9active forms ×AZ/RU/EN ×360/390/768/1024/1280/1440 =162editable cases, плюс18readonly catalogue. После actual-source baseline временно добавлялись ровно marker/col-12 и CSS кандидата; затем полный rollback с точным повторным сравнением геометрии. **Это DOM-прототип, не applied-source GREEN.**

| Набор | Результат |
| --- | --- |
| Final editable baseline,5геометрических checks/cell | 496 PASS /314 FAIL из810 |
| Final temporary editable prototype | 810/810 PASS |
| Final readonly baseline | 90 PASS /0 FAIL из90 |
| Final readonly prototype | 90/90 PASS; mobile actions остаются скрытыми |
| HTTP/language/точный rollback controls | 540/540 PASS |
| Rollback geometry | 180/180 совпадений с baseline |
| Static candidate compile /permission-model roots | 18/18 PASS,9actual consumers |

В final suites нет pageerrors/неожиданных local HTTP4xx. Внешние fonts.googleapis.com блокированы; diagnostic ERR_FAILED сохранены, console-clean не заявляется. Состояние SiteSettings/CatalogContentSettings подтверждено одинаковым hash; admin_log_count0. Auth/setlang работали только на синтетических локальных sessions. 136PNG включают discovery, неудачные прототипы и final. [Визуальный review](visual-review.json), [команды](commands.md), matrix.csv, png-manifest.json.

Первый прототип не устранил file flex:none/Select2; diagnostics и candidate сохранены в prototype-v1. Второй прошёл8pilot cells, но полная162cell матрица оставила17analytics overflow checks; prototype-v2-full и native results сохранены. По диагностике добавлены shrink/caps для boolean help, final assertions усилены проверкой visible help blocks. App fixes не применялись, FAIL не скрывались/не ослаблялись. Первый static inherited render требовал missing request context Jazzmin; harness исправлен на full compile +точный root fragment и не выдаётся за runtime render.

## Целостность, риски и следующий шаг

Все1032source files unchanged, кандидат только внутри QA-пакета;33previous sealed packages/6536files, shared MO/.cbmignore/refs/index/empty staging/active_run NONE и foreign container identities/states сохранены. Guide/MASTER append-only. Нет commit/push/deploy/production. Действуют retained SITE01/15/06/19/21 и module09 composite LOCAL closures.

Собственная normal/test DB/cache/media/private-media/email, env clear до setup, read-only repo bind, текущие3locale в own path, внешние integration выключены. Browser prototype не проверяет реальную загрузку нового static asset, native save/upload/error/retry/public values или backend regressions: всё это **NOT RUN** сейчас и включено в точный future acceptance в плане. Full accessibility/global/module11 также NOT RUN. Самостоятельного разрешения на иные fixes этот отчёт не даёт.

Следующий шаг: одобрить конкретный proposed.diff/2files, затем fresh own source RED→exactapply→actual-source GREEN, native mobile saves/errors/files/Select2/ACL и105backend regression methods. AGENTS.md требует «Future implementation requires a concrete plan and user approval for its scope». Текущее «дальше» продолжает recheck/PLAN; прошлое одобрение SITE21 не распространяется на этот scope.
