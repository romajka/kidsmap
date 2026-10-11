# Модуль 10 — свежая приёмка AUDIT ONLY

**Goal:** принять реальные настройки, feature flags и общие страницы на собственном изолированном стенде; без исправлений приложения.
**Architecture:** один /root выполняет canonical orchestrator, Django, frontend-admin/public и browser-qa последовательно. Ownership: только новый QA10, ignored scratch, PG55441/HTTP8823/browser module10-r1 и строка 10 журнала. Старые отчёты — checklist, не свежие доказательства.
**Tech Stack:** текущий WORKTREE, Django/PostgreSQL, native Chromium через playwright-cli.
**Spec:** docs/qa/module-acceptance-prompts.md, канонический промпт 10.

- [x] Snapshot HEAD/branch/WORKTREE/active_run; preservation исходников/чужих файлов/стендов; graph-first/source contracts.
- [x] Новый isolated DB/testDB/cache/media/private-media/email, fictional data, blocked external integrations; runtime соответствует WORKTREE.
- [x] Native admin branding/about/contacts/footer/empty/hero save→reload→public, cache invalidation; errors, длинные тексты, missing images, save failure.
- [x] Native OFF/ON всех существующих section flags; menu/home/catalog/search/map/direct/API/account, data preservation/admin edit, отдельная проверка публикации/архива/удаления.
- [x] RU/AZ/EN ×360/390/768/1024/1280/1440: общие страницы/header/footer/menu/shared controls/404, fallback/language+params, keyboard/focus, loading/error, 200% zoom/contrast/fixed elements, fresh screenshots/console/network.
- [x] Unchanged targeted tests; nine-section report, SITE-QA findings/repair prompts, exact commands/counts/exits/NOT RUN и список собственных настроек; final preservation, только row10 и handoff11. Модуль13 последним.

Аудит завершён с явными NOT RUN. Обнаружен чужой source drift; сохранён, supplemental current runtime и повторные tests/native checks выполнены. См. SOURCE-DRIFT.md.

Аудит завершён с явными NOT RUN. Обнаружен чужой source drift; сохранён, supplemental current runtime и повторные tests/native checks выполнены. См. SOURCE-DRIFT.md.
